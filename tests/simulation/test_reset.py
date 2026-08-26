"""Reset: the precondition that makes "idempotent load" mean something.

Doc 13 §4 specifies load as *reset → seed → set clock offset*, and calls it
idempotent. A seeder that merely skips rows it already sees would not be enough,
because the history it skipped was written relative to a ``clock.now()`` that has
since moved. So reset removes everything this package wrote and leaves everything
it did not.
"""
import pytest

from src.simulation import seeder
from src.simulation.reset import reset_simulation

BASELINE_POSITIONS = {
    "SKU-GRO-0001": 167,
    "SKU-ELC-0001": 4,
    "SKU-ELC-0002": 0,
    "SKU-HHD-0001": 50,
    "SKU-PRC-0001": 0,
}


def _positions(db):
    from src.backend.models import Product, StockLevel

    return {
        product.sku: db.query(StockLevel)
        .filter(StockLevel.product_id == product.id)
        .first()
        .quantity_on_hand
        for product in db.query(Product).all()
    }


def _ledger(db, sku):
    from sqlalchemy import func

    from src.backend.models import Product, StockMovement

    product = db.query(Product).filter(Product.sku == sku).first()
    return int(
        db.query(func.coalesce(func.sum(StockMovement.quantity), 0))
        .filter(StockMovement.product_id == product.id)
        .scalar()
        or 0
    )


@pytest.fixture
def seeded(db):
    seeder.seed_dataset(
        db, demand=None, stock=None, autonomy={"mode": "assisted"}, supplier_products=None
    )
    return db


def test_the_baseline_satisfies_the_ledger_invariant(db):
    """The precondition reset depends on.

    ``_rebuild_stock_levels`` recomputes every position from the surviving ledger
    rather than restoring a hardcoded table — a second source of truth for a number
    the ledger already determines would eventually disagree with it. That is only
    correct because the baseline seeder's own movements already sum to its stated
    positions. If that ever stops being true, this test fails first and explains
    why the reset arithmetic went wrong.
    """
    seeder.ensure_baseline(db)
    assert _positions(db) == BASELINE_POSITIONS
    for sku, expected in BASELINE_POSITIONS.items():
        assert _ledger(db, sku) == expected, sku


def test_reset_restores_the_baseline_positions(db, seeded):
    reset_simulation(db)
    assert _positions(db) == BASELINE_POSITIONS


def test_reset_removes_the_simulation_movements_and_keeps_the_baseline(db, seeded):
    from src.backend.models import StockMovement
    from src.simulation.backfill import SIM_ACTOR, SIM_PREFIX

    assert db.query(StockMovement).filter(StockMovement.recorded_by == SIM_ACTOR).count() > 0

    reset_simulation(db)

    assert db.query(StockMovement).filter(StockMovement.recorded_by == SIM_ACTOR).count() == 0
    assert (
        db.query(StockMovement)
        .filter(StockMovement.reference_number.like(f"{SIM_PREFIX}%"))
        .count()
        == 0
    )
    # The baseline's own eleven movements are untouched.
    assert db.query(StockMovement).count() == 11


def test_reset_collapses_the_ledger_back_to_a_single_date(db, seeded):
    """The mirror image of the headline test: the ninety dates were entirely this
    package's work, and reset removes exactly that work."""
    from src.simulation.backfill import distinct_recorded_dates

    assert distinct_recorded_dates(db) >= 90
    reset_simulation(db)
    assert distinct_recorded_dates(db) == 1


def test_reset_removes_the_operational_pos_and_keeps_the_baseline_four(db, seeded):
    from src.backend.models import POItem, PurchaseOrder

    reset_simulation(db)

    numbers = {po.po_number for po in db.query(PurchaseOrder).all()}
    assert numbers == {"PO-2026-0001", "PO-2026-0002", "PO-2026-0003", "PO-2026-0004"}

    # No orphaned line items left behind pointing at a deleted header.
    po_ids = {po.id for po in db.query(PurchaseOrder).all()}
    assert all(item.po_id in po_ids for item in db.query(POItem).all())


def test_reset_clears_derived_signals(db, seeded, raise_signals):
    """Verifying a freshly loaded scenario against signals raised before the
    reload would be meaningless, so derived state goes with the history."""
    from src.backend.models_analytics import Signal

    raise_signals([{"signal_type": "threshold_breach", "sku": "SKU-ELC-0001", "severity": "high"}])
    assert db.query(Signal).count() == 1

    result = reset_simulation(db)
    assert db.query(Signal).count() == 0
    assert result["derived_deleted"]["signals"] == 1


def test_reset_keeps_users_suppliers_products_and_catalogue(db, seeded):
    from src.backend.models import Product, Supplier, User
    from src.backend.models_governance import AutonomyPolicy
    from src.backend.models_sourcing import SupplierProduct

    before = (
        db.query(User).count(),
        db.query(Supplier).count(),
        db.query(Product).count(),
        db.query(SupplierProduct).count(),
        db.query(AutonomyPolicy).count(),
    )
    reset_simulation(db)
    assert (
        db.query(User).count(),
        db.query(Supplier).count(),
        db.query(Product).count(),
        db.query(SupplierProduct).count(),
        db.query(AutonomyPolicy).count(),
    ) == before


def test_reset_recomputes_alerts_from_the_restored_positions(db, seeded):
    """Alerts are deleted and recomputed rather than resolved in place, so a
    reload cannot accumulate a growing tail of stale resolved rows."""
    from src.backend.models import Product, StockAlert

    reset_simulation(db)

    alerts = db.query(StockAlert).all()
    assert all(alert.is_resolved is False for alert in alerts)

    alerting = {
        db.query(Product).filter(Product.id == alert.product_id).first().sku for alert in alerts
    }
    # Both out-of-stock SKUs, plus nothing that is comfortably above its reorder point.
    assert {"SKU-ELC-0002", "SKU-PRC-0001"} <= alerting
    assert "SKU-GRO-0001" not in alerting


def test_reset_returns_the_clock_to_real_time(db, seeded, demo_mode):
    from src.core import clock

    clock.set_offset(30)
    assert clock.offset_days() == 30
    reset_simulation(db)
    assert clock.offset_days() == 0


def test_reset_can_leave_the_clock_alone(db, seeded, demo_mode):
    from src.core import clock

    clock.set_offset(30)
    reset_simulation(db, reset_clock=False)
    assert clock.offset_days() == 30


def test_reset_does_not_unsubscribe_event_handlers(db, seeded):
    """A deliberate divergence, and the reason it is deliberate.

    ``events.reset()`` names WS-2's scenario reloads in its docstring, but
    subscriptions are application wiring registered at startup — not scenario
    state. Clearing them mid-run would leave a live server with no detectors
    attached and no error to explain why. Filed in the integration requests.
    """
    from src.core import events

    seen = []
    events.subscribe("test.reset.probe", seen.append)
    try:
        reset_simulation(db)
        events.emit("test.reset.probe", {"still": "subscribed"})
        assert seen == [{"still": "subscribed"}]
    finally:
        events._subscribers.pop("test.reset.probe", None)


def test_reset_on_an_unseeded_database_is_a_no_op(db):
    """Every step is a delete over a filtered set, and an empty set deletes
    nothing — so reset is safe to call first, which is exactly what load does."""
    result = reset_simulation(db)
    assert result["movements_deleted"] == 0
    assert result["purchase_orders_deleted"] == []
    assert result["positions"] == {}


def test_reset_is_idempotent(db, seeded):
    first = reset_simulation(db)
    second = reset_simulation(db)
    assert second["movements_deleted"] == 0
    assert second["purchase_orders_deleted"] == []
    assert second["positions"] == first["positions"]


def test_reset_leaves_the_scenario_rows_but_clears_the_loaded_flags(db, seeded, demo_mode):
    from src.backend.models_simulation import DemoScenario
    from src.simulation.scenarios import SCENARIO_KEYS, load_scenario

    load_scenario(db, "D1_governed_order")
    assert db.query(DemoScenario).filter(DemoScenario.is_loaded.is_(True)).count() == 1

    reset_simulation(db)

    assert db.query(DemoScenario).count() == len(SCENARIO_KEYS)
    assert db.query(DemoScenario).filter(DemoScenario.is_loaded.is_(True)).count() == 0
