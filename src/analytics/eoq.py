"""Economic Order Quantity calculation (WS-1).

15-SHARED-CONTRACTS.md §5.1, §5.2 and manual §9 line 98:
EOQ = sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)
"""
import math
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.analytics.demand import compute_daily_demand
from src.analytics.sufficiency import Computed
from src.backend.models import Product


def compute_eoq(
    db: Session, product_id: int, ordering_cost: float, holding_rate: float
) -> Computed:
    """Compute Economic Order Quantity for optimal batch size.

    15-SHARED-CONTRACTS.md §5.2 and manual §9 line 98.
    Parameters:
    - ordering_cost: Cost per order placed (₹)
    - holding_rate: Annual holding cost rate as fraction of unit cost price (e.g. 0.20 for 20%)
    """
    demand = compute_daily_demand(db, product_id)
    inputs: dict[str, Any] = {
        "product_id": product_id,
        "ordering_cost": ordering_cost,
        "holding_rate": holding_rate,
    }

    if (
        demand.value is None
        or demand.sufficiency in ("insufficient", "none")
        or ordering_cost <= 0
        or holding_rate <= 0
    ):
        return Computed(
            value=None,
            sufficiency=demand.sufficiency if demand.value is None else "none",
            inputs=inputs,
            formula="sqrt((2 × annual_demand × ordering_cost) / holding_cost_per_unit)",
            citation="manual §9 line 98",
            sample_size=demand.sample_size,
            span_days=demand.span_days,
        )

    product = db.query(Product).filter(Product.id == product_id).first() if db else None
    unit_cost = product.cost_price if product and product.cost_price else 1.0
    holding_cost_per_unit = unit_cost * holding_rate

    if holding_cost_per_unit <= 0:
        return Computed(
            value=None,
            sufficiency="none",
            inputs=inputs,
            formula="sqrt((2 × annual_demand × ordering_cost) / holding_cost_per_unit)",
            citation="manual §9 line 98",
            sample_size=demand.sample_size,
            span_days=demand.span_days,
        )

    annual_demand = demand.value * 365.0
    raw_eoq = math.sqrt((2.0 * annual_demand * ordering_cost) / holding_cost_per_unit)
    eoq_value = round(raw_eoq, 2)

    inputs.update(
        {
            "daily_demand": demand.value,
            "annual_demand": annual_demand,
            "unit_cost_price": unit_cost,
            "holding_cost_per_unit": holding_cost_per_unit,
        }
    )

    return Computed(
        value=eoq_value,
        sufficiency=demand.sufficiency,
        inputs=inputs,
        formula="sqrt((2 × annual_demand × ordering_cost) / holding_cost_per_unit)",
        citation="manual §9 line 98",
        sample_size=demand.sample_size,
        span_days=demand.span_days,
    )
