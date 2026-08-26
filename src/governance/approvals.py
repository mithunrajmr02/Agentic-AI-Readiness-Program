"""Approval lifecycle management for Steward governance (WS-4).

15-SHARED-CONTRACTS.md §8 / §2.3 / §3.3.
Manages the human-in-the-loop approval lifecycle, SLA enforcement,
and audit trails for decisions requiring escalation.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session

from src.backend.models_governance import Approval, Decision
from src.core import clock, events, ids
from src.core.errors import PreconditionFailed
from src.governance.decisions import get_decision


def request_approval(
    db: Session,
    decision: Decision,
    *,
    requested_from_role: str = "manager",
    sla_hours: int = 24,
) -> Approval:
    """Create a pending approval request for a decision.

    15-SHARED-CONTRACTS.md §8.
    """
    now_ts = clock.now()
    approval_id = ids.next_id("APR")
    expires_at = now_ts + timedelta(hours=sla_hours)

    approval = Approval(
        approval_id=approval_id,
        decision_id=decision.decision_id,
        requested_at=now_ts,
        requested_from_role=requested_from_role,
        decided_by_user_id=None,
        decided_at=None,
        outcome=None,
        counter_payload=None,
        rationale=None,
        expires_at=expires_at,
        sla_breached=False,
    )

    decision.status = "pending_approval"
    db.add(approval)
    db.commit()
    db.refresh(approval)
    db.refresh(decision)

    events.emit(
        "decision.pending_approval",
        {
            "decision_id": decision.decision_id,
            "approval_id": approval.approval_id,
            "escalation_reason": decision.escalation_reason,
        },
    )

    return approval


def approve(
    db: Session,
    approval_id: str,
    user_id: int,
    rationale: Optional[str] = None,
) -> Decision:
    """Approve a pending approval request.

    15-SHARED-CONTRACTS.md §8.
    Note: approve does not require a rationale.
    """
    approval = db.query(Approval).filter(Approval.approval_id == approval_id).first()
    if approval is None:
        raise ValueError(f"Approval '{approval_id}' not found")

    if approval.outcome is not None:
        raise PreconditionFailed(
            "approval_already_resolved",
            f"Approval '{approval_id}' already resolved with outcome '{approval.outcome}'",
        )

    now_ts = clock.now()
    if now_ts > approval.expires_at:
        approval.sla_breached = True
        approval.outcome = "expired"
        approval.decided_at = now_ts
        decision = get_decision(db, approval.decision_id)
        if decision:
            decision.status = "expired"
            decision.decided_at = now_ts
        db.commit()
        raise PreconditionFailed(
            "approval_expired",
            f"Approval '{approval_id}' has expired (SLA breached)",
        )

    decision = get_decision(db, approval.decision_id)
    if decision is None:
        raise ValueError(f"Decision '{approval.decision_id}' not found for approval '{approval_id}'")

    approval.outcome = "approved"
    approval.decided_by_user_id = user_id
    approval.decided_at = now_ts
    approval.rationale = rationale

    decision.status = "approved"
    decision.decided_at = now_ts
    decision.actor = f"user:{user_id}"

    db.commit()
    db.refresh(approval)
    db.refresh(decision)

    return decision


def reject(
    db: Session,
    approval_id: str,
    user_id: int,
    rationale: str,
) -> Decision:
    """Reject a pending approval request.

    15-SHARED-CONTRACTS.md §8: reject requires a non-empty rationale.
    """
    if not rationale or not rationale.strip():
        raise ValueError("Rejection rationale is required")

    approval = db.query(Approval).filter(Approval.approval_id == approval_id).first()
    if approval is None:
        raise ValueError(f"Approval '{approval_id}' not found")

    if approval.outcome is not None:
        raise PreconditionFailed(
            "approval_already_resolved",
            f"Approval '{approval_id}' already resolved with outcome '{approval.outcome}'",
        )

    now_ts = clock.now()
    if now_ts > approval.expires_at:
        approval.sla_breached = True
        approval.outcome = "expired"
        approval.decided_at = now_ts
        decision = get_decision(db, approval.decision_id)
        if decision:
            decision.status = "expired"
            decision.decided_at = now_ts
        db.commit()
        raise PreconditionFailed(
            "approval_expired",
            f"Approval '{approval_id}' has expired (SLA breached)",
        )

    decision = get_decision(db, approval.decision_id)
    if decision is None:
        raise ValueError(f"Decision '{approval.decision_id}' not found for approval '{approval_id}'")

    approval.outcome = "rejected"
    approval.decided_by_user_id = user_id
    approval.decided_at = now_ts
    approval.rationale = rationale.strip()

    decision.status = "rejected"
    decision.decided_at = now_ts
    decision.actor = f"user:{user_id}"

    db.commit()
    db.refresh(approval)
    db.refresh(decision)

    return decision


def get_approval(db: Session, approval_id: str) -> Optional[Approval]:
    """Retrieve an approval by its identifier (e.g. APR-000012)."""
    return db.query(Approval).filter(Approval.approval_id == approval_id).first()


def get_approval_for_decision(db: Session, decision_id: str) -> Optional[Approval]:
    """Retrieve the approval row associated with a decision_id."""
    return db.query(Approval).filter(Approval.decision_id == decision_id).order_by(Approval.id.desc()).first()
