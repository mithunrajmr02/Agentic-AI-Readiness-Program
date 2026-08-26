"""Fixtures and test setup for Sourcing / Supplier Intelligence tests (WS-7)."""
from datetime import date
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.database import Base, get_db
import src.backend.models
from src.backend import models_registry
from src.backend.models import Category, MovementType, POStatus, Product, PurchaseOrder, Supplier
from src.backend.models_sourcing import SupplierProduct
from src.backend.routers.suppliers import router as suppliers_router
from src.core import clock, events


@pytest.fixture(autouse=True)
def reset_clock_and_events():
    """Reset clock offset and events between tests."""
    clock.reset()
    events.reset()
    yield
    clock.reset()
    events.reset()


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        # Seed standard test entities
        s1 = Supplier(
            id=1,
            name="Reliable Wholesale Ltd",
            supplier_code="SUP-0001",
            contact_email="reliable@wholesale.com",
            payment_terms_days=30,
            lead_time_days=7,
            is_active=True,
        )
        s2 = Supplier(
            id=2,
            name="Apex Logistics & Supplies",
            supplier_code="SUP-0002",
            contact_email="apex@logistics.com",
            payment_terms_days=30,
            lead_time_days=3,
            is_active=True,
        )
        s3 = Supplier(
            id=3,
            name="Metro Goods Distribution",
            supplier_code="SUP-0003",
            contact_email="metro@goods.com",
            payment_terms_days=45,
            lead_time_days=10,
            is_active=True,
        )
        s4 = Supplier(
            id=4,
            name="Global Logistics Corp",
            supplier_code="SUP-0004",
            contact_email="global@logistics.com",
            payment_terms_days=30,
            lead_time_days=5,
            is_active=True,
        )
        s5 = Supplier(
            id=5,
            name="Inactive Supplies Co",
            supplier_code="SUP-0005",
            contact_email="inactive@supplies.com",
            payment_terms_days=30,
            lead_time_days=4,
            is_active=False,
        )
        session.add_all([s1, s2, s3, s4, s5])

        p1 = Product(
            id=1,
            sku="SKU-GRO-0001",
            name="Organic Basmati Rice 10kg",
            category=Category.grocery,
            unit_price=800.0,
            cost_price=600.0,
            unit_of_measure="bag",
            reorder_point=15,
            reorder_quantity=50,
            supplier_id=4,
        )
        p2 = Product(
            id=2,
            sku="SKU-ELC-0001",
            name="Sony Headphones",
            category=Category.electronics,
            unit_price=25000.0,
            cost_price=22000.0,
            unit_of_measure="pieces",
            reorder_point=10,
            reorder_quantity=20,
            supplier_id=2,
        )
        session.add_all([p1, p2])

        # Add PO-2026-0001: ordered 2026-08-14, expected 2026-08-21, received 2026-08-23
        po1 = PurchaseOrder(
            id=1,
            po_number="PO-2026-0001",
            supplier_id=4,
            status=POStatus.received,
            total_amount=30000.0,
            order_date=date(2026, 8, 14),
            expected_delivery=date(2026, 8, 21),
            received_date=date(2026, 8, 23),
        )
        session.add(po1)

        # Supplier products
        sp1 = SupplierProduct(
            id=1,
            supplier_id=4,
            product_id=1,
            unit_price=600.0,
            lead_time_days=5,
            min_order_quantity=10,
            is_preferred=True,
        )
        sp2 = SupplierProduct(
            id=2,
            supplier_id=1,
            product_id=1,
            unit_price=620.0,
            lead_time_days=7,
            min_order_quantity=20,
            is_preferred=False,
        )
        session.add_all([sp1, sp2])

        session.commit()
        yield session
    finally:
        session.close()


@pytest.fixture
def test_app(db):
    """Create a FastAPI test app with suppliers router mounted."""
    app = FastAPI()
    app.include_router(suppliers_router)

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)
