"""Autonomy & Governance Metric Computers (M-7 to M-13).

10-IMPACT-METRICS.md §2.2.
Computes autonomy rates, escalation breakdowns, approval mix, refusal rates,
policy citations, and actor attribution metrics.
"""
from __future__ import annotations

import statistics
from typing import Optional

from sqlalchemy.orm import Session

from src.backend.models import StockMovement
from src.backend.models_governance import Approval, Decision
from src.metrics.registry import MetricDefinition, MetricValue, register_metric


def compute_m7_autonomy_rate(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-7: Autonomy rate.

    Formula: count(status=executed AND actor=agent) / count(all executed).
    """
    executed = db.query(Decision).filter(Decision.status == "executed").all()
    if not executed:
        # Default when no decisions have been executed yet
        return MetricValue(
            key="M-7",
            label="Autonomy rate",
            value=0.0,
            tier="T1",
            formula="count(status=executed AND actor=agent) / count(all executed)",
            missing_input=None,
            data_disclosure="synthetic",
            window=window,
            scope=scope,
        )

    agent_executed = sum(1 for d in executed if d.actor and d.actor.startswith("agent"))
    rate = round(float(agent_executed) / len(executed), 4)

    return MetricValue(
        key="M-7",
        label="Autonomy rate",
        value=rate,
        tier="T1",
        formula="count(status=executed AND actor=agent) / count(all executed)",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m8_escalation_rate(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-8: Escalation rate by reason.

    Formula: count(decisions where escalation_reason is not null) / count(all decisions).
    """
    total = db.query(Decision).count()
    if total == 0:
        return MetricValue(
            key="M-8",
            label="Escalation rate by reason",
            value=0.0,
            tier="T1",
            formula="count(decisions with escalation_reason) / count(all decisions)",
            missing_input=None,
            data_disclosure="synthetic",
            window=window,
            scope=scope,
        )

    escalated = db.query(Decision).filter(Decision.escalation_reason.isnot(None)).count()
    rate = round(float(escalated) / total, 4)

    return MetricValue(
        key="M-8",
        label="Escalation rate by reason",
        value=rate,
        tier="T1",
        formula="count(decisions with escalation_reason) / count(all decisions)",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m9_approval_outcome_mix(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-9: Approval outcome mix.

    Formula: Proportions of approved / rejected / countered / expired.
    Headline value: total decided approvals.
    """
    total = db.query(Approval).count()
    return MetricValue(
        key="M-9",
        label="Approval outcome mix",
        value=float(total),
        tier="T1",
        formula="approved / rejected / countered / expired as proportions",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m10_approval_latency(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-10: Approval latency.

    Formula: approvals.decided_at − approvals.requested_at (median in hours).
    """
    approvals = (
        db.query(Approval)
        .filter(Approval.decided_at.isnot(None), Approval.requested_at.isnot(None))
        .all()
    )
    latencies_hours: list[float] = []
    for app in approvals:
        if app.decided_at and app.requested_at and app.decided_at >= app.requested_at:
            diff_hours = (app.decided_at - app.requested_at).total_seconds() / 3600.0
            latencies_hours.append(diff_hours)

    value: Optional[float] = None
    if latencies_hours:
        value = round(float(statistics.median(latencies_hours)), 2)

    return MetricValue(
        key="M-10",
        label="Approval latency",
        value=value,
        tier="T1",
        formula="approvals.decided_at − approvals.requested_at (median hours)",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m11_refusal_rate(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-11: Refusal rate.

    Formula: count(status=insufficient_data) / count(all decisions).
    """
    total = db.query(Decision).count()
    if total == 0:
        return MetricValue(
            key="M-11",
            label="Refusal rate",
            value=0.0,
            tier="T1",
            formula="count(status=insufficient_data) / count(all decisions)",
            missing_input=None,
            data_disclosure="synthetic",
            window=window,
            scope=scope,
        )

    refused = db.query(Decision).filter(Decision.status == "insufficient_data").count()
    rate = round(float(refused) / total, 4)

    return MetricValue(
        key="M-11",
        label="Refusal rate",
        value=rate,
        tier="T1",
        formula="count(status=insufficient_data) / count(all decisions)",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m12_policy_citation_coverage(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-12: Policy citation coverage.

    Formula: count(decisions with non-null policy_citation) / count(decisions requiring policy check).
    Target: 1.0 (100%).
    """
    decisions = db.query(Decision).all()
    if not decisions:
        return MetricValue(
            key="M-12",
            label="Policy citation coverage",
            value=1.0,
            tier="T1",
            formula="count(decisions with non-null policy_citation) / count(all decisions)",
            missing_input=None,
            data_disclosure="synthetic",
            window=window,
            scope=scope,
        )

    with_citation = sum(1 for d in decisions if d.policy_citation and len(d.policy_citation.strip()) > 0)
    rate = round(float(with_citation) / len(decisions), 4)

    return MetricValue(
        key="M-12",
        label="Policy citation coverage",
        value=rate,
        tier="T1",
        formula="count(decisions with non-null policy_citation) / count(all decisions)",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def compute_m13_attribution_completeness(
    db: Session,
    window: str = "all_time",
    scope: str = "global",
) -> MetricValue:
    """M-13: Attribution completeness.

    Formula: count(writes with a resolved actor) / count(all writes).
    """
    movements = db.query(StockMovement).all()
    if not movements:
        return MetricValue(
            key="M-13",
            label="Attribution completeness",
            value=1.0,
            tier="T1",
            formula="count(writes with resolved actor) / count(all writes)",
            missing_input=None,
            data_disclosure="synthetic",
            window=window,
            scope=scope,
        )

    resolved = sum(1 for m in movements if m.recorded_by and len(m.recorded_by.strip()) > 0)
    rate = round(float(resolved) / len(movements), 4)

    return MetricValue(
        key="M-13",
        label="Attribution completeness",
        value=rate,
        tier="T1",
        formula="count(writes with resolved actor) / count(all writes)",
        missing_input=None,
        data_disclosure="synthetic",
        window=window,
        scope=scope,
    )


def register_governance_metrics() -> None:
    """Register all autonomy & governance metrics in the catalog."""
    register_metric(
        MetricDefinition(
            key="M-7",
            label="Autonomy rate",
            category="decision",
            tier="T1",
            formula="count(status=executed AND actor=agent) / count(all executed)",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m7_autonomy_rate,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-8",
            label="Escalation rate by reason",
            category="decision",
            tier="T1",
            formula="count group by escalation_reason",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m8_escalation_rate,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-9",
            label="Approval outcome mix",
            category="decision",
            tier="T1",
            formula="approved / rejected / countered / expired as proportions",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m9_approval_outcome_mix,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-10",
            label="Approval latency",
            category="decision",
            tier="T1",
            formula="approvals.decided_at − decisions.proposed_at (median hours)",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m10_approval_latency,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-11",
            label="Refusal rate",
            category="decision",
            tier="T1",
            formula="count(status=insufficient_data) / count(all runs)",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m11_refusal_rate,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-12",
            label="Policy citation coverage",
            category="decision",
            tier="T1",
            formula="count(decisions with non-null policy_citation) / count(decisions requiring a policy check)",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m12_policy_citation_coverage,
        )
    )
    register_metric(
        MetricDefinition(
            key="M-13",
            label="Attribution completeness",
            category="decision",
            tier="T1",
            formula="count(writes with a resolved actor) / count(all writes)",
            missing_input=None,
            data_disclosure="synthetic",
            computer=compute_m13_attribution_completeness,
        )
    )
