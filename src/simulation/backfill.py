"""The ninety-day movement backfill.

Doc 12 §4 and §9; doc 13 §3.1. This module writes the history that makes demand
computable. Three properties matter and each is enforced by construction rather
than checked afterwards:

**1. Every movement carries an explicit ``recorded_at``.** The column's
``server_default=func.now()`` is evaluated by SQLite at insert time, so omitting
the value collapses ninety days onto today and silently invalidates every
downstream number. Timestamps here are always ``clock.now() - timedelta(days=n)``.

**2. The ledger invariant survives.** ``sum(stock_movements.quantity)`` must equal
``stock_levels.quantity_on_hand`` for every product (CI invariant M-16). Rather
than write movements and hope, this module works *backwards from the known final
position*: the caller states where the product should end up, the schedule is
derived from that, and the residual lands in a single opening-balance adjustment
dated one day before the window. The arithmetic then closes exactly.

**3. Demand is designed, not random.** There is no RNG. Day-to-day variance comes
from the weekday/weekend category shape and from the fractional accumulator that
turns a rate like 1.5/day into an integer unit count. The same call produces the
same ledger every time, which is what makes ``expected_signals`` an assertion
instead of a hope.

The backward receipt schedule
-----------------------------
Walking the window from the last day to the first, undoing each day's sales makes
the running position climb as we move into the past. Whenever it climbs above
``reorder_point + reorder_quantity`` a replenishment must have arrived on that
day, so one is emitted and the position drops by ``reorder_quantity``. Forwards in
time this reads as the familiar saw-tooth between the reorder point and the top of
the band — and because the walk *starts* from the target position, the final leg
naturally runs down below the reorder point without a replenishment. That is not a
contrivance: it is exactly the state the threshold-breach scenarios describe, and
the reason the headphones end at 4 units with an unsubmitted draft PO beside them.

Sufficiency
-----------
``sale_event_stats`` and ``sufficiency_of`` exist so this module can *prove its own
output* is dense enough to compute from. They mirror the frozen thresholds in
15-SHARED-CONTRACTS.md §5.4 and are fixture self-verification only. WS-1 owns the
production demand and sufficiency computation; once it lands, its implementation
is the single source of truth and these two functions stay here purely as the
harness's own check.
"""
from datetime import timedelta

import structlog

from src.backend.models import MovementType, Product, StockLevel, StockMovement
from src.backend.services.inventory_service import check_stock_alerts
from src.core import clock

logger = structlog.get_logger()

#: Length of the history window, in days. Doc 13 §3.1.
BACKFILL_DAYS = 90

#: Every row this package writes is stamped so ``reset`` can remove exactly its
#: own work and leave the baseline seeder's rows untouched.
SIM_PREFIX = "SIM-"
SIM_ACTOR = "simulation"

#: Per-SKU average daily demand, doc 13 §3.1. Colgate is deliberately 0.0 — D4
#: (the refusal) needs one SKU with no sales history at all, and a fixture that
#: quietly gave it a trickle of demand would destroy the scenario it exists for.
BASE_DEMAND = {
    "SKU-GRO-0001": 4.0,   # rice        — high velocity, weekend-skewed
    "SKU-ELC-0001": 1.5,   # headphones  — low velocity, weekday-skewed
    "SKU-ELC-0002": 0.2,   # television  — very low velocity, lands on `thin`
    "SKU-HHD-0001": 6.0,   # detergent   — highest velocity, flat and predictable
    "SKU-PRC-0001": 0.0,   # colgate     — no history, reserved for D4
}

_WEEKEND = frozenset({5, 6})  # Python weekday(): Monday is 0

#: (weekday multiplier, weekend multiplier) per category. Each pair is chosen so
#: ``5 * weekday + 2 * weekend == 7.0`` — the shape redistributes demand across
#: the week without changing the weekly mean, so the rate a detector measures
#: still matches the rate this module was asked to seed.
CATEGORY_SHAPE = {
    "grocery": (0.8, 1.5),        # groceries skew to weekends (doc 12 §9)
    "personal_care": (0.8, 1.5),
    "household": (1.0, 1.0),      # "moderate velocity, highly predictable"
    "electronics": (1.1, 0.75),   # considered purchases, made on weekdays
}
_DEFAULT_SHAPE = (1.0, 1.0)

# Hour-of-day for each kind of backfilled movement. Deliveries land in the
# morning, sales are booked at close of trade, and the opening balance predates
# both. Distinct hours keep the intra-day ordering unambiguous.
_HOUR_OPENING = 8
_HOUR_RECEIPT = 9
_HOUR_SALE = 17

# --- §5.4 sufficiency thresholds (frozen) -------------------------------------
_SUFFICIENT_EVENTS, _SUFFICIENT_DAYS = 14, 21
_THIN_EVENTS, _THIN_DAYS = 5, 7


def category_shape(product: Product) -> tuple[float, float]:
    """The (weekday, weekend) demand multipliers for a product's category."""
    category = getattr(product.category, "value", product.category)
    return CATEGORY_SHAPE.get(category, _DEFAULT_SHAPE)


def daily_sales(rate: float, shape: tuple[float, float], days: int, first_day) -> list[int]:
    """Integer sale quantities for each day of the window, oldest first.

    Deterministic: a fractional accumulator carries the remainder forward, so a
    rate of 0.2/day emits a single unit roughly every fifth day rather than
    rounding to nothing, and a rate of 1.5/day alternates 1 and 2. A rate of 0.0
    emits nothing at all, which is the point for Colgate.
    """
    weekday_mult, weekend_mult = shape
    quantities: list[int] = []
    carry = 0.0
    for offset in range(days):
        day = first_day + timedelta(days=offset)
        carry += rate * (weekend_mult if day.weekday() in _WEEKEND else weekday_mult)
        units = int(carry)  # carry is never negative, so int() is floor()
        carry -= units
        quantities.append(units)
    return quantities


def receipt_schedule(
    sales: list[int], target_final: int, reorder_point: int, reorder_quantity: int
) -> tuple[list[int], int]:
    """Derive replenishments by walking the window backwards from ``target_final``.

    Returns ``(receipts, opening_quantity)`` where ``receipts[n]`` is the quantity
    that arrived on day ``n`` and ``opening_quantity`` is the position the product
    must have held before the window began for the arithmetic to land exactly on
    ``target_final``.

    At most one replenishment per day, so a target far above the reorder band
    unwinds over consecutive days rather than stacking several deliveries onto one.
    """
    receipts = [0] * len(sales)
    if reorder_quantity <= 0:
        # Nothing sensible to replenish with; the opening balance absorbs it all.
        return receipts, target_final + sum(sales)

    band_top = reorder_point + reorder_quantity
    position = target_final
    for index in range(len(sales) - 1, -1, -1):
        position += sales[index]          # undo that day's sales
        if position > band_top:
            receipts[index] = reorder_quantity
            position -= reorder_quantity  # a delivery must have arrived that day
    return receipts, position


def sufficiency_of(events: int, distinct_days: int) -> str:
    """The frozen §5.4 verdict for a sale-event count over a day count.

    Fixture self-verification only — WS-1 owns the production computation. Kept
    here so the harness can prove the history it just wrote is dense enough to
    compute from, without importing a module WS-2 does not own.
    """
    if events <= 0:
        return "none"
    if events >= _SUFFICIENT_EVENTS and distinct_days >= _SUFFICIENT_DAYS:
        return "sufficient"
    if events >= _THIN_EVENTS and distinct_days >= _THIN_DAYS:
        return "thin"
    return "insufficient"


def sale_event_stats(
    db, product_id: int, *, window_days: int = BACKFILL_DAYS, now=None
) -> tuple[int, int]:
    """``(sale_events, distinct_sale_days)`` for a product inside the window.

    The cutoff is snapped to midnight so a movement written on the oldest day of
    the window is inside it regardless of the hour ``clock.now()`` happens to
    return. Without that, the first day of every ninety-day window would drop in
    and out depending on the time of day the demo was run.
    """
    reference = now or clock.now()
    cutoff = (reference - timedelta(days=window_days)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    rows = (
        db.query(StockMovement.recorded_at)
        .filter(
            StockMovement.product_id == product_id,
            StockMovement.movement_type == MovementType.sale,
            StockMovement.recorded_at >= cutoff,
        )
        .all()
    )
    stamps = [row[0] for row in rows if row[0] is not None]
    return len(stamps), len({stamp.date() for stamp in stamps})


def _ledger_sum(db, product_id: int) -> int:
    from sqlalchemy import func

    return int(
        db.query(func.coalesce(func.sum(StockMovement.quantity), 0))
        .filter(StockMovement.product_id == product_id)
        .scalar()
        or 0
    )


def _stock_row(db, product_id: int) -> StockLevel:
    stock = db.query(StockLevel).filter(StockLevel.product_id == product_id).first()
    if stock is None:
        stock = StockLevel(product_id=product_id, quantity_on_hand=0, quantity_reserved=0)
        db.add(stock)
        db.flush()
    return stock


def _reference(kind: str, sku: str, day=None) -> str:
    """A ``SIM-``-prefixed reference number: the reset key and the idempotency key.

    ``reference_number`` is ``String(50)``; ``SIM-SALE-GRO-0001-20260601`` fits
    comfortably.
    """
    tail = sku[4:] if sku.startswith("SKU-") else sku
    if day is None:
        return f"{SIM_PREFIX}{kind}-{tail}"
    return f"{SIM_PREFIX}{kind}-{tail}-{day:%Y%m%d}"


def backfill_product(
    db,
    product: Product,
    rate: float,
    *,
    days: int = BACKFILL_DAYS,
    target_final: int | None = None,
    now=None,
) -> dict:
    """Write one product's history and leave it holding exactly ``target_final``.

    ``target_final`` defaults to the product's current on-hand position, so a
    backfill that is not asked to move stock adds ninety days of history without
    changing a single reported number.

    Returns a summary of what was written, including the sufficiency verdict the
    resulting history earns.
    """
    reference_now = now or clock.now()
    first_day = (reference_now - timedelta(days=days)).date()

    baseline_ledger = _ledger_sum(db, product.id)
    stock = _stock_row(db, product.id)
    if target_final is None:
        target_final = int(stock.quantity_on_hand or 0)

    sales = daily_sales(rate, category_shape(product), days, first_day)
    receipts, opening_quantity = receipt_schedule(
        sales,
        target_final,
        int(product.reorder_point or 0),
        int(product.reorder_quantity or 0),
    )

    written = 0

    # The opening balance sits one day before the window so it can never be
    # mistaken for trading activity, and so it never pollutes the demand window.
    opening_delta = opening_quantity - baseline_ledger
    if opening_delta:
        written += _add_movement(
            db,
            product,
            MovementType.adjustment,
            opening_delta,
            _reference("OPEN", product.sku),
            "Opening balance carried forward from legacy system (synthetic fixture)",
            reference_now - timedelta(days=days + 1),
            _HOUR_OPENING,
        )

    for index in range(days):
        day = first_day + timedelta(days=index)
        stamp_base = reference_now - timedelta(days=days - index)
        if receipts[index]:
            written += _add_movement(
                db,
                product,
                MovementType.receipt,
                receipts[index],
                _reference("RCV", product.sku, day),
                "Replenishment delivery (synthetic fixture)",
                stamp_base,
                _HOUR_RECEIPT,
            )
        if sales[index]:
            written += _add_movement(
                db,
                product,
                MovementType.sale,
                -sales[index],
                _reference("SALE", product.sku, day),
                "Daily counter sales (synthetic fixture)",
                stamp_base,
                _HOUR_SALE,
            )

    db.flush()

    # Derived, never asserted: the ledger is the source of truth and the stock
    # level follows it. With the backward schedule this equals target_final, and
    # the caller's tests assert exactly that.
    stock.quantity_on_hand = _ledger_sum(db, product.id)

    # Alerts are evaluated once, against the final position. The baseline seeder
    # calls check_stock_alerts per movement, which is right for a handful of rows
    # and wrong for five hundred: it would leave hundreds of resolved alert rows
    # behind for no gain, since only the current position can be alerting.
    check_stock_alerts(product, stock, db)
    db.flush()

    events, distinct_days = sale_event_stats(db, product.id, window_days=days, now=reference_now)
    return {
        "sku": product.sku,
        "rate": rate,
        "movements_written": written,
        "sale_events": events,
        "sale_days": distinct_days,
        "sufficiency": sufficiency_of(events, distinct_days),
        "receipts": sum(1 for quantity in receipts if quantity),
        "opening_adjustment": opening_delta,
        "target_final": target_final,
        "quantity_on_hand": stock.quantity_on_hand,
    }


def _add_movement(db, product, movement_type, quantity, reference_number, notes, stamp, hour):
    """Insert one movement with an explicit ``recorded_at``. Returns 1 if written.

    Idempotent on ``(product_id, reference_number)``, so re-running a backfill
    over history that is already present is a no-op rather than a doubling.
    """
    exists = (
        db.query(StockMovement.id)
        .filter(
            StockMovement.product_id == product.id,
            StockMovement.reference_number == reference_number,
        )
        .first()
    )
    if exists:
        return 0

    db.add(
        StockMovement(
            product_id=product.id,
            movement_type=movement_type,
            quantity=quantity,
            reference_number=reference_number,
            notes=notes,
            # THE line this module exists for. Omit it and the column default
            # stamps wall-clock now, collapsing the window onto a single day.
            recorded_at=stamp.replace(hour=hour, minute=0, second=0, microsecond=0),
            recorded_by=SIM_ACTOR,
        )
    )
    return 1


def backfill_history(
    db,
    *,
    demand: dict[str, float] | None = None,
    days: int = BACKFILL_DAYS,
    stock_targets: dict[str, int] | None = None,
    now=None,
) -> dict:
    """Backfill every product that has a demand rate.

    Named ``backfill_history`` rather than ``backfill`` so it does not shadow this
    module's own name when the package re-exports it.

    ``demand`` is an *override* layered on ``BASE_DEMAND``, matching how
    ``stock_targets`` overrides current positions. A scenario that names one SKU is
    stating what is different about that SKU, not silently erasing the history of
    the other four.
    """
    rates = dict(BASE_DEMAND)
    rates.update(demand or {})
    targets = stock_targets or {}
    reference_now = now or clock.now()

    per_product = []
    for product in db.query(Product).order_by(Product.id).all():
        if product.sku not in rates:
            continue
        per_product.append(
            backfill_product(
                db,
                product,
                rates[product.sku],
                days=days,
                target_final=targets.get(product.sku),
                now=reference_now,
            )
        )
    db.commit()

    summary = {
        "days": days,
        "products": per_product,
        "movements_written": sum(row["movements_written"] for row in per_product),
        "distinct_recorded_dates": distinct_recorded_dates(db),
        "sufficient_products": sum(
            1 for row in per_product if row["sufficiency"] == "sufficient"
        ),
    }
    logger.info(
        "simulation_backfill_complete",
        poc_id="POC-07",
        days=days,
        movements=summary["movements_written"],
        distinct_dates=summary["distinct_recorded_dates"],
        sufficient=summary["sufficient_products"],
    )
    return summary


def distinct_recorded_dates(db) -> int:
    """How many distinct calendar dates the movement ledger spans.

    The headline number for this workstream: before the backfill it was 1.
    """
    from sqlalchemy import func

    return int(
        db.query(func.count(func.distinct(func.date(StockMovement.recorded_at)))).scalar() or 0
    )
