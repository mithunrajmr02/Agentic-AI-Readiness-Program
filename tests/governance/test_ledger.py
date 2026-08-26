"""Tests for decision and approval ledger filtering and querying (WS-4)."""
import pytest

from src.governance.approvals import request_approval
from src.governance.decisions import create_decision
from src.governance.ledger import (
    format_approval_record,
    format_decision_record,
    list_approvals,
    list_decisions,
)


def test_list_decisions_filtering(db):
    d1 = create_decision(
        db,
        signal_id="SIG-001",
        action_type="raise_po",
        inputs={"product_id": 1},
        computation={},
        provenance={},
        verdict={"allowed": True, "requires_approval": False},
        status="auto_approved",
        actor="agent:replenishment",
    )
    d2 = create_decision(
        db,
        signal_id="SIG-002",
        action_type="adjust_reorder_point",
        inputs={"product_id": 2},
        computation={},
        provenance={},
        verdict={"allowed": True, "requires_approval": True},
        status="pending_approval",
        actor="agent:replenishment",
    )

    # Filter by status
    pending = list_decisions(db, status="pending_approval")
    assert len(pending) == 1
    assert pending[0].decision_id == d2.decision_id

    # Filter by action_type
    rp_changes = list_decisions(db, action_type="adjust_reorder_point")
    assert len(rp_changes) == 1
    assert rp_changes[0].decision_id == d2.decision_id

    # Filter by signal_id
    sig1 = list_decisions(db, signal_id="SIG-001")
    assert len(sig1) == 1
    assert sig1[0].decision_id == d1.decision_id


def test_list_approvals_filtering(db):
    d = create_decision(
        db,
        action_type="raise_po",
        inputs={},
        computation={},
        provenance={},
        verdict={"requires_approval": True},
        status="pending_approval",
    )
    app = request_approval(db, d)

    pending_apps = list_approvals(db, pending_only=True)
    assert len(pending_apps) >= 1
    assert any(a.approval_id == app.approval_id for a in pending_apps)

    formatted = format_approval_record(app, d)
    assert formatted["approval_id"] == app.approval_id
    assert formatted["decision"]["decision_id"] == d.decision_id
