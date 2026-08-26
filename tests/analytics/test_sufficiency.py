"""Tests for data sufficiency assessment (src.analytics.sufficiency).

15-SHARED-CONTRACTS.md §5.1, §5.2, §5.4.
"""
import pytest
from src.analytics.sufficiency import score_sufficiency, Computed
from src.backend.database import SessionLocal
from src.backend.models import Product


def test_score_sufficiency_on_seeded_database():
    """Every product in baseline DB returns sufficiency in ('insufficient', 'none') and value=None."""
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        assert len(products) >= 5

        for p in products:
            res = score_sufficiency(db, p.id)
            assert isinstance(res, Computed)
            assert res.sufficiency in ("insufficient", "none")
            assert res.value is None
            assert res.formula == "score_sufficiency(sales_count, distinct_days)"
            assert res.citation == "manual §4 line 45"
    finally:
        db.close()


def test_score_sufficiency_with_sufficient_and_thin():
    """score_sufficiency returns value=1.0 for sufficient, 0.5 for thin, None for insufficient/none."""
    class MockDemandSufficient:
        value = 5.0
        sufficiency = "sufficient"
        inputs = {"sale_events_count": 20, "distinct_sale_days": 22}
        formula = "sum(sale_quantities) / window_days"
        citation = "manual §3 line 33"
        sample_size = 20
        span_days = 30

    class MockDemandThin:
        value = 3.0
        sufficiency = "thin"
        inputs = {"sale_events_count": 6, "distinct_sale_days": 8}
        formula = "sum(sale_quantities) / window_days"
        citation = "manual §3 line 33"
        sample_size = 6
        span_days = 30

    class MockDemandInsufficient:
        value = None
        sufficiency = "insufficient"
        inputs = {"sale_events_count": 2, "distinct_sale_days": 1}
        formula = "sum(sale_quantities) / window_days"
        citation = "manual §3 line 33"
        sample_size = 2
        span_days = 30

    import src.analytics.demand as demand_mod
    orig_fn = demand_mod.compute_daily_demand
    try:
        demand_mod.compute_daily_demand = lambda db, pid, **kwargs: MockDemandSufficient()
        s_res = score_sufficiency(None, product_id=1)
        assert s_res.sufficiency == "sufficient"
        assert s_res.value == 1.0

        demand_mod.compute_daily_demand = lambda db, pid, **kwargs: MockDemandThin()
        t_res = score_sufficiency(None, product_id=1)
        assert t_res.sufficiency == "thin"
        assert t_res.value == 0.5

        demand_mod.compute_daily_demand = lambda db, pid, **kwargs: MockDemandInsufficient()
        i_res = score_sufficiency(None, product_id=1)
        assert i_res.sufficiency == "insufficient"
        assert i_res.value is None
    finally:
        demand_mod.compute_daily_demand = orig_fn
