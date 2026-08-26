"""Projected stockout / breach detector (WS-3).

Grounding: manual §3 line 33 rearranged; §4 line 45.
Fires when current stock is currently above reorder point, but sales velocity
implies inventory will deplete below safety stock within the supplier lead time.
"""
from typing import Optional

from sqlalchemy.orm import Session

from src.backend.models import Product, StockLevel, Supplier
from src.signals.analytics_adapter import compute_daily_demand
from src.signals.dedup import dedup_key_for
from src.signals.detectors.base import SignalCandidate


SIGNAL_TYPE = "projected_breach"


def detect(
    db: Session,
    product_id: int,
    safety_stock_days: int = 2,
) -> Optional[SignalCandidate]:
    """Check whether a product is projected to breach before an order can arrive."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    stock = db.query(StockLevel).filter(StockLevel.product_id == product_id).first()
    if not stock:
        return None

    on_hand = stock.quantity_on_hand or 0
    configured_rop = getattr(product, "reorder_point", 0) or 0

    # If it's already in threshold breach, threshold_breach handles it
    if on_hand <= configured_rop:
        return None

    demand = compute_daily_demand(db, product_id)
    if demand.value is None or demand.value <= 0 or demand.sufficiency in ("insufficient", "none"):
        return None

    velocity = demand.value
    lead_time_days = 5
    if product.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
        if supplier and supplier.lead_time_days:
            lead_time_days = supplier.lead_time_days

    # Required stock during lead time plus buffer
    lead_time_consumption = velocity * lead_time_days
    safety_stock = velocity * safety_stock_days
    projected_on_hand_at_arrival = on_hand - lead_time_consumption

    # Trigger: inventory will drop into safety stock or zero before arrival
    if projected_on_hand_at_arrival <= safety_stock:
        days_of_cover = round(on_hand / velocity, 1)
        severity = "critical" if projected_on_hand_at_arrival <= 0 else "high"

        detected_from = (
            f"Projected breach: {days_of_cover} days of stock cover remaining, "
            f"which cannot cover supplier lead time ({lead_time_days} days) + safety stock"
        )

        evidence = {
            "product_id": product.id,
            "sku": product.sku,
            "product_name": product.name,
            "quantity_on_hand": on_hand,
            "configured_reorder_point": configured_rop,
            "average_daily_demand": velocity,
            "lead_time_days": lead_time_days,
            "safety_stock_days": safety_stock_days,
            "lead_time_consumption": round(lead_time_consumption, 2),
            "safety_stock": round(safety_stock, 2),
            "projected_on_hand_at_arrival": round(projected_on_hand_at_arrival, 2),
            "days_of_cover": days_of_cover,
            "formula": "quantity_available - (velocity * lead_time_days) <= safety_stock",
            "citation": "manual §3 line 33, §4 line 45",
        }

        return SignalCandidate(
            signal_type=SIGNAL_TYPE,
            severity=severity,
            product_id=product.id,
            supplier_id=product.supplier_id,
            po_id=None,
            detected_from=detected_from,
            evidence=evidence,
            sufficiency=demand.sufficiency,
            dedup_key=dedup_key_for(SIGNAL_TYPE, product_id=product.id),
        )

    return None


def detect_all(db: Session) -> list[SignalCandidate]:
    """Scan all products for projected breaches."""
    products = db.query(Product.id).all()
    results = []
    for (pid,) in products:
        candidate = detect(db, pid)
        if candidate:
            results.append(candidate)
    return results
