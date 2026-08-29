"""Metric snapshots persistence and historical querying (WS-17).

10-IMPACT-METRICS.md §6 / 12-DATA-AND-API-CHANGES.md §2.7.
Stores computed metric values at each tick/interval in metric_snapshots table.
Enforces explicit clock-sourced timestamps (clock.now()).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.backend.models_analytics import MetricSnapshot
from src.core import clock
from src.metrics.registry import MetricValue, compute_all, compute_metric, get_metric_definition


def take_snapshot(
    db: Session,
    metric_value: MetricValue,
    *,
    window_start: Optional[datetime] = None,
    window_end: Optional[datetime] = None,
    computed_at: Optional[datetime] = None,
) -> MetricSnapshot:
    """Persist a single MetricValue snapshot to the database.

    Timestamps explicitly sourced from clock.now() (CI invariant #3).
    """
    snap_time = computed_at if computed_at is not None else clock.now()
    scope_type = "global"
    scope_value = None
    if ":" in metric_value.scope:
        parts = metric_value.scope.split(":", 1)
        scope_type = parts[0]
        scope_value = parts[1]
    elif metric_value.scope:
        scope_type = metric_value.scope

    snapshot = MetricSnapshot(
        metric_key=metric_value.key,
        value=metric_value.value,
        computed_at=snap_time,
        window_start=window_start,
        window_end=window_end,
        scope_type=scope_type,
        scope_value=scope_value,
        tier=metric_value.tier,
        data_disclosure=metric_value.data_disclosure,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def snapshot_metric(
    db: Session,
    metric_key: str,
    *,
    window: str = "all_time",
    scope: str = "global",
) -> MetricSnapshot:
    """Compute and snapshot a single metric by key."""
    m_val = compute_metric(db, metric_key, window=window, scope=scope)
    return take_snapshot(db, m_val)


def snapshot_all(
    db: Session,
    *,
    window: str = "all_time",
    scope: str = "global",
) -> list[MetricSnapshot]:
    """Compute and snapshot all 36 metrics into the metric_snapshots table."""
    metrics = compute_all(db, window=window, scope=scope)
    snap_time = clock.now()
    snapshots: list[MetricSnapshot] = []

    for m in metrics:
        scope_type = "global"
        scope_value = None
        if ":" in m.scope:
            parts = m.scope.split(":", 1)
            scope_type = parts[0]
            scope_value = parts[1]
        elif m.scope:
            scope_type = m.scope

        snap = MetricSnapshot(
            metric_key=m.key,
            value=m.value,
            computed_at=snap_time,
            window_start=None,
            window_end=None,
            scope_type=scope_type,
            scope_value=scope_value,
            tier=m.tier,
            data_disclosure=m.data_disclosure,
        )
        db.add(snap)
        snapshots.append(snap)

    db.commit()
    for s in snapshots:
        db.refresh(s)

    return snapshots


def get_snapshots(
    db: Session,
    metric_key: Optional[str] = None,
    *,
    scope_type: Optional[str] = None,
    scope_value: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Retrieve historical snapshots with optional filters."""
    query = db.query(MetricSnapshot)
    if metric_key:
        query = query.filter(MetricSnapshot.metric_key == metric_key)
    if scope_type:
        query = query.filter(MetricSnapshot.scope_type == scope_type)
    if scope_value:
        query = query.filter(MetricSnapshot.scope_value == scope_value)

    results = (
        query.order_by(MetricSnapshot.computed_at.desc(), MetricSnapshot.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    formatted: list[dict[str, Any]] = []
    for s in results:
        defn = get_metric_definition(s.metric_key)
        formatted.append({
            "id": s.id,
            "metric_key": s.metric_key,
            "label": defn.label if defn else s.metric_key,
            "value": s.value,
            "computed_at": s.computed_at.isoformat() if s.computed_at else None,
            "window_start": s.window_start.isoformat() if s.window_start else None,
            "window_end": s.window_end.isoformat() if s.window_end else None,
            "scope_type": s.scope_type,
            "scope_value": s.scope_value,
            "tier": s.tier,
            "data_disclosure": s.data_disclosure,
            "formula": defn.formula if defn else "",
            "missing_input": defn.missing_input if defn else None,
        })

    return formatted
