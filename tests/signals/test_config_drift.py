"""Tests for configuration drift detector (WS-3)."""
from src.signals.detectors import config_drift


def test_config_drift_fires_on_divergent_reorder_point(db, sample_data):
    """When configured ROP (e.g. 20) is far from implied demand ROP (~58.3), drift must fire."""
    p_rice = sample_data["products"]["rice"]
    # Rice has demand ~8.33 units/day, lead time 5d, safety 2d -> implied ROP = 8.33 * 7 = 58.33.
    # Stored ROP is 40 -> |40 - 58.33| / 58.33 = 31.4% > 20% tolerance.
    candidate = config_drift.detect(db, p_rice.id)

    assert candidate is not None
    assert candidate.signal_type == "config_drift"
    assert candidate.product_id == p_rice.id
    assert candidate.evidence["configured_reorder_point"] == 40
    assert candidate.evidence["drift_percentage"] > 20.0
    assert "manual §3 line 33" in candidate.evidence["citation"]


def test_config_drift_does_not_fire_when_configured_within_tolerance(db, sample_data):
    """When configured ROP closely matches implied demand ROP (within 20%), no signal fires."""
    p_rice = sample_data["products"]["rice"]
    p_rice.reorder_point = 58
    db.commit()

    candidate = config_drift.detect(db, p_rice.id)
    assert candidate is None


def test_config_drift_does_not_fire_without_sufficient_demand(db, sample_data):
    """Cold start SKU with no valid baseline demand cannot evaluate config drift."""
    p_colgate = sample_data["products"]["colgate"]
    candidate = config_drift.detect(db, p_colgate.id)
    assert candidate is None
