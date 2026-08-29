"""Tests for src/backend/routers/receiving.py."""
from datetime import datetime
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.database import get_db
from src.backend.models import Category, POItem, POStatus, Product, PurchaseOrder, StockLevel, Supplier, User
from src.backend.routers.auth import get_current_user
from src.backend.routers.receiving import router
from src.core import clock


@pytest.fixture
def client(db_session):
    app = FastAPI()
    app.include_router(router)

    user = User(email="test@example.com", hashed_password="pw", role="manager", is_active=True)
    db_session.add(user)
    db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def _setup_po(db_session, qty=100, status=POStatus.submitted):
    supplier = Supplier(name="Acme", supplier_code="SUP-0001")
    db_session.add(supplier)
    db_session.flush()

    product = Product(
        sku="SKU-GRO-0001", name="Rice", category=Category.grocery,
        unit_price=100.0, cost_price=80.0, reorder_point=10,
        reorder_quantity=50, supplier_id=supplier.id,
    )
    db_session.add(product)
    db_session.flush()

    stock = StockLevel(product_id=product.id, quantity_on_hand=0, quantity_reserved=0)
    db_session.add(stock)

    po = PurchaseOrder(
        po_number="PO-2026-0001", supplier_id=supplier.id, status=status,
        order_date=clock.today(), total_amount=qty * 80.0,
    )
    db_session.add(po)
    db_session.flush()

    item = POItem(po_id=po.id, product_id=product.id, quantity_ordered=qty, unit_cost=80.0)
    db_session.add(item)
    db_session.commit()
    return po, item, product


def test_receive_endpoint_full_receipt(client, db_session):
    po, item, product = _setup_po(db_session, qty=100)

    res = client.post(f"/api/receiving/{po.id}/receive", json={})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "received"
    assert data["is_partially_received"] is False


def test_receive_endpoint_partial_receipt(client, db_session):
    po, item, product = _setup_po(db_session, qty=100)

    res = client.post(f"/api/receiving/{po.id}/receive", json={
        "item_receipts": [{"po_item_id": item.id, "quantity_received": 35}]
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "submitted"
    assert data["is_partially_received"] is True


def test_receiving_status_endpoint(client, db_session):
    po, item, product = _setup_po(db_session, qty=50)

    res = client.get(f"/api/receiving/{po.id}/status")
    assert res.status_code == 200
    data = res.json()
    assert data["po_number"] == po.po_number
    assert data["status"] == "submitted"


def test_receive_not_found(client):
    res = client.post("/api/receiving/99999/receive", json={})
    assert res.status_code == 404
