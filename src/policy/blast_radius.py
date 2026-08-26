"""Blast radius evaluation and rate-capping — WS-5.

15-SHARED-CONTRACTS.md §7 / 08-AGENTIC-WORKFLOWS.md §5.5.
Checks hourly decision frequency and daily cumulative expenditure against
configured autonomy policy limits. All time calculations strictly use clock.now().
"""
from __future__ import annotations

from datetime import timedelta
import json
from typing import Optional

from sqlalchemy.orm import Session

from src.backend.models_governance import AutonomyPolicy, Decision
from src.core import clock
from src.policy.rules import DecisionContext


def check_blast_radius(
    db: Session,
    context: DecisionContext,
    policy: Optional[AutonomyPolicy] = None,
) -> tuple[bool, int, Optional[str]]:
    """Evaluate whether the current context violates blast-radius constraints.

    Returns:
        (is_exceeded: bool, blast_radius_count: int, explanation: Optional[str])
    """
    blast_count = max(context.affected_product_count, 1)

    if policy is None:
        return False, blast_count, None

    current_time = clock.now()

    # 1. Check orders / decisions per hour
    if policy.max_orders_per_hour is not None and policy.max_orders_per_hour > 0:
        one_hour_ago = current_time - timedelta(hours=1)
        recent_orders_count = (
            db.query(Decision)
            .filter(
                Decision.proposed_at >= one_hour_ago,
                Decision.status.notin_(("rejected", "failed", "expired")),
            )
            .count()
        )
        total_projected_orders = recent_orders_count + blast_count
        if total_projected_orders > policy.max_orders_per_hour:
            detail = (
                f"Blast radius exceeded: {total_projected_orders} decisions in the last hour "
                f"exceeds limit of {policy.max_orders_per_hour}."
            )
            return True, blast_count, detail

    # 2. Check cumulative value per day
    if policy.max_value_per_day is not None and policy.max_value_per_day > 0:
        one_day_ago = current_time - timedelta(days=1)
        recent_decisions = (
            db.query(Decision)
            .filter(
                Decision.proposed_at >= one_day_ago,
                Decision.status.notin_(("rejected", "failed", "expired")),
            )
            .all()
        )

        cumulative_value = 0.0
        for dec in recent_decisions:
            if dec.inputs:
                try:
                    inputs_data = json.loads(dec.inputs)
                    if isinstance(inputs_data, dict):
                        cumulative_value += float(
                            inputs_data.get("value_inr")
                            or inputs_data.get("order_value")
                            or inputs_data.get("total_value")
                            or 0.0
                        )
                except Exception:
                    pass

        proposed_value = float(context.value_inr or 0.0)
        projected_day_value = cumulative_value + proposed_value

        if projected_day_value > policy.max_value_per_day:
            detail = (
                f"Blast radius exceeded: 24h cumulative value ₹{projected_day_value:,.2f} "
                f"exceeds limit of ₹{policy.max_value_per_day:,.2f}."
            )
            return True, blast_count, detail

    return False, blast_count, None
