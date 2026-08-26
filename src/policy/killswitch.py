"""Kill switch operations and state management — WS-5.

15-SHARED-CONTRACTS.md §7 / 12-DATA-AND-API-CHANGES.md §5.4.
Provides functions to check, engage, and release the global or scoped kill switch
with full audit trail recording explicit timestamps via clock.now().
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.backend.models_governance import AutonomyPolicy
from src.core import clock
from src.core.errors import PreconditionFailed


def get_or_create_policy_record(
    db: Session,
    scope_type: str = "global",
    scope_value: Optional[str] = None,
) -> AutonomyPolicy:
    """Retrieve or initialize the AutonomyPolicy record for the given scope."""
    policy = (
        db.query(AutonomyPolicy)
        .filter(
            AutonomyPolicy.scope_type == scope_type,
            AutonomyPolicy.scope_value == scope_value,
        )
        .first()
    )
    if policy is None:
        policy = AutonomyPolicy(
            scope_type=scope_type,
            scope_value=scope_value,
            mode="autonomous",
            max_order_value=None,  # None means default retrieved limit (₹50,000)
            max_orders_per_hour=10,
            max_value_per_day=500000.0,
            min_sale_events=10,
            min_history_days=30,
            safety_stock_days=2,
            drift_tolerance_pct=20.0,
            kill_switch_engaged=False,
            kill_switch_reason=None,
            kill_switch_by_user_id=None,
            consecutive_failures=0,
            updated_at=clock.now(),
            updated_by_user_id=None,
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
    return policy


def is_kill_switch_engaged(
    db: Session,
    scope_type: str = "global",
    scope_value: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """Check whether the kill switch is active for the specified scope.

    Checks global scope first (a global kill switch overrides all scopes),
    then the specific scope if different from global.
    """
    global_policy = (
        db.query(AutonomyPolicy)
        .filter(AutonomyPolicy.scope_type == "global")
        .first()
    )
    if global_policy is not None and global_policy.kill_switch_engaged:
        return True, global_policy.kill_switch_reason

    if scope_type != "global":
        scoped_policy = (
            db.query(AutonomyPolicy)
            .filter(
                AutonomyPolicy.scope_type == scope_type,
                AutonomyPolicy.scope_value == scope_value,
            )
            .first()
        )
        if scoped_policy is not None and scoped_policy.kill_switch_engaged:
            return True, scoped_policy.kill_switch_reason

    return False, None


def engage_kill_switch(
    db: Session,
    user_id: int,
    reason: str,
    scope_type: str = "global",
    scope_value: Optional[str] = None,
) -> AutonomyPolicy:
    """Engage the kill switch for the specified scope. Reason is mandatory."""
    if not reason or not reason.strip():
        raise PreconditionFailed("kill_switch_reason", "A valid reason is required to engage the kill switch")

    policy = get_or_create_policy_record(db, scope_type=scope_type, scope_value=scope_value)
    policy.kill_switch_engaged = True
    policy.kill_switch_reason = reason.strip()
    policy.kill_switch_by_user_id = user_id
    policy.updated_at = clock.now()
    policy.updated_by_user_id = user_id

    db.commit()
    db.refresh(policy)
    return policy


def release_kill_switch(
    db: Session,
    user_id: int,
    reason: Optional[str] = None,
    scope_type: str = "global",
    scope_value: Optional[str] = None,
) -> AutonomyPolicy:
    """Release the kill switch for the specified scope."""
    policy = get_or_create_policy_record(db, scope_type=scope_type, scope_value=scope_value)
    policy.kill_switch_engaged = False
    policy.kill_switch_reason = reason.strip() if reason else None
    policy.kill_switch_by_user_id = user_id
    policy.updated_at = clock.now()
    policy.updated_by_user_id = user_id

    db.commit()
    db.refresh(policy)
    return policy
