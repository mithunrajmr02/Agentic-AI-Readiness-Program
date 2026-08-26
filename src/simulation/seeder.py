"""Everything the ninety days of history sit inside.

Doc 12 §9 lists what the dataset must contain before any detector can be
demonstrated honestly. The baseline seeder supplies suppliers, products, four
purchase orders and an opening ledger; this module supplies the rest:

* **The three demo users.** Doc 13 §2.4. The baseline creates one manager. A
  demo about approval routing needs someone to route *to*, and the agent's
  actions need an actor that is not a person.
* **Supplier catalogue terms.** ``supplier_products`` — WS-0 owns the schema,
  WS-7 owns the logic, WS-2 seeds the rows. Two SKUs get a competing offer so
  supplier comparison has something to compare.
* **The autonomy policy.** The envelope the scenarios bound the agent with.
* **Two operational purchase orders.** One overdue and one partially received.
  Both are conditions that exist in every real ERP and in no fixture, so
  ``po_overdue`` and partial-receipt reconciliation would otherwise have nothing
  to fire on.

Ordering matters in one specific way
------------------------------------
``seed_dataset`` captures each product's on-hand position **before** it seeds the
operational purchase orders, and hands that snapshot to the backfill as the
default target. The partial receipt adds forty bottles to the ledger; the backfill
then lands the product on its documented position anyway, absorbing the difference
into the opening balance. Without the snapshot, seeding a partial receipt would
quietly move a number that doc 13 §7.1 states as fact.

New purchase orders, never edited history
-----------------------------------------
``PO-2026-0001..0004`` are the baseline seeder's and are never modified — both D1
and D2 name them in ``preserve_pos``. The operational cases are new rows
(``PO-2026-0005`` and ``PO-2026-0006``), because rewriting the dates on existing
history to manufacture an overdue condition is precisely the kind of fixture
dishonesty this package is supposed to make unnecessary.
"""
from datetime import timedelta

import structlog

from src.backend.models import (
    POItem,
    POStatus,
    Product,
    PurchaseOrder,
    StockLevel,
    StockMovement,
    Supplier,
    MovementType,
    User,
)
from src.backend.models_governance import AutonomyPolicy
from src.backend.models_sourcing import SupplierProduct
from src.core import clock
from src.simulation.backfill import BACKFILL_DAYS, SIM_ACTOR, SIM_PREFIX, backfill_history

logger = structlog.get_logger()

#: One credential for the whole demo. Demo-only by construction: these accounts
#: exist in a database that ``reset`` rebuilds and that ships with DEMO_MODE.
DEMO_PASSWORD = "admin"

#: Doc 13 §2.4. ``agent`` is not self-registerable — ``routers/auth.VALID_ROLES``
#: allows only manager and staff — so the agent identity is seeded directly.
#: ``users.role`` is ``String(50)``, so this costs no migration.
DEMO_USERS = [
    ("admin@retail.com", "Demo Manager", "manager"),
    ("staff@retail.com", "Demo Store Staff", "staff"),
    ("agent@retail.com", "Steward Agent", "agent"),
]

#: Alternative supply for two SKUs, so ``switch_supplier`` and supplier drift have
#: a real comparison rather than a single-row catalogue. The rice pair is the one
#: D2 names explicitly (doc 13 §6): the incumbent quotes less and delivers later.
ALTERNATIVE_OFFERS = [
    # (sku, supplier_code, unit_price, lead_time_days)
    ("SKU-GRO-0001", "SUP-0001", 625.0, 7),
    ("SKU-HHD-0001", "SUP-0005", 318.0, 5),
]

#: The overdue PO and the partial receipt. Doc 12 §9.
OVERDUE_PO_NUMBER = "PO-2026-0005"
PARTIAL_PO_NUMBER = "PO-2026-0006"
SIM_PO_NUMBERS = (OVERDUE_PO_NUMBER, PARTIAL_PO_NUMBER)

_PARTIAL_ORDERED = 100
_PARTIAL_RECEIVED = 40


def ensure_baseline(db) -> dict:
    """Make sure the baseline seeder's dataset is present, without duplicating it.

    Calls the frozen ``seed_demo_data`` helpers, which are all idempotent on their
    natural keys and all take an explicit session. Building the baseline by
    importing it rather than restating it means this package can never drift from
    the numbers the graded phases assert.
    """
    from src.backend import seed_demo_data

    return {
        "suppliers": seed_demo_data._seed_suppliers(db),
        "products": seed_demo_data._seed_products(db),
        "purchase_orders": seed_demo_data._seed_purchase_orders(db),
        "movements": seed_demo_data._seed_movements(db),
    }


def seed_users(db) -> dict:
    """Create the three demo identities. Idempotent on email."""
    from src.backend.routers.auth import get_password_hash

    created = []
    for email, full_name, role in DEMO_USERS:
        if db.query(User).filter(User.email == email).first():
            continue
        db.add(
            User(
                email=email,
                hashed_password=get_password_hash(DEMO_PASSWORD),
                full_name=full_name,
                role=role,
                is_active=True,
            )
        )
        created.append(email)
    db.commit()
    return {"created": created, "roles": sorted({role for _, _, role in DEMO_USERS})}


def _products_by_sku(db) -> dict[str, Product]:
    return {product.sku: product for product in db.query(Product).all()}


def _suppliers_by_code(db) -> dict[str, Supplier]:
    return {supplier.supplier_code: supplier for supplier in db.query(Supplier).all()}


def _upsert_supplier_product(db, supplier_id, product_id, unit_price, lead_time_days, preferred):
    """Insert or update one catalogue row, keyed on ``(supplier_id, product_id)``.

    The ``flush`` is load-bearing, not tidiness. ``seed_supplier_products`` can
    reach the same pair twice in a single call — a scenario override that restates
    a product's *incumbent* terms is exactly that case, and D2 does it — and
    sessions here are ``autoflush=False``, so without the flush the second lookup
    would not see the row the first pass had added and both inserts would reach the
    unique constraint together at commit time.
    """
    row = (
        db.query(SupplierProduct)
        .filter(
            SupplierProduct.supplier_id == supplier_id,
            SupplierProduct.product_id == product_id,
        )
        .first()
    )
    if row is None:
        db.add(
            SupplierProduct(
                supplier_id=supplier_id,
                product_id=product_id,
                unit_price=unit_price,
                lead_time_days=lead_time_days,
                min_order_quantity=1,
                pack_size=1,
                is_preferred=preferred,
                last_price_update=clock.now(),
            )
        )
        db.flush()
        return "created"

    changed = (
        row.unit_price != unit_price
        or row.lead_time_days != lead_time_days
        or bool(row.is_preferred) != bool(preferred)
    )
    if changed:
        row.unit_price = unit_price
        row.lead_time_days = lead_time_days
        row.is_preferred = preferred
        row.last_price_update = clock.now()
        return "updated"
    return "unchanged"


def seed_supplier_products(db, extra: list[dict] | None = None) -> dict:
    """Seed catalogue terms: the incumbent offer per product, plus alternatives.

    The incumbent offer restates the product's own ``cost_price`` and its
    supplier's stated ``lead_time_days`` — the terms the business believes it is
    buying on. Whether reality agrees is what ``supplier_drift`` is for.

    ``extra`` accepts a scenario's ``supplier_products`` block:
    ``{"sku", "supplier_id" | "supplier_code", "unit_price", "lead_time_days"}``.
    """
    products = _products_by_sku(db)
    suppliers = _suppliers_by_code(db)
    outcomes = {"created": 0, "updated": 0, "unchanged": 0}

    def record(outcome):
        outcomes[outcome] = outcomes.get(outcome, 0) + 1

    for product in products.values():
        if not product.supplier_id:
            continue
        supplier = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
        record(
            _upsert_supplier_product(
                db,
                product.supplier_id,
                product.id,
                float(product.cost_price or 0.0),
                int(supplier.lead_time_days or 0) if supplier else 0,
                True,
            )
        )

    for sku, supplier_code, unit_price, lead_time_days in ALTERNATIVE_OFFERS:
        product, supplier = products.get(sku), suppliers.get(supplier_code)
        if product is None or supplier is None:
            continue
        record(
            _upsert_supplier_product(
                db, supplier.id, product.id, unit_price, lead_time_days, False
            )
        )

    for spec in extra or []:
        product = products.get(spec.get("sku"))
        if product is None:
            continue
        supplier_id = spec.get("supplier_id")
        if supplier_id is None:
            supplier = suppliers.get(spec.get("supplier_code"))
            supplier_id = supplier.id if supplier else None
        if supplier_id is None:
            continue
        record(
            _upsert_supplier_product(
                db,
                supplier_id,
                product.id,
                float(spec.get("unit_price", product.cost_price or 0.0)),
                int(spec.get("lead_time_days", 0)),
                bool(spec.get("is_preferred", False)),
            )
        )

    db.commit()
    return outcomes


def seed_autonomy_policy(db, spec: dict | None) -> dict:
    """Write the global autonomy envelope from a scenario's ``autonomy`` block.

    Scope is global; ``scope_value`` stays NULL. Only the keys the scenario names
    are written — every other bound keeps the model's default, because a fixture
    inventing a blast-radius limit it was never asked for would be a governance
    decision disguised as test data.
    """
    if not spec:
        return {"outcome": "skipped"}

    row = (
        db.query(AutonomyPolicy)
        .filter(AutonomyPolicy.scope_type == "global", AutonomyPolicy.scope_value.is_(None))
        .first()
    )
    mode = spec.get("mode", "assisted")
    outcome = "unchanged"
    if row is None:
        row = AutonomyPolicy(scope_type="global", scope_value=None, mode=mode)
        db.add(row)
        outcome = "created"
    elif row.mode != mode:
        row.mode = mode
        outcome = "updated"

    for key in ("max_order_value", "max_orders_per_hour", "max_value_per_day"):
        if key in spec and getattr(row, key) != spec[key]:
            setattr(row, key, spec[key])
            outcome = "created" if outcome == "created" else "updated"

    row.updated_at = clock.now()
    db.commit()
    return {"outcome": outcome, "mode": row.mode, "max_order_value": row.max_order_value}


def _create_po(db, po_number, supplier_code, status, order_date, expected_delivery, items):
    supplier = db.query(Supplier).filter(Supplier.supplier_code == supplier_code).first()
    if supplier is None:
        return None

    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=supplier.id,
        status=status,
        order_date=order_date,
        expected_delivery=expected_delivery,
        total_amount=0.0,
    )
    db.add(po)
    db.flush()

    total = 0.0
    for sku, quantity, unit_cost, received in items:
        product = db.query(Product).filter(Product.sku == sku).first()
        if product is None:
            continue
        db.add(
            POItem(
                po_id=po.id,
                product_id=product.id,
                quantity_ordered=quantity,
                unit_cost=unit_cost,
                quantity_received=received,
            )
        )
        total += quantity * unit_cost
    # Derived from the line items, so the header can never disagree with what was
    # ordered — the same rule the baseline seeder's verify() enforces.
    po.total_amount = total
    db.flush()
    return po


def seed_operational_pos(db) -> dict:
    """The overdue PO and the partially received PO. Idempotent on ``po_number``.

    The partial receipt is written by hand because
    ``inventory_service.receive_purchase_order`` only knows how to receive an
    order in full. A short delivery is the interesting case — the one where the
    header says received and the line items say otherwise — so it is written as
    what it is: a submitted order, a line item recording forty of one hundred, and
    a receipt movement for exactly forty.
    """
    today = clock.today()
    created = []

    if not db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number == OVERDUE_PO_NUMBER
    ).first():
        # Ordered 20 days ago against a 5-day lead time and promised a fortnight
        # ago. Nothing has arrived and nothing in the current system says so.
        po = _create_po(
            db,
            OVERDUE_PO_NUMBER,
            "SUP-0005",
            POStatus.submitted,
            today - timedelta(days=20),
            today - timedelta(days=14),
            [("SKU-GRO-0001", 60, 600.0, None)],
        )
        if po is not None:
            created.append(OVERDUE_PO_NUMBER)

    if not db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number == PARTIAL_PO_NUMBER
    ).first():
        po = _create_po(
            db,
            PARTIAL_PO_NUMBER,
            "SUP-0001",
            POStatus.submitted,
            today - timedelta(days=12),
            today - timedelta(days=5),
            [("SKU-HHD-0001", _PARTIAL_ORDERED, 310.0, _PARTIAL_RECEIVED)],
        )
        if po is not None:
            _record_partial_receipt(db, po)
            created.append(PARTIAL_PO_NUMBER)

    db.commit()
    return {"created": created}


def _record_partial_receipt(db, po: PurchaseOrder) -> None:
    """Book the forty bottles that did arrive, ledger and stock level together."""
    product = db.query(Product).filter(Product.sku == "SKU-HHD-0001").first()
    if product is None:
        return

    stock = db.query(StockLevel).filter(StockLevel.product_id == product.id).first()
    if stock is None:
        stock = StockLevel(product_id=product.id, quantity_on_hand=0, quantity_reserved=0)
        db.add(stock)
        db.flush()

    stock.quantity_on_hand = (stock.quantity_on_hand or 0) + _PARTIAL_RECEIVED
    db.add(
        StockMovement(
            product_id=product.id,
            movement_type=MovementType.receipt,
            quantity=_PARTIAL_RECEIVED,
            reference_number=f"{SIM_PREFIX}PARTIAL-{po.po_number[-4:]}",
            notes=f"Partial receipt {_PARTIAL_RECEIVED}/{_PARTIAL_ORDERED} against {po.po_number}",
            # Explicit, clock-derived: the delivery landed five days ago, not now.
            recorded_at=(clock.now() - timedelta(days=5)).replace(
                hour=10, minute=0, second=0, microsecond=0
            ),
            recorded_by=SIM_ACTOR,
        )
    )
    db.flush()


def seed_dataset(
    db,
    *,
    demand: dict[str, float] | None = None,
    stock: dict[str, int] | None = None,
    backfill_days: int = BACKFILL_DAYS,
    autonomy: dict | None = None,
    supplier_products: list[dict] | None = None,
) -> dict:
    """Seed the complete dataset a scenario needs, then backfill the history.

    Assumes ``reset_simulation`` has already run if idempotency is wanted; on its
    own every step here is idempotent, but the backfill's targets are relative to
    whatever position it finds.
    """
    baseline = ensure_baseline(db)

    # Captured before the operational POs move anything, so the documented on-hand
    # positions survive the partial receipt (see the module docstring).
    baseline_stock = {
        product.sku: int(
            (
                db.query(StockLevel)
                .filter(StockLevel.product_id == product.id)
                .first()
                or StockLevel(quantity_on_hand=0)
            ).quantity_on_hand
            or 0
        )
        for product in db.query(Product).all()
    }

    users = seed_users(db)
    catalogue = seed_supplier_products(db, supplier_products)
    policy = seed_autonomy_policy(db, autonomy)
    orders = seed_operational_pos(db)

    targets = dict(baseline_stock)
    targets.update(stock or {})

    history = backfill_history(db, demand=demand, days=backfill_days, stock_targets=targets)

    logger.info(
        "simulation_dataset_seeded",
        poc_id="POC-07",
        users=len(users["created"]),
        purchase_orders=orders["created"],
        movements=history["movements_written"],
        distinct_dates=history["distinct_recorded_dates"],
    )
    return {
        "baseline": baseline,
        "users": users,
        "supplier_products": catalogue,
        "autonomy_policy": policy,
        "purchase_orders": orders,
        "history": history,
    }
