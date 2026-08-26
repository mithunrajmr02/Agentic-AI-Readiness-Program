"""Tests for daily demand calculation (src.analytics.demand).

15-SHARED-CONTRACTS.md §5.1, §5.2, §5.4.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.core import clock
from src.core.vocab import SUFFICIENCY
from src.backend.models import StockMovement, MovementType, Product
from src.backend.database import SessionLocal
from src.analytics.demand import compute_daily_demand, _is_sale_movement
from src.analytics.sufficiency import Computed


def test_is_sale_movement_variants():
    """Verify _is_sale_movement handles Enum, string, and casing."""
    m_enum = MagicMock()
    m_enum.movement_type = MovementType.sale
    assert _is_sale_movement(m_enum) is True

    m_str = MagicMock()
    m_str.movement_type = "sale"
    assert _is_sale_movement(m_str) is True

    m_str_upper = MagicMock()
    m_str_upper.movement_type = "SALE"
    assert _is_sale_movement(m_str_upper) is True

    m_receipt = MagicMock()
    m_receipt.movement_type = MovementType.receipt
    assert _is_sale_movement(m_receipt) is False

    m_none = MagicMock()
    m_none.movement_type = None
    assert _is_sale_movement(m_none) is False


def test_zero_history_returns_none_sufficiency_and_none_value():
    """Zero sale events -> sufficiency='none', value=None (never 0.0)."""
    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def all(self):
            return []

    class MockDB:
        def query(self, model):
            return MockQuery()

    res = compute_daily_demand(MockDB(), product_id=999, window_days=30)
    assert isinstance(res, Computed)
    assert res.sufficiency == "none"
    assert res.value is None  # Invariant: value is None, never 0.0
    assert res.sample_size == 0
    assert res.span_days == 30
    assert "sale_events_count" in res.inputs
    assert res.inputs["sale_events_count"] == 0


def test_single_day_history_returns_insufficient_and_none_value():
    """1-3 sale events on 1 distinct day -> sufficiency='insufficient', value=None."""
    now_dt = clock.now()
    m1 = MagicMock()
    m1.movement_type = MovementType.sale
    m1.quantity = -5
    m1.recorded_at = now_dt

    m2 = MagicMock()
    m2.movement_type = MovementType.sale
    m2.quantity = -10
    m2.recorded_at = now_dt

    m3 = MagicMock()
    m3.movement_type = MovementType.sale
    m3.quantity = -15
    m3.recorded_at = now_dt

    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def all(self):
            return [m1, m2, m3]

    class MockDB:
        def query(self, model):
            return MockQuery()

    res = compute_daily_demand(MockDB(), product_id=1, window_days=30)
    assert res.sufficiency == "insufficient"
    assert res.value is None  # Invariant: insufficient returns None, never 0.0
    assert res.sample_size == 3
    assert res.inputs["distinct_sale_days"] == 1


def test_thin_sufficiency_produces_value():
    """>= 5 sale events across >= 7 distinct days -> sufficiency='thin', value is computed float."""
    now_dt = clock.now()
    movements = []
    # 7 distinct days, 7 sale events of 10 units each -> 70 units over 30 days = 2.3333 units/day
    for d in range(7):
        m = MagicMock()
        m.movement_type = MovementType.sale
        m.quantity = -10
        m.recorded_at = now_dt - timedelta(days=d)
        movements.append(m)

    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def all(self):
            return movements

    class MockDB:
        def query(self, model):
            return MockQuery()

    res = compute_daily_demand(MockDB(), product_id=1, window_days=30)
    assert res.sufficiency == "thin"
    assert res.value is not None
    assert isinstance(res.value, float)
    assert res.value == round(70.0 / 30.0, 4)
    assert res.sample_size == 7
    assert res.inputs["distinct_sale_days"] == 7
    assert res.inputs["total_units_sold"] == 70


def test_sufficient_sufficiency_produces_value():
    """>= 14 sale events across >= 21 distinct days -> sufficiency='sufficient', value is computed float."""
    now_dt = clock.now()
    movements = []
    # 21 distinct days, 21 sale events of 10 units each -> 210 units over 30 days = 7.0 units/day
    for d in range(21):
        m = MagicMock()
        m.movement_type = MovementType.sale
        m.quantity = -10
        m.recorded_at = now_dt - timedelta(days=d)
        movements.append(m)

    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def all(self):
            return movements

    class MockDB:
        def query(self, model):
            return MockQuery()

    res = compute_daily_demand(MockDB(), product_id=1, window_days=30)
    assert res.sufficiency == "sufficient"
    assert res.value == 7.0
    assert res.sample_size == 21
    assert res.inputs["distinct_sale_days"] == 21


def test_non_sale_movements_are_ignored():
    """Receipts, transfers, adjustments must not contribute to sales demand."""
    now_dt = clock.now()
    movements = []
    # 10 receipts, 0 sales
    for d in range(10):
        m = MagicMock()
        m.movement_type = MovementType.receipt
        m.quantity = 50
        m.recorded_at = now_dt - timedelta(days=d)
        movements.append(m)

    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def all(self):
            return movements

    class MockDB:
        def query(self, model):
            return MockQuery()

    res = compute_daily_demand(MockDB(), product_id=1, window_days=30)
    assert res.sufficiency == "none"
    assert res.value is None


def test_real_database_initial_seeded_products_all_insufficient_or_none():
    """In the baseline DB: Rice has 3 sales on 1 day (insufficient); all other 4 have 0 (none)."""
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        assert len(products) >= 5

        for p in products:
            res = compute_daily_demand(db, p.id, window_days=30)
            assert res.sufficiency in ("insufficient", "none")
            assert res.value is None, f"Product {p.sku} should have value=None, got {res.value}"

        # Rice (id=1 / SKU-GRO-0001) has 3 movements on 1 day -> insufficient
        rice_demand = compute_daily_demand(db, 1, window_days=30)
        assert rice_demand.sufficiency == "insufficient"
        assert rice_demand.value is None
    finally:
        db.close()


@pytest.mark.parametrize("product_id", [1, 2, 3, 4, 5])
def test_insufficient_never_returns_zero(product_id):
    """18-INTEGRATION-AND-TESTING.md §4.4: parametrized test."""
    db = SessionLocal()
    try:
        c = compute_daily_demand(db, product_id)
        if c.sufficiency in ("insufficient", "none"):
            assert c.value is None
    finally:
        db.close()

