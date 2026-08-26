"""Tests for decision creation, refusal recording, and status projection (WS-4)."""
from dataclasses import dataclass
from typing import Optional
import pytest

from src.backend.models_governance import Decision
from src.core import clock, events, vocab
from src.governance.decisions import create_decision, get_decision, record_refusal
from src.governance.ledger import format_decision_record


@dataclass(frozen=True)
class MockPolicyVerdict:
    allowed: bool
    requires_approval: bool
    matched_rule: str
    escalation_reason: Optional[str] = None
    citation: Optional[str] = None
    blast_radius: int = 1
    explanation: str = "Policy check result"


def test_create_decision_auto_approved(db):
    verdict = MockPolicyVerdict(
        allowed=True,
        requires_approval=False,
        matched_rule="R10: within_authority",
        citation="manual §10 line 113",
    )

    emitted_events = []
    events.subscribe("decision.created", lambda payload: emitted_events.append(payload))

    decision = create_decision(
        db,
        signal_id="SIG-000001",
        action_type="raise_po",
        inputs={"product_id": 1, "quantity": 100},
        computation={"daily_demand": 5.0, "reorder_point": 40},
        provenance={"daily_demand": "computed", "reorder_point": "computed"},
        verdict=verdict,
        run_id="RUN-000001",
    )

    assert decision.decision_id.startswith("DEC-")
    assert decision.status == "auto_approved"
    assert decision.action_type == "raise_po"
    assert decision.signal_id == "SIG-000001"
    assert decision.run_id == "RUN-000001"
    assert decision.policy_citation == "manual §10 line 113"
    assert decision.proposed_at is not None
    assert decision.decided_at is not None

    # Event emitted
    assert len(emitted_events) == 1
    assert emitted_events[0]["decision_id"] == decision.decision_id
    assert emitted_events[0]["action_type"] == "raise_po"


def test_create_decision_requires_approval(db):
    verdict = MockPolicyVerdict(
        allowed=True,
        requires_approval=True,
        matched_rule="R8: value_threshold",
        escalation_reason="value_threshold",
        citation="manual §10 line 113",
    )

    decision = create_decision(
        db,
        signal_id="SIG-000002",
        action_type="raise_po",
        inputs={"product_id": 2, "quantity": 200},
        computation={"order_value": 68400.0},
        provenance={"order_value": "computed"},
        verdict=verdict,
    )

    assert decision.status == "pending_approval"
    assert decision.escalation_reason == "value_threshold"
    assert decision.decided_at is None


def test_record_refusal(db):
    emitted_refusals = []
    events.subscribe("decision.refused", lambda p: emitted_refusals.append(p))

    decision = record_refusal(
        db,
        signal_id="SIG-000003",
        reason="Insufficient sale history for Colgate",
        needed="14 sale events across 21 days",
        have="0 sale events",
        run_id="RUN-000002",
    )

    assert decision.decision_id.startswith("DEC-")
    assert decision.status == "insufficient_data"
    assert decision.action_type == "no_action"
    assert decision.escalation_reason == "insufficient_evidence"
    assert decision.decided_at is not None

    assert len(emitted_refusals) == 1
    assert emitted_refusals[0]["decision_id"] == decision.decision_id
    assert "Insufficient sale history" in emitted_refusals[0]["reason"]


def test_all_twelve_decision_statuses_project_to_graded_analysis_status(db):
    """Verify projection from each 12-value internal status to the 4-value graded vocabulary."""
    for st in vocab.DECISION_STATUS:
        for action in ("raise_po", "no_action"):
            proj = vocab.project_analysis_status(st, action)
            assert proj in ("analyzing", "reorder_required", "healthy", "complete"), (
                f"Status {st} with action {action} produced invalid projection {proj}"
            )

    # Specific contract projections from doc 15 §2.5
    assert vocab.project_analysis_status("proposed", "raise_po") == "analyzing"
    assert vocab.project_analysis_status("policy_checked", "raise_po") == "analyzing"
    assert vocab.project_analysis_status("executing", "raise_po") == "analyzing"

    assert vocab.project_analysis_status("pending_approval", "raise_po") == "reorder_required"
    assert vocab.project_analysis_status("approved", "raise_po") == "reorder_required"
    assert vocab.project_analysis_status("auto_approved", "raise_po") == "reorder_required"
    assert vocab.project_analysis_status("executed", "raise_po") == "reorder_required"

    # executed with no_action is healthy
    assert vocab.project_analysis_status("executed", "no_action") == "healthy"

    # terminations project to complete
    assert vocab.project_analysis_status("rejected", "raise_po") == "complete"
    assert vocab.project_analysis_status("expired", "raise_po") == "complete"
    assert vocab.project_analysis_status("failed", "raise_po") == "complete"
    assert vocab.project_analysis_status("countered", "raise_po") == "complete"
    assert vocab.project_analysis_status("insufficient_data", "no_action") == "complete"


def test_format_decision_record_deserializes_json_and_attaches_projection(db):
    verdict = MockPolicyVerdict(
        allowed=True,
        requires_approval=False,
        matched_rule="R10",
        citation="citation text",
    )
    decision = create_decision(
        db,
        action_type="raise_po",
        inputs={"qty": 50},
        computation={"cost": 1000.0},
        provenance={"cost": "computed"},
        verdict=verdict,
    )

    formatted = format_decision_record(decision)
    assert formatted["decision_id"] == decision.decision_id
    assert formatted["inputs"] == {"qty": 50}
    assert formatted["computation"] == {"cost": 1000.0}
    assert formatted["provenance"] == {"cost": "computed"}
    assert formatted["analysis_status"] == "reorder_required"
