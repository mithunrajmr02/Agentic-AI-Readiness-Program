"""Tests for Kill Switch operations and audit persistence — WS-5.

15-SHARED-CONTRACTS.md §7 / 12-DATA-AND-API-CHANGES.md §5.4.
"""
import pytest

from src.core.errors import PreconditionFailed
from src.policy.killswitch import (
    engage_kill_switch,
    get_or_create_policy_record,
    is_kill_switch_engaged,
    release_kill_switch,
)


def test_initial_kill_switch_state_is_disengaged(db):
    engaged, reason = is_kill_switch_engaged(db)
    assert engaged is False
    assert reason is None


def test_engage_kill_switch_records_audit_trail(db, users):
    manager_id = users["manager"].id
    policy = engage_kill_switch(
        db,
        user_id=manager_id,
        reason="Manual audit initiated due to supplier discrepancy",
    )
    assert policy.kill_switch_engaged is True
    assert policy.kill_switch_reason == "Manual audit initiated due to supplier discrepancy"
    assert policy.kill_switch_by_user_id == manager_id
    assert policy.updated_at is not None
    assert policy.updated_by_user_id == manager_id

    # Verify query
    engaged, reason = is_kill_switch_engaged(db)
    assert engaged is True
    assert reason == "Manual audit initiated due to supplier discrepancy"


def test_engage_kill_switch_requires_reason(db, users):
    manager_id = users["manager"].id
    with pytest.raises(PreconditionFailed) as exc:
        engage_kill_switch(db, user_id=manager_id, reason="")
    assert "reason is required" in str(exc.value)

    with pytest.raises(PreconditionFailed):
        engage_kill_switch(db, user_id=manager_id, reason="   ")


def test_release_kill_switch(db, users):
    manager_id = users["manager"].id
    engage_kill_switch(db, user_id=manager_id, reason="Emergency hold")
    assert is_kill_switch_engaged(db)[0] is True

    released_policy = release_kill_switch(
        db,
        user_id=manager_id,
        reason="Emergency hold resolved",
    )
    assert released_policy.kill_switch_engaged is False
    assert released_policy.kill_switch_reason == "Emergency hold resolved"
    assert released_policy.updated_by_user_id == manager_id

    engaged, _ = is_kill_switch_engaged(db)
    assert engaged is False


def test_scoped_kill_switch_and_global_override(db, users):
    manager_id = users["manager"].id

    # Engage kill switch on grocery category only
    engage_kill_switch(
        db,
        user_id=manager_id,
        reason="Grocery supplier outage",
        scope_type="category",
        scope_value="grocery",
    )

    # Grocery scope is engaged
    grocery_engaged, reason = is_kill_switch_engaged(db, scope_type="category", scope_value="grocery")
    assert grocery_engaged is True
    assert reason == "Grocery supplier outage"

    # Electronics scope is NOT engaged
    elec_engaged, _ = is_kill_switch_engaged(db, scope_type="category", scope_value="electronics")
    assert elec_engaged is False

    # Global scope is NOT engaged
    global_engaged, _ = is_kill_switch_engaged(db, scope_type="global")
    assert global_engaged is False

    # Now engage global kill switch -> electronics is now also engaged via global override
    engage_kill_switch(db, user_id=manager_id, reason="Global security event")
    elec_now_engaged, global_reason = is_kill_switch_engaged(db, scope_type="category", scope_value="electronics")
    assert elec_now_engaged is True
    assert global_reason == "Global security event"
