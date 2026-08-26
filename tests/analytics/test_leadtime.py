"""Tests for supplier lead time measurement (src.analytics.leadtime).

15-SHARED-CONTRACTS.md §5.1, §5.2, §10 and manual §6 line 70, §6 line 74.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock

from src.analytics.leadtime import measured_lead_time
from src.analytics.sufficiency import Computed
from src.backend.database import SessionLocal
from src.backend.models import PurchaseOrder, Supplier


def test_supplier_with_no_completed_pos_returns_none_sufficiency():
    """Supplier with 0 completed POs -> sufficiency='none', value=None."""
    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def all(self):
            return []

    class MockDB:
        def query(self, model):
            return MockQuery()

    res = measured_lead_time(MockDB(), supplier_id=999)
    assert isinstance(res, Computed)
    assert res.sufficiency == "none"
    assert res.value is None  # Invariant: none -> value is None
    assert res.sample_size == 0
    assert res.formula == "avg(received_date - order_date)"
    assert res.citation == "manual §6 line 74"


def test_supplier_with_single_po_returns_thin_sufficiency():
    """Supplier with 1 completed PO -> sample_size=1, sufficiency='thin', value=lead_time."""
    po = MagicMock()
    po.order_date = date(2026, 8, 1)
    po.expected_delivery = date(2026, 8, 6)
    po.received_date = date(2026, 8, 10)  # 9 days actual lead time (4 days late)

    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def all(self):
            return [po]

    class MockDB:
        def query(self, model):
            return MockQuery()

    res = measured_lead_time(MockDB(), supplier_id=1)
    assert res.sufficiency == "thin"
    assert res.value == 9.0
    assert res.sample_size == 1
    assert res.inputs["on_time_count"] == 0
    assert res.inputs["on_time_rate"] == 0.0


def test_supplier_with_multiple_pos_returns_sufficient():
    """>= 3 completed POs -> sufficiency='sufficient'."""
    pos = []
    # 3 POs: 5 days (on-time), 7 days (on-time), 9 days (late) -> avg 7.0 days, on-time rate 2/3 = 0.6667
    for order_d, exp_d, rec_d in [
        (date(2026, 7, 1), date(2026, 7, 6), date(2026, 7, 6)),
        (date(2026, 7, 10), date(2026, 7, 18), date(2026, 7, 17)),
        (date(2026, 8, 1), date(2026, 8, 6), date(2026, 8, 10)),
    ]:
        po = MagicMock()
        po.order_date = order_d
        po.expected_delivery = exp_d
        po.received_date = rec_d
        pos.append(po)

    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def all(self):
            return pos

    class MockDB:
        def query(self, model):
            return MockQuery()

    res = measured_lead_time(MockDB(), supplier_id=1)
    assert res.sufficiency == "sufficient"
    assert res.value == 7.0
    assert res.sample_size == 3
    assert res.inputs["on_time_count"] == 2
    assert res.inputs["on_time_rate"] == round(2.0 / 3.0, 4)


def test_measured_lead_time_on_seeded_database():
    """In baseline DB: SUP-0004 (id=4) has PO-2026-0001 received. Others have 0 completed POs."""
    db = SessionLocal()
    try:
        # Supplier 4: PO-2026-0001 order_date=2026-08-14, expected=2026-08-21, received=2026-08-23 (9 days)
        res4 = measured_lead_time(db, supplier_id=4)
        assert res4.sample_size == 1
        assert res4.sufficiency == "thin"
        assert res4.value == 9.0

        # Suppliers with no completed POs (1, 2, 3, 5)
        for sid in [1, 2, 3, 5]:
            res = measured_lead_time(db, supplier_id=sid)
            assert res.sample_size == 0
            assert res.sufficiency == "none"
            assert res.value is None
    finally:
        db.close()
