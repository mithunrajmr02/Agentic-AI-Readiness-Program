"""Policy Engine — WS-5.

15-SHARED-CONTRACTS.md §7 / 14-PARALLEL-WORKSTREAMS.md §WS-5.
Publishes evaluate(db, context) -> PolicyVerdict, PolicyVerdict, DecisionContext,
and policy management functions for the Steward platform.
"""
from src.policy.blast_radius import check_blast_radius
from src.policy.evaluator import evaluate, get_effective_policy, get_policy_threshold
from src.policy.killswitch import (
    engage_kill_switch,
    is_kill_switch_engaged,
    release_kill_switch,
)
from src.policy.rules import (
    CITATIONS,
    DEFAULT_POLICY_LIMIT,
    DecisionContext,
    PolicyVerdict,
    evaluate_rules,
)

__all__ = [
    "PolicyVerdict",
    "DecisionContext",
    "evaluate",
    "evaluate_rules",
    "DEFAULT_POLICY_LIMIT",
    "CITATIONS",
    "is_kill_switch_engaged",
    "engage_kill_switch",
    "release_kill_switch",
    "check_blast_radius",
    "get_effective_policy",
    "get_policy_threshold",
]
