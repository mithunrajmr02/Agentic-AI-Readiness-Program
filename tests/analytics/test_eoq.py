"""Tests for Economic Order Quantity calculation (src.analytics.eoq).

15-SHARED-CONTRACTS.md §5.1, §5.2 and manual §9 line 98:
EOQ = sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)
"""
import math
import pytest
from unittest.mock import MagicMock

from src.analytics.eoq import compute_eoq
from src.analytics.sufficiency import Computed
from src.backend.database import SessionLocal
from src.backend.models import Product


def test_compute_eoq_with_insufficient_demand_returns_none():
    """If demand is insufficient or none, EOQ returns value=None."""
    class MockDemand:
        value = None
        sufficiency = "insufficient"
        inputs = {"daily_demand": None}
        formula = "sum(sale_quantities) / window_days"
        citation = "manual §3 line 33"
        sample_size = 2
        span_days = 30

    import src.analytics.eoq as eoq_mod
    orig_fn = eoq_mod.compute_daily_demand
    try:
        eoq_mod.compute_daily_demand = lambda db, pid, **kwargs: MockDemand()
        res = compute_eoq(None, product_id=1, ordering_cost=500.0, holding_rate=0.20)
        assert res.value is None
        assert res.sufficiency == "insufficient"
        assert res.citation == "manual §9 line 98"
        assert res.formula == "sqrt((2 × annual_demand × ordering_cost) / holding_cost_per_unit)"
    finally:
        eoq_mod.compute_daily_demand = orig_fn


def test_compute_eoq_with_valid_inputs():
    """EOQ formula: sqrt((2 * D * S) / H).

    Let daily_demand = 10 -> annual_demand D = 3650 units/yr.
    ordering_cost S = 200.
    holding_cost_per_unit H = cost_price (100) * holding_rate (0.20) = 20.
    EOQ = sqrt((2 * 3650 * 200) / 20) = sqrt(73000) = 270.19.
    """
    class MockDemand:
        value = 10.0
        sufficiency = "sufficient"
        inputs = {"daily_demand": 10.0}
        formula = "sum(sale_quantities) / window_days"
        citation = "manual §3 line 33"
        sample_size = 20
        span_days = 30

    class MockProduct:
        id = 1
        cost_price = 100.0

    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            return MockProduct()

    class MockDB:
        def query(self, model):
            return MockQuery()

    import src.analytics.eoq as eoq_mod
    orig_fn = eoq_mod.compute_daily_demand
    try:
        eoq_mod.compute_daily_demand = lambda db, pid, **kwargs: MockDemand()
        res = compute_eoq(MockDB(), product_id=1, ordering_cost=200.0, holding_rate=0.20)
        assert res.sufficiency == "sufficient"
        expected = round(math.sqrt((2.0 * 3650.0 * 200.0) / 20.0), 2)
        assert res.value == expected
        assert res.inputs["annual_demand"] == 3650.0
        assert res.inputs["ordering_cost"] == 200.0
        assert res.inputs["holding_cost_per_unit"] == 20.0
    finally:
        eoq_mod.compute_daily_demand = orig_fn


def test_compute_eoq_invalid_parameters():
    """Negative or zero costs result in value=None."""
    class MockDemand:
        value = 10.0
        sufficiency = "sufficient"
        inputs = {"daily_demand": 10.0}
        formula = "sum(sale_quantities) / window_days"
        citation = "manual §3 line 33"
        sample_size = 20
        span_days = 30

    import src.analytics.eoq as eoq_mod
    orig_fn = eoq_mod.compute_daily_demand
    try:
        eoq_mod.compute_daily_demand = lambda db, pid, **kwargs: MockDemand()
        res = compute_eoq(None, product_id=1, ordering_cost=-10.0, holding_rate=0.20)
        assert res.value is None
        assert res.sufficiency == "none"
    finally:
        eoq_mod.compute_daily_demand = orig_fn
