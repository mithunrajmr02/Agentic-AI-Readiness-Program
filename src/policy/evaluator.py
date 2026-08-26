"""Policy Evaluator and threshold resolution — WS-5.

15-SHARED-CONTRACTS.md §7 / 08-AGENTIC-WORKFLOWS.md §5.5 / 12-DATA-AND-API-CHANGES.md §5.4.
Provides evaluate(db, context) -> PolicyVerdict, get_effective_policy, and get_policy_threshold.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from src.backend.models_governance import AutonomyPolicy
from src.core import clock
from src.policy.blast_radius import check_blast_radius
from src.policy.killswitch import get_or_create_policy_record, is_kill_switch_engaged
from src.policy.rules import (
    DEFAULT_POLICY_LIMIT,
    DecisionContext,
    PolicyVerdict,
    evaluate_rules,
)

RETRIEVED_POLICY_CITATION = (
    'Purchase Orders with a total value above ₹50,000 require formal Store Manager '
    'approval prior to supplier submission.'
)
RETRIEVED_POLICY_SECTION = "Section 10: Procurement Officer Responsibilities"


def get_effective_policy(
    db: Session,
    scope_type: str = "global",
    scope_value: Optional[str] = None,
) -> AutonomyPolicy:
    """Retrieve the effective AutonomyPolicy record for the given scope, falling back to global."""
    if scope_type != "global" and scope_value is not None:
        scoped = (
            db.query(AutonomyPolicy)
            .filter(
                AutonomyPolicy.scope_type == scope_type,
                AutonomyPolicy.scope_value == scope_value,
            )
            .first()
        )
        if scoped is not None:
            return scoped

    return get_or_create_policy_record(db, scope_type="global", scope_value=None)


def get_policy_threshold(
    db: Optional[Session] = None,
    scope_type: str = "global",
    scope_value: Optional[str] = None,
) -> dict[str, Any]:
    """Return the retrieved threshold, citation, and section information (doc 12 §5.4)."""
    override_limit = None
    if db is not None:
        policy = get_effective_policy(db, scope_type=scope_type, scope_value=scope_value)
        override_limit = policy.max_order_value

    effective_limit = override_limit if override_limit is not None else DEFAULT_POLICY_LIMIT

    return {
        "threshold_inr": effective_limit,
        "default_threshold_inr": DEFAULT_POLICY_LIMIT,
        "is_overridden": override_limit is not None,
        "citation": RETRIEVED_POLICY_CITATION,
        "section": RETRIEVED_POLICY_SECTION,
        "source": "retrieved",
    }


def evaluate(
    db: Session,
    context: DecisionContext,
    scope_type: str = "global",
    scope_value: Optional[str] = None,
) -> PolicyVerdict:
    """Evaluate a proposed decision context against policy in strict rule order.

    Published contract for WS-8 (doc 15 §7).
    """
    policy = get_effective_policy(db, scope_type=scope_type, scope_value=scope_value)

    # Use context mode if explicitly overridden, else use configured policy mode
    effective_mode = context.autonomy_mode or policy.mode

    effective_context = DecisionContext(
        action_type=context.action_type,
        product_id=context.product_id,
        supplier_id=context.supplier_id,
        quantity=context.quantity,
        value_inr=context.value_inr,
        sufficiency=context.sufficiency,
        is_cheapest_supplier=context.is_cheapest_supplier,
        affected_product_count=context.affected_product_count,
        autonomy_mode=effective_mode,
    )

    kill_switch_active, _ = is_kill_switch_engaged(db, scope_type=scope_type, scope_value=scope_value)
    blast_radius_exceeded, blast_count, blast_detail = check_blast_radius(db, effective_context, policy)

    return evaluate_rules(
        effective_context,
        policy_limit=policy.max_order_value,
        kill_switch_engaged=kill_switch_active,
        blast_radius_exceeded=blast_radius_exceeded,
        blast_radius_count=blast_count,
        blast_radius_detail=blast_detail,
    )
