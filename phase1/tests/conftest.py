import sys
import os
import pytest

# Ensure phase1 directory is in sys.path
phase1_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if phase1_dir not in sys.path:
    sys.path.insert(0, phase1_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models import Supplier, Product, StockLevel, Category


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Override FastAPI DB dependency to use the static pool engine
    def _override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = _override_get_db
    
    try:
        yield db
    finally:
        db.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="function")
def client(db_session):
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def seeded_supplier(client, auth_headers):
    payload = {
        "name": "Reliable Wholesale Ltd",
        "supplier_code": "SUP-0001",
        "contact_email": "orders@reliablewholesale.com",
        "payment_terms_days": 30,
        "lead_time_days": 7
    }
    response = client.post("/api/v1/suppliers", json=payload, headers=auth_headers)
    assert response.status_code == 201
    return response.json()

@pytest.fixture
def seeded_supplier_db(db_session):
    supplier = Supplier(
        name="Reliable Wholesale Ltd",
        supplier_code="SUP-0001",
        contact_email="orders@reliablewholesale.com",
        payment_terms_days=30,
        lead_time_days=7
    )
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier

@pytest.fixture
def seeded_product(client, auth_headers, seeded_supplier):
    payload = {
        "name": "Basmati Rice 5kg",
        "category": "grocery",
        "unit_price": 350.0,
        "cost_price": 280.0,
        "unit_of_measure": "box",
        "reorder_point": 20,
        "reorder_quantity": 100,
        "supplier_id": seeded_supplier["id"]
    }
    response = client.post("/api/v1/products", json=payload, headers=auth_headers)
    assert response.status_code == 201
    return response.json()

@pytest.fixture
def seeded_product_db(db_session, seeded_supplier_db):
    product = Product(
        sku="SKU-GRO-0001",
        name="Basmati Rice 5kg",
        category=Category.grocery,
        unit_price=350.0,
        cost_price=280.0,
        unit_of_measure="box",
        reorder_point=20,
        reorder_quantity=100,
        supplier_id=seeded_supplier_db.id
    )
    db_session.add(product)
    db_session.flush()
    stock = StockLevel(product_id=product.id, quantity_on_hand=100, quantity_reserved=0)
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(product)
    return product

@pytest.fixture
def submitted_po(client, auth_headers, seeded_supplier, seeded_product):
    payload = {
        "supplier_id": seeded_supplier["id"],
        "order_date": "2026-06-18",
        "expected_delivery": "2026-06-25",
        "items": [
            {
                "product_id": seeded_product["id"],
                "quantity_ordered": 100,
                "unit_cost": 280.0
            }
        ]
    }
    response = client.post("/api/v1/orders", json=payload, headers=auth_headers)
    assert response.status_code == 201
    po = response.json()
    return po["id"]
