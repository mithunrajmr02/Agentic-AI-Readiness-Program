"""Supplier reliability / lead-time drift detector (WS-3).

Grounding: manual §6 line 74 ("Supplier selection criteria include price competitiveness,
lead time reliability, quality compliance").
Fires when a supplier's actual delivery lead time exceeds contractual lead time,
or when on-time delivery rate falls below standard.
"""
from typing import Optional

from sqlalchemy.orm import Session

from src.backend.models import Supplier
from src.signals.analytics_adapter import measured_lead_time
from src.signals.dedup import dedup_key_for
from src.signals.detectors.base import SignalCandidate


SIGNAL_TYPE = "supplier_drift"


def detect(db: Session, supplier_id: int) -> Optional[SignalCandidate]:
    """Check whether a supplier has drifted from contract lead time or reliability targets."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        return None

    measured = measured_lead_time(db, supplier_id)
    if measured.value is None or measured.sample_size == 0:
        return None

    contract_lt = supplier.lead_time_days or 5
    avg_measured_lt = measured.value
    drift_days = round(avg_measured_lt - contract_lt, 2)
    on_time_rate = measured.inputs.get("on_time_rate", 1.0)

    # Condition: measured lead time > contracted, or on-time rate < 80%
    is_late_drift = drift_days > 0.5
    is_unreliable = on_time_rate < 0.80

    if is_late_drift or is_unreliable:
        if drift_days >= 3.0 or on_time_rate < 0.50:
            severity = "high"
        else:
            severity = "medium"

        if is_late_drift and is_unreliable:
            detected_from = (
                f"Supplier {supplier.name} lead time drift ({avg_measured_lt:.1f}d vs contract {contract_lt}d, "
                f"+{drift_days:.1f}d) and low on-time rate ({on_time_rate * 100:.1f}%)"
            )
        elif is_late_drift:
            detected_from = (
                f"Supplier {supplier.name} measured lead time ({avg_measured_lt:.1f}d) "
                f"exceeds contract ({contract_lt}d) by +{drift_days:.1f} days"
            )
        else:
            detected_from = (
                f"Supplier {supplier.name} on-time delivery rate is {on_time_rate * 100:.1f}% "
                f"(below 80% threshold across {measured.sample_size} deliveries)"
            )

        evidence = {
            "supplier_id": supplier.id,
            "supplier_name": supplier.name,
            "supplier_code": getattr(supplier, "supplier_code", f"SUP-{supplier.id}"),
            "contract_lead_time_days": contract_lt,
            "measured_lead_time_days": avg_measured_lt,
            "drift_days": drift_days,
            "on_time_rate": on_time_rate,
            "sample_size": measured.sample_size,
            "formula": "measured_lead_time > contract_lead_time or on_time_rate < 0.80",
            "citation": "manual §6 line 74",
        }

        return SignalCandidate(
            signal_type=SIGNAL_TYPE,
            severity=severity,
            product_id=None,
            supplier_id=supplier.id,
            po_id=None,
            detected_from=detected_from,
            evidence=evidence,
            sufficiency=measured.sufficiency,
            dedup_key=dedup_key_for(SIGNAL_TYPE, supplier_id=supplier.id),
        )

    return None


def detect_all(db: Session) -> list[SignalCandidate]:
    """Scan all active suppliers for delivery/lead-time drift."""
    suppliers = db.query(Supplier.id).all()
    results = []
    for (sid,) in suppliers:
        candidate = detect(db, sid)
        if candidate:
            results.append(candidate)
    return results
