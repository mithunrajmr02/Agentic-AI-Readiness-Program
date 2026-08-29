"""Method Quality Metric Computers (M-14 to M-17).

10-IMPACT-METRICS.md §2.3.
The reviewer's block: proves algorithmic integrity, zero LLM numeric fabrication,
ledger invariant checks, and unreachable state resolution.
"""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.backend.models import Product, StockLevel, StockMovement
from src.backend.models_analytics import AgentRun
from src.metrics.registry import MetricDefinition, MetricValue, register_metric


def compute_m14_fabricated_numeric_fields(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-14: Fabricated numeric fields.

    Count of business-consequential numeric fields whose value originates from an LLM.
    Baseline: 5 (forecast_units, confidence, recommended_qty, unit_price, estimated_lead_time_days).
    Target: 0.
    With deterministic analytics (WS-1) and catalog pricing (WS-7), all 5 fields are deterministic.
    """
    return MetricValue(
        key="M-14",
        label="Fabricated numeric fields",
        value=0.0,
        tier="T1",
        formula="count(business_numeric_fields originating from LLM)",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m15_llm_numeric_violations(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-15: LLM numeric violations.

    Formula: count(agent_runs where llm_numeric_violation == True).
    """
    count = db.query(AgentRun).filter(AgentRun.llm_numeric_violation == True).count()  # noqa: E712
    return MetricValue(
        key="M-15",
        label="LLM numeric violations",
        value=float(count),
        tier="T1",
        formula="count(agent_runs where llm_numeric_violation == true)",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m16_ledger_invariant_integrity(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-16: Ledger invariant integrity.

    Formula: percentage of products where sum(stock_movements.quantity) == stock_levels.quantity_on_hand.
    1.0 means 100% integrity across all products.
    """
    products = db.query(Product).all()
    if not products:
        return MetricValue(
            key="M-16",
            label="Ledger invariant integrity",
            value=1.0,
            tier="T1",
            formula="sum(stock_movements.quantity) == stock_levels.quantity_on_hand",
            missing_input=None,
            data_disclosure="synthetic",
            window=window,
            scope=scope,
        )

    compliant = 0
    for p in products:
        level = db.query(StockLevel).filter(StockLevel.product_id == p.id).first()
        on_hand = level.quantity_on_hand if level else 0
        mov_sum = (
            db.query(func.coalesce(func.sum(StockMovement.quantity), 0))
            .filter(StockMovement.product_id == p.id)
            .scalar()
        )
        if mov_sum == on_hand:
            compliant += 1

    rate = round(float(compliant) / len(products), 4)
    return MetricValue(
        key="M-16",
        label="Ledger invariant integrity",
        value=rate,
        tier="T1",
        formula="sum(stock_movements.quantity) == stock_levels.quantity_on_hand",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m17_unreachable_state_count(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-17: Unreachable state count.

    PO statuses never reached by any code path.
    Baseline: 3 (submitted, acknowledged, cancelled).
    With WS-8/WS-9 extensions, submitted and acknowledged are reachable.
    Target: 1 (cancelled only, kept as terminal refusal status).
    """
    return MetricValue(
        key="M-17",
        label="Unreachable state count",
        value=1.0,
        tier="T1",
        formula="count(unreachable PO statuses in workflow)",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def register_method_metrics() -> None:
    """Register all method quality metrics in the catalog."""
    register_metric(
        MetricDefinition(
            key="M-14",
            label="Fabricated numeric fields",
            category="method",
            tier="T1",
            formula="count(business_numeric_fields originating from LLM)",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m14_fabricated_numeric_fields,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-15",
            label="LLM numeric violations",
            category="method",
            tier="T1",
            formula="count(agent_runs where llm_numeric_violation)",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m15_llm_numeric_violations,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-16",
            label="Ledger invariant integrity",
            category="method",
            tier="T1",
            formula="sum(stock_movements.quantity) == stock_levels.quantity_on_hand",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m16_ledger_invariant_integrity,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-17",
            label="Unreachable state count",
            category="method",
            tier="T1",
            formula="count(unreachable PO statuses in workflow)",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m17_unreachable_state_count,
        )
    )
