"""The ninety-day backfill: explicit timestamps, closed ledger, designed demand.

The first test in this file is the one the workstream exists for. Before the
backfill, ``stock_movements`` spanned exactly **one** distinct calendar date,
because ``recorded_at`` carries ``server_default=func.now()`` and every insert let
the column default fire. Ninety rows, one day, and every downstream demand rate
silently wrong.
"""
from datetime import date, timedelta

import pytest

from src.core import clock
from src.simulation import backfill as bf


# --- pure functions: no database, no clock -----------------------------------

MONDAY = date(2026, 6, 1)  # a Monday, so a 70-day window is exactly 10 weeks


def test_daily_sales_is_deterministic():
    """No RNG anywhere. The same call must produce the same ledger, forever —
    it is what lets ``expected_signals`` be an assertion instead of a hope."""
    first = bf.daily_sales(1.5, (1.1, 0.75), 90, MONDAY)
    second = bf.daily_sales(1.5, (1.1, 0.75), 90, MONDAY)
    assert first == second


@pytest.mark.parametrize("rate", [0.2, 1.5, 4.0, 6.0])
def test_daily_sales_preserves_the_weekly_mean(rate):
    """The category shape redistributes demand without moving the average.

    Over ten whole weeks the shaped total must land within one unit of
    ``rate * days`` — the only slack is the fractional accumulator's remainder.
    """
    for shape in bf.CATEGORY_SHAPE.values():
        total = sum(bf.daily_sales(rate, shape, 70, MONDAY))
        assert abs(total - rate * 70) < 1.0, shape


def test_category_shapes_are_mean_preserving_by_construction():
    """``5 * weekday + 2 * weekend == 7`` for every category, checked directly."""
    for category, (weekday, weekend) in bf.CATEGORY_SHAPE.items():
        assert 5 * weekday + 2 * weekend == pytest.approx(7.0), category


def test_zero_rate_emits_nothing():
    """Colgate's whole scenario rests on this. A trickle of demand would make
    D4's refusal indefensible."""
    assert sum(bf.daily_sales(0.0, (1.0, 1.0), 90, MONDAY)) == 0


def test_a_very_low_rate_still_emits_events():
    """0.2/day must not round to nothing — the television needs a real, sparse
    history so it can land on ``thin`` rather than ``none``."""
    sales = bf.daily_sales(0.2, (1.1, 0.75), 90, MONDAY)
    assert 10 <= sum(sales) <= 25
    assert sum(1 for quantity in sales if quantity) >= 10


@pytest.mark.parametrize(
    "target,reorder_point,reorder_quantity",
    [(4, 10, 25), (167, 15, 60), (0, 30, 120), (50, 20, 100), (20, 15, 60)],
)
def test_receipt_schedule_closes_the_arithmetic(target, reorder_point, reorder_quantity):
    """opening + receipts − sales == target, exactly. This is the ledger
    invariant (M-16), proved on the schedule before a row is ever written."""
    sales = bf.daily_sales(4.0, (0.8, 1.5), 90, MONDAY)
    receipts, opening = bf.receipt_schedule(sales, target, reorder_point, reorder_quantity)
    assert opening + sum(receipts) - sum(sales) == target


def test_receipt_schedule_replenishes_within_the_band():
    """Every replenishment is exactly one reorder quantity, and there is at most
    one per day — a target far above the band unwinds over consecutive days
    rather than stacking several deliveries onto a single date."""
    sales = bf.daily_sales(6.0, (1.0, 1.0), 90, MONDAY)
    receipts, _ = bf.receipt_schedule(sales, 50, 20, 100)
    assert set(receipts) <= {0, 100}


def test_receipt_schedule_without_a_reorder_quantity_uses_the_opening_balance():
    """A product with no reorder quantity has nothing sensible to replenish
    with, so the whole window is funded by the opening balance."""
    sales = bf.daily_sales(4.0, (0.8, 1.5), 90, MONDAY)
    receipts, opening = bf.receipt_schedule(sales, 10, 15, 0)
    assert receipts == [0] * 90
    assert opening == 10 + sum(sales)


@pytest.mark.parametrize(
    "events,days,expected",
    [
        (0, 0, "none"),
        (14, 21, "sufficient"),      # both frozen floors, exactly
        (20, 30, "sufficient"),
        (14, 20, "thin"),            # enough events, not enough spread
        (13, 21, "thin"),            # enough spread, not enough events
        (5, 7, "thin"),              # both thin floors, exactly
        (4, 7, "insufficient"),
        (1, 1, "insufficient"),
    ],
)
def test_sufficiency_thresholds_match_the_frozen_contract(events, days, expected):
    """§5.4, boundaries included. These four verdicts decide whether a number is
    published or refused, so the floors are tested at the floor."""
    assert bf.sufficiency_of(events, days) == expected


# --- against a database -------------------------------------------------------


@pytest.fixture
def seeded(db):
    from src.simulation.seeder import ensure_baseline

    ensure_baseline(db)
    return bf.backfill_history(db)


def test_history_spans_at_least_ninety_distinct_dates(db, seeded):
    """**The headline assertion.** Before this workstream the ledger held one
    distinct date; ninety days of movements had collapsed onto today."""
    assert seeded["distinct_recorded_dates"] >= 90


def test_no_backfilled_movement_lands_on_today(db, seeded):
    """The defect, tested directly.

    If a single ``recorded_at`` were omitted, SQLite's column default would stamp
    wall-clock now and that row would land on today. The window runs from day −91
    to day −1, so *today* is precisely the date that must not appear.
    """
    from src.backend.models import StockMovement

    stamps = [
        row[0]
        for row in db.query(StockMovement.recorded_at)
        .filter(StockMovement.recorded_by == bf.SIM_ACTOR)
        .all()
    ]
    assert stamps, "the backfill wrote nothing"
    assert all(stamp is not None for stamp in stamps)
    assert clock.today() not in {stamp.date() for stamp in stamps}


def test_the_backfill_window_is_contiguous(db, seeded):
    """Every date from day −90 to day −1 carries at least one movement.

    A sparse window would still pass a distinct-date count while leaving gaps
    that make a daily demand rate meaningless.
    """
    from src.backend.models import StockMovement

    dates = {
        row[0].date()
        for row in db.query(StockMovement.recorded_at)
        .filter(StockMovement.recorded_by == bf.SIM_ACTOR)
        .all()
        if row[0] is not None
    }
    today = clock.today()
    expected = {today - timedelta(days=offset) for offset in range(1, bf.BACKFILL_DAYS + 1)}
    assert expected <= dates


def test_ledger_invariant_holds_for_every_product(db, seeded):
    """M-16: ``sum(stock_movements.quantity) == stock_levels.quantity_on_hand``."""
    from sqlalchemy import func

    from src.backend.models import Product, StockLevel, StockMovement

    for product in db.query(Product).all():
        ledger = int(
            db.query(func.coalesce(func.sum(StockMovement.quantity), 0))
            .filter(StockMovement.product_id == product.id)
            .scalar()
            or 0
        )
        stock = db.query(StockLevel).filter(StockLevel.product_id == product.id).first()
        assert stock is not None, product.sku
        assert stock.quantity_on_hand == ledger, product.sku


def test_a_backfill_that_is_not_asked_to_move_stock_moves_nothing(db, seeded):
    """``target_final`` defaults to the current position, so adding ninety days of
    history must not change a single reported number. The baseline positions the
    graded phases assert survive untouched."""
    from src.backend.models import Product, StockLevel

    positions = {
        product.sku: db.query(StockLevel)
        .filter(StockLevel.product_id == product.id)
        .first()
        .quantity_on_hand
        for product in db.query(Product).all()
    }
    assert positions == {
        "SKU-GRO-0001": 167,
        "SKU-ELC-0001": 4,
        "SKU-ELC-0002": 0,
        "SKU-HHD-0001": 50,
        "SKU-PRC-0001": 0,
    }


def test_stock_targets_are_honoured_exactly(db):
    from src.backend.models import Product, StockLevel
    from src.simulation.seeder import ensure_baseline

    ensure_baseline(db)
    bf.backfill_history(db, stock_targets={"SKU-GRO-0001": 20, "SKU-ELC-0001": 4})

    for sku, expected in (("SKU-GRO-0001", 20), ("SKU-ELC-0001", 4)):
        product = db.query(Product).filter(Product.sku == sku).first()
        stock = db.query(StockLevel).filter(StockLevel.product_id == product.id).first()
        assert stock.quantity_on_hand == expected, sku


def test_backfill_is_idempotent(db, seeded):
    """Re-running over history that is already present is a no-op, not a
    doubling — the reference number is the idempotency key."""
    from src.backend.models import StockMovement

    before = db.query(StockMovement).count()
    again = bf.backfill_history(db)
    assert again["movements_written"] == 0
    assert db.query(StockMovement).count() == before
    assert again["distinct_recorded_dates"] == seeded["distinct_recorded_dates"]


def test_at_least_three_products_reach_sufficient(db, seeded):
    """The stated target. Without it, WS-1 has nothing to compute a defensible
    demand rate from and every metric would be refused."""
    assert seeded["sufficient_products"] >= 3


def test_the_sufficiency_spectrum_is_covered(db, seeded):
    """All four verdicts appear in one dataset, so every branch of the sufficiency
    UI has a real subject: three sufficient, the television thin, Colgate none."""
    verdicts = {row["sku"]: row["sufficiency"] for row in seeded["products"]}
    assert verdicts["SKU-GRO-0001"] == "sufficient"
    assert verdicts["SKU-HHD-0001"] == "sufficient"
    assert verdicts["SKU-ELC-0001"] == "sufficient"
    assert verdicts["SKU-ELC-0002"] == "thin"
    assert verdicts["SKU-PRC-0001"] == "none"


def test_colgate_has_no_sale_events_at_all(db, seeded):
    """D4's evidence. A single synthetic sale here would make the refusal a bug."""
    from src.backend.models import Product

    product = db.query(Product).filter(Product.sku == "SKU-PRC-0001").first()
    events, days = bf.sale_event_stats(db, product.id)
    assert (events, days) == (0, 0)


def test_sufficient_products_clear_the_frozen_floors(db, seeded):
    """Not just the verdict — the underlying counts, so a mistake in
    ``sufficiency_of`` could not make a thin history look sufficient."""
    for row in seeded["products"]:
        if row["sufficiency"] == "sufficient":
            assert row["sale_events"] >= 14, row["sku"]
            assert row["sale_days"] >= 21, row["sku"]


def test_the_opening_adjustment_predates_the_window(db, seeded):
    """The opening balance sits one day before day −90, so it can never be
    mistaken for trading activity or pollute the demand window."""
    from src.backend.models import StockMovement

    openings = (
        db.query(StockMovement)
        .filter(StockMovement.reference_number.like(f"{bf.SIM_PREFIX}OPEN-%"))
        .all()
    )
    assert openings
    boundary = clock.today() - timedelta(days=bf.BACKFILL_DAYS)
    for movement in openings:
        assert movement.recorded_at.date() < boundary
