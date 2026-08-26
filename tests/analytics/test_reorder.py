"""Tests for reorder point derivation (src.analytics.reorder).

15-SHARED-CONTRACTS.md §5.2, §5.3 and manual §3 line 35, §9 line 102.
"""
import pytest
from unittest.mock import MagicMock

from src.analytics.reorder import derive_reorder_point, derive_reorder_quantity
from src.analytics.sufficiency import Computed
from src.backend.database import SessionLocal
from src.backend.models import Product, Supplier


def test_derive_reorder_point_with_insufficient_data_returns_none_value():
    """When demand sufficiency is insufficient or none, derive_reorder_point returns value=None."""
    db = SessionLocal()
    try:
        # All 5 products in baseline DB have insufficient or none demand
        for p in db.query(Product).all():
            res = derive_reorder_point(db, p.id)
            assert res.sufficiency in ("insufficient", "none")
            assert res.value is None
            assert res.citation == "manual §3 line 35"
            assert res.formula == "(demand × lead_time) + (demand × safety_days)"
    finally:
        db.close()


def test_derive_reorder_point_with_thin_or_sufficient_demand():
    """derive_reorder_point computes (demand * lead_time) + (demand * safety_days)."""
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
        supplier_id = 2

    class MockSupplier:
        id = 2
        lead_time_days = 5

    class MockQuery:
        def __init__(self, model):
            self.model = model
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            if "Product" in str(self.model):
                return MockProduct()
            if "Supplier" in str(self.model):
                return MockSupplier()
            return None

    class MockDB:
        def query(self, model):
            return MockQuery(model)

    import src.analytics.reorder as reorder_mod
    orig_demand_fn = reorder_mod.compute_daily_demand
    try:
        reorder_mod.compute_daily_demand = lambda db, pid, **kwargs: MockDemand()
        
        # default safety_stock_days=2 -> (10 * 5) + (10 * 2) = 70
        res = derive_reorder_point(MockDB(), product_id=1)
        assert res.value == 70.0
        assert res.sufficiency == "sufficient"
        assert res.inputs["lead_time_days"] == 5
        assert res.inputs["safety_stock_days"] == 2
        assert res.inputs["daily_demand"] == 10.0

        # custom safety_stock_days=3 -> (10 * 5) + (10 * 3) = 80
        res3 = derive_reorder_point(MockDB(), product_id=1, safety_stock_days=3)
        assert res3.value == 80.0
    finally:
        reorder_mod.compute_daily_demand = orig_demand_fn


def test_derive_reorder_point_use_measured_lead_time():
    """When use_measured_lead_time=True, measured_lead_time is used if available."""
    class MockDemand:
        value = 10.0
        sufficiency = "sufficient"
        inputs = {"daily_demand": 10.0}
        formula = "sum(sale_quantities) / window_days"
        citation = "manual §3 line 33"
        sample_size = 20
        span_days = 30

    class MockMeasuredLT:
        value = 8.0
        sufficiency = "sufficient"
        inputs = {"avg_lead_time_days": 8.0}
        formula = "avg(received_date - order_date)"
        citation = "manual §6 line 70"
        sample_size = 5
        span_days = 0

    class MockProduct:
        id = 1
        supplier_id = 2

    class MockSupplier:
        id = 2
        lead_time_days = 5

    class MockQuery:
        def __init__(self, model):
            self.model = model
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            if "Product" in str(self.model):
                return MockProduct()
            if "Supplier" in str(self.model):
                return MockSupplier()
            return None

    class MockDB:
        def query(self, model):
            return MockQuery(model)

    import src.analytics.reorder as reorder_mod
    orig_demand_fn = reorder_mod.compute_daily_demand
    orig_mlt_fn = reorder_mod.measured_lead_time
    try:
        reorder_mod.compute_daily_demand = lambda db, pid, **kwargs: MockDemand()
        reorder_mod.measured_lead_time = lambda db, sid: MockMeasuredLT()

        # With measured lead time: (10 * 8) + (10 * 2) = 100
        res = derive_reorder_point(MockDB(), product_id=1, use_measured_lead_time=True)
        assert res.value == 100.0
        assert res.inputs["lead_time_days"] == 8
    finally:
        reorder_mod.compute_daily_demand = orig_demand_fn
        reorder_mod.measured_lead_time = orig_mlt_fn


def test_derive_reorder_quantity():
    """derive_reorder_quantity computes (demand * lead_time) + (demand * safety_days)."""
    class MockDemand:
        value = 5.0
        sufficiency = "sufficient"
        inputs = {"daily_demand": 5.0}
        formula = "sum(sale_quantities) / window_days"
        citation = "manual §3 line 33"
        sample_size = 20
        span_days = 30

    class MockProduct:
        id = 1
        supplier_id = 2

    class MockSupplier:
        id = 2
        lead_time_days = 7

    class MockQuery:
        def __init__(self, model):
            self.model = model
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            if "Product" in str(self.model):
                return MockProduct()
            if "Supplier" in str(self.model):
                return MockSupplier()
            return None

    class MockDB:
        def query(self, model):
            return MockQuery(model)

    import src.analytics.reorder as reorder_mod
    orig_demand_fn = reorder_mod.compute_daily_demand
    try:
        reorder_mod.compute_daily_demand = lambda db, pid, **kwargs: MockDemand()

        # manual §9 line 102: demand=5, lead_time=7, safety_days=14 -> (5*7) + (5*14) = 105
        res = derive_reorder_quantity(MockDB(), product_id=1, safety_days=14)
        assert res.value == 105.0
        assert res.sufficiency == "sufficient"
        assert res.citation == "manual §9 line 102"
    finally:
        reorder_mod.compute_daily_demand = orig_demand_fn
