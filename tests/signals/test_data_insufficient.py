"""Tests for data insufficiency / cold-start detector (WS-3)."""
from src.signals.detectors import data_insufficient


def test_data_insufficient_fires_on_colgate(db, sample_data):
    """Colgate has 0 sales events in history, so data_insufficient MUST fire (WS-3 hard requirement)."""
    p_colgate = sample_data["products"]["colgate"]
    candidate = data_insufficient.detect(db, p_colgate.id)

    assert candidate is not None
    assert candidate.signal_type == "data_insufficient"
    assert candidate.product_id == p_colgate.id
    assert candidate.sufficiency == "none"
    assert candidate.evidence["sample_size"] == 0
    assert candidate.evidence["needed"] == "14 sale events across 21 distinct days"
    assert "manual §4 line 45" in candidate.evidence["citation"]


def test_data_insufficient_does_not_fire_on_product_with_sufficient_history(db, sample_data):
    """Rice has 25 sales events across 25 distinct days, so sufficiency is 'sufficient' and signal does not fire."""
    p_rice = sample_data["products"]["rice"]
    candidate = data_insufficient.detect(db, p_rice.id)
    assert candidate is None


def test_data_insufficient_detect_all(db, sample_data):
    """detect_all flags all cold-start / unmeasured SKUs across the catalog."""
    results = data_insufficient.detect_all(db)
    insufficient_pids = {c.product_id for c in results}

    assert sample_data["products"]["colgate"].id in insufficient_pids
    assert sample_data["products"]["rice"].id not in insufficient_pids
