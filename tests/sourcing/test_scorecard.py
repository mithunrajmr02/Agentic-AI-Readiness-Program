"""Tests for supplier scorecard derivation (WS-7).

15-SHARED-CONTRACTS.md §10 / 18-INTEGRATION-AND-TESTING.md §4.7.
Verifies sample-size honesty (n = 1 produces no reliability percentage)
and accurate calculation of lead times, lateness, and contractual drift.
"""
from datetime import date
from unittest.mock import MagicMock

import pytest

from src.backend.database import SessionLocal
from src.backend.models import PurchaseOrder, Supplier
from src.sourcing.scorecard import Scorecard, scorecard


def test_scorecard_empty_history():
    """Supplier with 0 completed POs returns sample_size=0, on_time_rate=None."""
    supp = MagicMock()
    supp.id = 1
    supp.lead_time_days = 7

    class MockQuery:
        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return supp

        def all(self):
            return []

    class MockDB:
        def query(self, model):
            return MockQuery()

    sc = scorecard(MockDB(), supplier_id=1)
    assert isinstance(sc, Scorecard)
    assert sc.supplier_id == 1
    assert sc.contract_lead_time == 7
    assert sc.sample_size == 0
    assert sc.on_time_rate is None
    assert sc.measured_lead_time is None
    assert sc.drift_days is None
    assert sc.avg_days_late is None


def test_scorecard_single_observation_honesty():
    """Doc 18 §4.7: n = 1 reports sample_size=1 and on_time_rate=None."""
    supp = MagicMock()
    supp.id = 4
    supp.lead_time_days = 5

    # PO-2026-0001: ordered 08-14, expected 08-21 (7d promise), received 08-23 (9d actual)
    po = MagicMock()
    po.supplier_id = 4
    po.order_date = date(2026, 8, 14)
    po.expected_delivery = date(2026, 8, 21)
    po.received_date = date(2026, 8, 23)

    class MockQuery:
        def __init__(self, model):
            self.model = model

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return supp

        def all(self):
            return [po]

    class MockDB:
        def query(self, model):
            return MockQuery(model)

    sc = scorecard(MockDB(), supplier_id=4)
    assert sc.sample_size == 1
    # Crucial honesty assertion: n = 1 must NOT report a percentage
    assert sc.on_time_rate is None or sc.sample_size >= 5
    assert sc.on_time_rate is None
    assert sc.contract_lead_time == 5
    assert sc.measured_lead_time == 9.0
    assert sc.drift_days == 4.0  # 9.0 - 5.0 = +4 days
    assert sc.avg_days_late == 2.0  # 23 - 21 = 2 days late vs expected


def test_scorecard_multiple_observations_produces_rate():
    """When sample_size >= 5, on_time_rate is populated."""
    supp = MagicMock()
    supp.id = 2
    supp.lead_time_days = 5

    pos = []
    # 5 POs: 4 on time, 1 late -> 80% on-time rate
    dates = [
        (date(2026, 6, 1), date(2026, 6, 6), date(2026, 6, 5)),  # on time (4d)
        (date(2026, 6, 10), date(2026, 6, 15), date(2026, 6, 15)),  # on time (5d)
        (date(2026, 6, 20), date(2026, 6, 25), date(2026, 6, 24)),  # on time (4d)
        (date(2026, 7, 1), date(2026, 7, 6), date(2026, 7, 6)),  # on time (5d)
        (date(2026, 7, 10), date(2026, 7, 15), date(2026, 7, 18)),  # late by 3d (8d)
    ]
    for o_d, exp_d, rec_d in dates:
        p = MagicMock()
        p.supplier_id = 2
        p.order_date = o_d
        p.expected_delivery = exp_d
        p.received_date = rec_d
        pos.append(p)

    class MockQuery:
        def __init__(self, model):
            self.model = model

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return supp

        def all(self):
            return pos

    class MockDB:
        def query(self, model):
            return MockQuery(model)

    sc = scorecard(MockDB(), supplier_id=2)
    assert sc.sample_size == 5
    assert sc.on_time_rate == 0.8
    assert sc.contract_lead_time == 5
    assert sc.measured_lead_time == round((4 + 5 + 4 + 5 + 8) / 5.0, 2)  # 5.2
    assert sc.drift_days == 0.2


def test_scorecard_invalid_supplier_raises_value_error():
    """Non-existent supplier ID raises ValueError."""
    class MockQuery:
        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return None

    class MockDB:
        def query(self, model):
            return MockQuery()

    with pytest.raises(ValueError, match="Supplier with ID 999 not found"):
        scorecard(MockDB(), supplier_id=999)


def test_scorecard_on_seeded_database():
    """Verify scorecard on the live seeded database."""
    db = SessionLocal()
    try:
        # Supplier 4: PO-2026-0001
        sc4 = scorecard(db, supplier_id=4)
        assert sc4.sample_size == 1
        assert sc4.on_time_rate is None  # n=1 honesty
        assert sc4.contract_lead_time == 5
        assert sc4.measured_lead_time == 9.0
        assert sc4.drift_days == 4.0

        # Suppliers 1, 2, 3 have 0 completed POs in the initial seed
        for sid in [1, 2, 3]:
            sc = scorecard(db, supplier_id=sid)
            assert sc.sample_size == 0
            assert sc.on_time_rate is None
            assert sc.measured_lead_time is None
            assert sc.drift_days is None
    finally:
        db.close()
