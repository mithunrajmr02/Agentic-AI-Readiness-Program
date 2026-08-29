"""Tests for Tier 3 Metrics & 'WHAT WE CANNOT MEASURE YET' gaps (WS-17).

10-IMPACT-METRICS.md §3 / 15-SHARED-CONTRACTS.md §14 (CI Invariant #8).
Hard Rule: Every T3 metric returns value = None, ALWAYS.
"""
import pytest

from src.metrics.registry import MetricValue, compute_all, gaps


def test_t3_metrics_all_return_none(test_db):
    """CI Invariant #8: Every T3 metric in gaps() must have value is None."""
    t3_metrics = gaps(test_db)
    assert len(t3_metrics) == 8, f"Expected 8 T3 metrics, got {len(t3_metrics)}"

    for m in t3_metrics:
        assert m.tier == "T3"
        assert m.value is None, f"T3 metric {m.key} must return value=None, got {m.value}"
        assert m.missing_input is not None and len(m.missing_input.strip()) > 0, (
            f"T3 metric {m.key} must have non-empty missing_input"
        )
        assert m.formula is not None and len(m.formula.strip()) > 0, (
            f"T3 metric {m.key} must have non-empty formula"
        )


def test_compute_all_includes_t3_with_none(test_db):
    """Verify that compute_all returns all 8 T3 metrics with value=None."""
    all_metrics = compute_all(test_db)
    t3_metrics = [m for m in all_metrics if m.tier == "T3"]
    assert len(t3_metrics) == 8

    for m in t3_metrics:
        assert m.value is None
        assert m.missing_input is not None


def test_t3_metric_value_dataclass_raises_on_non_none():
    """Verify that MetricValue enforces value=None for tier='T3' at creation time."""
    with pytest.raises(ValueError, match="Violation of CI invariant #8"):
        MetricValue(
            key="M-23",
            label="Revenue protected",
            value=1000.0,  # FORBIDDEN for T3
            tier="T3",
            formula="x * y",
            missing_input="Sales history",
            data_disclosure="synthetic",
        )


def test_t3_metric_value_dataclass_raises_on_empty_missing_input():
    """Verify that MetricValue requires missing_input for tier='T3'."""
    with pytest.raises(ValueError, match="non-empty missing_input"):
        MetricValue(
            key="M-23",
            label="Revenue protected",
            value=None,
            tier="T3",
            formula="x * y",
            missing_input=None,  # FORBIDDEN for T3
            data_disclosure="synthetic",
        )
