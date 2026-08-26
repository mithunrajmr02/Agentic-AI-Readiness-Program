"""Tests for threshold breach detector (WS-3)."""
from src.signals.detectors import threshold_breach


def test_threshold_breach_fires_on_out_of_stock(db, sample_data):
    """Out of stock (0 on hand) must raise a critical threshold_breach."""
    p_headphones = sample_data["products"]["headphones"]
    candidate = threshold_breach.detect(db, p_headphones.id)

    assert candidate is not None
    assert candidate.signal_type == "threshold_breach"
    assert candidate.severity == "critical"
    assert candidate.product_id == p_headphones.id
    assert candidate.evidence["quantity_on_hand"] == 0
    assert "manual §4 line 41" in candidate.evidence["citation"]


def test_threshold_breach_fires_on_low_stock(db, sample_data):
    """Low stock (15 on hand <= 30 reorder point) must raise a threshold_breach."""
    p_oil = sample_data["products"]["oil"]
    candidate = threshold_breach.detect(db, p_oil.id)

    assert candidate is not None
    assert candidate.signal_type == "threshold_breach"
    assert candidate.severity in ("high", "medium")
    assert candidate.product_id == p_oil.id
    assert candidate.evidence["quantity_on_hand"] == 15
    assert candidate.evidence["reorder_point"] == 30


def test_threshold_breach_does_not_fire_on_healthy_sku(db, sample_data):
    """Healthy stock (150 on hand > 40 reorder point) must NOT fire."""
    p_rice = sample_data["products"]["rice"]
    candidate = threshold_breach.detect(db, p_rice.id)

    assert candidate is None


def test_threshold_breach_detect_all(db, sample_data):
    """detect_all scans entire catalog and returns all breaches."""
    results = threshold_breach.detect_all(db)
    breached_pids = {c.product_id for c in results}

    assert sample_data["products"]["headphones"].id in breached_pids
    assert sample_data["products"]["oil"].id in breached_pids
    assert sample_data["products"]["rice"].id not in breached_pids
