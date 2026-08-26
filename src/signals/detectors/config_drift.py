"""Configuration drift detector (WS-3).

Grounding: manual §3 line 33 vs measured velocity; §3 line 35 worked example.
Fires when the configured reorder point diverges significantly (> 20%) from the
reorder point implied by measured demand and supplier lead time.
"""
from typing import Optional

from sqlalchemy.orm import Session

from src.backend.models import Product, StockLevel
from src.signals.analytics_adapter import derive_reorder_point
from src.signals.dedup import dedup_key_for
from src.signals.detectors.base import SignalCandidate


SIGNAL_TYPE = "config_drift"
DEFAULT_TOLERANCE_PCT = 0.20  # 20% relative drift tolerance


def detect(
    db: Session,
    product_id: int,
    tolerance: float = DEFAULT_TOLERANCE_PCT,
) -> Optional[SignalCandidate]:
    """Check whether a product's configured reorder point has drifted from implied demand."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    stock = db.query(StockLevel).filter(StockLevel.product_id == product_id).first()
    if not stock:
        return None

    stored_rop = getattr(product, "reorder_point", 0) or 0

    computed = derive_reorder_point(db, product_id)
    if (
        computed.value is None
        or computed.value <= 0
        or computed.sufficiency in ("insufficient", "none")
    ):
        return None

    computed_rop = computed.value
    relative_divergence = abs(stored_rop - computed_rop) / computed_rop

    if relative_divergence > tolerance:
        drift_pct = round(relative_divergence * 100.0, 1)
        direction = "under-configured" if stored_rop < computed_rop else "over-configured"

        if relative_divergence >= 0.50:
            severity = "critical"
        elif relative_divergence >= 0.20:
            severity = "high"
        else:
            severity = "medium"

        detected_from = (
            f"Config drift: configured reorder point ({stored_rop}) is {direction} "
            f"by {drift_pct}% compared to demand-implied reorder point ({computed_rop:.1f})"
        )

        evidence = {
            "product_id": product.id,
            "sku": product.sku,
            "product_name": product.name,
            "configured_reorder_point": stored_rop,
            "computed_reorder_point": computed_rop,
            "relative_drift": round(relative_divergence, 4),
            "drift_percentage": drift_pct,
            "tolerance_percentage": round(tolerance * 100.0, 1),
            "direction": direction,
            "computed_inputs": computed.inputs,
            "formula": "abs(configured_reorder_point - computed_reorder_point) / computed_reorder_point > tolerance",
            "citation": "manual §3 line 33, §3 line 35",
        }

        return SignalCandidate(
            signal_type=SIGNAL_TYPE,
            severity=severity,
            product_id=product.id,
            supplier_id=product.supplier_id,
            po_id=None,
            detected_from=detected_from,
            evidence=evidence,
            sufficiency=computed.sufficiency,
            dedup_key=dedup_key_for(SIGNAL_TYPE, product_id=product.id),
        )

    return None


def detect_all(db: Session, tolerance: float = DEFAULT_TOLERANCE_PCT) -> list[SignalCandidate]:
    """Scan all products for configuration drift."""
    products = db.query(Product.id).all()
    results = []
    for (pid,) in products:
        candidate = detect(db, pid, tolerance=tolerance)
        if candidate:
            results.append(candidate)
    return results
