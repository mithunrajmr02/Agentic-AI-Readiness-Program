"""Impact & Metrics REST API router (WS-17).

15-SHARED-CONTRACTS.md §12 / 12-DATA-AND-API-CHANGES.md §5.6.
Exposes impact metrics by category, the reviewer's method block (M-14..M-17),
and the transparent 'What we cannot measure yet' gaps endpoint (/api/impact/gaps).
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.backend.contracts import success_envelope
from src.backend.database import get_db
from src.metrics.registry import (
    MetricValue,
    compute_all,
    compute_category,
    compute_metric,
    gaps,
    get_all_metric_definitions,
    get_metric_definition,
)
from src.metrics.snapshots import get_snapshots, snapshot_all, snapshot_metric

router = APIRouter(prefix="/api/impact", tags=["impact"])


def _format_metric(m: MetricValue) -> dict[str, Any]:
    """Format a MetricValue into an API JSON dictionary."""
    return {
        "key": m.key,
        "label": m.label,
        "value": m.value,
        "tier": m.tier,
        "formula": m.formula,
        "missing_input": m.missing_input,
        "data_disclosure": m.data_disclosure,
        "window": m.window,
        "scope": m.scope,
    }


# --- Endpoints ---------------------------------------------------------------

@router.get("", response_model=None)
@router.get("/summary", response_model=None)
def get_impact_summary(
    window: str = Query("all_time", description="Time window for computation"),
    scope: str = Query("global", description="Scope: global, category:name, product:id"),
    db: Session = Depends(get_db),
):
    """Get high-level summary of all Computable T1 impact metrics."""
    t1_metrics = [
        m for m in compute_all(db, window=window, scope=scope) if m.tier == "T1"
    ]
    # Build categorized summary breakdown
    categories: dict[str, list[dict[str, Any]]] = {
        "detection": [_format_metric(m) for m in compute_category(db, "detection", window=window, scope=scope)],
        "decision": [_format_metric(m) for m in compute_category(db, "decision", window=window, scope=scope)],
        "method": [_format_metric(m) for m in compute_category(db, "method", window=window, scope=scope)],
        "position": [_format_metric(m) for m in compute_category(db, "position", window=window, scope=scope)],
    }
    return success_envelope(
        data={
            "metrics": [_format_metric(m) for m in t1_metrics],
            "categories": categories,
        },
        provenance={"metrics": "computed"},
        data_disclosure="synthetic",
    )


@router.get("/detection", response_model=None)
def get_detection_metrics(
    window: str = Query("all_time", description="Time window"),
    scope: str = Query("global", description="Scope"),
    db: Session = Depends(get_db),
):
    """Get Detection & Signal metrics (M-1 to M-6)."""
    metrics = compute_category(db, "detection", window=window, scope=scope)
    return success_envelope(
        data=[_format_metric(m) for m in metrics],
        provenance={"detection_metrics": "computed"},
        data_disclosure="synthetic",
    )


@router.get("/decision", response_model=None)
def get_decision_metrics(
    window: str = Query("all_time", description="Time window"),
    scope: str = Query("global", description="Scope"),
    db: Session = Depends(get_db),
):
    """Get Autonomy & Governance metrics (M-7 to M-13)."""
    metrics = compute_category(db, "decision", window=window, scope=scope)
    return success_envelope(
        data=[_format_metric(m) for m in metrics],
        provenance={"decision_metrics": "computed"},
        data_disclosure="synthetic",
    )


@router.get("/method", response_model=None)
def get_method_metrics(
    window: str = Query("all_time", description="Time window"),
    scope: str = Query("global", description="Scope"),
    db: Session = Depends(get_db),
):
    """Get Method Quality metrics — the Technical Reviewer's block (M-14 to M-17)."""
    metrics = compute_category(db, "method", window=window, scope=scope)
    return success_envelope(
        data=[_format_metric(m) for m in metrics],
        provenance={"method_metrics": "computed"},
        data_disclosure="synthetic",
    )


@router.get("/position", response_model=None)
def get_position_metrics(
    window: str = Query("all_time", description="Time window"),
    scope: str = Query("global", description="Scope"),
    db: Session = Depends(get_db),
):
    """Get Capital and Inventory Position metrics (M-18 to M-22, disclosed synthetic)."""
    metrics = compute_category(db, "position", window=window, scope=scope)
    return success_envelope(
        data=[_format_metric(m) for m in metrics],
        provenance={"position_metrics": "computed"},
        data_disclosure="synthetic",
    )


@router.get("/gaps", response_model=None)
def get_impact_gaps(
    window: str = Query("all_time", description="Time window"),
    scope: str = Query("global", description="Scope"),
    db: Session = Depends(get_db),
):
    """Get Tier 3 metrics — 'WHAT WE CANNOT MEASURE YET' (M-23 to M-30).

    Hard rule: every metric in this response carries value=null, with its formula
    and explicit named missing_input populated.
    """
    t3_metrics = gaps(db, window=window, scope=scope)
    return success_envelope(
        data=[_format_metric(m) for m in t3_metrics],
        provenance={"gaps": "retrieved"},
        data_disclosure="synthetic",
    )


@router.get("/all", response_model=None)
def get_all_metrics(
    window: str = Query("all_time", description="Time window"),
    scope: str = Query("global", description="Scope"),
    db: Session = Depends(get_db),
):
    """Get all 36 metrics catalog across T1, T2, and T3."""
    all_metrics = compute_all(db, window=window, scope=scope)
    return success_envelope(
        data=[_format_metric(m) for m in all_metrics],
        provenance={"all_metrics": "computed"},
        data_disclosure="synthetic",
    )


@router.get("/metric/{key}", response_model=None)
def get_single_metric(
    key: str,
    window: str = Query("all_time", description="Time window"),
    scope: str = Query("global", description="Scope"),
    db: Session = Depends(get_db),
):
    """Get a single metric by key (e.g. M-14)."""
    defn = get_metric_definition(key)
    if defn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metric '{key}' not found in registry",
        )
    m = compute_metric(db, key, window=window, scope=scope)
    return success_envelope(
        data=_format_metric(m),
        provenance={"metric": "computed"},
        data_disclosure=m.data_disclosure,
    )


@router.post("/snapshots", response_model=None)
def create_snapshots(
    metric_key: Optional[str] = None,
    window: str = "all_time",
    scope: str = "global",
    db: Session = Depends(get_db),
):
    """Trigger snapshot calculation and persistence to metric_snapshots table."""
    if metric_key:
        defn = get_metric_definition(metric_key)
        if defn is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Metric '{metric_key}' not found",
            )
        snap = snapshot_metric(db, metric_key, window=window, scope=scope)
        return success_envelope(
            data={"id": snap.id, "metric_key": snap.metric_key, "value": snap.value},
            provenance={"snapshot": "computed"},
            data_disclosure="synthetic",
        )

    snaps = snapshot_all(db, window=window, scope=scope)
    return success_envelope(
        data=[{"id": s.id, "metric_key": s.metric_key, "value": s.value} for s in snaps],
        provenance={"snapshots": "computed"},
        data_disclosure="synthetic",
    )


@router.get("/snapshots/{metric_key}", response_model=None)
def query_metric_snapshots(
    metric_key: str,
    scope_type: Optional[str] = None,
    scope_value: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Query historical snapshot records for a metric."""
    defn = get_metric_definition(metric_key)
    if defn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metric '{metric_key}' not found in catalog",
        )
    history = get_snapshots(
        db,
        metric_key=metric_key,
        scope_type=scope_type,
        scope_value=scope_value,
        limit=limit,
        offset=offset,
    )
    return success_envelope(
        data=history,
        provenance={"snapshots_history": "retrieved"},
        data_disclosure="synthetic",
    )
