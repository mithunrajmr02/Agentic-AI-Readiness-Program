"""Metrics & Impact API package (WS-17).

15-SHARED-CONTRACTS.md §14.
Computes all 36 metrics with strict tier distinctions (T1, T2, T3),
no numeric fabrication, explicit clock timestamps, and snapshot persistence.
"""
# Ensure all metric definitions are registered
import src.metrics.computers  # noqa: F401
from src.metrics.registry import (
    MetricDefinition,
    MetricValue,
    compute_all,
    compute_category,
    compute_metric,
    gaps,
    get_all_metric_definitions,
    get_metric_definition,
    register_metric,
)
from src.metrics.snapshots import (
    get_snapshots,
    snapshot_all,
    snapshot_metric,
    take_snapshot,
)

__all__ = [
    "MetricValue",
    "MetricDefinition",
    "register_metric",
    "get_metric_definition",
    "get_all_metric_definitions",
    "compute_metric",
    "compute_all",
    "gaps",
    "compute_category",
    "take_snapshot",
    "snapshot_metric",
    "snapshot_all",
    "get_snapshots",
]
