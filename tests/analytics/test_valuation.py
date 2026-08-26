"""Tests for inventory valuation, days on hand, and stock turn (src.analytics.valuation).

15-SHARED-CONTRACTS.md §4.3, §5.1, §5.2 and manual §8 line 91, §13 line 137, §13 line 139.
"""
import pytest
from unittest.mock import MagicMock

from src.analytics.valuation import inventory_value, days_on_hand, stock_turn
from src.analytics.sufficiency import Computed
from src.backend.database import SessionLocal
from src.backend.models import Product, StockLevel


def test_inventory_value_uses_cost_price():
    """Inventory is valued at cost_price, NEVER unit_price (15-SHARED-CONTRACTS.md §4.3, manual §8 line 91)."""
    p1 = MagicMock()
    p1.id = 1
    p1.cost_price = 50.0
    p1.unit_price = 100.0  # Selling price should be ignored
    p1.category = "grocery"

    s1 = MagicMock()
    s1.product_id = 1
    s1.quantity_on_hand = 100

    p2 = MagicMock()
    p2.id = 2
    p2.cost_price = 200.0
    p2.unit_price = 350.0
    p2.category = "electronics"

    s2 = MagicMock()
    s2.product_id = 2
    s2.quantity_on_hand = 10

    # Total value = (50 * 100) + (200 * 10) = 5000 + 2000 = 7000.0
    class MockQuery:
        def __init__(self, data):
            self.data = data
        def outerjoin(self, *args, **kwargs):
            return self
        def filter(self, *args, **kwargs):
            return self
        def all(self):
            return self.data

    class MockDB:
        def query(self, *entities):
            return MockQuery([(p1, s1), (p2, s2)])

    res = inventory_value(MockDB(), scope="global")
    assert res.value == 7000.0
    assert res.sufficiency == "sufficient"
    assert res.citation == "manual §8 line 91"
    assert res.formula == "sum(cost_price × quantity_on_hand)"
    assert res.inputs["total_units"] == 110


def test_inventory_value_on_seeded_database():
    """In baseline DB: total stock value is ₹203,700.0."""
    db = SessionLocal()
    try:
        res = inventory_value(db, scope="global")
        assert res.value == 203700.0
        assert res.sufficiency == "sufficient"
        assert res.inputs["product_count"] == 5
    finally:
        db.close()


def test_days_on_hand_with_insufficient_demand_returns_none():
    """If demand is insufficient or none, days_on_hand returns value=None."""
    class MockDemand:
        value = None
        sufficiency = "insufficient"
        inputs = {}
        formula = "sum(sale_quantities) / window_days"
        citation = "manual §3 line 33"
        sample_size = 2
        span_days = 30

    import src.analytics.valuation as val_mod
    orig_fn = val_mod.compute_daily_demand
    try:
        val_mod.compute_daily_demand = lambda db, pid, **kwargs: MockDemand()
        res = days_on_hand(None, product_id=1)
        assert res.value is None
        assert res.sufficiency == "insufficient"
        assert res.citation == "manual §13 line 139"
        assert res.formula == "quantity_on_hand / daily_demand"
    finally:
        val_mod.compute_daily_demand = orig_fn


def test_days_on_hand_with_sufficient_demand():
    """days_on_hand = on_hand / daily_demand (manual §13 line 139)."""
    class MockDemand:
        value = 10.0
        sufficiency = "sufficient"
        inputs = {"daily_demand": 10.0}
        formula = "sum(sale_quantities) / window_days"
        citation = "manual §3 line 33"
        sample_size = 20
        span_days = 30

    class MockStockLevel:
        product_id = 1
        quantity_on_hand = 150

    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            return MockStockLevel()

    class MockDB:
        def query(self, model):
            return MockQuery()

    import src.analytics.valuation as val_mod
    orig_fn = val_mod.compute_daily_demand
    try:
        val_mod.compute_daily_demand = lambda db, pid, **kwargs: MockDemand()
        # 150 units on hand / 10 units/day = 15.0 days
        res = days_on_hand(MockDB(), product_id=1)
        assert res.value == 15.0
        assert res.sufficiency == "sufficient"
        assert res.inputs["quantity_on_hand"] == 150
        assert res.inputs["daily_demand"] == 10.0
    finally:
        val_mod.compute_daily_demand = orig_fn


def test_stock_turn():
    """stock_turn = cogs / average_inventory_value (manual §13 line 137)."""
    db = SessionLocal()
    try:
        res = stock_turn(db, window_days=90)
        assert isinstance(res, Computed)
        assert res.citation == "manual §13 line 137"
        assert res.formula == "cogs / average_inventory_value"
    finally:
        db.close()
