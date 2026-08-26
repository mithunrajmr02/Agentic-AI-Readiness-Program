"""Approvals REST API router — WS-4.

15-SHARED-CONTRACTS.md §12 / 12-DATA-AND-API-CHANGES.md §5.3 / §8.
Provides manager-facing approval workflows (approve, reject, counter-propose)
with enforced RBAC (M-34: 403 naming required role), equal-weight actions,
and counter-proposal recomputation.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.contracts import success_envelope
from src.backend.database import get_db
from src.backend.models import User
from src.backend.routers.auth import MANAGER_ROLE, get_current_user
from src.core.errors import PreconditionFailed, StewardError
from src.governance.approvals import approve, get_approval, reject
from src.governance.counter import counter
from src.governance.decisions import get_decision
from src.governance.ledger import format_approval_record, format_decision_record, list_approvals

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


# --- Request Schemas ---------------------------------------------------------

class ApproveRequest(BaseModel):
    rationale: Optional[str] = Field(None, description="Optional approval rationale")


class RejectRequest(BaseModel):
    rationale: str = Field(..., min_length=1, description="Required rejection rationale (audit data)")


class CounterRequest(BaseModel):
    quantity: Optional[int] = Field(None, description="Proposed order quantity")
    modified_quantity: Optional[int] = Field(None, description="Alternative key for quantity")
    modified_supplier_id: Optional[int] = Field(None, description="Proposed supplier ID")
    rationale: Optional[str] = Field(None, description="Reason for counter-proposal")
    note: Optional[str] = Field(None, description="Additional notes")


# --- RBAC Dependency ---------------------------------------------------------

def require_manager_user(current_user: User = Depends(get_current_user)) -> User:
    """Enforce manager-role authorization on approval mutations (M-34, doc 12 §8).

    The agent is forbidden from approving its own decisions. Staff users receive
    an explicit 403 naming the manager requirement.
    """
    if current_user.role == "agent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The agent cannot approve its own decision. Manager role required.",
        )
    if current_user.role != MANAGER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Manager role required. Current role '{current_user.role}' lacks approval authority.",
        )
    return current_user


# --- Endpoints ---------------------------------------------------------------

@router.get("", response_model=None)
def get_approvals_list(
    pending_only: bool = Query(False, description="Filter to pending approvals only"),
    outcome: Optional[str] = Query(None, description="Filter by outcome (approved, rejected, countered, expired)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List approval requests with decision summaries."""
    approvals = list_approvals(
        db,
        outcome=outcome,
        pending_only=pending_only,
        limit=limit,
        offset=offset,
    )

    data = []
    for app in approvals:
        dec = get_decision(db, app.decision_id)
        data.append(format_approval_record(app, dec))

    return success_envelope(
        data=data,
        provenance={"approvals": "retrieved"},
        data_disclosure="synthetic",
    )


@router.get("/{approval_id}", response_model=None)
def get_approval_by_id(
    approval_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full detail for an approval request and its linked decision."""
    app = get_approval(db, approval_id)
    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval '{approval_id}' not found",
        )

    dec = get_decision(db, app.decision_id)
    return success_envelope(
        data=format_approval_record(app, dec),
        provenance={"approval": "retrieved"},
        data_disclosure="synthetic",
    )


@router.post("/{approval_id}/approve", response_model=None)
def post_approve(
    approval_id: str,
    body: Optional[ApproveRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
):
    """Approve a pending decision request (Door 1)."""
    rationale = body.rationale if body else None
    try:
        decision = approve(db, approval_id, user_id=current_user.id, rationale=rationale)
    except PreconditionFailed as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return success_envelope(
        data=format_decision_record(decision),
        provenance={"decision": "computed"},
        data_disclosure="synthetic",
    )


@router.post("/{approval_id}/reject", response_model=None)
def post_reject(
    approval_id: str,
    body: RejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
):
    """Reject a pending decision request with a mandatory rationale (Door 2)."""
    if not body.rationale or not body.rationale.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection rationale is required",
        )

    try:
        decision = reject(db, approval_id, user_id=current_user.id, rationale=body.rationale)
    except PreconditionFailed as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return success_envelope(
        data=format_decision_record(decision),
        provenance={"decision": "computed"},
        data_disclosure="synthetic",
    )


@router.post("/{approval_id}/counter", response_model=None)
def post_counter(
    approval_id: str,
    body: CounterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
):
    """Submit a counter-proposal with recomputation and system objection analysis (Door 3)."""
    payload = body.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Counter-proposal payload cannot be empty",
        )

    try:
        res = counter(db, approval_id, user_id=current_user.id, payload=payload)
    except PreconditionFailed as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return success_envelope(
        data={
            "decision": format_decision_record(res.decision),
            "recomputed": res.recomputed,
            "system_objection": res.system_objection,
            "accepted": res.accepted,
        },
        provenance={"counter": "computed"},
        data_disclosure="synthetic",
    )
