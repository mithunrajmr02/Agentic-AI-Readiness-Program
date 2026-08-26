"""Signals REST API router (WS-3).

15-SHARED-CONTRACTS.md §12 / 12-DATA-AND-API-CHANGES.md §5.1.
Exposes signal queries, manual scans, and dismissal workflows.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.contracts import success_envelope
from src.backend.database import get_db
from src.backend.models_analytics import Signal
from src.signals.engine import get_signal, list_signals, resolve_signal, run_detectors

router = APIRouter(prefix="/api/signals", tags=["signals"])


# --- Request Schemas ---------------------------------------------------------

class ScanRequest(BaseModel):
    product_ids: Optional[list[int]] = Field(
        None, description="Optional subset of product IDs to scan. If omitted, scans all."
    )


class DismissRequest(BaseModel):
    reason: Optional[str] = Field(
        "Dismissed by manager", description="Reason for dismissing / resolving this signal"
    )


# --- Helpers -----------------------------------------------------------------

def format_signal_record(signal: Signal) -> dict[str, Any]:
    """Format a Signal ORM instance into an API dictionary with parsed JSON evidence."""
    evidence_parsed = None
    if signal.evidence:
        try:
            evidence_parsed = json.loads(signal.evidence)
        except Exception:
            evidence_parsed = signal.evidence

    return {
        "id": signal.id,
        "signal_id": signal.signal_id,
        "signal_type": signal.signal_type,
        "severity": signal.severity,
        "product_id": signal.product_id,
        "supplier_id": signal.supplier_id,
        "po_id": signal.po_id,
        "raised_at": signal.raised_at.isoformat() if signal.raised_at else None,
        "detected_from": signal.detected_from,
        "evidence": evidence_parsed,
        "sufficiency": signal.sufficiency,
        "dedup_key": signal.dedup_key,
        "status": signal.status,
        "resolution": signal.resolution,
    }


# --- Endpoints ---------------------------------------------------------------

@router.get("", response_model=None)
def get_signals(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (open/resolved)"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    po_id: Optional[int] = Query(None, description="Filter by purchase order ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List detected signals with optional filtering and pagination."""
    signals = list_signals(
        db,
        status=status_filter,
        signal_type=signal_type,
        severity=severity,
        product_id=product_id,
        supplier_id=supplier_id,
        po_id=po_id,
        limit=limit,
        offset=offset,
    )
    return success_envelope(
        data=[format_signal_record(s) for s in signals],
        provenance={"signals": "retrieved"},
        data_disclosure="synthetic",
    )


@router.post("/scan", response_model=None)
def scan_signals(
    request: Optional[ScanRequest] = None,
    db: Session = Depends(get_db),
):
    """Run anomaly detectors on demand across all or specified products."""
    pids = request.product_ids if request else None
    signals = run_detectors(db, product_ids=pids)
    return success_envelope(
        data=[format_signal_record(s) for s in signals],
        provenance={"signals": "computed"},
        data_disclosure="synthetic",
    )


@router.get("/{signal_id}", response_model=None)
def get_signal_by_id(
    signal_id: str,
    db: Session = Depends(get_db),
):
    """Get full details and evidence for a specific signal."""
    signal = get_signal(db, signal_id)
    if signal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signal '{signal_id}' not found",
        )
    return success_envelope(
        data=format_signal_record(signal),
        provenance={"signal": "retrieved"},
        data_disclosure="synthetic",
    )


@router.post("/{signal_id}/dismiss", response_model=None)
def dismiss_signal(
    signal_id: str,
    request: Optional[DismissRequest] = None,
    db: Session = Depends(get_db),
):
    """Dismiss / resolve an open signal with a recorded rationale."""
    reason = request.reason if request and request.reason else "Dismissed by operator"
    signal = resolve_signal(db, signal_id, resolution=reason)
    if signal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signal '{signal_id}' not found",
        )
    return success_envelope(
        data=format_signal_record(signal),
        provenance={"signal": "retrieved"},
        data_disclosure="synthetic",
    )
