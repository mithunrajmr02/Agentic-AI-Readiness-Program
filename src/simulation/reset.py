"""Return the database to the baseline so a scenario load is genuinely idempotent.

Doc 13 §4 specifies load as *reset → seed → set clock offset*, and calls it
idempotent. That word is doing real work: the pre-flight checklist loads a
scenario, verifies it, and loads it again, and the second load has to produce
byte-identical numbers. A seeder that is merely re-runnable — one that skips rows
it already sees — is not enough, because the history it skipped was written
relative to a ``clock.now()`` that has since moved.

So reset removes everything this package wrote and leaves everything it did not.

What goes
---------
* Movements stamped ``SIM-`` / ``recorded_by='simulation'`` — the whole backfill.
* ``PO-2026-0005`` and ``PO-2026-0006``, the operational cases, with their line
  items. They are deleted rather than reused because the partial receipt's ledger
  entry goes with the backfill; leaving the header behind while its movement
  disappeared would break the very invariant this package exists to protect.
* Derived analytics and governance rows — signals, decisions, approvals, agent
  runs, metric snapshots. Doc 13 §4: a load wipes derived state. Verifying a
  freshly loaded scenario against signals raised before the reload would be
  meaningless.
* Stock alerts, which are then recomputed from the restored positions.

What stays
----------
Suppliers, products, ``PO-2026-0001..0004`` and the baseline movement ledger (both
D1 and D2 name those POs in ``preserve_pos``), users, supplier catalogue terms, the
autonomy policy, and the ``demo_scenarios`` rows themselves — only their
``is_loaded`` flags are cleared.

Stock levels are **recomputed from the surviving ledger**, never restored from a
hardcoded table. A reset that asserted "rice is 167" would be a second source of
truth for a number the ledger already determines, and the two would eventually
disagree.

One thing reset deliberately does not do
----------------------------------------
It does not call ``events.reset()``. Event subscriptions are application wiring
registered at startup, not scenario state; clearing them would leave a running
server with no detectors attached and no error to explain why.
"""
import structlog
from sqlalchemy import inspect

from src.backend.models import (
    POItem,
    Product,
    PurchaseOrder,
    StockAlert,
    StockLevel,
    StockMovement,
)
from src.backend.models_simulation import DemoScenario
from src.backend.services.inventory_service import check_stock_alerts
from src.core import clock
from src.simulation.backfill import SIM_ACTOR, SIM_PREFIX
from src.simulation.seeder import SIM_PO_NUMBERS

logger = structlog.get_logger()

#: Derived state, cleared on every load. Order is FK-safe; the new→new references
#: are plain strings rather than foreign keys, so nothing here cascades.
DERIVED_TABLES = (
    ("approvals", "src.backend.models_governance", "Approval"),
    ("decisions", "src.backend.models_governance", "Decision"),
    ("agent_runs", "src.backend.models_analytics", "AgentRun"),
    ("metric_snapshots", "src.backend.models_analytics", "MetricSnapshot"),
    ("signals", "src.backend.models_analytics", "Signal"),
)


def _clear_derived(db) -> dict:
    """Delete every derived row whose table actually exists on this database."""
    import importlib

    inspector = inspect(db.get_bind())
    deleted = {}
    for table_name, module_path, class_name in DERIVED_TABLES:
        if not inspector.has_table(table_name):
            continue
        model = getattr(importlib.import_module(module_path), class_name)
        deleted[table_name] = db.query(model).delete(synchronize_session=False)
    return deleted


def _clear_simulation_purchase_orders(db) -> list[str]:
    removed = []
    for po in (
        db.query(PurchaseOrder).filter(PurchaseOrder.po_number.in_(SIM_PO_NUMBERS)).all()
    ):
        db.query(POItem).filter(POItem.po_id == po.id).delete(synchronize_session=False)
        db.delete(po)
        removed.append(po.po_number)
    return removed


def _clear_simulation_movements(db) -> int:
    return (
        db.query(StockMovement)
        .filter(
            (StockMovement.reference_number.like(f"{SIM_PREFIX}%"))
            | (StockMovement.recorded_by == SIM_ACTOR)
        )
        .delete(synchronize_session=False)
    )


def _rebuild_stock_levels(db) -> dict[str, int]:
    """Set every on-hand position to the sum of its surviving movements."""
    from sqlalchemy import func

    positions = {}
    for product in db.query(Product).order_by(Product.id).all():
        ledger = int(
            db.query(func.coalesce(func.sum(StockMovement.quantity), 0))
            .filter(StockMovement.product_id == product.id)
            .scalar()
            or 0
        )
        stock = db.query(StockLevel).filter(StockLevel.product_id == product.id).first()
        if stock is None:
            stock = StockLevel(product_id=product.id, quantity_on_hand=0, quantity_reserved=0)
            db.add(stock)
            db.flush()
        stock.quantity_on_hand = ledger
        positions[product.sku] = ledger
    return positions


def reset_simulation(db, *, reset_clock: bool = True) -> dict:
    """Remove everything this package wrote and restore the baseline positions.

    Safe to call on a database that has never been seeded: every step is a delete
    over a filtered set, and an empty set deletes nothing.
    """
    derived = _clear_derived(db)
    purchase_orders = _clear_simulation_purchase_orders(db)
    movements = _clear_simulation_movements(db)

    # Alerts are recomputed rather than resolved in place, so a reload cannot
    # accumulate a growing tail of stale resolved rows.
    alerts = db.query(StockAlert).delete(synchronize_session=False)
    db.flush()

    positions = _rebuild_stock_levels(db)
    for product in db.query(Product).order_by(Product.id).all():
        stock = db.query(StockLevel).filter(StockLevel.product_id == product.id).first()
        if stock is not None:
            check_stock_alerts(product, stock, db)

    unloaded = (
        db.query(DemoScenario)
        .filter(DemoScenario.is_loaded.is_(True))
        .update({"is_loaded": False, "loaded_at": None}, synchronize_session=False)
    )
    db.commit()

    if reset_clock:
        clock.reset()

    summary = {
        "movements_deleted": movements,
        "purchase_orders_deleted": purchase_orders,
        "alerts_deleted": alerts,
        "derived_deleted": derived,
        "scenarios_unloaded": unloaded,
        "positions": positions,
    }
    logger.info(
        "simulation_reset",
        poc_id="POC-07",
        movements_deleted=movements,
        purchase_orders_deleted=purchase_orders,
        derived_deleted=derived,
    )
    return summary
