"""Supplier delivery drift detection and lead-time analysis (WS-7).

15-SHARED-CONTRACTS.md §10 / 14-PARALLEL-WORKSTREAMS.md §WS-7.
Analyzes supplier delivery history to detect systematic divergence between
contractual lead time and measured fulfillment time (e.g. PO-2026-0001 drift).
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from src.backend.models import PurchaseOrder, Supplier
from src.sourcing.scorecard import Scorecard, scorecard


def compute_supplier_drift(db: Session, supplier_id: int) -> dict[str, Any]:
    """Compute detailed drift metrics for a supplier.

    Compares contractual lead time from the Supplier record with actual
    delivery history from completed PurchaseOrder records.
    """
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier is None:
        raise ValueError(f"Supplier with ID {supplier_id} not found")

    sc = scorecard(db, supplier_id)

    # Fetch recent completed POs for evidence
    completed_pos = (
        db.query(PurchaseOrder)
        .filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.received_date.isnot(None),
        )
        .order_by(PurchaseOrder.received_date.desc())
        .all()
    )

    po_evidence: list[dict[str, Any]] = []
    for po in completed_pos:
        if po.received_date and po.order_date:
            actual_days = (po.received_date - po.order_date).days
            promised_days = (
                (po.expected_delivery - po.order_date).days if po.expected_delivery else None
            )
            variance_vs_contract = actual_days - sc.contract_lead_time
            po_evidence.append({
                "po_number": po.po_number,
                "order_date": po.order_date.isoformat() if po.order_date else None,
                "expected_delivery": (
                    po.expected_delivery.isoformat() if po.expected_delivery else None
                ),
                "received_date": po.received_date.isoformat() if po.received_date else None,
                "actual_lead_time_days": actual_days,
                "promised_lead_time_days": promised_days,
                "variance_vs_contract_days": variance_vs_contract,
            })

    drift_days = sc.drift_days or 0.0
    drift_pct = (
        round((drift_days / float(sc.contract_lead_time)) * 100.0, 1)
        if sc.contract_lead_time > 0 and sc.drift_days is not None
        else 0.0
    )

    is_drifting = bool(sc.drift_days is not None and sc.drift_days > 0.0)

    return {
        "supplier_id": supplier.id,
        "supplier_name": supplier.name,
        "supplier_code": supplier.supplier_code,
        "is_active": supplier.is_active,
        "contract_lead_time": sc.contract_lead_time,
        "measured_lead_time": sc.measured_lead_time,
        "drift_days": sc.drift_days,
        "drift_pct": drift_pct,
        "sample_size": sc.sample_size,
        "avg_days_late": sc.avg_days_late,
        "on_time_rate": sc.on_time_rate,
        "is_drifting": is_drifting,
        "po_evidence": po_evidence,
    }


def detect_supplier_drift(
    db: Session,
    supplier_id: int,
    tolerance_days: float = 0.0,
) -> Optional[dict[str, Any]]:
    """Detect if a supplier exhibits delivery drift exceeding tolerance_days.

    Returns the drift detail dictionary if drift > tolerance_days, else None.
    """
    drift_data = compute_supplier_drift(db, supplier_id)
    if drift_data["sample_size"] == 0:
        return None

    drift_days = drift_data.get("drift_days")
    if drift_days is not None and drift_days > tolerance_days:
        return drift_data

    return None


def list_supplier_drifts(
    db: Session,
    tolerance_days: float = 0.0,
) -> list[dict[str, Any]]:
    """List all suppliers currently exhibiting lead-time drift above tolerance."""
    suppliers = db.query(Supplier).all()
    results: list[dict[str, Any]] = []

    for s in suppliers:
        drift = detect_supplier_drift(db, s.id, tolerance_days=tolerance_days)
        if drift is not None:
            results.append(drift)

    return results
