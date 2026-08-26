"""Tests for supplier reliability and lead-time drift detector (WS-3)."""
from src.signals.detectors import supplier_drift


def test_supplier_drift_fires_on_late_delivery_history(db, sample_data):
    """Supplier s2 with contract 3d and measured avg 9d (10d, 8d, 9d) must fire supplier_drift."""
    s2 = sample_data["suppliers"]["s2"]
    candidate = supplier_drift.detect(db, s2.id)

    assert candidate is not None
    assert candidate.signal_type == "supplier_drift"
    assert candidate.supplier_id == s2.id
    assert candidate.severity == "high"
    assert candidate.evidence["contract_lead_time_days"] == 3
    assert candidate.evidence["measured_lead_time_days"] >= 8.0
    assert candidate.evidence["drift_days"] >= 5.0
    assert "manual §6 line 74" in candidate.evidence["citation"]


def test_supplier_drift_does_not_fire_when_no_completed_orders(db, sample_data):
    """Supplier s3 has no completed orders in history, so sample size is 0 and no drift fires."""
    s3 = sample_data["suppliers"]["s3"]
    candidate = supplier_drift.detect(db, s3.id)
    assert candidate is None


def test_supplier_drift_detect_all(db, sample_data):
    """detect_all identifies only drifting suppliers across the supplier registry."""
    results = supplier_drift.detect_all(db)
    drifting_sids = {c.supplier_id for c in results}

    assert sample_data["suppliers"]["s2"].id in drifting_sids
    assert sample_data["suppliers"]["s3"].id not in drifting_sids
