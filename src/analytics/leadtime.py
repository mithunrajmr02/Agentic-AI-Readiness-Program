"""Supplier lead time measurement and performance (WS-1).

15-SHARED-CONTRACTS.md §5.1, §5.2, §10 and manual §6 line 70, §6 line 74.
Pure function querying completed PurchaseOrder records for a supplier.
"""
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.analytics.sufficiency import Computed
from src.backend.models import PurchaseOrder


def measured_lead_time(db: Session, supplier_id: int) -> Computed:
    """Compute measured supplier lead time and on-time rate from completed POs.

    15-SHARED-CONTRACTS.md §5.2, §10.
    Pure read query against purchase_orders.
    Returns :class:`Computed` with:
    - 'none' if 0 completed POs -> value is None
    - 'thin' if 1-2 completed POs -> value is avg lead time (float)
    - 'sufficient' if >= 3 completed POs -> value is avg lead time (float)
    """
    pos = (
        db.query(PurchaseOrder)
        .filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.received_date.isnot(None),
        )
        .all()
    )

    lead_times: list[int] = []
    on_time_count = 0

    for po in pos:
        if po.received_date and po.order_date:
            lt = (po.received_date - po.order_date).days
            lead_times.append(lt)
            if po.expected_delivery and po.received_date <= po.expected_delivery:
                on_time_count += 1

    sample_size = len(lead_times)
    inputs: dict[str, Any] = {
        "supplier_id": supplier_id,
        "sample_size": sample_size,
    }

    if sample_size == 0:
        return Computed(
            value=None,
            sufficiency="none",
            inputs=inputs,
            formula="avg(received_date - order_date)",
            citation="manual §6 line 74",
            sample_size=0,
            span_days=0,
        )

    avg_lt = round(sum(lead_times) / float(sample_size), 2)
    on_time_rate = round(on_time_count / float(sample_size), 4)
    inputs["avg_lead_time_days"] = avg_lt
    inputs["on_time_count"] = on_time_count
    inputs["on_time_rate"] = on_time_rate

    sufficiency_status = "sufficient" if sample_size >= 3 else "thin"

    return Computed(
        value=avg_lt,
        sufficiency=sufficiency_status,
        inputs=inputs,
        formula="avg(received_date - order_date)",
        citation="manual §6 line 74",
        sample_size=sample_size,
        span_days=0,
    )
