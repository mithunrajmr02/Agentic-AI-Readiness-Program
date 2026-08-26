"""Overdue purchase order detector (WS-3).

Grounding: manual §10 item 4 ("Confirming supplier acknowledgement and expected delivery dates").
Fires when an open purchase order has passed its expected delivery date without being received.
"""
from typing import Optional

from sqlalchemy.orm import Session

from src.backend.models import POItem, POStatus, PurchaseOrder
from src.core import clock
from src.signals.dedup import dedup_key_for
from src.signals.detectors.base import SignalCandidate


SIGNAL_TYPE = "po_overdue"


def _is_terminal_status(status_val) -> bool:
    name = getattr(status_val, "name", str(status_val)).lower()
    val = getattr(status_val, "value", str(status_val)).lower()
    return name in ("received", "cancelled") or val in ("received", "cancelled")


def detect(db: Session, po_id: int) -> Optional[SignalCandidate]:
    """Check whether a single purchase order is overdue."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        return None

    if po.received_date is not None or _is_terminal_status(po.status):
        return None

    if po.expected_delivery is None:
        return None

    today = clock.today()
    if po.expected_delivery < today:
        days_late = (today - po.expected_delivery).days
        total_amt = po.total_amount or 0.0

        if days_late >= 3 or total_amt > 50000.0:
            severity = "critical"
        elif days_late >= 1:
            severity = "high"
        else:
            severity = "medium"

        # Try to identify affected product id if any
        first_item = db.query(POItem).filter(POItem.po_id == po.id).first()
        product_id = first_item.product_id if first_item else None

        detected_from = (
            f"PO {po.po_number} is {days_late} day(s) overdue "
            f"(expected delivery: {po.expected_delivery}, current: {today})"
        )

        status_str = getattr(po.status, "name", str(po.status))

        evidence = {
            "po_id": po.id,
            "po_number": po.po_number,
            "supplier_id": po.supplier_id,
            "product_id": product_id,
            "order_date": str(po.order_date) if po.order_date else None,
            "expected_delivery": str(po.expected_delivery),
            "current_date": str(today),
            "days_late": days_late,
            "total_amount": total_amt,
            "status": status_str,
            "formula": "expected_delivery < clock.today() and received_date is None",
            "citation": "manual §10 item 4",
        }

        return SignalCandidate(
            signal_type=SIGNAL_TYPE,
            severity=severity,
            product_id=product_id,
            supplier_id=po.supplier_id,
            po_id=po.id,
            detected_from=detected_from,
            evidence=evidence,
            sufficiency="sufficient",
            dedup_key=dedup_key_for(SIGNAL_TYPE, po_id=po.id),
        )

    return None


def detect_all(db: Session) -> list[SignalCandidate]:
    """Scan all open purchase orders for overdue delivery dates."""
    pos = db.query(PurchaseOrder.id).all()
    results = []
    for (poid,) in pos:
        candidate = detect(db, poid)
        if candidate:
            results.append(candidate)
    return results
