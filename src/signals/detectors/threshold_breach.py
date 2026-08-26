"""Threshold breach detector (WS-3).

Grounding: manual §4 line 41 ("Triggered when quantity_available <= reorder_point").
Fires when on-hand stock falls to or below configured reorder point.
"""
from typing import Optional

from sqlalchemy.orm import Session

from src.backend.models import Product, StockLevel
from src.signals.dedup import dedup_key_for
from src.signals.detectors.base import SignalCandidate


SIGNAL_TYPE = "threshold_breach"


def detect(db: Session, product_id: int) -> Optional[SignalCandidate]:
    """Check whether a single product is in threshold breach."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    stock = db.query(StockLevel).filter(StockLevel.product_id == product_id).first()
    if not stock:
        return None

    on_hand = stock.quantity_on_hand or 0
    reorder_point = getattr(product, "reorder_point", 0) or 0

    if on_hand <= reorder_point:
        # manual §4 line 43: quantity_available = 0 is a critical alert
        if on_hand <= 0:
            severity = "critical"
            detected_from = (
                f"Out of stock: current on-hand is {on_hand} (reorder point {reorder_point})"
            )
        elif on_hand <= reorder_point / 2:
            severity = "high"
            detected_from = (
                f"Low stock breach: on-hand {on_hand} is well below reorder point {reorder_point}"
            )
        else:
            severity = "medium"
            detected_from = (
                f"Threshold breach: on-hand {on_hand} is at or below reorder point {reorder_point}"
            )

        evidence = {
            "product_id": product.id,
            "sku": product.sku,
            "product_name": product.name,
            "quantity_on_hand": on_hand,
            "reorder_point": reorder_point,
            "difference": reorder_point - on_hand,
            "unit_price": product.unit_price,
            "cost_price": product.cost_price,
            "formula": "quantity_available <= reorder_point",
            "citation": "manual §4 line 41",
        }

        return SignalCandidate(
            signal_type=SIGNAL_TYPE,
            severity=severity,
            product_id=product.id,
            supplier_id=product.supplier_id,
            po_id=None,
            detected_from=detected_from,
            evidence=evidence,
            sufficiency="sufficient",
            dedup_key=dedup_key_for(SIGNAL_TYPE, product_id=product.id),
        )

    return None


def detect_all(db: Session) -> list[SignalCandidate]:
    """Scan all products for threshold breaches."""
    products = db.query(Product.id).all()
    results = []
    for (pid,) in products:
        candidate = detect(db, pid)
        if candidate:
            results.append(candidate)
    return results
