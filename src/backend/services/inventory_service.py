from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.backend.models import (
    Product, StockLevel, StockMovement, PurchaseOrder, POItem,
    StockAlert, MovementType, POStatus, CATEGORY_PREFIXES
)
from src.execution import clock
from src.core import events
import structlog

logger = structlog.get_logger()

# WS-9 defect fix (:133): a PO is receivable only from these statuses. Was a
# blacklist that only excluded `cancelled` (any other unexpected status, plus
# `draft`, passed through silently); this is now an explicit whitelist so an
# unrecognised status fails safe. `draft` stays receivable -- the only
# existing PO-creation path (`POST /api/v1/orders`) hard-codes `draft` and the
# graded API suite (`test_receive_po_updates_stock`) receives directly from
# it, so narrowing this further would be a regression, not a fix.
RECEIVABLE_PO_STATUSES = (POStatus.draft, POStatus.submitted, POStatus.acknowledged)


def _next_sequence(db: Session, column, prefix: str) -> int:
    """Return the next free sequence number for identifiers shaped `<prefix><NNNN>`.

    Counting rows and adding one is only correct while nothing is ever deleted.
    Reproduced against the live database: with PO-2026-0001..0009 on file,
    deleting one row left 8 rows, so `count() + 1` proposed PO-2026-0009 -- which
    still existed -- and `POST /api/v1/orders` answered HTTP 500 on the
    `po_number` UNIQUE constraint. Every subsequent order creation failed the
    same way, permanently, because the count never catches back up. The same
    defect applied to `generate_sku`.

    Deriving from the highest number issued rather than the population size also
    means deleting a mid-sequence identifier no longer drags every future one
    backwards: retiring PO-2026-0008 leaves PO-2026-0009 in place and the next
    order becomes PO-2026-0010. It is not a monotonic guarantee -- deleting the
    *highest* identifier does free its number for reuse, and only a persisted
    counter would prevent that -- but it removes the collision.

    The trailing loop closes gaps left by identifiers that do not parse or that
    were inserted out of band. It does not make this safe against two concurrent
    inserts -- that needs a retry on IntegrityError or a real sequence -- but
    SQLite serialises writers, and the reproduced failure was deletion, not
    concurrency.
    """
    highest = 0
    taken = set()
    for (value,) in db.query(column).filter(column.like(f"{prefix}%")).all():
        taken.add(value)
        try:
            highest = max(highest, int(str(value)[len(prefix):]))
        except (TypeError, ValueError):
            continue  # hand-edited or legacy identifier; it cannot own a slot

    candidate = highest + 1
    while f"{prefix}{candidate:04d}" in taken:
        candidate += 1
    return candidate


def generate_sku(category: str, db: Session) -> str:
    prefix = CATEGORY_PREFIXES.get(category, "GEN")
    return f"SKU-{prefix}-{_next_sequence(db, Product.sku, f'SKU-{prefix}-'):04d}"


def generate_po_number(db: Session) -> str:
    year = clock.today().year
    return f"PO-{year}-{_next_sequence(db, PurchaseOrder.po_number, f'PO-{year}-'):04d}"


def check_stock_alerts(product: Product, stock: StockLevel, db: Session) -> None:
    if not product or not stock:
        return

    available = stock.quantity_available
    reorder_point = product.reorder_point or 0

    if available > reorder_point:
        # Resolve existing alerts if stock level is healthy
        existing_alerts = db.query(StockAlert).filter(
            StockAlert.product_id == product.id,
            StockAlert.is_resolved == False
        ).all()
        for alert in existing_alerts:
            alert.is_resolved = True
        return

    # Check existing active alert type
    existing_alerts = db.query(StockAlert).filter(
        StockAlert.product_id == product.id,
        StockAlert.is_resolved == False
    ).all()

    for alert in existing_alerts:
        alert.is_resolved = True

    # `<= 0`, not `== 0`: quantity_available is no longer clamped at zero, so an
    # oversold product can be negative. Spec rule 2 says "quantity_available = 0
    # -> out_of_stock"; negative stock is strictly worse than zero and must not
    # fall through to the milder low_stock branch below.
    if available <= 0:
        alert = StockAlert(
            product_id=product.id,
            alert_type="out_of_stock",
            message=f"SKU {product.sku} is OUT OF STOCK."
        )
        db.add(alert)
        logger.info(
            "out_of_stock_alert",
            poc_id="POC-07",
            phase="P1",
            product_sku=product.sku,
            quantity_available=available,
        )
    elif available <= reorder_point:
        alert = StockAlert(
            product_id=product.id,
            alert_type="low_stock",
            message=f"SKU {product.sku}: only {available} units left (reorder point: {reorder_point})."
        )
        db.add(alert)
        logger.info(
            "low_stock_alert",
            poc_id="POC-07",
            phase="P1",
            product_sku=product.sku,
            quantity_available=available,
            reorder_point=reorder_point,
        )


def is_partially_received(po: PurchaseOrder) -> bool:
    """Derived predicate, not a status (file 09 §7.3) -- `POStatus` renders as
    VARCHAR + CHECK on SQLite and cannot gain a sixth `partially_received`
    member. Carries the quantities rather than a label.
    """
    return po.status in (POStatus.submitted, POStatus.acknowledged) and any(
        0 < (item.quantity_received or 0) < item.quantity_ordered for item in po.items
    )


def receive_purchase_order(
    po_id: int,
    db: Session,
    *,
    item_receipts: Optional[Dict[int, int]] = None,
    received_at: Optional[datetime] = None,
) -> PurchaseOrder:
    """Record a receipt against a PO. Supports partial and full receipt.

    `item_receipts` maps `po_item.id` -> quantity received in THIS event (not
    cumulative). Omitting an item, or the whole mapping, receives that item's
    full outstanding quantity -- the pre-existing full-receipt behaviour every
    current caller relies on.

    WS-9 defect fixes:
    - `:133` guard is now the `RECEIVABLE_PO_STATUSES` whitelist above.
    - `:137` used `date.today()`, bypassing the clock; now `clock.now()`
      (or an explicit `received_at`, e.g. a seeder backdating history).
    - `:140-141` `quantity_received or quantity_ordered` silently booked any
      partial receipt as complete. Each item's outstanding quantity is now
      tracked individually and the PO only advances to `received` once every
      item is fully received; a genuine partial receipt leaves the PO's
      status untouched (`is_partially_received` becomes true).
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise ValueError(f"Purchase order {po_id} not found")

    if po.status == POStatus.received:
        raise ValueError(f"Purchase order {po.po_number} has already been received")

    if po.status not in RECEIVABLE_PO_STATUSES:
        raise ValueError(
            f"Cannot receive cancelled purchase order {po.po_number}"
            if po.status == POStatus.cancelled
            else f"Purchase order {po.po_number} cannot be received while in status '{po.status.value}'"
        )

    receipt_time = received_at or clock.now()

    for item in po.items:
        already_received = item.quantity_received or 0
        outstanding = item.quantity_ordered - already_received

        if item_receipts is not None and item.id in item_receipts:
            qty = item_receipts[item.id]
        else:
            qty = outstanding

        if qty < 0 or qty > outstanding:
            raise ValueError(
                f"Cannot receive {qty} units of item {item.id}: only {outstanding} outstanding"
            )
        if qty == 0:
            continue

        item.quantity_received = already_received + qty

        stock = db.query(StockLevel).filter(StockLevel.product_id == item.product_id).first()
        if not stock:
            stock = StockLevel(product_id=item.product_id, quantity_on_hand=0)
            db.add(stock)
            db.flush()

        stock.quantity_on_hand += qty

        movement = StockMovement(
            product_id=item.product_id,
            movement_type=MovementType.receipt,
            quantity=qty,
            reference_number=po.po_number,
            notes=f"Received from PO {po.po_number}",
            recorded_at=receipt_time,
        )
        db.add(movement)
        events.emit("stock.movement_recorded", {"product_id": item.product_id, "quantity": qty, "movement_type": "receipt"})
        events.emit("stock.level_changed", {"product_id": item.product_id, "quantity_on_hand": stock.quantity_on_hand})

        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            check_stock_alerts(product, stock, db)

    if all((item.quantity_received or 0) >= item.quantity_ordered for item in po.items):
        po.status = POStatus.received
        po.received_date = receipt_time.date()

    db.commit()
    db.refresh(po)

    # Emit po.received event with days_late calculation
    days_late = (receipt_time.date() - po.expected_delivery).days if po.expected_delivery else 0
    events.emit("po.received", {"po_number": po.po_number, "days_late": max(0, days_late)})

    logger.info(
        "po_received", poc_id="POC-07", phase="P1", po_number=po.po_number,
        partial=is_partially_received(po),
    )
    return po


def get_dashboard_data(db: Session) -> Dict[str, Any]:
    products = db.query(Product).all()
    total_products = len(products)

    low_stock_count = 0
    out_of_stock_count = 0
    total_stock_value = 0.0

    for product in products:
        stock = product.stock_level
        if stock:
            available = stock.quantity_available
            # `<= 0` for the same reason as check_stock_alerts: an oversold
            # product has negative availability and is out of stock, not low.
            if available <= 0:
                out_of_stock_count += 1
            elif available <= (product.reorder_point or 0):
                low_stock_count += 1

            total_stock_value += (stock.quantity_on_hand or 0) * (product.cost_price or 0.0)

    open_po_count = db.query(PurchaseOrder).filter(
        PurchaseOrder.status.in_([POStatus.draft, POStatus.submitted, POStatus.acknowledged])
    ).count()

    return {
        "total_products": total_products,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "open_po_count": open_po_count,
        "total_stock_value": round(total_stock_value, 2),
    }

