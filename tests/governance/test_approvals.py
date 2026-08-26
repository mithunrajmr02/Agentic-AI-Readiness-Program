"""Tests for approval request creation, SLA expiration, approve, and reject (WS-4)."""
import pytest

from src.backend.models_governance import Approval, Decision
from src.core import clock, events
from src.core.errors import PreconditionFailed
from src.governance.approvals import approve, get_approval, reject, request_approval
from src.governance.decisions import create_decision


@pytest.fixture
def pending_decision(db):
    return create_decision(
        db,
        signal_id="SIG-000010",
        action_type="raise_po",
        inputs={"product_id": 1, "quantity": 100},
        computation={"order_value": 60000.0},
        provenance={"order_value": "computed"},
        verdict={"requires_approval": True, "escalation_reason": "value_threshold", "citation": "manual §10"},
        status="pending_approval",
    )


def test_request_approval_lifecycle(db, pending_decision):
    pending_events = []
    events.subscribe("decision.pending_approval", lambda p: pending_events.append(p))

    approval = request_approval(db, pending_decision, requested_from_role="manager", sla_hours=24)

    assert approval.approval_id.startswith("APR-")
    assert approval.decision_id == pending_decision.decision_id
    assert approval.outcome is None
    assert approval.requested_from_role == "manager"
    assert approval.sla_breached is False
    assert approval.expires_at > approval.requested_at

    assert len(pending_events) == 1
    assert pending_events[0]["approval_id"] == approval.approval_id
    assert pending_events[0]["decision_id"] == pending_decision.decision_id


def test_approve_decision(db, pending_decision, users):
    approval = request_approval(db, pending_decision)
    manager = users["manager"]

    decision = approve(db, approval.approval_id, user_id=manager.id, rationale="Budget approved")

    assert decision.status == "approved"
    assert decision.actor == f"user:{manager.id}"
    assert decision.decided_at is not None

    db.refresh(approval)
    assert approval.outcome == "approved"
    assert approval.decided_by_user_id == manager.id
    assert approval.rationale == "Budget approved"


def test_approve_does_not_require_rationale(db, pending_decision, users):
    approval = request_approval(db, pending_decision)
    manager = users["manager"]

    # Rationale omitted is valid for approve
    decision = approve(db, approval.approval_id, user_id=manager.id, rationale=None)
    assert decision.status == "approved"


def test_reject_requires_rationale(db, pending_decision, users):
    approval = request_approval(db, pending_decision)
    manager = users["manager"]

    # Reject without rationale must fail
    with pytest.raises(ValueError, match="rationale is required"):
        reject(db, approval.approval_id, user_id=manager.id, rationale="")

    with pytest.raises(ValueError, match="rationale is required"):
        reject(db, approval.approval_id, user_id=manager.id, rationale="   ")


def test_reject_decision(db, pending_decision, users):
    approval = request_approval(db, pending_decision)
    manager = users["manager"]

    decision = reject(db, approval.approval_id, user_id=manager.id, rationale="Supplier price too high")

    assert decision.status == "rejected"
    assert decision.actor == f"user:{manager.id}"

    db.refresh(approval)
    assert approval.outcome == "rejected"
    assert approval.rationale == "Supplier price too high"


def test_approval_sla_expiration(db, pending_decision, users):
    approval = request_approval(db, pending_decision, sla_hours=24)
    manager = users["manager"]

    # Advance clock by 25 hours (past SLA)
    # Enable demo mode for simulation clock advancement
    import os
    os.environ["DEMO_MODE"] = "true"
    clock.set_offset(2)  # 2 days later

    with pytest.raises(PreconditionFailed, match="expired"):
        approve(db, approval.approval_id, user_id=manager.id)

    db.refresh(approval)
    assert approval.outcome == "expired"
    assert approval.sla_breached is True

    db.refresh(pending_decision)
    assert pending_decision.status == "expired"


def test_cannot_resolve_already_decided_approval(db, pending_decision, users):
    approval = request_approval(db, pending_decision)
    manager = users["manager"]

    approve(db, approval.approval_id, user_id=manager.id)

    # Attempt second resolution
    with pytest.raises(PreconditionFailed, match="already resolved"):
        approve(db, approval.approval_id, user_id=manager.id)
