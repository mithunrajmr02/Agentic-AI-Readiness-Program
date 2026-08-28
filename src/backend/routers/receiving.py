"""New receiving surface (POST /api/receiving/*), separate from the legacy
`PATCH /api/v1/orders/{id}/receive` in `routers/inventory.py` (untouched --
not owned by WS-9). Exposes the partial-receipt support the defect fixes in
`inventory_service.py` now make possible.

Publishes a module-level `router` and stops there -- integration wires it
into `main.py` (EXECUTION-RUNBOOK.md DoD rule).
"""
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import structlog

from src.backend.database import get_db
from src.backend.models import PurchaseOrder, User
from src.backend.routers.auth import get_current_user
from src.backend.schemas import PurchaseOrderResponse
from src.backend.services.inventory_service import is_partially_received, receive_purchase_order

logger = structlog.get_logger()
router = APIRouter(prefix="/api/receiving", tags=["receiving"])


class ItemReceipt(BaseModel):
    po_item_id: int = Field(gt=0)
    quantity_received: int = Field(ge=0)


class ReceivingRequest(BaseModel):
    # Omit an item, or the whole body, to receive its full outstanding quantity.
    item_receipts: Optional[List[ItemReceipt]] = None
    received_at: Optional[datetime] = None


class ReceivingResponse(PurchaseOrderResponse):
    is_partially_received: bool


def _to_response(po: PurchaseOrder) -> ReceivingResponse:
    base = PurchaseOrderResponse.model_validate(po)
    return ReceivingResponse(**base.model_dump(), is_partially_received=is_partially_received(po))


@router.post("/{po_id}/receive", response_model=ReceivingResponse)
def receive(
    po_id: int,
    body: Optional[ReceivingRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item_receipts: Optional[Dict[int, int]] = None
    received_at: Optional[datetime] = None
    if body is not None:
        received_at = body.received_at
        if body.item_receipts is not None:
            item_receipts = {r.po_item_id: r.quantity_received for r in body.item_receipts}

    try:
        po = receive_purchase_order(po_id, db, item_receipts=item_receipts, received_at=received_at)
    except ValueError as e:
        detail = str(e)
        status_code = 404 if "not found" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail)

    logger.info("receiving_recorded", poc_id="POC-07", po_number=po.po_number)
    return _to_response(po)


@router.get("/{po_id}/status", response_model=ReceivingResponse)
def receiving_status(
    po_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail=f"Purchase order {po_id} not found")
    return _to_response(po)
