"""Everything the ninety days of history sit inside.

The interesting cases here are the ones a fixture normally omits because they are
awkward: a purchase order that was promised a fortnight ago and never arrived, and
a delivery that turned up forty short. Both exist in every real ERP, so a detector
for either has nothing to fire on until they exist here.
"""
import pytest

from src.core import clock
from src.simulation import seeder


@pytest.fixture
def baseline(db):
    return seeder.ensure_baseline(db)


def test_ensure_baseline_reuses_the_frozen_seeder(db, baseline):
    """The baseline is built by *importing* ``seed_demo_data``, never by restating
    it. A second copy of these numbers would eventually disagree with the one the
    graded phases assert."""
    from src.backend.models import Product, PurchaseOrder, Supplier

    assert db.query(Supplier).count() == 4
    assert db.query(Product).count() == 5
    assert db.query(PurchaseOrder).count() == 4


def test_ensure_baseline_is_idempotent(db, baseline):
    from src.backend.models import Product, PurchaseOrder, StockMovement, Supplier

    counts = (
        db.query(Supplier).count(),
        db.query(Product).count(),
        db.query(PurchaseOrder).count(),
        db.query(StockMovement).count(),
    )
    seeder.ensure_baseline(db)
    assert (
        db.query(Supplier).count(),
        db.query(Product).count(),
        db.query(PurchaseOrder).count(),
        db.query(StockMovement).count(),
    ) == counts


# --- users --------------------------------------------------------------------


def test_seeds_a_manager_a_staff_user_and_an_agent(db, baseline):
    """§15 line 310: *"WS-2 seeds a ``staff`` user; without it, M-34's RBAC 403
    cannot be demonstrated and AD-12's least-privilege agent identity has no second
    subject."*"""
    from src.backend.models import User

    seeder.seed_users(db)
    roles = {user.email: user.role for user in db.query(User).all()}
    assert roles["admin@retail.com"] == "manager"
    assert roles["staff@retail.com"] == "staff"
    assert roles["agent@retail.com"] == "agent"


def test_the_agent_role_is_not_self_registerable(db):
    """Which is exactly why the agent identity is seeded directly rather than
    through the registration endpoint. If this ever changes, the seeder can be
    simplified — and this test is where that will surface."""
    from src.backend.routers import auth

    assert "agent" not in auth.VALID_ROLES


def test_seed_users_is_idempotent(db, baseline):
    from src.backend.models import User

    seeder.seed_users(db)
    before = db.query(User).count()
    second = seeder.seed_users(db)
    assert second["created"] == []
    assert db.query(User).count() == before


# --- supplier catalogue -------------------------------------------------------


def test_every_product_gets_its_incumbent_offer(db, baseline):
    """The terms the business believes it is buying on: the product's own
    ``cost_price`` and its supplier's stated lead time. Whether reality agrees is
    what ``supplier_drift`` exists to find out."""
    from src.backend.models import Product, Supplier
    from src.backend.models_sourcing import SupplierProduct

    seeder.seed_supplier_products(db)
    for product in db.query(Product).all():
        row = (
            db.query(SupplierProduct)
            .filter(
                SupplierProduct.product_id == product.id,
                SupplierProduct.supplier_id == product.supplier_id,
            )
            .first()
        )
        assert row is not None, product.sku
        assert row.unit_price == pytest.approx(product.cost_price)
        assert row.is_preferred is True
        supplier = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
        assert row.lead_time_days == supplier.lead_time_days


def test_rice_has_a_competing_offer(db, baseline):
    """D2 needs two rows to compare, and the incumbent must be the cheaper one —
    the point of the scenario is that price alone is the wrong lens."""
    from src.backend.models import Product
    from src.backend.models_sourcing import SupplierProduct

    seeder.seed_supplier_products(db)
    rice = db.query(Product).filter(Product.sku == "SKU-GRO-0001").first()
    offers = db.query(SupplierProduct).filter(SupplierProduct.product_id == rice.id).all()
    assert len(offers) == 2

    incumbent = next(offer for offer in offers if offer.is_preferred)
    alternative = next(offer for offer in offers if not offer.is_preferred)
    assert incumbent.unit_price < alternative.unit_price


def test_supplier_products_accepts_a_scenario_override_by_code(db, baseline):
    """Scenario specs name suppliers by code, which survives a renumbered
    database; ``supplier_id`` is accepted too."""
    from src.backend.models import Product, Supplier
    from src.backend.models_sourcing import SupplierProduct

    seeder.seed_supplier_products(
        db,
        [
            {
                "sku": "SKU-GRO-0001",
                "supplier_code": "SUP-0003",
                "unit_price": 590.0,
                "lead_time_days": 12,
            }
        ],
    )
    rice = db.query(Product).filter(Product.sku == "SKU-GRO-0001").first()
    supplier = db.query(Supplier).filter(Supplier.supplier_code == "SUP-0003").first()
    row = (
        db.query(SupplierProduct)
        .filter(
            SupplierProduct.product_id == rice.id,
            SupplierProduct.supplier_id == supplier.id,
        )
        .first()
    )
    assert row is not None
    assert (row.unit_price, row.lead_time_days) == (590.0, 12)


def test_an_override_naming_the_incumbent_supplier_updates_it(db, baseline):
    """Regression. D2 restates rice's *incumbent* terms — quoted price and quoted
    lead time — so the override reaches a ``(supplier, product)`` pair the
    incumbent pass has already added within the same uncommitted call. Sessions
    here are ``autoflush=False``, so this used to insert a duplicate and fail on
    the unique constraint at commit.
    """
    from src.backend.models import Product
    from src.backend.models_sourcing import SupplierProduct

    rice = db.query(Product).filter(Product.sku == "SKU-GRO-0001").first()
    incumbent_code = (
        db.query(seeder.Supplier).filter(seeder.Supplier.id == rice.supplier_id).one()
    ).supplier_code

    seeder.seed_supplier_products(
        db,
        [
            {
                "sku": "SKU-GRO-0001",
                "supplier_code": incumbent_code,
                "unit_price": 600.0,
                "lead_time_days": 5,
                "is_preferred": True,
            }
        ],
    )

    rows = (
        db.query(SupplierProduct)
        .filter(
            SupplierProduct.product_id == rice.id,
            SupplierProduct.supplier_id == rice.supplier_id,
        )
        .all()
    )
    assert len(rows) == 1
    assert (rows[0].unit_price, rows[0].lead_time_days) == (600.0, 5)
    assert rows[0].is_preferred is True


def test_supplier_products_is_idempotent(db, baseline):
    from src.backend.models_sourcing import SupplierProduct

    seeder.seed_supplier_products(db)
    before = db.query(SupplierProduct).count()
    outcomes = seeder.seed_supplier_products(db)
    assert outcomes["created"] == 0
    assert db.query(SupplierProduct).count() == before


# --- autonomy policy ----------------------------------------------------------


def test_autonomy_policy_is_written_from_the_scenario_spec(db, baseline):
    from src.backend.models_governance import AutonomyPolicy

    seeder.seed_autonomy_policy(db, {"mode": "assisted", "max_order_value": 50000})
    row = db.query(AutonomyPolicy).filter(AutonomyPolicy.scope_type == "global").one()
    assert row.mode == "assisted"
    assert row.max_order_value == 50000
    assert row.scope_value is None
    assert row.updated_at is not None


def test_autonomy_policy_leaves_unnamed_bounds_at_their_defaults(db, baseline):
    """A fixture inventing a blast-radius limit it was never asked for would be a
    governance decision disguised as test data."""
    from src.backend.models_governance import AutonomyPolicy

    seeder.seed_autonomy_policy(db, {"mode": "autonomous", "max_order_value": 50000})
    row = db.query(AutonomyPolicy).filter(AutonomyPolicy.scope_type == "global").one()
    assert row.max_orders_per_hour is None
    assert row.max_value_per_day is None


def test_autonomy_policy_updates_rather_than_duplicates(db, baseline):
    from src.backend.models_governance import AutonomyPolicy

    seeder.seed_autonomy_policy(db, {"mode": "assisted", "max_order_value": 50000})
    seeder.seed_autonomy_policy(db, {"mode": "autonomous", "max_order_value": 25000})
    rows = db.query(AutonomyPolicy).all()
    assert len(rows) == 1
    assert rows[0].mode == "autonomous"
    assert rows[0].max_order_value == 25000


def test_no_autonomy_spec_writes_no_policy(db, baseline):
    from src.backend.models_governance import AutonomyPolicy

    assert seeder.seed_autonomy_policy(db, None)["outcome"] == "skipped"
    assert db.query(AutonomyPolicy).count() == 0


# --- the two operational purchase orders --------------------------------------


def test_the_overdue_po_was_promised_in_the_past_and_never_arrived(db, baseline):
    """``po_overdue`` has nothing to fire on until a PO is actually overdue, and
    no fixture ships with one."""
    from src.backend.models import POStatus, PurchaseOrder

    seeder.seed_operational_pos(db)
    po = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.po_number == seeder.OVERDUE_PO_NUMBER)
        .one()
    )
    assert po.status == POStatus.submitted
    assert po.expected_delivery < clock.today()
    assert po.received_date is None


def test_the_partial_receipt_books_only_what_arrived(db, baseline):
    """The header says forty of one hundred and the ledger says forty. A short
    delivery is the interesting case precisely because the two can disagree."""
    from src.backend.models import POItem, PurchaseOrder, StockMovement

    seeder.seed_operational_pos(db)
    po = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.po_number == seeder.PARTIAL_PO_NUMBER)
        .one()
    )
    item = db.query(POItem).filter(POItem.po_id == po.id).one()
    assert (item.quantity_ordered, item.quantity_received) == (100, 40)

    movement = (
        db.query(StockMovement)
        .filter(StockMovement.reference_number.like("SIM-PARTIAL-%"))
        .one()
    )
    assert movement.quantity == 40


def test_the_partial_receipt_is_dated_when_it_landed(db, baseline):
    """Not today. The whole point of this package is that a movement's timestamp
    is stated, never defaulted."""
    from datetime import timedelta

    from src.backend.models import StockMovement

    seeder.seed_operational_pos(db)
    movement = (
        db.query(StockMovement)
        .filter(StockMovement.reference_number.like("SIM-PARTIAL-%"))
        .one()
    )
    assert movement.recorded_at.date() == (clock.now() - timedelta(days=5)).date()
    assert movement.recorded_at.date() != clock.today()


def test_purchase_order_totals_are_derived_from_the_line_items(db, baseline):
    """The same rule the baseline seeder's ``verify()`` enforces, so the header can
    never disagree with what was ordered."""
    from src.backend.models import POItem, PurchaseOrder

    seeder.seed_operational_pos(db)
    for number in seeder.SIM_PO_NUMBERS:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == number).one()
        items = db.query(POItem).filter(POItem.po_id == po.id).all()
        assert po.total_amount == pytest.approx(
            sum(item.quantity_ordered * item.unit_cost for item in items)
        )


def test_operational_pos_are_idempotent(db, baseline):
    from src.backend.models import PurchaseOrder, StockMovement

    seeder.seed_operational_pos(db)
    before = (db.query(PurchaseOrder).count(), db.query(StockMovement).count())
    second = seeder.seed_operational_pos(db)
    assert second["created"] == []
    assert (db.query(PurchaseOrder).count(), db.query(StockMovement).count()) == before


def test_the_baseline_purchase_orders_are_never_modified(db, baseline):
    """D1 and D2 name ``PO-2026-0001..0004`` in ``preserve_pos``. Rewriting dates on
    existing history to manufacture an overdue condition is the kind of fixture
    dishonesty this package exists to make unnecessary."""
    from src.backend.models import PurchaseOrder

    before = {
        po.po_number: (po.status, po.order_date, po.expected_delivery, po.total_amount)
        for po in db.query(PurchaseOrder).all()
    }
    seeder.seed_dataset(db, demand=None, stock=None, autonomy=None, supplier_products=None)
    after = {
        po.po_number: (po.status, po.order_date, po.expected_delivery, po.total_amount)
        for po in db.query(PurchaseOrder).all()
    }
    for number in ("PO-2026-0001", "PO-2026-0002", "PO-2026-0003", "PO-2026-0004"):
        assert after[number] == before[number], number


# --- the whole dataset --------------------------------------------------------


def test_the_documented_positions_survive_the_partial_receipt(db):
    """``seed_dataset`` snapshots each position *before* seeding the operational
    POs, so the forty bottles are absorbed into the opening balance rather than
    quietly moving a number doc 13 §7.1 states as fact."""
    from src.backend.models import Product, StockLevel

    seeder.seed_dataset(db, demand=None, stock=None, autonomy=None, supplier_products=None)
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


def test_seed_dataset_produces_a_dense_history(db):
    result = seeder.seed_dataset(
        db, demand=None, stock=None, autonomy={"mode": "assisted"}, supplier_products=None
    )
    assert result["history"]["distinct_recorded_dates"] >= 90
    assert result["history"]["sufficient_products"] >= 3


def test_seed_dataset_ledger_invariant(db):
    from sqlalchemy import func

    from src.backend.models import Product, StockLevel, StockMovement

    seeder.seed_dataset(db, demand=None, stock=None, autonomy=None, supplier_products=None)
    for product in db.query(Product).all():
        ledger = int(
            db.query(func.coalesce(func.sum(StockMovement.quantity), 0))
            .filter(StockMovement.product_id == product.id)
            .scalar()
            or 0
        )
        stock = db.query(StockLevel).filter(StockLevel.product_id == product.id).first()
        assert stock.quantity_on_hand == ledger, product.sku
