"""Tier 3 Metrics: 'WHAT WE CANNOT MEASURE YET' (M-23 to M-30).

10-IMPACT-METRICS.md §3 / 15-SHARED-CONTRACTS.md §14.
Hard Rule (CI invariant #8):
  Every T3 metric ALWAYS returns value=None. Never 0.0. Never an estimate.
  Formula and named missing_input are always populated.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.metrics.registry import MetricDefinition, MetricValue, register_metric


def compute_m23_revenue_protected(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-23: Revenue protected.

    Formula: stockout_days_avoided × daily_units × (unit_price − cost_price).
    Missing input: Real demand history only (margin is available).
    """
    return MetricValue(
        key="M-23",
        label="Revenue protected",
        value=None,
        tier="T3",
        formula="stockout_days_avoided * daily_units * (unit_price − cost_price)",
        missing_input="Real demand history (90 days of sales history to establish unconstrained demand baseline)",
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m24_fte_hours_saved(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-24: FTE hours saved.

    Formula: decisions_automated × minutes_per_manual_decision.
    Missing input: Time-and-motion baseline for actual manual decision workflow.
    """
    return MetricValue(
        key="M-24",
        label="FTE hours saved",
        value=None,
        tier="T3",
        formula="decisions_automated * minutes_per_manual_decision",
        missing_input="Time-and-motion baseline for manual replenishment decision workflow",
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m25_fill_rate(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-25: Fill rate.

    Formula: orders_fulfilled_immediately / total_orders (§13 line 138).
    Missing input: Customer order entity and fulfillment tracking.
    """
    return MetricValue(
        key="M-25",
        label="Fill rate",
        value=None,
        tier="T3",
        formula="orders_fulfilled_immediately / total_orders",
        missing_input="Customer order entity and order fulfillment tracking table",
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m26_stockout_cost_avoided(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-26: Stockout cost avoided.

    Formula: stockout_days × lost_units × (unit_price − cost_price).
    Missing input: Real demand history and customer stockout duration records.
    """
    return MetricValue(
        key="M-26",
        label="Stockout cost avoided",
        value=None,
        tier="T3",
        formula="stockout_days * lost_units * (unit_price − cost_price)",
        missing_input="Real demand history and verified stockout duration records",
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m27_true_stock_turn(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-27: True stock turn.

    Formula: COGS / average_inventory_value (§13 line 137).
    Missing input: Real sales volume over a 12-month operating cycle.
    """
    return MetricValue(
        key="M-27",
        label="True stock turn",
        value=None,
        tier="T3",
        formula="COGS / average_inventory_value",
        missing_input="Real sales volume over a 12-month operating cycle",
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m28_working_capital_released(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-28: Working capital released.

    Formula: Δ inventory_value against opening baseline.
    Missing input: Historical opening inventory valuations from client enterprise ERP.
    """
    return MetricValue(
        key="M-28",
        label="Working capital released",
        value=None,
        tier="T3",
        formula="delta inventory_value against opening baseline",
        missing_input="Historical opening inventory valuations from client enterprise ERP",
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m29_expediting_cost_avoided(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-29: Expediting cost avoided.

    Formula: rush_orders_avoided × premium_rate.
    Missing input: Rush-order surcharge and premium freight schedules.
    """
    return MetricValue(
        key="M-29",
        label="Expediting cost avoided",
        value=None,
        tier="T3",
        formula="rush_orders_avoided * premium_rate",
        missing_input="Rush-order surcharge and premium freight cost schedules",
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m30_supplier_price_improvement(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-30: Supplier price improvement.

    Formula: Σ (previous_price − selected_price) × qty.
    Missing input: Historical supplier purchase price negotiation records.
    """
    return MetricValue(
        key="M-30",
        label="Supplier price improvement",
        value=None,
        tier="T3",
        formula="sum((previous_price − selected_price) * qty)",
        missing_input="Historical supplier price negotiation logs and multi-quote procurement records",
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def register_t3_metrics() -> None:
    """Register all T3 gap metrics in the catalog."""
    register_metric(
        MetricDefinition(
            key="M-23",
            label="Revenue protected",
            category="t3_gaps",
            tier="T3",
            formula="stockout_days_avoided * daily_units * (unit_price − cost_price)",
            missing_input="Real demand history (90 days of sales history to establish unconstrained demand baseline)",
            data_disclosure="synthetic",
            computer=compute_m23_revenue_protected,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-24",
            label="FTE hours saved",
            category="t3_gaps",
            tier="T3",
            formula="decisions_automated * minutes_per_manual_decision",
            missing_input="Time-and-motion baseline for manual replenishment decision workflow",
            data_disclosure="synthetic",
            computer=compute_m24_fte_hours_saved,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-25",
            label="Fill rate",
            category="t3_gaps",
            tier="T3",
            formula="orders_fulfilled_immediately / total_orders",
            missing_input="Customer order entity and order fulfillment tracking table",
            data_disclosure="synthetic",
            computer=compute_m25_fill_rate,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-26",
            label="Stockout cost avoided",
            category="t3_gaps",
            tier="T3",
            formula="stockout_days * lost_units * (unit_price − cost_price)",
            missing_input="Real demand history and verified stockout duration records",
            data_disclosure="synthetic",
            computer=compute_m26_stockout_cost_avoided,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-27",
            label="True stock turn",
            category="t3_gaps",
            tier="T3",
            formula="COGS / average_inventory_value",
            missing_input="Real sales volume over a 12-month operating cycle",
            data_disclosure="synthetic",
            computer=compute_m27_true_stock_turn,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-28",
            label="Working capital released",
            category="t3_gaps",
            tier="T3",
            formula="delta inventory_value against opening baseline",
            missing_input="Historical opening inventory valuations from client enterprise ERP",
            data_disclosure="synthetic",
            computer=compute_m28_working_capital_released,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-29",
            label="Expediting cost avoided",
            category="t3_gaps",
            tier="T3",
            formula="rush_orders_avoided * premium_rate",
            missing_input="Rush-order surcharge and premium freight cost schedules",
            data_disclosure="synthetic",
            computer=compute_m29_expediting_cost_avoided,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-30",
            label="Supplier price improvement",
            category="t3_gaps",
            tier="T3",
            formula="sum((previous_price − selected_price) * qty)",
            missing_input="Historical supplier price negotiation logs and multi-quote procurement records",
            data_disclosure="synthetic",
            computer=compute_m30_supplier_price_improvement,
        )
    )
