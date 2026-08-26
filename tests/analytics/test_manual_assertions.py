"""WS-1 Manual worked example assertions and reorder point tests.

15-SHARED-CONTRACTS.md §5.3 / §5.4 and manual §3 line 35, §9 line 102.
"""
import pytest
from src.analytics.reorder import derive_reorder_point, derive_reorder_quantity
from src.analytics.demand import compute_daily_demand
from src.core.vocab import SUFFICIENCY


def test_manual_worked_examples_literal_assertions():
    """Write these two tests FIRST, before any implementation (WS-1 requirement):
    assert (10*5)+(10*2) == 70    # manual §3 line 35
    assert (5*7)+(5*14) == 105    # manual §9 line 102
    """
    # manual §3 line 35 — reorder point worked example
    assert (10 * 5) + (10 * 2) == 70

    # manual §9 line 102 — order quantity worked example
    assert (5 * 7) + (5 * 14) == 105


def test_reorder_point_matches_manual_worked_example_direct():
    """18-INTEGRATION-AND-TESTING.md §4.1."""
    from src.analytics.reorder import derive_reorder_point_from
    res = derive_reorder_point_from(demand=10, lead_time=5, safety_days=2)
    assert res.value == 70
    assert res.citation == "manual §3 line 35"


def test_order_quantity_matches_manual_worked_example_direct():
    """18-INTEGRATION-AND-TESTING.md §4.1."""
    from src.analytics.reorder import order_quantity_from
    res = order_quantity_from(demand=5, lead_time=7, safety_days=14)
    assert res.value == 105
    assert res.citation == "manual §9 line 102"


def test_derive_reorder_point_reproduces_manual_worked_example():
    """manual §3 line 35: demand=10, lead_time=5, safety_stock_days=2 -> 70 units."""
    class FakeDemandComputed:
        value = 10.0
        sufficiency = "sufficient"
        inputs = {"daily_demand": 10.0}
        formula = "sum(sale_quantities) / window_days"
        citation = "manual §3 line 33"
        sample_size = 30
        span_days = 30

    class FakeSupplier:
        id = 1
        lead_time_days = 5

    class FakeProduct:
        id = 1
        supplier_id = 1

    class FakeQuery:
        def __init__(self, model):
            self.model = model

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            if "Product" in str(self.model):
                return FakeProduct()
            if "Supplier" in str(self.model):
                return FakeSupplier()
            return None

    class FakeDB:
        def query(self, model):
            return FakeQuery(model)

    import src.analytics.reorder as reorder_mod
    orig_demand_fn = reorder_mod.compute_daily_demand
    try:
        reorder_mod.compute_daily_demand = lambda db, pid, **kwargs: FakeDemandComputed()
        computed = derive_reorder_point(FakeDB(), product_id=1, safety_stock_days=2)
        assert computed.value == 70.0
        assert computed.sufficiency == "sufficient"
        assert computed.citation == "manual §3 line 35"
        assert computed.formula == "(demand × lead_time) + (demand × safety_days)"
    finally:
        reorder_mod.compute_daily_demand = orig_demand_fn


def test_derive_reorder_quantity_reproduces_manual_worked_example():
    """manual §9 line 102: demand=5, lead_time=7, safety_days=14 -> (5*7) + (5*14) = 105 units."""
    class FakeDemandComputed:
        value = 5.0
        sufficiency = "sufficient"
        inputs = {"daily_demand": 5.0}
        formula = "sum(sale_quantities) / window_days"
        citation = "manual §3 line 33"
        sample_size = 25
        span_days = 30

    class FakeSupplier:
        id = 1
        lead_time_days = 7

    class FakeProduct:
        id = 1
        supplier_id = 1

    class FakeQuery:
        def __init__(self, model):
            self.model = model

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            if "Product" in str(self.model):
                return FakeProduct()
            if "Supplier" in str(self.model):
                return FakeSupplier()
            return None

    class FakeDB:
        def query(self, model):
            return FakeQuery(model)

    import src.analytics.reorder as reorder_mod
    orig_demand_fn = reorder_mod.compute_daily_demand
    try:
        reorder_mod.compute_daily_demand = lambda db, pid, **kwargs: FakeDemandComputed()
        computed = derive_reorder_quantity(FakeDB(), product_id=1, safety_days=14)
        assert computed.value == 105.0
        assert computed.sufficiency == "sufficient"
        assert computed.citation == "manual §9 line 102"
    finally:
        reorder_mod.compute_daily_demand = orig_demand_fn
