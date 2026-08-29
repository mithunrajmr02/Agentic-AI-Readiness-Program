"""Regression tests for the three WS-9 `inventory_service.py` defects
(:133 status guard, :137 clock, :140-141 partial receipt) plus the M-16
ledger invariant.
"""
from datetime import datetime

import pytest

from src.backend.models import (
    Category, MovementType, POItem, POStatus, Product, PurchaseOrder,
    StockLevel, StockMovement, Supplier,
)
from src.backend.services.inventory_service import (
    generate_po_number, is_partially_received, receive_purchase_order,
)
from src.execution import clock


def _make_supplier(db):
    supplier = Supplier(name="Acme", supplier_code="SUP-0001")
    db.add(supplier)
    db.flush()
    return supplier


def _make_product(db, supplier, reorder_point=10):
    product = Product(
        sku="SKU-GRO-0001", name="Rice", category=Category.grocery,
        unit_price=100.0, cost_price=80.0, reorder_point=reorder_point,
        reorder_quantity=50, supplier_id=supplier.id,
    )
    db.add(product)
    db.flush()
    stock = StockLevel(product_id=product.id, quantity_on_hand=0, quantity_reserved=0)
    db.add(stock)
    db.commit()
    return product


def _make_po(db, supplier, product, quantity_ordered=100, unit_cost=80.0, status=POStatus.submitted):
    po = PurchaseOrder(
        po_number="PO-2026-0001", supplier_id=supplier.id, status=status,
        order_date=clock.today(), total_amount=quantity_ordered * unit_cost,
    )
    db.add(po)
    db.flush()
    item = POItem(po_id=po.id, product_id=product.id, quantity_ordered=quantity_ordered, unit_cost=unit_cost)
    db.add(item)
    db.commit()
    return po


def _movements_sum(db, product_id):
    return sum(m.quantity for m in db.query(StockMovement).filter(StockMovement.product_id == product_id).all())


def _stock(db, product_id):
    return db.query(StockLevel).filter(StockLevel.product_id == product_id).first()


# --- :133 status guard ---

@pytest.mark.parametrize("status", [POStatus.draft, POStatus.submitted, POStatus.acknowledged])
def test_receivable_statuses_succeed(db_session, status):
    supplier = _make_supplier(db_session)
    product = _make_product(db_session, supplier)
    po = _make_po(db_session, supplier, product, status=status)

    result = receive_purchase_order(po.id, db_session)
    assert result.status == POStatus.received


def test_cancelled_po_cannot_be_received(db_session):
    supplier = _make_supplier(db_session)
    product = _make_product(db_session, supplier)
    po = _make_po(db_session, supplier, product, status=POStatus.cancelled)

    with pytest.raises(ValueError, match="cancelled"):
        receive_purchase_order(po.id, db_session)


def test_already_received_po_cannot_be_received_again(db_session):
    supplier = _make_supplier(db_session)
    product = _make_product(db_session, supplier)
    po = _make_po(db_session, supplier, product, status=POStatus.submitted)

    receive_purchase_order(po.id, db_session)
    with pytest.raises(ValueError, match="already been received"):
        receive_purchase_order(po.id, db_session)


# --- :137 clock, not date.today() ---

def test_generate_po_number_uses_clock_year(monkeypatch):
    class FakeDB:
        def query(self, *_):
            return self

        def filter(self, *_):
            return self

        def all(self):
            return []

    monkeypatch.setattr(clock, "now", lambda: datetime(2031, 1, 1))
    assert generate_po_number(FakeDB()) == "PO-2031-0001"


def test_receive_uses_clock_now_not_real_today(db_session, monkeypatch):
    supplier = _make_supplier(db_session)
    product = _make_product(db_session, supplier)
    po = _make_po(db_session, supplier, product, status=POStatus.submitted)

    fixed_now = datetime(2030, 3, 4, 9, 0, 0)
    monkeypatch.setattr(clock, "now", lambda: fixed_now)

    result = receive_purchase_order(po.id, db_session)
    assert result.received_date == fixed_now.date()


def test_receive_accepts_explicit_backdated_received_at(db_session):
    """The seeder needs to backdate historical receipts (§13 demo scenarios);
    `received_at` lets it do so without touching the clock's global offset.
    """
    supplier = _make_supplier(db_session)
    product = _make_product(db_session, supplier)
    po = _make_po(db_session, supplier, product, status=POStatus.submitted)

    backdated = datetime(2026, 6, 1, 8, 0, 0)
    result = receive_purchase_order(po.id, db_session, received_at=backdated)
    assert result.received_date == backdated.date()

    movement = db_session.query(StockMovement).filter(StockMovement.product_id == product.id).first()
    assert movement.recorded_at == backdated


# --- :140-141 partial receipt ---

def test_partial_receipt_does_not_advance_status_to_received(db_session):
    supplier = _make_supplier(db_session)
    product = _make_product(db_session, supplier)
    po = _make_po(db_session, supplier, product, quantity_ordered=100, status=POStatus.submitted)
    item = po.items[0]

    result = receive_purchase_order(po.id, db_session, item_receipts={item.id: 40})

    assert result.status == POStatus.submitted
    assert is_partially_received(result)
    assert _stock(db_session, product.id).quantity_on_hand == 40
    assert _movements_sum(db_session, product.id) == _stock(db_session, product.id).quantity_on_hand


def test_partial_receipt_then_completion_advances_to_received(db_session):
    supplier = _make_supplier(db_session)
    product = _make_product(db_session, supplier)
    po = _make_po(db_session, supplier, product, quantity_ordered=100, status=POStatus.submitted)
    item = po.items[0]

    receive_purchase_order(po.id, db_session, item_receipts={item.id: 40})
    result = receive_purchase_order(po.id, db_session, item_receipts={item.id: 60})

    assert result.status == POStatus.received
    assert not is_partially_received(result)
    assert _stock(db_session, product.id).quantity_on_hand == 100
    assert _movements_sum(db_session, product.id) == 100


def test_partial_receipt_cannot_exceed_outstanding_quantity(db_session):
    supplier = _make_supplier(db_session)
    product = _make_product(db_session, supplier)
    po = _make_po(db_session, supplier, product, quantity_ordered=100, status=POStatus.submitted)
    item = po.items[0]

    receive_purchase_order(po.id, db_session, item_receipts={item.id: 40})
    with pytest.raises(ValueError, match="outstanding"):
        receive_purchase_order(po.id, db_session, item_receipts={item.id: 61})


def test_no_receipt_map_receives_full_outstanding_quantity_backward_compatible(db_session):
    supplier = _make_supplier(db_session)
    product = _make_product(db_session, supplier)
    po = _make_po(db_session, supplier, product, quantity_ordered=100, status=POStatus.submitted)

    result = receive_purchase_order(po.id, db_session)
    assert result.status == POStatus.received
    assert _stock(db_session, product.id).quantity_on_hand == 100
