"""Data insufficiency / cold-start detector (WS-3).

Grounding: manual §4 line 45 ("The system may also suggest reorder quantities
based on historical consumption patterns" — absent history, the condition fails).
15-SHARED-CONTRACTS.md §5.4 / §6.
Fires for any active stocked SKU that lacks the statistical minimum (14 sale events across
21 distinct days) required to compute a defensible daily sales velocity.
"""
from typing import Optional

from sqlalchemy.orm import Session

from src.backend.models import Product
from src.signals.analytics_adapter import compute_daily_demand
from src.signals.dedup import dedup_key_for
from src.signals.detectors.base import SignalCandidate


SIGNAL_TYPE = "data_insufficient"


def detect(db: Session, product_id: int) -> Optional[SignalCandidate]:
    """Check whether a product has insufficient sales history for velocity modeling."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    demand = compute_daily_demand(db, product_id)
    if demand.sufficiency in ("insufficient", "none"):
        sample_size = demand.sample_size
        distinct_days = demand.inputs.get("distinct_sale_days", 0)

        detected_from = (
            f"Data insufficient: {product.name} ({product.sku}) has only {sample_size} "
            f"sale event(s) across {distinct_days} distinct day(s) "
            f"(minimum requirement: 14 sale events across 21 distinct days)"
        )

        evidence = {
            "product_id": product.id,
            "sku": product.sku,
            "product_name": product.name,
            "category": getattr(product.category, "name", str(product.category)) if product.category else None,
            "sufficiency": demand.sufficiency,
            "sample_size": sample_size,
            "distinct_sale_days": distinct_days,
            "needed": "14 sale events across 21 distinct days",
            "have": f"{sample_size} sale event(s) across {distinct_days} distinct day(s)",
            "formula": "sufficiency in ('insufficient', 'none')",
            "citation": "manual §4 line 45",
        }

        severity = "medium" if demand.sufficiency == "insufficient" else "low"

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
    """Scan all products for missing/insufficient sales history."""
    products = db.query(Product.id).all()
    results = []
    for (pid,) in products:
        candidate = detect(db, pid)
        if candidate:
            results.append(candidate)
    return results
