"""Counter-proposal engine for Steward governance (WS-4).

15-SHARED-CONTRACTS.md §8 / 13-DEMO-SCENARIOS.md §5.5.
Handles human counter-proposals, recomputes stock cover and re-breach horizons,
and generates deterministic system objections when an operator overrides
a recommended decision.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Optional
from sqlalchemy.orm import Session

from src.backend.models_governance import Approval, Decision
from src.core import clock
from src.core.errors import PreconditionFailed
from src.governance.decisions import get_decision


@dataclass(frozen=True)
class CounterResult:
    """The outcome of a counter-proposal (15-SHARED-CONTRACTS.md §8)."""

    decision: Decision
    recomputed: dict
    system_objection: Optional[str]  # non-null when the human's number is worse
    accepted: bool


def counter(
    db: Session,
    approval_id: str,
    user_id: int,
    payload: dict,
) -> CounterResult:
    """Evaluate and apply a human counter-proposal.

    15-SHARED-CONTRACTS.md §8 / 13-DEMO-SCENARIOS.md §5.5 / BW-2.
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

    # Parse existing inputs and computation
    inputs: dict = {}
    if decision.inputs:
        try:
            inputs = json.loads(decision.inputs)
        except Exception:
            inputs = {}

    computation: dict = {}
    if decision.computation:
        try:
            computation = json.loads(decision.computation)
        except Exception:
            computation = {}

    # Extract parameters for recomputation
    recommended_qty = (
        computation.get("reorder_quantity")
        or computation.get("proposed_quantity")
        or inputs.get("proposed_quantity")
        or inputs.get("quantity")
        or 12
    )

    new_qty_raw = payload.get("quantity")
    if new_qty_raw is None:
        new_qty_raw = payload.get("modified_quantity")

    daily_demand = (
        inputs.get("daily_demand")
        or inputs.get("avg_daily_demand")
        or computation.get("daily_demand")
        or computation.get("avg_daily_demand")
        or 1.5
    )
    on_hand = (
        inputs.get("quantity_on_hand")
        or inputs.get("on_hand")
        or inputs.get("current_stock")
        or 4
    )
    reorder_point = (
        inputs.get("reorder_point")
        or inputs.get("computed_reorder_point")
        or inputs.get("stored_reorder_point")
        or computation.get("reorder_point")
        or 8
    )
    unit_price = (
        inputs.get("unit_price")
        or inputs.get("unit_price_used")
        or inputs.get("cost_price")
        or 22000.0
    )

    system_objection: Optional[str] = None
    recomputed: dict = {}

    if new_qty_raw is not None:
        new_qty = int(new_qty_raw)
        new_order_value = float(new_qty * unit_price)
        available_after = int(on_hand + new_qty)
        margin_above_rop = float(available_after - reorder_point)
        cover_days = (
            (margin_above_rop / daily_demand)
            if daily_demand and daily_demand > 0
            else 0.0
        )

        # Deterministic objection when human reduces quantity below recommendation
        if recommended_qty and new_qty < recommended_qty:
            if margin_above_rop >= 0:
                margin_str = f"{int(margin_above_rop)}" if margin_above_rop == int(margin_above_rop) else f"{margin_above_rop:.1f}"
                system_objection = (
                    f"{new_qty} units returns available stock to {available_after}, {margin_str} above "
                    f"the derived reorder point of {reorder_point}. At {daily_demand} units/day this SKU "
                    f"re-breaches in {cover_days:.1f} days and will require a second order — and a second ordering cost "
                    f"— inside the week. Recommended quantity remains {recommended_qty}."
                )
            else:
                system_objection = (
                    f"{new_qty} units leaves available stock at {available_after}, which is below "
                    f"the derived reorder point of {reorder_point}. At {daily_demand} units/day this SKU "
                    f"remains in breach immediately. Recommended quantity remains {recommended_qty}."
                )

        recomputed = {
            "counter_quantity": new_qty,
            "recommended_quantity": recommended_qty,
            "available_stock_after": available_after,
            "reorder_point": reorder_point,
            "margin_above_rop": margin_above_rop,
            "cover_days_above_rop": round(cover_days, 1),
            "order_value": new_order_value,
            "daily_demand": daily_demand,
        }
    else:
        recomputed = dict(payload)
        system_objection = payload.get("system_objection")

    # Update approval
    approval.outcome = "countered"
    approval.counter_payload = json.dumps(payload)
    approval.decided_by_user_id = user_id
    approval.decided_at = now_ts
    approval.rationale = payload.get("rationale") or payload.get("note")

    # Update decision
    decision.status = "countered"
    decision.system_objection = system_objection
    decision.decided_at = now_ts
    decision.actor = f"user:{user_id}"

    # Merge recomputed numbers into computation
    merged_computation = {**computation, "counter_recompute": recomputed}
    decision.computation = json.dumps(merged_computation)

    db.commit()
    db.refresh(approval)
    db.refresh(decision)

    return CounterResult(
        decision=decision,
        recomputed=recomputed,
        system_objection=system_objection,
        accepted=True,
    )
