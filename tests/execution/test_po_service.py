"""Duplicate-order guard and idempotency for WS-9's PO write path
(`src/backend/services/po_service.py`)."""
import pytest

from src.backend.models import Category, POStatus, Product, StockLevel, Supplier
from src.backend.services.po_service import DuplicateOpenPurchaseOrder, create_purchase_order, has_open_purchase_order


def _make_supplier(db):
    supplier = Supplier(name="Acme", supplier_code="SUP-0001")
    db.add(supplier)
    db.flush()
    return supplier


def _make_product(db, supplier):
    product = Product(
        sku="SKU-GRO-0001", name="Rice", category=Category.grocery,
        unit_price=100.0, cost_price=80.0, reorder_point=10,
        reorder_quantity=50, supplier_id=supplier.id,
    )
    db.add(product)
    db.flush()
    db.add(StockLevel(product_id=product.id, quantity_on_hand=5, quantity_reserved=0))
    db.commit()
    return product


def test_duplicate_open_po_guard_blocks_second_order_for_same_sku(db_session):
    supplier = _make_supplier(db_session)
    product = _make_product(db_session, supplier)

    first = create_purchase_order(
        db_session, supplier_id=supplier.id,
        items=[{"product_id": product.id, "quantity_ordered": 50, "unit_cost": 80.0}],
    )
    assert first.status == POStatus.draft
    assert has_open_purchase_order(db_session, product.id)

    with pytest.raises(DuplicateOpenPurchaseOrder):
        create_purchase_order(
            db_session, supplier_id=supplier.id,
            items=[{"product_id": product.id, "quantity_ordered": 30, "unit_cost": 80.0}],
        )


def test_idempotency_key_replay_returns_original_po_no_second_write(db_session):
    supplier = _make_supplier(db_session)
    product = _make_product(db_session, supplier)

    first = create_purchase_order(
        db_session, supplier_id=supplier.id,
        items=[{"product_id": product.id, "quantity_ordered": 50, "unit_cost": 80.0}],
        idempotency_key="fixed-key-1",
    )
    replay = create_purchase_order(
        db_session, supplier_id=supplier.id,
        items=[{"product_id": product.id, "quantity_ordered": 999, "unit_cost": 1.0}],
        idempotency_key="fixed-key-1",
    )

    assert replay.id == first.id
    assert replay.po_number == first.po_number

    from src.backend.models import PurchaseOrder
    assert db_session.query(PurchaseOrder).count() == 1
