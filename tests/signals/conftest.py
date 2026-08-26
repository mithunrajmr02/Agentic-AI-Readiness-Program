"""Test fixtures for Signal Engine test suite (WS-3)."""
from datetime import timedelta
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.database import Base, get_db
import src.backend.models
from src.backend import models_registry
from src.backend.models import (
    Category,
    MovementType,
    POItem,
    POStatus,
    Product,
    PurchaseOrder,
    StockLevel,
    StockMovement,
    Supplier,
    User,
)
from src.backend.models_analytics import Signal
from src.backend.routers.auth import create_access_token, get_password_hash
from src.backend.routers.signals import router as signals_router
from src.core import clock, events


@pytest.fixture(autouse=True)
def reset_clock_and_events():
    """Reset clock offset and in-process subscribers between tests."""
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
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_data(db):
    """Seed comprehensive dataset for testing all seven anomaly detectors."""
    # 1. Suppliers
    s1 = Supplier(
        name="Acme Supplies",
        supplier_code="SUP-0001",
        contact_email="alice@acme.com",
        lead_time_days=5,
        is_active=True,
    )
    s2 = Supplier(
        name="Slowpoke Logistics",
        supplier_code="SUP-0002",
        contact_email="bob@slowpoke.com",
        lead_time_days=3,  # Contract is 3 days
        is_active=True,
    )
    s3 = Supplier(
        name="Punctual Partners",
        supplier_code="SUP-0003",
        contact_email="carol@punctual.com",
        lead_time_days=7,
        is_active=True,
    )
    db.add_all([s1, s2, s3])
    db.commit()

    # 2. Products
    p1 = Product(
        sku="SKU-GRO-0001",
        name="Basmati Rice 5kg",
        category=Category.grocery,
        unit_price=800.0,
        cost_price=600.0,
        reorder_point=40,
        reorder_quantity=50,
        supplier_id=s1.id,
    )
    p2 = Product(
        sku="SKU-ELC-0001",
        name="Wireless Noise Cancelling Headphones",
        category=Category.electronics,
        unit_price=29999.0,
        cost_price=22000.0,
        reorder_point=10,
        reorder_quantity=20,
        supplier_id=s1.id,
    )
    p3 = Product(
        sku="SKU-GRO-0002",
        name="Premium Sunflower Oil 1L",
        category=Category.grocery,
        unit_price=220.0,
        cost_price=160.0,
        reorder_point=30,
        reorder_quantity=40,
        supplier_id=s1.id,
    )
    p4 = Product(
        sku="SKU-HSD-0001",
        name="Organic Laundry Detergent 2L",
        category=Category.household,
        unit_price=650.0,
        cost_price=450.0,
        reorder_point=20,
        reorder_quantity=50,
        supplier_id=s1.id,
    )
    p5 = Product(
        sku="SKU-PRC-0001",
        name="Colgate Total Toothpaste 150g",
        category=Category.personal_care,
        unit_price=120.0,
        cost_price=85.0,
        reorder_point=20,
        reorder_quantity=50,
        supplier_id=s1.id,
    )
    db.add_all([p1, p2, p3, p4, p5])
    db.commit()

    # 3. Stock levels
    # p1: Healthy stock on hand (150 > 40)
    sl1 = StockLevel(product_id=p1.id, quantity_on_hand=150, quantity_reserved=0)
    # p2: Out of stock (0 units <= 10)
    sl2 = StockLevel(product_id=p2.id, quantity_on_hand=0, quantity_reserved=0)
    # p3: Low stock / threshold breach (15 <= 30)
    sl3 = StockLevel(product_id=p3.id, quantity_on_hand=15, quantity_reserved=0)
    # p4: Excess stock on hand (500 units, capital drag)
    sl4 = StockLevel(product_id=p4.id, quantity_on_hand=500, quantity_reserved=0)
    # p5: Colgate with 50 units but zero sales history
    sl5 = StockLevel(product_id=p5.id, quantity_on_hand=50, quantity_reserved=0)
    db.add_all([sl1, sl2, sl3, sl4, sl5])
    db.commit()

    # 4. Purchase Orders
    today = clock.today()
    # PO 1: Overdue PO for p1 (expected 3 days ago, unreceived)
    po1 = PurchaseOrder(
        po_number="PO-2026-0001",
        supplier_id=s1.id,
        status=POStatus.submitted,
        total_amount=30000.0,
        order_date=today - timedelta(days=10),
        expected_delivery=today - timedelta(days=3),
    )
    # PO 2: Completed historical PO for s2 delivered 7 days late (order took 10 days vs 3 contract)
    po2 = PurchaseOrder(
        po_number="PO-2026-0002",
        supplier_id=s2.id,
        status=POStatus.received,
        total_amount=50000.0,
        order_date=today - timedelta(days=25),
        expected_delivery=today - timedelta(days=22),
        received_date=today - timedelta(days=15),  # 10 days lead time
    )
    # PO 3: Another late historical PO for s2 (8 days lead time vs 3 contract)
    po3 = PurchaseOrder(
        po_number="PO-2026-0003",
        supplier_id=s2.id,
        status=POStatus.received,
        total_amount=45000.0,
        order_date=today - timedelta(days=40),
        expected_delivery=today - timedelta(days=37),
        received_date=today - timedelta(days=32),
    )
    # PO 4: Third late historical PO for s2 (9 days lead time vs 3 contract)
    po4 = PurchaseOrder(
        po_number="PO-2026-0004",
        supplier_id=s2.id,
        status=POStatus.received,
        total_amount=60000.0,
        order_date=today - timedelta(days=60),
        expected_delivery=today - timedelta(days=57),
        received_date=today - timedelta(days=51),
    )
    # PO 5: Future on-time PO
    po5 = PurchaseOrder(
        po_number="PO-2026-0005",
        supplier_id=s3.id,
        status=POStatus.submitted,
        total_amount=15000.0,
        order_date=today - timedelta(days=2),
        expected_delivery=today + timedelta(days=5),
    )
    db.add_all([po1, po2, po3, po4, po5])
    db.commit()

    poi1 = POItem(po_id=po1.id, product_id=p1.id, quantity_ordered=50, unit_cost=600.0)
    poi2 = POItem(po_id=po2.id, product_id=p2.id, quantity_ordered=10, unit_cost=5000.0)
    db.add_all([poi1, poi2])
    db.commit()

    # 5. Sales Movements
    # For p1 (Rice): 25 sale events across 25 days -> sufficient
    base_time = clock.now()
    movements = []
    for i in range(1, 26):
        movements.append(
            StockMovement(
                product_id=p1.id,
                movement_type=MovementType.sale,
                quantity=-10,  # 10 units/day -> 250 units sold
                recorded_at=base_time - timedelta(days=i),
                recorded_by="system",
            )
        )
    db.add_all(movements)
    db.commit()

    return {
        "suppliers": {"s1": s1, "s2": s2, "s3": s3},
        "products": {"rice": p1, "headphones": p2, "oil": p3, "detergent": p4, "colgate": p5},
        "stock": {"sl1": sl1, "sl2": sl2, "sl3": sl3, "sl4": sl4, "sl5": sl5},
        "pos": {"po1": po1, "po2": po2, "po3": po3, "po4": po4, "po5": po5},
    }


@pytest.fixture
def test_app(db):
    """Create FastAPI test app with signals router mounted."""
    app = FastAPI()
    app.include_router(signals_router)

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)
