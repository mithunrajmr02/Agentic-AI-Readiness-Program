"""Analytics core package (WS-1).

15-SHARED-CONTRACTS.md §5.
Pure, deterministic business calculations with no language models and no database writes.
"""
from src.analytics.demand import compute_daily_demand
from src.analytics.eoq import compute_eoq
from src.analytics.leadtime import measured_lead_time
from src.analytics.reorder import (
    derive_reorder_point,
    derive_reorder_point_from,
    derive_reorder_quantity,
    order_quantity_from,
)
from src.analytics.sufficiency import Computed, score_sufficiency
from src.analytics.valuation import days_on_hand, inventory_value, stock_turn

__all__ = [
    "Computed",
    "compute_daily_demand",
    "derive_reorder_point",
    "derive_reorder_point_from",
    "derive_reorder_quantity",
    "order_quantity_from",
    "compute_eoq",
    "score_sufficiency",
    "measured_lead_time",
    "inventory_value",
    "days_on_hand",
    "stock_turn",
]
