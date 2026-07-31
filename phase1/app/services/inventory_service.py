from datetime import date
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import (
    Product, StockLevel, StockMovement, PurchaseOrder, POItem,
    StockAlert, MovementType, POStatus, CATEGORY_PREFIXES
)
import structlog

logger = structlog.get_logger()


def generate_sku(category: str, db: Session) -> str:
    prefix = CATEGORY_PREFIXES.get(category, "GEN")
    count = db.query(Product).filter(Product.sku.like(f"SKU-{prefix}-%")).count()
    return f"SKU-{prefix}-{count + 1:04d}"


def generate_po_number(db: Session) -> str:
    year = date.today().year
    count = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number.like(f"PO-{year}-%")
    ).count()
    return f"PO-{year}-{count + 1:04d}"


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

    if available == 0:
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


def receive_purchase_order(po_id: int, db: Session) -> PurchaseOrder:
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise ValueError(f"Purchase order {po_id} not found")

    if po.status == POStatus.received:
        raise ValueError(f"Purchase order {po.po_number} has already been received")

    if po.status == POStatus.cancelled:
        raise ValueError(f"Cannot receive cancelled purchase order {po.po_number}")

    po.status = POStatus.received
    po.received_date = date.today()

    for item in po.items:
        qty = item.quantity_received or item.quantity_ordered
        item.quantity_received = qty

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
            notes=f"Received from PO {po.po_number}"
        )
        db.add(movement)

        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            check_stock_alerts(product, stock, db)

    db.commit()
    db.refresh(po)

    logger.info("po_received", poc_id="POC-07", phase="P1", po_number=po.po_number)
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
            if available == 0:
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

