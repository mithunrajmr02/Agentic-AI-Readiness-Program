"""Pure rule evaluation and data types for the Policy Engine — WS-5.

15-SHARED-CONTRACTS.md §7 / 08-AGENTIC-WORKFLOWS.md §5.5.
Defines PolicyVerdict, DecisionContext, and the ten ordered authority rules.
Rules are evaluated in strict priority order where the first match wins.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

DEFAULT_POLICY_LIMIT: float = 50000.0

CITATIONS = {
    "R4": "Operations Manual §4, line 45: reorder suggestions based on historical consumption patterns",
    "R6": "Operations Manual §6, line 74: supplier selection criteria and active status verification",
    "R7": "Operations Manual §3, line 33: reorder point and safety stock parameters configuration",
    "R8": (
        'Operations Manual §10, line 113: "Purchase Orders with a total value above '
        '₹50,000 require formal Store Manager approval prior to supplier submission."'
    ),
}


@dataclass(frozen=True)
class PolicyVerdict:
    """The authority verdict for a proposed replenishment decision (doc 15 §7)."""

    allowed: bool
    requires_approval: bool
    matched_rule: str            # e.g. "R8: value_threshold"
    escalation_reason: Optional[str]
    citation: Optional[str]
    blast_radius: int
    explanation: str


@dataclass(frozen=True)
class DecisionContext:
    """Input parameters representing a proposed decision to evaluate (doc 15 §7)."""

    action_type: str
    product_id: Optional[int] = None
    supplier_id: Optional[int] = None
    quantity: Optional[int] = None
    value_inr: Optional[float] = None
    sufficiency: str = "sufficient"
    is_cheapest_supplier: Optional[bool] = None
    affected_product_count: int = 1
    autonomy_mode: str = "autonomous"


def evaluate_rules(
    context: DecisionContext,
    *,
    policy_limit: Optional[float] = None,
    kill_switch_engaged: bool = False,
    blast_radius_exceeded: bool = False,
    blast_radius_count: int = 1,
    blast_radius_detail: Optional[str] = None,
) -> PolicyVerdict:
    """Evaluate the 10 ordered authority rules in strict order. First match wins.

    Rule Order (doc 08 §5.5):
    1. Kill switch engaged -> forbidden
    2. Autonomy mode 'off' -> forbidden
    3. Autonomy mode 'shadow' -> forbidden (record only, never execute)
    4. Data sufficiency in {insufficient, none, thin} -> requires approval
    5. Blast-radius cap exceeded -> requires approval
    6. Non-cheapest supplier selected -> requires approval
    7. Reorder-point change proposed -> requires approval
    8. Order value > policy_limit -> requires approval (§10 threshold: ₹50,000)
    9. Autonomy mode 'assisted' -> requires approval
    10. Otherwise -> within authority (autonomous)
    """
    effective_limit = policy_limit if policy_limit is not None else DEFAULT_POLICY_LIMIT
    radius = blast_radius_count if blast_radius_count >= 1 else context.affected_product_count

    # 1. Kill switch engaged
    if kill_switch_engaged:
        return PolicyVerdict(
            allowed=False,
            requires_approval=False,
            matched_rule="R1: kill_switch",
            escalation_reason="kill_switch",
            citation=None,
            blast_radius=radius,
            explanation="Kill switch engaged: automated execution is forbidden.",
        )

    # 2. Autonomy mode 'off'
    if context.autonomy_mode == "off":
        return PolicyVerdict(
            allowed=False,
            requires_approval=False,
            matched_rule="R2: policy_off",
            escalation_reason="policy_off",
            citation=None,
            blast_radius=radius,
            explanation="Autonomy mode is OFF: automated execution is forbidden.",
        )

    # 3. Autonomy mode 'shadow'
    if context.autonomy_mode == "shadow":
        return PolicyVerdict(
            allowed=False,
            requires_approval=False,
            matched_rule="R3: mode_shadow",
            escalation_reason="policy_off",
            citation=None,
            blast_radius=radius,
            explanation="Autonomy mode is SHADOW: decide and record only, execution forbidden.",
        )

    # 4. Data sufficiency insufficient / none / thin
    if context.sufficiency in ("insufficient", "none", "thin"):
        return PolicyVerdict(
            allowed=True,
            requires_approval=True,
            matched_rule="R4: insufficient_evidence",
            escalation_reason="insufficient_evidence",
            citation=CITATIONS["R4"],
            blast_radius=radius,
            explanation=(
                f"Data sufficiency is '{context.sufficiency}': human approval required "
                "regardless of order value."
            ),
        )

    # 5. Blast-radius cap exceeded
    if blast_radius_exceeded:
        return PolicyVerdict(
            allowed=True,
            requires_approval=True,
            matched_rule="R5: blast_radius",
            escalation_reason="blast_radius",
            citation=None,
            blast_radius=radius,
            explanation=blast_radius_detail or "Blast radius limit exceeded: human approval required.",
        )

    # 6. Non-cheapest supplier selected
    if context.is_cheapest_supplier is False:
        return PolicyVerdict(
            allowed=True,
            requires_approval=True,
            matched_rule="R6: non_cheapest_supplier",
            escalation_reason="non_cheapest_supplier",
            citation=CITATIONS["R6"],
            blast_radius=radius,
            explanation=(
                "Non-cheapest supplier selected: spending more for qualitative reasons "
                "requires human approval."
            ),
        )

    # 7. Reorder-point / configuration change proposed
    if context.action_type in ("adjust_reorder_point", "adjust_reorder_quantity", "config_change"):
        return PolicyVerdict(
            allowed=True,
            requires_approval=True,
            matched_rule="R7: config_change",
            escalation_reason="config_change",
            citation=CITATIONS["R7"],
            blast_radius=radius,
            explanation="Configuration changes (reorder point / quantity) always require human approval.",
        )

    # 8. Order value > policy_limit
    if context.value_inr is not None and context.value_inr > effective_limit:
        return PolicyVerdict(
            allowed=True,
            requires_approval=True,
            matched_rule="R8: value_threshold",
            escalation_reason="value_threshold",
            citation=CITATIONS["R8"],
            blast_radius=radius,
            explanation=(
                f"Order value ₹{context.value_inr:,.2f} exceeds policy limit of "
                f"₹{effective_limit:,.2f}."
            ),
        )

    # 9. Autonomy mode 'assisted'
    if context.autonomy_mode == "assisted":
        return PolicyVerdict(
            allowed=True,
            requires_approval=True,
            matched_rule="R9: mode_assisted",
            escalation_reason="policy_off",
            citation=None,
            blast_radius=radius,
            explanation="Autonomy mode is ASSISTED: all actions require human approval.",
        )

    # 10. Within autonomous authority
    return PolicyVerdict(
        allowed=True,
        requires_approval=False,
        matched_rule="R10: within_authority",
        escalation_reason=None,
        citation=None,
        blast_radius=radius,
        explanation="Action is within autonomous authority.",
    )
