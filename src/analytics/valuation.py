"""Inventory valuation, days on hand, and stock turn ratio (WS-1).

15-SHARED-CONTRACTS.md §4.3, §5.1, §5.2 and manual §8 line 91, §13 line 137, §13 line 139.
Pure functions for capital valuation and inventory efficiency.
"""
from datetime import timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.analytics.demand import compute_daily_demand, _is_sale_movement
from src.analytics.sufficiency import Computed
from src.backend.models import Product, StockLevel, StockMovement
from src.core import clock


def inventory_value(
    db: Session, *, scope: str = "global", scope_id: Optional[Any] = None
) -> Computed:
    """Compute total inventory stock value at cost price.

    15-SHARED-CONTRACTS.md §4.3, §5.2 and manual §8 line 91.
    Valued at cost_price, NEVER unit_price (selling price).
    Scopes: 'global', 'category', 'product'.
    """
    query = db.query(Product, StockLevel).outerjoin(
        StockLevel, Product.id == StockLevel.product_id
    )

    if scope == "category" and scope_id is not None:
        cat_str = scope_id.value if hasattr(scope_id, "value") else str(scope_id)
        query = query.filter(Product.category == cat_str)
    elif scope == "product" and scope_id is not None:
        query = query.filter(Product.id == int(scope_id))

    rows = query.all()
    product_count = len(rows)

    total_value = 0.0
    total_units = 0

    for product, stock in rows:
        on_hand = stock.quantity_on_hand if stock and stock.quantity_on_hand else 0
        total_units += on_hand
        cost = product.cost_price if product and product.cost_price else 0.0
        total_value += cost * on_hand

    rounded_val = round(total_value, 2)
    sufficiency_status = "sufficient" if product_count > 0 else "none"

    inputs: dict[str, Any] = {
        "scope": scope,
        "scope_id": scope_id,
        "product_count": product_count,
        "total_units": total_units,
        "valuation_basis": "cost_price",
    }

    return Computed(
        value=rounded_val if sufficiency_status == "sufficient" else None,
        sufficiency=sufficiency_status,
        inputs=inputs,
        formula="sum(cost_price × quantity_on_hand)",
        citation="manual §8 line 91",
        sample_size=product_count,
        span_days=0,
    )


def days_on_hand(db: Session, product_id: int) -> Computed:
    """Compute days of inventory supply remaining given current stock and velocity.

    15-SHARED-CONTRACTS.md §5.2 and manual §13 line 139:
    days_on_hand = quantity_on_hand / average_daily_sales
    """
    demand = compute_daily_demand(db, product_id)
    stock = (
        db.query(StockLevel).filter(StockLevel.product_id == product_id).first()
        if db
        else None
    )
    on_hand = stock.quantity_on_hand if stock and stock.quantity_on_hand else 0

    inputs: dict[str, Any] = {
        "product_id": product_id,
        "quantity_on_hand": on_hand,
    }

    if demand.value is None or demand.value <= 0:
        return Computed(
            value=None,
            sufficiency=demand.sufficiency,
            inputs=inputs,
            formula="quantity_on_hand / daily_demand",
            citation="manual §13 line 139",
            sample_size=demand.sample_size,
            span_days=demand.span_days,
        )

    doh = max(0.0, round(on_hand / demand.value, 2))
    inputs["daily_demand"] = demand.value

    return Computed(
        value=doh,
        sufficiency=demand.sufficiency,
        inputs=inputs,
        formula="quantity_on_hand / daily_demand",
        citation="manual §13 line 139",
        sample_size=demand.sample_size,
        span_days=demand.span_days,
    )


def stock_turn(db: Session, window_days: int = 90) -> Computed:
    """Compute stock turn ratio: cost of goods sold / average inventory value.

    15-SHARED-CONTRACTS.md §5.2 and manual §13 line 137.
    """
    current_dt = clock.now()
    window_start = current_dt - timedelta(days=window_days)

    movements = (
        db.query(StockMovement, Product)
        .join(Product, StockMovement.product_id == Product.id)
        .filter(
            StockMovement.recorded_at >= window_start,
            StockMovement.recorded_at <= current_dt,
        )
        .all()
    )

    sale_moves = [
        (m, p) for m, p in movements if _is_sale_movement(m)
    ]
    sample_size = len(sale_moves)

    cogs = 0.0
    for m, p in sale_moves:
        cogs += abs(m.quantity) * (p.cost_price or 0.0)

    inv_computed = inventory_value(db, scope="global")
    avg_inventory_val = inv_computed.value or 0.0

    inputs: dict[str, Any] = {
        "window_days": window_days,
        "cogs": round(cogs, 2),
        "average_inventory_value": avg_inventory_val,
        "sale_events_count": sample_size,
    }

    if sample_size == 0 or avg_inventory_val <= 0:
        return Computed(
            value=None,
            sufficiency="none" if sample_size == 0 else "insufficient",
            inputs=inputs,
            formula="cogs / average_inventory_value",
            citation="manual §13 line 137",
            sample_size=sample_size,
            span_days=window_days,
        )

    turn_ratio = round(cogs / avg_inventory_val, 4)
    sufficiency_status = "sufficient" if sample_size >= 14 else "thin"

    return Computed(
        value=turn_ratio,
        sufficiency=sufficiency_status,
        inputs=inputs,
        formula="cogs / average_inventory_value",
        citation="manual §13 line 137",
        sample_size=sample_size,
        span_days=window_days,
    )
