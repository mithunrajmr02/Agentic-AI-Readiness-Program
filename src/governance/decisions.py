"""Decision ledger management for Steward governance (WS-4).

15-SHARED-CONTRACTS.md §8 / §2.3 / §3.2.
Every decision in the system is created through this module with explicit
clock-derived timestamps and immutable JSON audit trails.
"""
from __future__ import annotations

import json
from typing import Any, Optional
from sqlalchemy.orm import Session

from src.backend.models_governance import Decision
from src.core import clock, events, ids, vocab


def _extract_verdict_field(verdict: Any, field_name: str, default: Any = None) -> Any:
    """Extract a field from a PolicyVerdict dataclass, pydantic model, or dict."""
    if verdict is None:
        return default
    if isinstance(verdict, dict):
        return verdict.get(field_name, default)
    return getattr(verdict, field_name, default)


def create_decision(
    db: Session,
    *,
    signal_id: Optional[str] = None,
    action_type: str,
    inputs: dict,
    computation: dict,
    provenance: dict,
    verdict: Any,
    run_id: Optional[str] = None,
    status: Optional[str] = None,
    actor: str = "agent:replenishment",
    autonomy_mode: str = "autonomous",
    execution_ref: Optional[str] = None,
    reversal_of: Optional[str] = None,
    system_objection: Optional[str] = None,
) -> Decision:
    """Create a new Decision in the append-only ledger.

    15-SHARED-CONTRACTS.md §8.
    """
    if action_type not in vocab.ACTION_TYPES:
        raise ValueError(
            f"Invalid action_type '{action_type}'. Permitted: {vocab.ACTION_TYPES}"
        )
    if autonomy_mode not in vocab.AUTONOMY_MODES:
        raise ValueError(
            f"Invalid autonomy_mode '{autonomy_mode}'. Permitted: {vocab.AUTONOMY_MODES}"
        )

    requires_approval = _extract_verdict_field(verdict, "requires_approval", False)
    allowed = _extract_verdict_field(verdict, "allowed", True)
    escalation_reason = _extract_verdict_field(verdict, "escalation_reason", None)
    citation = _extract_verdict_field(verdict, "citation", None)

    # Determine initial status if not explicitly overridden
    if status is None:
        if requires_approval:
            status = "pending_approval"
        elif not allowed:
            status = "rejected"
        else:
            status = "auto_approved"

    if status not in vocab.DECISION_STATUS:
        raise ValueError(
            f"Invalid status '{status}'. Permitted: {vocab.DECISION_STATUS}"
        )

    now_ts = clock.now()
    decided_at_ts = now_ts if status in ("auto_approved", "rejected", "failed") else None

    decision = Decision(
        decision_id=ids.next_id("DEC"),
        signal_id=signal_id,
        run_id=run_id,
        action_type=action_type,
        status=status,
        actor=actor,
        proposed_at=now_ts,
        decided_at=decided_at_ts,
        executed_at=None,
        inputs=json.dumps(inputs) if isinstance(inputs, dict) else inputs,
        computation=json.dumps(computation) if isinstance(computation, dict) else computation,
        policy_citation=citation,
        escalation_reason=escalation_reason,
        system_objection=system_objection,
        autonomy_mode=autonomy_mode,
        execution_ref=execution_ref,
        reversal_of=reversal_of,
        provenance=json.dumps(provenance) if isinstance(provenance, dict) else provenance,
    )

    db.add(decision)
    db.commit()
    db.refresh(decision)

    events.emit(
        "decision.created",
        {
            "decision_id": decision.decision_id,
            "signal_id": decision.signal_id,
            "action_type": decision.action_type,
        },
    )

    return decision


def record_refusal(
    db: Session,
    *,
    signal_id: Optional[str] = None,
    reason: str,
    needed: str,
    have: str,
    run_id: Optional[str] = None,
    actor: str = "agent:replenishment",
    autonomy_mode: str = "autonomous",
) -> Decision:
    """Record an honest refusal to act due to data insufficiency (BW-5, D4).

    15-SHARED-CONTRACTS.md §8 / §2.3.
    """
    if autonomy_mode not in vocab.AUTONOMY_MODES:
        raise ValueError(
            f"Invalid autonomy_mode '{autonomy_mode}'. Permitted: {vocab.AUTONOMY_MODES}"
        )

    now_ts = clock.now()
    refusal_inputs = {"needed": needed, "have": have, "reason": reason}
    refusal_comp = {"refusal": refusal_inputs}
    refusal_prov = {"refusal": "computed"}

    decision = Decision(
        decision_id=ids.next_id("DEC"),
        signal_id=signal_id,
        run_id=run_id,
        action_type="no_action",
        status="insufficient_data",
        actor=actor,
        proposed_at=now_ts,
        decided_at=now_ts,
        executed_at=None,
        inputs=json.dumps(refusal_inputs),
        computation=json.dumps(refusal_comp),
        policy_citation=None,
        escalation_reason="insufficient_evidence",
        system_objection=None,
        autonomy_mode=autonomy_mode,
        execution_ref=None,
        reversal_of=None,
        provenance=json.dumps(refusal_prov),
    )

    db.add(decision)
    db.commit()
    db.refresh(decision)

    events.emit(
        "decision.refused",
        {
            "decision_id": decision.decision_id,
            "reason": reason,
        },
    )

    return decision


def get_decision(db: Session, decision_id: str) -> Optional[Decision]:
    """Retrieve a decision by its business identifier (e.g. DEC-000123)."""
    return db.query(Decision).filter(Decision.decision_id == decision_id).first()
