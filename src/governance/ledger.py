"""Decision ledger and audit query service (WS-4).

15-SHARED-CONTRACTS.md §2.5 / §3.2 / §3.3.
Provides read views, filters, and display projections (such as the 12-status
to 4-graded analysis_status mapping) over the append-only ledger.
"""
from __future__ import annotations

import json
from typing import Any, Optional
from sqlalchemy.orm import Session

from src.backend.models_governance import Approval, Decision
from src.core import clock, vocab


def format_decision_record(decision: Decision) -> dict[str, Any]:
    """Format a Decision model instance into a detailed presentation dictionary.

    Attaches the projected 4-value graded analysis_status per 15-SHARED-CONTRACTS.md §2.5.
    """
    inputs: Any = None
    if decision.inputs:
        try:
            inputs = json.loads(decision.inputs)
        except Exception:
            inputs = decision.inputs

    computation: Any = None
    if decision.computation:
        try:
            computation = json.loads(decision.computation)
        except Exception:
            computation = decision.computation

    provenance: Any = None
    if decision.provenance:
        try:
            provenance = json.loads(decision.provenance)
        except Exception:
            provenance = decision.provenance

    # 15-SHARED-CONTRACTS.md §2.5 projection
    projected_analysis = vocab.project_analysis_status(
        decision.status, decision.action_type
    )

    return {
        "id": decision.id,
        "decision_id": decision.decision_id,
        "signal_id": decision.signal_id,
        "run_id": decision.run_id,
        "action_type": decision.action_type,
        "status": decision.status,
        "analysis_status": projected_analysis,
        "actor": decision.actor,
        "proposed_at": decision.proposed_at.isoformat() if decision.proposed_at else None,
        "decided_at": decision.decided_at.isoformat() if decision.decided_at else None,
        "executed_at": decision.executed_at.isoformat() if decision.executed_at else None,
        "inputs": inputs,
        "computation": computation,
        "policy_citation": decision.policy_citation,
        "escalation_reason": decision.escalation_reason,
        "system_objection": decision.system_objection,
        "autonomy_mode": decision.autonomy_mode,
        "execution_ref": decision.execution_ref,
        "reversal_of": decision.reversal_of,
        "provenance": provenance,
    }


def list_decisions(
    db: Session,
    *,
    status: Optional[str] = None,
    action_type: Optional[str] = None,
    actor: Optional[str] = None,
    signal_id: Optional[str] = None,
    run_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Decision]:
    """List decisions with optional filtering."""
    query = db.query(Decision)

    if status:
        query = query.filter(Decision.status == status)
    if action_type:
        query = query.filter(Decision.action_type == action_type)
    if actor:
        query = query.filter(Decision.actor == actor)
    if signal_id:
        query = query.filter(Decision.signal_id == signal_id)
    if run_id:
        query = query.filter(Decision.run_id == run_id)

    return query.order_by(Decision.id.desc()).offset(offset).limit(limit).all()


def format_approval_record(
    approval: Approval,
    decision: Optional[Decision] = None,
) -> dict[str, Any]:
    """Format an Approval model instance into a presentation dictionary."""
    counter_payload: Any = None
    if approval.counter_payload:
        try:
            counter_payload = json.loads(approval.counter_payload)
        except Exception:
            counter_payload = approval.counter_payload

    now_ts = clock.now()
    is_expired = (
        approval.outcome == "expired"
        or (approval.outcome is None and now_ts > approval.expires_at)
    )

    result = {
        "id": approval.id,
        "approval_id": approval.approval_id,
        "decision_id": approval.decision_id,
        "requested_at": approval.requested_at.isoformat() if approval.requested_at else None,
        "requested_from_role": approval.requested_from_role,
        "decided_by_user_id": approval.decided_by_user_id,
        "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
        "outcome": approval.outcome,
        "counter_payload": counter_payload,
        "rationale": approval.rationale,
        "expires_at": approval.expires_at.isoformat() if approval.expires_at else None,
        "sla_breached": approval.sla_breached or is_expired,
        "is_expired": is_expired,
    }

    if decision is not None:
        result["decision"] = format_decision_record(decision)

    return result


def list_approvals(
    db: Session,
    *,
    outcome: Optional[str] = None,
    pending_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Approval]:
    """List approvals with optional filtering."""
    query = db.query(Approval)

    if pending_only:
        query = query.filter(Approval.outcome.is_(None))
    elif outcome:
        query = query.filter(Approval.outcome == outcome)

    return query.order_by(Approval.id.desc()).offset(offset).limit(limit).all()
