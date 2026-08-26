"""Tests for supplier drift detection (WS-7).

15-SHARED-CONTRACTS.md §10 / 14-PARALLEL-WORKSTREAMS.md §WS-7 / 13-DEMO-SCENARIOS.md §6.3.
Verifies supplier lead-time drift detection and evidence generation (e.g. PO-2026-0001).
"""
from datetime import date
from unittest.mock import MagicMock

import pytest

from src.backend.database import SessionLocal
from src.sourcing.drift import (
    compute_supplier_drift,
    detect_supplier_drift,
    list_supplier_drifts,
)


def test_supplier_drift_computation():
    """Doc 14 §WS-7: PO-2026-0001 yields +4 days vs contract."""
    supp = MagicMock()
    supp.id = 4
    supp.name = "Global Logistics Corp"
    supp.supplier_code = "SUP-0004"
    supp.is_active = True
    supp.lead_time_days = 5

    po = MagicMock()
    po.po_number = "PO-2026-0001"
    po.supplier_id = 4
    po.order_date = date(2026, 8, 14)
    po.expected_delivery = date(2026, 8, 21)
    po.received_date = date(2026, 8, 23)

    class MockQuery:
        def filter(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def first(self):
            return supp

        def all(self):
            return [po]

    class MockDB:
        def query(self, model):
            return MockQuery()

    report = compute_supplier_drift(MockDB(), supplier_id=4)
    assert report["supplier_id"] == 4
    assert report["contract_lead_time"] == 5
    assert report["measured_lead_time"] == 9.0
    assert report["drift_days"] == 4.0
    assert report["drift_pct"] == 80.0
    assert report["is_drifting"] is True
    assert len(report["po_evidence"]) == 1
    assert report["po_evidence"][0]["po_number"] == "PO-2026-0001"
    assert report["po_evidence"][0]["actual_lead_time_days"] == 9
    assert report["po_evidence"][0]["variance_vs_contract_days"] == 4


def test_detect_supplier_drift_with_tolerance():
    """detect_supplier_drift respects tolerance_days."""
    supp = MagicMock()
    supp.id = 4
    supp.name = "Global Logistics Corp"
    supp.supplier_code = "SUP-0004"
    supp.is_active = True
    supp.lead_time_days = 5

    po = MagicMock()
    po.po_number = "PO-2026-0001"
    po.supplier_id = 4
    po.order_date = date(2026, 8, 14)
    po.expected_delivery = date(2026, 8, 21)
    po.received_date = date(2026, 8, 23)

    class MockQuery:
        def filter(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def first(self):
            return supp

        def all(self):
            return [po]

    class MockDB:
        def query(self, model):
            return MockQuery()

    # Drift is 4.0 days; tolerance 2.0 -> detected
    detected = detect_supplier_drift(MockDB(), supplier_id=4, tolerance_days=2.0)
    assert detected is not None
    assert detected["drift_days"] == 4.0

    # Tolerance 5.0 -> not detected
    not_detected = detect_supplier_drift(MockDB(), supplier_id=4, tolerance_days=5.0)
    assert not_detected is None


def test_supplier_drift_on_seeded_database():
    """Verify drift detection on live seeded database (PO-2026-0001)."""
    db = SessionLocal()
    try:
        report = compute_supplier_drift(db, supplier_id=4)
        assert report["supplier_id"] == 4
        assert report["contract_lead_time"] == 5
        assert report["measured_lead_time"] == 9.0
        assert report["drift_days"] == 4.0
        assert report["is_drifting"] is True
        assert len(report["po_evidence"]) >= 1

        drifts = list_supplier_drifts(db, tolerance_days=0.0)
        assert any(d["supplier_id"] == 4 for d in drifts)
    finally:
        db.close()
