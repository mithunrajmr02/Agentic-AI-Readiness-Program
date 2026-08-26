"""Policies REST API router — WS-5.

15-SHARED-CONTRACTS.md §12 / 12-DATA-AND-API-CHANGES.md §5.4.
Provides policy inspection, autonomy mode configuration, kill-switch operations,
and retrieved policy threshold quoting with manager RBAC.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.contracts import success_envelope
from src.backend.database import get_db
from src.backend.models import User
from src.backend.models_governance import AutonomyPolicy
from src.backend.routers.auth import MANAGER_ROLE, get_current_user, get_optional_user
from src.core import clock, vocab
from src.core.errors import PreconditionFailed
from src.policy.evaluator import get_effective_policy, get_policy_threshold
from src.policy.killswitch import engage_kill_switch, release_kill_switch

router = APIRouter(prefix="/api/policies", tags=["policies"])


# --- Request Schemas ---------------------------------------------------------

class UpdatePolicyRequest(BaseModel):
    scope_type: Optional[str] = Field(None, description="Scope type: global, category, product")
    scope_value: Optional[str] = Field(None, description="Scope value (e.g. category name)")
    mode: Optional[str] = Field(None, description="Autonomy mode: off, shadow, assisted, autonomous")
    max_order_value: Optional[float] = Field(None, description="Override threshold limit")
    max_orders_per_hour: Optional[int] = Field(None, description="Blast radius: max orders per hour")
    max_value_per_day: Optional[float] = Field(None, description="Blast radius: max spend per day")
    min_sale_events: Optional[int] = Field(None, description="Sufficiency: min sale events")
    min_history_days: Optional[int] = Field(None, description="Sufficiency: min history span days")
    safety_stock_days: Optional[int] = Field(None, description="Safety stock days")
    drift_tolerance_pct: Optional[float] = Field(None, description="Drift tolerance percentage")


class KillSwitchRequest(BaseModel):
    engaged: bool = Field(..., description="Whether to engage (True) or release (False) the kill switch")
    reason: Optional[str] = Field(None, description="Reason for engaging/releasing the kill switch")
    scope_type: str = Field("global", description="Scope type: global, category, product")
    scope_value: Optional[str] = Field(None, description="Scope value")


# --- RBAC Dependency ---------------------------------------------------------

def require_manager_user(current_user: User = Depends(get_current_user)) -> User:
    """Enforce manager-role authorization on policy mutations (M-34, doc 12 §8)."""
    if current_user.role != MANAGER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Manager role required. Current role '{current_user.role}' lacks policy mutation authority.",
        )
    return current_user


# --- Serialization Helper ----------------------------------------------------

def format_policy_record(policy: AutonomyPolicy) -> dict[str, Any]:
    """Format an AutonomyPolicy database record into a clean dictionary."""
    return {
        "id": policy.id,
        "scope_type": policy.scope_type,
        "scope_value": policy.scope_value,
        "mode": policy.mode,
        "max_order_value": policy.max_order_value,
        "max_orders_per_hour": policy.max_orders_per_hour,
        "max_value_per_day": policy.max_value_per_day,
        "min_sale_events": policy.min_sale_events,
        "min_history_days": policy.min_history_days,
        "safety_stock_days": policy.safety_stock_days,
        "drift_tolerance_pct": policy.drift_tolerance_pct,
        "kill_switch_engaged": policy.kill_switch_engaged,
        "kill_switch_reason": policy.kill_switch_reason,
        "kill_switch_by_user_id": policy.kill_switch_by_user_id,
        "consecutive_failures": policy.consecutive_failures,
        "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
        "updated_by_user_id": policy.updated_by_user_id,
    }


# --- Endpoints ---------------------------------------------------------------

@router.get("/autonomy", response_model=None)
def get_autonomy_policy(
    scope_type: str = Query("global", description="Scope type: global, category, product"),
    scope_value: Optional[str] = Query(None, description="Scope value (e.g. grocery)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Get the current autonomy policy, mode, caps, and kill-switch state (Role: any)."""
    policy = get_effective_policy(db, scope_type=scope_type, scope_value=scope_value)
    return success_envelope(
        data=format_policy_record(policy),
        provenance={"policy": "retrieved"},
        data_disclosure="real",
    )


@router.patch("/autonomy", response_model=None)
def update_autonomy_policy(
    body: UpdatePolicyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
):
    """Update autonomy mode, blast-radius caps, or sufficiency thresholds (Manager only)."""
    scope_type = body.scope_type or "global"
    scope_value = body.scope_value

    if body.mode is not None and body.mode not in vocab.AUTONOMY_MODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid autonomy mode '{body.mode}'. Must be one of {vocab.AUTONOMY_MODES}",
        )

    policy = get_effective_policy(db, scope_type=scope_type, scope_value=scope_value)

    if body.mode is not None:
        policy.mode = body.mode
    if body.max_order_value is not None:
        policy.max_order_value = body.max_order_value
    if body.max_orders_per_hour is not None:
        policy.max_orders_per_hour = body.max_orders_per_hour
    if body.max_value_per_day is not None:
        policy.max_value_per_day = body.max_value_per_day
    if body.min_sale_events is not None:
        policy.min_sale_events = body.min_sale_events
    if body.min_history_days is not None:
        policy.min_history_days = body.min_history_days
    if body.safety_stock_days is not None:
        policy.safety_stock_days = body.safety_stock_days
    if body.drift_tolerance_pct is not None:
        policy.drift_tolerance_pct = body.drift_tolerance_pct

    policy.updated_at = clock.now()
    policy.updated_by_user_id = current_user.id

    db.commit()
    db.refresh(policy)

    return success_envelope(
        data=format_policy_record(policy),
        provenance={"policy": "computed"},
        data_disclosure="real",
    )


@router.post("/kill-switch", response_model=None)
def toggle_kill_switch(
    body: KillSwitchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
):
    """Engage or release the kill switch (Manager only). Reason required when engaging."""
    try:
        if body.engaged:
            if not body.reason or not body.reason.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A valid reason is required to engage the kill switch",
                )
            policy = engage_kill_switch(
                db,
                user_id=current_user.id,
                reason=body.reason,
                scope_type=body.scope_type,
                scope_value=body.scope_value,
            )
        else:
            policy = release_kill_switch(
                db,
                user_id=current_user.id,
                reason=body.reason,
                scope_type=body.scope_type,
                scope_value=body.scope_value,
            )
    except PreconditionFailed as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return success_envelope(
        data=format_policy_record(policy),
        provenance={"kill_switch": "computed"},
        data_disclosure="real",
    )


@router.get("/threshold", response_model=None)
def get_threshold_citation(
    scope_type: str = Query("global", description="Scope type"),
    scope_value: Optional[str] = Query(None, description="Scope value"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Get the retrieved ₹50,000 threshold, verbatim manual citation, and section (Role: any)."""
    threshold_data = get_policy_threshold(db, scope_type=scope_type, scope_value=scope_value)
    return success_envelope(
        data=threshold_data,
        provenance={"threshold": "retrieved"},
        data_disclosure="real",
    )


@router.get("/reload", response_model=None)
def reload_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
):
    """Reload policy configuration and return current effective global policy (Manager only)."""
    policy = get_effective_policy(db, scope_type="global", scope_value=None)
    threshold_info = get_policy_threshold(db, scope_type="global", scope_value=None)
    return success_envelope(
        data={
            "policy": format_policy_record(policy),
            "threshold": threshold_info,
            "reloaded_at": clock.now().isoformat(),
        },
        provenance={"policy": "retrieved"},
        data_disclosure="real",
    )
