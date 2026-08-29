"""The seven preconditions (15-SHARED-CONTRACTS.md §9), re-checked at
execution time -- never trusted from proposal time, because on the approval
path arbitrary time has passed and any of them may have flipped.

`decision` is accepted duck-typed: the real `Decision` row from WS-0/WS-4's
`models_governance.py` once it exists, or any object exposing the same
attributes. That module is not published in this worktree yet -- see
docs/implementation/integration-requests/WS-9.md. WS-9 decides nothing here;
it only re-verifies what someone else already authorised.
"""
from __future__ import annotations

from typing import Any, List

from sqlalchemy.orm import Session

from src.backend.models import Product, StockLevel, Supplier
from src.backend.services.po_service import has_open_purchase_order
from src.execution import idempotency

KILL_SWITCH_ENGAGED = "kill_switch_engaged"
AUTONOMY_MODE_FORBIDS = "autonomy_mode_forbids"
DUPLICATE_OPEN_PO = "duplicate_open_po"
SUPPLIER_INACTIVE = "supplier_inactive"
NEED_ALREADY_RESOLVED = "need_already_resolved"
IDEMPOTENCY_KEY_CONSUMED = "idempotency_key_consumed"
VALUE_OUT_OF_BAND = "value_out_of_band"

# Autonomy modes that forbid execution outright (contract §2.4 AUTONOMY_MODES).
# `assisted` and `autonomous` may execute; `off`/`shadow` may not.
_EXECUTABLE_AUTONOMY_MODES = ("assisted", "autonomous")


def check_preconditions(db: Session, decision: Any) -> List[str]:
    """Return the failed precondition names, in contract order. `[]` means
    clear to execute.
    """
    failed: List[str] = []

    if getattr(decision, "kill_switch_engaged", False):
        failed.append(KILL_SWITCH_ENGAGED)

    autonomy_mode = getattr(decision, "autonomy_mode", "off")
    if autonomy_mode not in _EXECUTABLE_AUTONOMY_MODES:
        failed.append(AUTONOMY_MODE_FORBIDS)

    product_id = getattr(decision, "product_id", None)
    if product_id is not None and has_open_purchase_order(
        db, product_id, exclude_po_id=getattr(decision, "execution_ref_po_id", None)
    ):
        failed.append(DUPLICATE_OPEN_PO)

    supplier_id = getattr(decision, "supplier_id", None)
    if supplier_id is not None:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if supplier is None or not supplier.is_active:
            failed.append(SUPPLIER_INACTIVE)

    if _need_already_resolved(db, product_id):
        failed.append(NEED_ALREADY_RESOLVED)

    idempotency_key = getattr(decision, "idempotency_key", None)
    if idempotency_key and idempotency.is_key_consumed(db, idempotency_key):
        failed.append(IDEMPOTENCY_KEY_CONSUMED)

    order_value = getattr(decision, "order_value", None)
    authority_limit = getattr(decision, "authority_limit", None)
    if order_value is not None and authority_limit is not None and order_value > authority_limit:
        failed.append(VALUE_OUT_OF_BAND)

    return failed


def _need_already_resolved(db: Session, product_id) -> bool:
    """Precondition 5: has the stock position already resolved the need that
    triggered the proposal -- e.g. a delivery arrived while an approval sat
    in a manager's queue.
    """
    if product_id is None:
        return False
    product = db.query(Product).filter(Product.id == product_id).first()
    stock = db.query(StockLevel).filter(StockLevel.product_id == product_id).first()
    if product is None or stock is None:
        return False
    return stock.quantity_available > (product.reorder_point or 0)
