"""Supplier reliability scoring and scorecard generation (WS-7).

15-SHARED-CONTRACTS.md §10 / 14-PARALLEL-WORKSTREAMS.md §WS-7.
Calculates lead-time performance and reliability metrics from completed PurchaseOrder records.
Honesty invariant: sample_size < 5 is reported with on_time_rate=None to prevent fabricating
reliability percentages from insufficient historical observations (n = 1 honesty rule).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional

from sqlalchemy.orm import Session

from src.backend.models import PurchaseOrder, Supplier


@dataclass(frozen=True)
class Scorecard:
    """Supplier performance scorecard contract (doc 15 §10)."""

    supplier_id: int
    on_time_rate: Optional[float]  # None when sample_size == 0 or sample_size < 5
    sample_size: int  # ALWAYS rendered beside the rate
    avg_days_late: Optional[float]
    contract_lead_time: int
    measured_lead_time: Optional[float]
    drift_days: Optional[float]

    def to_dict(self) -> dict:
        return asdict(self)


def scorecard(db: Session, supplier_id: int) -> Scorecard:
    """Compute supplier scorecard from completed purchase order delivery records.

    15-SHARED-CONTRACTS.md §10.
    Queries PurchaseOrder records where received_date is set.
    """
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier is None:
        raise ValueError(f"Supplier with ID {supplier_id} not found")

    contract_lead_time = int(supplier.lead_time_days) if supplier.lead_time_days is not None else 7

    pos = (
        db.query(PurchaseOrder)
        .filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.received_date.isnot(None),
        )
        .all()
    )

    lead_times: list[int] = []
    days_late_list: list[int] = []
    on_time_count = 0

    for po in pos:
        if po.received_date and po.order_date:
            lt = (po.received_date - po.order_date).days
            lead_times.append(lt)

            if po.expected_delivery:
                days_late = max(0, (po.received_date - po.expected_delivery).days)
                if po.received_date <= po.expected_delivery:
                    on_time_count += 1
            else:
                days_late = max(0, lt - contract_lead_time)
                if lt <= contract_lead_time:
                    on_time_count += 1

            days_late_list.append(days_late)

    sample_size = len(lead_times)
    if sample_size == 0:
        return Scorecard(
            supplier_id=supplier_id,
            on_time_rate=None,
            sample_size=0,
            avg_days_late=None,
            contract_lead_time=contract_lead_time,
            measured_lead_time=None,
            drift_days=None,
        )

    avg_lead_time = round(sum(lead_times) / float(sample_size), 2)
    avg_days_late = round(sum(days_late_list) / float(sample_size), 2)
    drift_days = round(avg_lead_time - contract_lead_time, 2)

    # Honesty invariant (§4.7 / §WS-7): sample_size < 5 never produces a reliability percentage
    on_time_rate = round(on_time_count / float(sample_size), 4) if sample_size >= 5 else None

    return Scorecard(
        supplier_id=supplier_id,
        on_time_rate=on_time_rate,
        sample_size=sample_size,
        avg_days_late=avg_days_late,
        contract_lead_time=contract_lead_time,
        measured_lead_time=avg_lead_time,
        drift_days=drift_days,
    )
