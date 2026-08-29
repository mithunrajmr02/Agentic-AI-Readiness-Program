"""The only write path for an authorised decision (15-SHARED-CONTRACTS.md §9).

WS-9 decides nothing here -- `execute_decision` re-checks the seven
preconditions against present reality and either writes a purchase order or
refuses, naming exactly which precondition blocked it. The decision to act
was made upstream (WS-4/WS-5); this module never second-guesses the verdict,
only whether it is still safe to carry out.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.backend.services.po_service import DuplicateOpenPurchaseOrder, create_purchase_order
from src.execution.preconditions import check_preconditions


@dataclass(frozen=True)
class ExecutionResult:
    ok: bool
    execution_ref: Optional[str]     # e.g. PO-2026-0042
    failed_precondition: Optional[str]
    detail: str


def execute_decision(db: Session, decision: Any) -> ExecutionResult:
    """Re-check the seven preconditions, then write. Refuses rather than
    guesses -- any failed precondition stops the write and is reported by
    name.
    """
    failed = check_preconditions(db, decision)
    if failed:
        return ExecutionResult(
            ok=False,
            execution_ref=None,
            failed_precondition=failed[0],
            detail=f"Preconditions failed: {', '.join(failed)}",
        )

    quantity = getattr(decision, "quantity", None)
    unit_cost = getattr(decision, "unit_cost", None)
    product_id = getattr(decision, "product_id", None)
    supplier_id = getattr(decision, "supplier_id", None)
    idempotency_key = getattr(decision, "idempotency_key", None)
    expected_delivery = getattr(decision, "expected_delivery", None)

    try:
        po = create_purchase_order(
            db,
            supplier_id=supplier_id,
            items=[{"product_id": product_id, "quantity_ordered": quantity, "unit_cost": unit_cost}],
            expected_delivery=expected_delivery,
            idempotency_key=idempotency_key,
        )
    except DuplicateOpenPurchaseOrder as exc:
        return ExecutionResult(
            ok=False,
            execution_ref=None,
            failed_precondition="duplicate_open_po",
            detail=str(exc),
        )

    return ExecutionResult(ok=True, execution_ref=po.po_number, failed_precondition=None, detail="Purchase order created")
