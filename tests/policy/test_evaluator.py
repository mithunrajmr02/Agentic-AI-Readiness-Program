"""Tests for Policy Evaluator and threshold resolution — WS-5.

15-SHARED-CONTRACTS.md §7 / 08-AGENTIC-WORKFLOWS.md §5.5 / 12-DATA-AND-API-CHANGES.md §5.4.
"""
import pytest

from src.backend.models_governance import AutonomyPolicy
from src.core import clock
from src.policy.evaluator import (
    DEFAULT_POLICY_LIMIT,
    DecisionContext,
    PolicyVerdict,
    evaluate,
    get_effective_policy,
    get_policy_threshold,
)
from src.policy.killswitch import engage_kill_switch


def test_evaluate_within_autonomous_authority(db):
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=35000.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="autonomous",
    )
    verdict = evaluate(db, ctx)
    assert isinstance(verdict, PolicyVerdict)
    assert verdict.allowed is True
    assert verdict.requires_approval is False
    assert verdict.matched_rule == "R10: within_authority"


def test_evaluate_escalates_on_value_threshold(db):
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=65000.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="autonomous",
    )
    verdict = evaluate(db, ctx)
    assert verdict.allowed is True
    assert verdict.requires_approval is True
    assert verdict.matched_rule == "R8: value_threshold"
    assert verdict.escalation_reason == "value_threshold"
    assert "§10, line 113" in verdict.citation


def test_evaluate_respects_kill_switch_in_db(db, users):
    engage_kill_switch(db, user_id=users["manager"].id, reason="Testing kill switch")

    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=1000.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="autonomous",
    )
    verdict = evaluate(db, ctx)
    assert verdict.allowed is False
    assert verdict.requires_approval is False
    assert verdict.matched_rule == "R1: kill_switch"
    assert verdict.escalation_reason == "kill_switch"


def test_get_policy_threshold_default(db):
    threshold_data = get_policy_threshold(db)
    assert threshold_data["threshold_inr"] == 50000.0
    assert threshold_data["default_threshold_inr"] == 50000.0
    assert threshold_data["is_overridden"] is False
    assert "Section 10" in threshold_data["section"]
    assert "₹50,000" in threshold_data["citation"]
    assert threshold_data["source"] == "retrieved"


def test_get_policy_threshold_with_override(db):
    policy = get_effective_policy(db, scope_type="global")
    policy.max_order_value = 75000.0
    db.commit()

    threshold_data = get_policy_threshold(db)
    assert threshold_data["threshold_inr"] == 75000.0
    assert threshold_data["default_threshold_inr"] == 50000.0
    assert threshold_data["is_overridden"] is True


def test_scoped_policy_resolution(db):
    # Create category-specific policy for 'electronics' in 'assisted' mode
    elec_policy = AutonomyPolicy(
        scope_type="category",
        scope_value="electronics",
        mode="assisted",
        max_order_value=20000.0,
        kill_switch_engaged=False,
        updated_at=clock.now(),
    )
    db.add(elec_policy)
    db.commit()

    resolved = get_effective_policy(db, scope_type="category", scope_value="electronics")
    assert resolved.mode == "assisted"
    assert resolved.max_order_value == 20000.0

    # Evaluating under category='electronics' uses assisted mode from DB
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=2,
        value_inr=5000.0,
        sufficiency="sufficient",
        is_cheapest_supplier=True,
        autonomy_mode="",  # empty implies fallback to DB policy mode
    )
    verdict = evaluate(db, ctx, scope_type="category", scope_value="electronics")
    assert verdict.requires_approval is True
    assert verdict.matched_rule == "R9: mode_assisted"
