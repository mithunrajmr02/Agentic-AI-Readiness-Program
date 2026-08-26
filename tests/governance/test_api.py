"""REST API endpoint tests for /api/decisions and /api/approvals (WS-4)."""
import pytest

from src.backend.models_analytics import AgentRun
from src.core import clock
from src.governance.approvals import request_approval
from src.governance.decisions import create_decision


@pytest.fixture
def seeded_decision(db):
    return create_decision(
        db,
        signal_id="SIG-000099",
        action_type="raise_po",
        inputs={"product_id": 1, "quantity": 100},
        computation={"reorder_quantity": 100, "daily_demand": 5.0, "reorder_point": 50},
        provenance={"reorder_quantity": "computed"},
        verdict={"requires_approval": True, "escalation_reason": "value_threshold", "citation": "manual §10 line 113"},
        status="pending_approval",
    )


@pytest.fixture
def seeded_approval(db, seeded_decision):
    return request_approval(db, seeded_decision, requested_from_role="manager", sla_hours=24)


# --- /api/decisions Tests ----------------------------------------------------

def test_get_decisions_list(client, seeded_decision):
    response = client.get("/api/decisions")
    assert response.status_code == 200
    body = response.json()

    assert "data" in body
    assert "meta" in body
    assert body["meta"]["data_disclosure"] == "synthetic"
    assert body["meta"]["provenance"]["decisions"] == "retrieved"

    decisions = body["data"]
    assert len(decisions) >= 1
    assert decisions[0]["decision_id"] == seeded_decision.decision_id
    assert decisions[0]["analysis_status"] == "reorder_required"


def test_get_decision_by_id(client, seeded_decision):
    response = client.get(f"/api/decisions/{seeded_decision.decision_id}")
    assert response.status_code == 200
    body = response.json()

    assert body["data"]["decision_id"] == seeded_decision.decision_id
    assert body["data"]["inputs"]["product_id"] == 1
    assert body["data"]["policy_citation"] == "manual §10 line 113"


def test_get_decision_not_found(client):
    response = client.get("/api/decisions/DEC-999999")
    assert response.status_code == 404


def test_get_decision_run(client, db):
    # Decision with run
    run = AgentRun(
        run_id="RUN-000099",
        trigger="scheduled",
        signal_id="SIG-000099",
        status="completed",
        started_at=clock.now(),
        completed_at=clock.now(),
        node_trace='{"demand_forecaster": "ok"}',
        llm_calls=2,
        llm_tokens=150,
        llm_errors=0,
        llm_numeric_violation=False,
        messages_count=4,
    )
    db.add(run)
    db.commit()

    dec = create_decision(
        db,
        signal_id="SIG-000099",
        action_type="raise_po",
        inputs={},
        computation={},
        provenance={},
        verdict={"requires_approval": False},
        run_id=run.run_id,
    )

    response = client.get(f"/api/decisions/{dec.decision_id}/run")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["run_id"] == "RUN-000099"
    assert body["data"]["node_trace"] == {"demand_forecaster": "ok"}


# --- /api/approvals Tests ----------------------------------------------------

def test_get_approvals_list(client, manager_token, seeded_approval):
    response = client.get(
        "/api/approvals",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    body = response.json()

    assert "data" in body
    assert any(a["approval_id"] == seeded_approval.approval_id for a in body["data"])


def test_get_approval_by_id(client, manager_token, seeded_approval):
    response = client.get(
        f"/api/approvals/{seeded_approval.approval_id}",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["data"]["approval_id"] == seeded_approval.approval_id
    assert body["data"]["decision"]["decision_id"] == seeded_approval.decision_id


def test_post_approve_by_manager(client, manager_token, seeded_approval):
    response = client.post(
        f"/api/approvals/{seeded_approval.approval_id}/approve",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"rationale": "Approved within operating budget"},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["data"]["status"] == "approved"
    assert "user:" in body["data"]["actor"]


def test_post_reject_requires_rationale(client, manager_token, seeded_approval):
    # Reject without rationale -> 422 or 400
    response = client.post(
        f"/api/approvals/{seeded_approval.approval_id}/reject",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={},
    )
    assert response.status_code in (400, 422)

    # Reject with empty string -> 400 or 422
    response = client.post(
        f"/api/approvals/{seeded_approval.approval_id}/reject",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"rationale": ""},
    )
    assert response.status_code in (400, 422)

    # Reject with valid rationale -> 200
    response = client.post(
        f"/api/approvals/{seeded_approval.approval_id}/reject",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"rationale": "Price quote exceeds expected budget"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "rejected"


def test_post_counter_proposal(client, manager_token, seeded_approval):
    response = client.post(
        f"/api/approvals/{seeded_approval.approval_id}/counter",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"quantity": 50, "rationale": "Order half batch"},
    )
    assert response.status_code == 200
    body = response.json()

    assert "recomputed" in body["data"]
    assert body["data"]["recomputed"]["counter_quantity"] == 50
    assert body["data"]["decision"]["status"] == "countered"
    assert body["data"]["accepted"] is True


# --- RBAC Enforcement Tests (M-34) -------------------------------------------

def test_rbac_unauthenticated_request_rejected(client, seeded_approval):
    response = client.post(f"/api/approvals/{seeded_approval.approval_id}/approve", json={})
    assert response.status_code == 401


def test_rbac_staff_role_denied_with_403_naming_manager_role(client, staff_token, seeded_approval):
    """M-34: Non-manager (staff) receives 403 naming the required manager role."""
    response = client.post(
        f"/api/approvals/{seeded_approval.approval_id}/approve",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={},
    )
    assert response.status_code == 403
    assert "Manager role required" in response.json()["detail"]


def test_rbac_agent_cannot_approve_own_decision(client, agent_token, seeded_approval):
    """AD-12: The agent cannot approve its own decisions."""
    response = client.post(
        f"/api/approvals/{seeded_approval.approval_id}/approve",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={},
    )
    assert response.status_code == 403
    assert "The agent cannot approve its own decision" in response.json()["detail"]
