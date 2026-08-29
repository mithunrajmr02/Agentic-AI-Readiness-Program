"""Tier 2 Metrics: 'DEMONSTRABLE LIVE' (M-31 to M-36).

10-IMPACT-METRICS.md §4.
Measured live in the room during interactive demonstrations, not stored.
Defines specifications and verification criteria for live tests.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.metrics.registry import MetricDefinition, MetricValue, register_metric


def compute_m31_timing_race(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-31: The timing race.

    Wall-clock: a signal fires; a volunteer navigates the current UI to raise the
    equivalent PO while the agent completes end to end.
    """
    return MetricValue(
        key="M-31",
        label="The timing race",
        value=None,
        tier="T2",
        formula="wall_clock(human_manual_flow) − wall_clock(agent_autonomous_flow)",
        missing_input=None,
        data_disclosure="real",
        window=window,
        scope=scope,
    )


def compute_m32_detection_of_invisible(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-32: Detection of the invisible.

    The clock advances; the overdue signal fires automatically.
    """
    return MetricValue(
        key="M-32",
        label="Detection of the invisible",
        value=None,
        tier="T2",
        formula="time_to_signal_after_clock_advance(po_overdue)",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m33_the_refusal(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-33: The refusal.

    An insufficient-data SKU is presented; the agent declines and names the shortfall.
    """
    return MetricValue(
        key="M-33",
        label="The refusal",
        value=None,
        tier="T2",
        formula="verdict(sku_with_zero_sales) == 'insufficient_data' with exact shortfall",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m34_rbac_403(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-34: The RBAC 403.

    Staff attempts an approval and is refused with HTTP 403.
    """
    return MetricValue(
        key="M-34",
        label="The RBAC 403",
        value=None,
        tier="T2",
        formula="http_status(staff_user_approval_request) == 403 Forbidden",
        missing_input=None,
        data_disclosure="real",
        window=window,
        scope=scope,
    )


def compute_m35_rejection_path(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-35: The rejection path.

    A manager rejects; the signal stays open and re-raises on the next cycle.
    """
    return MetricValue(
        key="M-35",
        label="The rejection path",
        value=None,
        tier="T2",
        formula="signal.status == 'open' after manager_rejection",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m36_graceful_llm_failure(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-36: Graceful LLM failure.

    Quota exhausted mid-run; the decision completes deterministically without a narrative.
    """
    return MetricValue(
        key="M-36",
        label="Graceful LLM failure",
        value=None,
        tier="T2",
        formula="decision.status in {'executed', 'pending_approval'} when llm_available == False",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def register_t2_metrics() -> None:
    """Register all T2 live demonstration metrics in the catalog."""
    register_metric(
        MetricDefinition(
            key="M-31",
            label="The timing race",
            category="t2_live",
            tier="T2",
            formula="wall_clock(human_manual_flow) − wall_clock(agent_autonomous_flow)",
            missing_input=None,
            data_disclosure="real",
            computer=compute_m31_timing_race,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-32",
            label="Detection of the invisible",
            category="t2_live",
            tier="T2",
            formula="time_to_signal_after_clock_advance(po_overdue)",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m32_detection_of_invisible,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-33",
            label="The refusal",
            category="t2_live",
            tier="T2",
            formula="verdict(sku_with_zero_sales) == 'insufficient_data' with exact shortfall",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m33_the_refusal,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-34",
            label="The RBAC 403",
            category="t2_live",
            tier="T2",
            formula="http_status(staff_user_approval_request) == 403 Forbidden",
            missing_input=None,
            data_disclosure="real",
            computer=compute_m34_rbac_403,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-35",
            label="The rejection path",
            category="t2_live",
            tier="T2",
            formula="signal.status == 'open' after manager_rejection",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m35_rejection_path,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-36",
            label="Graceful LLM failure",
            category="t2_live",
            tier="T2",
            formula="decision.status in {'executed', 'pending_approval'} when llm_available == False",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m36_graceful_llm_failure,
        )
    )
