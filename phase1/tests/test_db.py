import pytest
from datetime import date
from sqlalchemy.exc import IntegrityError
from app.models import Product, StockMovement, PurchaseOrder, StockLevel, Category

def test_sku_unique(db_session):
    """TC-07-P1-DB-01: SKU Unique Constraint"""
    p1 = Product(sku="SKU-GRO-9999", name="Test 1", category=Category.grocery,
                 unit_price=100.0, cost_price=80.0)
    db_session.add(p1)
    db_session.commit()
    
    with pytest.raises(IntegrityError):
        p2 = Product(sku="SKU-GRO-9999", name="Test 2", category=Category.grocery,
                     unit_price=100.0, cost_price=80.0)
        db_session.add(p2)
        db_session.commit()
    db_session.rollback()

def test_movement_linked(db_session, seeded_product_db):
    """TC-07-P1-DB-02: StockMovement Linked to Product"""
    m = StockMovement(product_id=seeded_product_db.id, movement_type="receipt",
                      quantity=50, recorded_by="Kiran")
    db_session.add(m)
    db_session.commit()
    assert m.id is not None and m.product_id == seeded_product_db.id

def test_po_unique(db_session, seeded_supplier_db):
    """TC-07-P1-DB-03: PO Number Unique"""
    po1 = PurchaseOrder(po_number="PO-2026-9999", supplier_id=seeded_supplier_db.id,
                        order_date=date.today())
    db_session.add(po1)
    db_session.commit()
    
    with pytest.raises(IntegrityError):
        po2 = PurchaseOrder(po_number="PO-2026-9999", supplier_id=seeded_supplier_db.id,
                            order_date=date.today())
        db_session.add(po2)
        db_session.commit()
    db_session.rollback()

def test_stock_level_one_to_one(db_session, seeded_product_db):
    """TC-07-P1-DB-04: StockLevel One-to-One with Product"""
    # seeded_product_db already has a StockLevel created in fixture
    with pytest.raises(IntegrityError):
        s2 = StockLevel(product_id=seeded_product_db.id, quantity_on_hand=50)
        db_session.add(s2)
        db_session.commit()
    db_session.rollback()
