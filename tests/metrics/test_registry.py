"""Test metrics registry, catalogs, and vocabulary constraints (WS-17)."""
import pytest

from src.core.vocab import DATA_DISCLOSURE, METRIC_TIERS
from src.metrics.registry import (
    MetricDefinition,
    MetricValue,
    get_all_metric_definitions,
    get_metric_definition,
)


def test_all_36_metrics_registered():
    """Verify that all 36 metrics (M-1 to M-36) are registered in the catalog."""
    definitions = get_all_metric_definitions()
    assert len(definitions) == 36, f"Expected 36 metrics, found {len(definitions)}"

    keys = {d.key for d in definitions}
    expected_keys = {f"M-{i}" for i in range(1, 37)}
    assert keys == expected_keys


def test_metric_tiers_and_disclosure_vocab():
    """Verify that every metric uses frozen vocabularies for tier and data_disclosure."""
    definitions = get_all_metric_definitions()
    for d in definitions:
        assert d.tier in METRIC_TIERS, f"Metric {d.key} has invalid tier '{d.tier}'"
        assert d.data_disclosure in DATA_DISCLOSURE, f"Metric {d.key} has invalid disclosure '{d.data_disclosure}'"
        assert d.formula and len(d.formula.strip()) > 0, f"Metric {d.key} has empty formula"


def test_tier_breakdown_counts():
    """Verify the distribution across tiers: T1 (22), T3 (8), T2 (6)."""
    definitions = get_all_metric_definitions()
    t1_count = sum(1 for d in definitions if d.tier == "T1")
    t2_count = sum(1 for d in definitions if d.tier == "T2")
    t3_count = sum(1 for d in definitions if d.tier == "T3")

    assert t1_count == 22, f"Expected 22 T1 metrics (M-1..M-22), got {t1_count}"
    assert t3_count == 8, f"Expected 8 T3 metrics (M-23..M-30), got {t3_count}"
    assert t2_count == 6, f"Expected 6 T2 metrics (M-31..M-36), got {t2_count}"


def test_metric_value_validation():
    """Test validation errors in MetricValue dataclass."""
    # Invalid tier
    with pytest.raises(ValueError, match="Invalid metric tier"):
        MetricValue(
            key="M-1",
            label="Test",
            value=1.0,
            tier="INVALID",
            formula="x",
            missing_input=None,
            data_disclosure="synthetic",
        )

    # Invalid data_disclosure
    with pytest.raises(ValueError, match="Invalid data_disclosure"):
        MetricValue(
            key="M-1",
            label="Test",
            value=1.0,
            tier="T1",
            formula="x",
            missing_input=None,
            data_disclosure="invalid_disclosure",
        )
