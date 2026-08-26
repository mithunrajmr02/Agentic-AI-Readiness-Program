"""Unit tests for the ten ordered authority rules — WS-5.

15-SHARED-CONTRACTS.md §7 / 14-PARALLEL-WORKSTREAMS.md §WS-5 / 08-AGENTIC-WORKFLOWS.md §5.5.
Tests:
- One test per rule, in order
- Kill switch beats everything
- Mode off / shadow beat subsequent rules
- ₹50,001 escalates and ₹49,999 does not
- A reorder-point change escalates at ANY value
- Non-cheapest supplier escalates at ANY value
- Low sufficiency (insufficient, none, thin) escalates at ANY value
- Strict first-match precedence
"""
import pytest

from src.policy.rules import (
    DEFAULT_POLICY_LIMIT,
    DecisionContext,
    PolicyVerdict,
    evaluate_rules,
)


# --- Rule 1: Kill switch engaged ----------------------------------------------

def test_rule_1_kill_switch_engaged_forbidden():
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=1000.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="autonomous",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=True)
    assert isinstance(verdict, PolicyVerdict)
    assert verdict.allowed is False
    assert verdict.requires_approval is False
    assert verdict.matched_rule == "R1: kill_switch"
    assert verdict.escalation_reason == "kill_switch"
    assert "Kill switch" in verdict.explanation


def test_rule_1_kill_switch_beats_everything():
    """Kill switch takes priority over mode, value, sufficiency, and all other rules."""
    ctx = DecisionContext(
        action_type="adjust_reorder_point",
        product_id=1,
        value_inr=1000000.0,
        sufficiency="none",
        is_cheapest_supplier=False,
        autonomy_mode="autonomous",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=True, blast_radius_exceeded=True)
    assert verdict.allowed is False
    assert verdict.requires_approval is False
    assert verdict.matched_rule == "R1: kill_switch"
    assert verdict.escalation_reason == "kill_switch"


# --- Rule 2: Autonomy mode 'off' ---------------------------------------------

def test_rule_2_mode_off_forbidden():
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=500.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="off",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=False)
    assert verdict.allowed is False
    assert verdict.requires_approval is False
    assert verdict.matched_rule == "R2: policy_off"
    assert verdict.escalation_reason == "policy_off"
    assert "OFF" in verdict.explanation


# --- Rule 3: Autonomy mode 'shadow' ------------------------------------------

def test_rule_3_mode_shadow_forbidden():
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=500.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="shadow",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=False)
    assert verdict.allowed is False
    assert verdict.requires_approval is False
    assert verdict.matched_rule == "R3: mode_shadow"
    assert verdict.escalation_reason == "policy_off"
    assert "SHADOW" in verdict.explanation


# --- Rule 4: Data sufficiency insufficient / none / thin ---------------------

@pytest.mark.parametrize("sufficiency", ["insufficient", "none", "thin"])
def test_rule_4_low_sufficiency_requires_approval_at_any_value(sufficiency):
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=50.0,  # Tiny order value
        sufficiency=sufficiency,
        is_cheapest_supplier=True,
        autonomy_mode="autonomous",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=False)
    assert verdict.allowed is True
    assert verdict.requires_approval is True
    assert verdict.matched_rule == "R4: insufficient_evidence"
    assert verdict.escalation_reason == "insufficient_evidence"
    assert verdict.citation is not None
    assert "§4, line 45" in verdict.citation


# --- Rule 5: Blast-radius cap exceeded ---------------------------------------

def test_rule_5_blast_radius_exceeded_requires_approval():
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=1000.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="autonomous",
    )
    verdict = evaluate_rules(
        ctx,
        kill_switch_engaged=False,
        blast_radius_exceeded=True,
        blast_radius_count=15,
        blast_radius_detail="Too many orders",
    )
    assert verdict.allowed is True
    assert verdict.requires_approval is True
    assert verdict.matched_rule == "R5: blast_radius"
    assert verdict.escalation_reason == "blast_radius"
    assert verdict.blast_radius == 15
    assert verdict.explanation == "Too many orders"


# --- Rule 6: Non-cheapest supplier selected -----------------------------------

def test_rule_6_non_cheapest_supplier_requires_approval_at_any_value():
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=200.0,
        sufficiency="sufficient",
        is_cheapest_supplier=False,
        autonomy_mode="autonomous",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=False)
    assert verdict.allowed is True
    assert verdict.requires_approval is True
    assert verdict.matched_rule == "R6: non_cheapest_supplier"
    assert verdict.escalation_reason == "non_cheapest_supplier"
    assert verdict.citation is not None
    assert "§6, line 74" in verdict.citation


# --- Rule 7: Reorder-point / configuration change -----------------------------

@pytest.mark.parametrize("action", ["adjust_reorder_point", "adjust_reorder_quantity", "config_change"])
@pytest.mark.parametrize("value", [0.0, 10.0, 1000.0, 100000.0])
def test_rule_7_config_change_requires_approval_at_any_value(action, value):
    ctx = DecisionContext(
        action_type=action,
        product_id=1,
        value_inr=value,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="autonomous",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=False)
    assert verdict.allowed is True
    assert verdict.requires_approval is True
    assert verdict.matched_rule == "R7: config_change"
    assert verdict.escalation_reason == "config_change"
    assert verdict.citation is not None
    assert "§3, line 33" in verdict.citation


# --- Rule 8: Value threshold precision (₹50,000) ------------------------------

def test_rule_8_value_50001_escalates():
    """₹50,001.00 is strictly above ₹50,000 -> requires approval."""
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=50001.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="autonomous",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=False)
    assert verdict.allowed is True
    assert verdict.requires_approval is True
    assert verdict.matched_rule == "R8: value_threshold"
    assert verdict.escalation_reason == "value_threshold"
    assert verdict.citation is not None
    assert "§10, line 113" in verdict.citation


def test_rule_8_value_50000_does_not_escalate():
    """₹50,000.00 is NOT above ₹50,000 -> within autonomous authority."""
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=50000.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="autonomous",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=False)
    assert verdict.allowed is True
    assert verdict.requires_approval is False
    assert verdict.matched_rule == "R10: within_authority"
    assert verdict.escalation_reason is None


def test_rule_8_value_49999_does_not_escalate():
    """₹49,999.00 is below ₹50,000 -> within autonomous authority."""
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=49999.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="autonomous",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=False)
    assert verdict.allowed is True
    assert verdict.requires_approval is False
    assert verdict.matched_rule == "R10: within_authority"
    assert verdict.escalation_reason is None


def test_rule_8_custom_policy_limit():
    """Custom policy limit overrides default limit."""
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=25000.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="autonomous",
    )
    # With limit of ₹20,000, ₹25,000 escalates
    verdict = evaluate_rules(ctx, policy_limit=20000.0, kill_switch_engaged=False)
    assert verdict.requires_approval is True
    assert verdict.matched_rule == "R8: value_threshold"

    # With limit of ₹30,000, ₹25,000 does not escalate
    verdict = evaluate_rules(ctx, policy_limit=30000.0, kill_switch_engaged=False)
    assert verdict.requires_approval is False
    assert verdict.matched_rule == "R10: within_authority"


# --- Rule 9: Autonomy mode 'assisted' ----------------------------------------

def test_rule_9_mode_assisted_requires_approval():
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=100.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="assisted",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=False)
    assert verdict.allowed is True
    assert verdict.requires_approval is True
    assert verdict.matched_rule == "R9: mode_assisted"
    assert verdict.escalation_reason == "policy_off"


# --- Rule 10: Within autonomous authority ------------------------------------

def test_rule_10_autonomous_within_authority():
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=15000.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="autonomous",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=False)
    assert verdict.allowed is True
    assert verdict.requires_approval is False
    assert verdict.matched_rule == "R10: within_authority"
    assert verdict.escalation_reason is None
    assert verdict.citation is None


# --- Rule Precedence / Order Verification -------------------------------------

def test_precedence_sufficiency_over_value():
    """Rule 4 (sufficiency) triggers before Rule 8 (value threshold)."""
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=100000.0,  # Above threshold
        sufficiency="insufficient",  # Low sufficiency
        is_cheapest_supplier=True,
        autonomy_mode="autonomous",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=False)
    assert verdict.matched_rule == "R4: insufficient_evidence"
    assert verdict.escalation_reason == "insufficient_evidence"


def test_precedence_non_cheapest_over_value():
    """Rule 6 (non-cheapest) triggers before Rule 8 (value threshold)."""
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=80000.0,  # Above threshold
        sufficiency="sufficient",
        is_cheapest_supplier=False,  # Non cheapest
        autonomy_mode="autonomous",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=False)
    assert verdict.matched_rule == "R6: non_cheapest_supplier"
    assert verdict.escalation_reason == "non_cheapest_supplier"


def test_precedence_config_change_over_value():
    """Rule 7 (config change) triggers before Rule 8 (value threshold)."""
    ctx = DecisionContext(
        action_type="adjust_reorder_point",
        product_id=1,
        value_inr=80000.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="autonomous",
    )
    verdict = evaluate_rules(ctx, kill_switch_engaged=False)
    assert verdict.matched_rule == "R7: config_change"
    assert verdict.escalation_reason == "config_change"
