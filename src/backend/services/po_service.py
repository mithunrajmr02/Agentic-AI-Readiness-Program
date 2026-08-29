"""The only path WS-9 uses to create purchase orders on behalf of an
authorised decision (governance's PO writes -- not the pre-existing manual
`POST /api/v1/orders` in `routers/inventory.py`, which is untouched).

Owned by WS-9 (docs/implementation/14-PARALLEL-WORKSTREAMS.md, WS-9 "Owns").
Enforces the duplicate-order guard (AD-15): an open PO already covering a SKU
blocks a second one.
"""
from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy.orm import Session

from src.backend.models import POItem, POStatus, PurchaseOrder
from src.backend.services.inventory_service import generate_po_number
from src.execution import clock, idempotency

OPEN_PO_STATUSES = (POStatus.draft, POStatus.submitted, POStatus.acknowledged)


class DuplicateOpenPurchaseOrder(Exception):
    """Raised when a product already has an open PO and a caller tries to
    raise a second one for it (the AD-15 duplicate-order guard)."""

    def __init__(self, product_id: int, existing_po_number: str):
        self.product_id = product_id
        self.existing_po_number = existing_po_number
        super().__init__(
            f"An open purchase order ({existing_po_number}) already covers product {product_id}"
        )


def has_open_purchase_order(db: Session, product_id: int, *, exclude_po_id: Optional[int] = None) -> bool:
    """True if any PO in draft/submitted/acknowledged status has a line item
    for this product. Used both as the creation-time guard and as
    precondition 3 at execution time.
    """
    return open_purchase_order_for(db, product_id, exclude_po_id=exclude_po_id) is not None


def open_purchase_order_for(
    db: Session, product_id: int, *, exclude_po_id: Optional[int] = None
) -> Optional[PurchaseOrder]:
    query = (
        db.query(PurchaseOrder)
        .join(POItem, POItem.po_id == PurchaseOrder.id)
        .filter(POItem.product_id == product_id)
        .filter(PurchaseOrder.status.in_(OPEN_PO_STATUSES))
    )
    if exclude_po_id is not None:
        query = query.filter(PurchaseOrder.id != exclude_po_id)
    return query.first()


def create_purchase_order(
    db: Session,
    *,
    supplier_id: int,
    items: Iterable[dict],
    expected_delivery=None,
    idempotency_key: Optional[str] = None,
    order_date=None,
) -> PurchaseOrder:
    """Raise a new PO, enforcing the duplicate-order guard and idempotency.

    `items` is an iterable of `{"product_id": int, "quantity_ordered": int,
    "unit_cost": float}`. A replay of the same `idempotency_key` returns the
    PO created the first time rather than writing a second order.
    """
    if idempotency_key and idempotency.is_key_consumed(db, idempotency_key):
        consumed = idempotency.get_consumed(db, idempotency_key)
        existing = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.po_number == consumed.execution_ref)
            .first()
            if consumed and consumed.execution_ref
            else None
        )
        if existing is not None:
            return existing
        raise ValueError(f"Idempotency key already consumed: {idempotency_key}")

    items = list(items)
    for item in items:
        blocking = open_purchase_order_for(db, item["product_id"])
        if blocking is not None:
            raise DuplicateOpenPurchaseOrder(item["product_id"], blocking.po_number)

    po = PurchaseOrder(
        po_number=generate_po_number(db),
        supplier_id=supplier_id,
        status=POStatus.draft,
        order_date=order_date or clock.today(),
        expected_delivery=expected_delivery,
        total_amount=0.0,
    )
    db.add(po)
    db.flush()

    total = 0.0
    for item in items:
        db.add(POItem(
            po_id=po.id,
            product_id=item["product_id"],
            quantity_ordered=item["quantity_ordered"],
            unit_cost=item["unit_cost"],
        ))
        total += item["quantity_ordered"] * item["unit_cost"]
    po.total_amount = total

    db.commit()
    db.refresh(po)

    if idempotency_key:
        idempotency.consume_key(db, idempotency_key, execution_ref=po.po_number)
        db.commit()

    return po
