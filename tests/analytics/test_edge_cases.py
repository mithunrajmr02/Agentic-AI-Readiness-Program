"""Edge cases for analytics core (WS-1).

14-PARALLEL-WORKSTREAMS.md §WS-1 test requirement:
"Plus zero-history, single-observation, and negative-stock cases"
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from src.analytics import (
    compute_daily_demand,
    derive_reorder_point,
    derive_reorder_quantity,
    compute_eoq,
    score_sufficiency,
    measured_lead_time,
    inventory_value,
    days_on_hand,
    stock_turn,
)
from src.core import clock


def test_zero_history_case():
    """Zero history product: all demand-derived metrics return sufficiency='none' and value=None."""
    class EmptyQuery:
        def filter(self, *args, **kwargs):
            return self
        def all(self):
            return []
        def first(self):
            return None

    class EmptyDB:
        def query(self, *args):
            return EmptyQuery()

    db = EmptyDB()
    demand = compute_daily_demand(db, product_id=999)
    assert demand.sufficiency == "none"
    assert demand.value is None
    assert demand.sample_size == 0

    rop = derive_reorder_point(db, product_id=999)
    assert rop.sufficiency == "none"
    assert rop.value is None

    roq = derive_reorder_quantity(db, product_id=999)
    assert roq.sufficiency == "none"
    assert roq.value is None

    eoq = compute_eoq(db, product_id=999, ordering_cost=200, holding_rate=0.2)
    assert eoq.sufficiency == "none"
    assert eoq.value is None

    doh = days_on_hand(db, product_id=999)
    assert doh.sufficiency == "none"
    assert doh.value is None

    suff = score_sufficiency(db, product_id=999)
    assert suff.sufficiency == "none"
    assert suff.value is None

    mlt = measured_lead_time(db, supplier_id=999)
    assert mlt.sufficiency == "none"
    assert mlt.value is None


def test_single_observation_case():
    """Single observation product (1 sale event on 1 day): sufficiency='insufficient' and value=None."""
    now = clock.now()
    m1 = MagicMock()
    m1.movement_type = "sale"
    m1.quantity = -10
    m1.recorded_at = now - timedelta(days=2)

    class SingleQuery:
        def filter(self, *args, **kwargs):
            return self
        def all(self):
            return [m1]
        def first(self):
            return None

    class SingleDB:
        def query(self, *args):
            return SingleQuery()

    db = SingleDB()
    demand = compute_daily_demand(db, product_id=101)
    assert demand.sufficiency == "insufficient"
    assert demand.value is None
    assert demand.sample_size == 1
    assert demand.inputs["distinct_sale_days"] == 1

    rop = derive_reorder_point(db, product_id=101)
    assert rop.sufficiency == "insufficient"
    assert rop.value is None

    roq = derive_reorder_quantity(db, product_id=101)
    assert roq.sufficiency == "insufficient"
    assert roq.value is None

    eoq = compute_eoq(db, product_id=101, ordering_cost=100, holding_rate=0.15)
    assert eoq.sufficiency == "insufficient"
    assert eoq.value is None

    doh = days_on_hand(db, product_id=101)
    assert doh.sufficiency == "insufficient"
    assert doh.value is None

    suff = score_sufficiency(db, product_id=101)
    assert suff.sufficiency == "insufficient"
    assert suff.value is None


def test_negative_stock_case():
    """Negative stock on hand (manual §15 data discrepancy / oversold): days_on_hand is 0.0, not negative."""
    now = clock.now()
    # 10 days of sales (sufficient / thin demand)
    movements = []
    for d in range(1, 11):
        m = MagicMock()
        m.movement_type = "sale"
        m.quantity = -5
        m.recorded_at = now - timedelta(days=d)
        movements.append(m)

    stock = MagicMock()
    stock.product_id = 42
    stock.quantity_on_hand = -8  # Negative stock level

    class StockQuery:
        def __init__(self, moves, stk):
            self.moves = moves
            self.stk = stk
        def filter(self, *args, **kwargs):
            return self
        def all(self):
            return self.moves
        def first(self):
            return self.stk

    class StockDB:
        def __init__(self, moves, stk):
            self.moves = moves
            self.stk = stk
        def query(self, *args):
            return StockQuery(self.moves, self.stk)

    db = StockDB(movements, stock)
    demand = compute_daily_demand(db, product_id=42, window_days=30)
    assert demand.sufficiency == "thin"
    assert demand.value == round(50 / 30.0, 4)

    # days_on_hand should be clamped to 0.0 for negative stock
    doh = days_on_hand(db, product_id=42)
    assert doh.sufficiency == "thin"
    assert doh.value == 0.0
    assert doh.inputs["quantity_on_hand"] == -8
