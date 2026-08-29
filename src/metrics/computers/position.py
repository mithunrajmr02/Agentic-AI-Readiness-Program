"""Capital & Inventory Position Metric Computers (M-18 to M-22).

10-IMPACT-METRICS.md §2.4 / 15-SHARED-CONTRACTS.md §4.3.
Computes inventory valuation at cost_price, days on hand, slow-moving items,
stock turn, and order consolidation savings (disclosed synthetic).
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from src.backend.models import MovementType, Product, StockLevel, StockMovement
from src.backend.models_governance import Decision
from src.core import clock
from src.metrics.registry import MetricDefinition, MetricValue, register_metric


def compute_m18_days_on_hand(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-18: Days on hand.

    Formula: quantity_on_hand / average_daily_sales (§13 line 139).
    """
    products = db.query(Product).all()
    if not products:
        return MetricValue(
            key="M-18",
            label="Days on hand",
            value=None,
            tier="T1",
            formula="quantity_on_hand / average_daily_sales",
            missing_input=None,
            data_disclosure="synthetic",
            window=window,
            scope=scope,
        )

    # Compute average days on hand across stocked items with sales
    doh_list: list[float] = []
    cutoff = clock.now() - timedelta(days=30)
    for p in products:
        level = db.query(StockLevel).filter(StockLevel.product_id == p.id).first()
        on_hand = level.quantity_on_hand if level else 0

        # Sales in 30-day window
        sales = (
            db.query(StockMovement)
            .filter(
                StockMovement.product_id == p.id,
                StockMovement.movement_type.in_([MovementType.sale, "sale"]),
                StockMovement.recorded_at >= cutoff,
            )
            .all()
        )
        total_sold = sum(abs(m.quantity) for m in sales)
        if total_sold > 0:
            daily_sales = total_sold / 30.0
            doh_list.append(on_hand / daily_sales)

    value: Optional[float] = None
    if doh_list:
        value = round(float(sum(doh_list) / len(doh_list)), 2)

    return MetricValue(
        key="M-18",
        label="Days on hand",
        value=value,
        tier="T1",
        formula="quantity_on_hand / average_daily_sales",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m19_slow_moving_count(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-19: Slow-moving count.

    Formula: Products with no movement in >= 30 days (§13 line 136).
    """
    products = db.query(Product).all()
    cutoff = clock.now() - timedelta(days=30)
    slow_count = 0

    for p in products:
        recent_mov = (
            db.query(StockMovement)
            .filter(
                StockMovement.product_id == p.id,
                StockMovement.recorded_at >= cutoff,
            )
            .first()
        )
        if recent_mov is None:
            slow_count += 1

    return MetricValue(
        key="M-19",
        label="Slow-moving count",
        value=float(slow_count),
        tier="T1",
        formula="count(products with no movement in >= 30 days)",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m20_stock_above_requirement(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-20: Stock above requirement.

    Formula: Σ max(0, on_hand − reorder_point) × cost_price.
    Uses cost_price (never unit_price).
    """
    products = db.query(Product).all()
    excess_value = 0.0

    for p in products:
        level = db.query(StockLevel).filter(StockLevel.product_id == p.id).first()
        on_hand = level.quantity_on_hand if level else 0
        rop = p.reorder_point or 0
        cost = p.cost_price or 0.0
        excess_qty = max(0, on_hand - rop)
        excess_value += excess_qty * cost

    return MetricValue(
        key="M-20",
        label="Stock above requirement",
        value=round(excess_value, 2),
        tier="T1",
        formula="sum(max(0, on_hand − reorder_point) * cost_price)",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m21_stock_turn_ratio(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-21: Stock turn ratio.

    Formula: COGS / average inventory value, where COGS = Σ (sale_qty × cost_price).
    Both valued at cost_price.
    """
    products = db.query(Product).all()
    if not products:
        return MetricValue(
            key="M-21",
            label="Stock turn ratio",
            value=None,
            tier="T1",
            formula="COGS / average_inventory_value",
            missing_input=None,
            data_disclosure="synthetic",
            window=window,
            scope=scope,
        )

    # 1. Total current inventory value at cost_price
    total_inv_val = 0.0
    cost_map: dict[int, float] = {}
    for p in products:
        cost = p.cost_price or 0.0
        cost_map[p.id] = cost
        level = db.query(StockLevel).filter(StockLevel.product_id == p.id).first()
        on_hand = level.quantity_on_hand if level else 0
        total_inv_val += on_hand * cost

    # 2. Total COGS from sales
    sales = (
        db.query(StockMovement)
        .filter(StockMovement.movement_type.in_([MovementType.sale, "sale"]))
        .all()
    )
    cogs = 0.0
    for s in sales:
        cost = cost_map.get(s.product_id, 0.0)
        cogs += abs(s.quantity) * cost

    value: Optional[float] = None
    if total_inv_val > 0 and cogs > 0:
        value = round(cogs / total_inv_val, 4)

    return MetricValue(
        key="M-21",
        label="Stock turn ratio",
        value=value,
        tier="T1",
        formula="COGS / average_inventory_value",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m22_order_cost_saving(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-22: Order-cost saving from consolidation.

    Formula: orders_avoided × ordering_cost (assumed base ₹500/PO).
    """
    consolidations = (
        db.query(Decision)
        .filter(
            Decision.action_type.in_(["consolidate_po", "consolidate"]),
            Decision.status == "executed",
        )
        .count()
    )
    assumed_ordering_cost = 500.0
    savings = float(consolidations) * assumed_ordering_cost

    return MetricValue(
        key="M-22",
        label="Order-cost saving from consolidation",
        value=round(savings, 2),
        tier="T1",
        formula="orders_avoided * ordering_cost (assumed ₹500 per PO)",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def register_position_metrics() -> None:
    """Register all capital and inventory position metrics in the catalog."""
    register_metric(
        MetricDefinition(
            key="M-18",
            label="Days on hand",
            category="position",
            tier="T1",
            formula="quantity_on_hand / average_daily_sales",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m18_days_on_hand,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-19",
            label="Slow-moving count",
            category="position",
            tier="T1",
            formula="count(products with no movement in >= 30 days)",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m19_slow_moving_count,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-20",
            label="Stock above requirement",
            category="position",
            tier="T1",
            formula="sum(max(0, on_hand − reorder_point) * cost_price)",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m20_stock_above_requirement,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-21",
            label="Stock turn ratio",
            category="position",
            tier="T1",
            formula="COGS / average_inventory_value",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m21_stock_turn_ratio,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-22",
            label="Order-cost saving from consolidation",
            category="position",
            tier="T1",
            formula="orders_avoided * ordering_cost",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m22_order_cost_saving,
        )
    )
