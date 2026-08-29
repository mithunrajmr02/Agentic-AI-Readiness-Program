"""Test fixtures and database setup for WS-17 metrics tests."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.database import Base
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
from src.backend.models_analytics import AgentRun, MetricSnapshot, Signal
from src.backend.models_governance import Approval, AutonomyPolicy, Decision
from src.core import clock


@pytest.fixture
def test_db():
    """In-memory SQLite database session with all registered models."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Seed test data
        _seed_test_data(db)
        yield db
    finally:
        db.close()


def _seed_test_data(db):
    """Seed minimal test fixtures for metric computations."""
    now = clock.now()

    # User
    user = User(
        id=1,
        email="manager@retail.com",
        full_name="Anita Sharma",
        role="manager",
        hashed_password="hashed",
    )
    db.add(user)

    # Suppliers
    sup1 = Supplier(
        id=1,
        supplier_code="SUP-001",
        name="Reliable Agro",
        lead_time_days=5,
        is_active=True,
    )
    db.add(sup1)

    # Products
    p1 = Product(
        id=1,
        sku="SKU-GRO-0001",
        name="Basmati Rice 5kg",
        category=Category.grocery,
        unit_price=350.0,
        cost_price=280.0,
        reorder_point=20,
        reorder_quantity=100,
        supplier_id=1,
    )
    p2 = Product(
        id=2,
        sku="SKU-ELE-0001",
        name="Wireless Headphones",
        category=Category.electronics,
        unit_price=2500.0,
        cost_price=1800.0,
        reorder_point=10,
        reorder_quantity=25,
        supplier_id=1,
    )
    db.add_all([p1, p2])
    db.flush()

    # Stock Levels
    lvl1 = StockLevel(product_id=1, quantity_on_hand=30, quantity_reserved=0)
    lvl2 = StockLevel(product_id=2, quantity_on_hand=5, quantity_reserved=0)
    db.add_all([lvl1, lvl2])

    # Stock Movements (Sum matches quantity_on_hand for M-16 invariant)
    m1 = StockMovement(
        product_id=1,
        movement_type=MovementType.receipt,
        quantity=50,
        reference_number="PO-2026-0001",
        recorded_by="agent:replenishment",
        recorded_at=now,
    )
    m2 = StockMovement(
        product_id=1,
        movement_type=MovementType.sale,
        quantity=-20,
        reference_number="SALE-001",
        recorded_by="pos:terminal1",
        recorded_at=now,
    )
    m3 = StockMovement(
        product_id=2,
        movement_type=MovementType.receipt,
        quantity=5,
        reference_number="PO-2026-0002",
        recorded_by="agent:replenishment",
        recorded_at=now,
    )
    db.add_all([m1, m2, m3])

    # Signals
    s1 = Signal(
        signal_id="SIG-000001",
        signal_type="projected_breach",
        severity="high",
        product_id=1,
        raised_at=now,
        detected_from="stockout projection",
        sufficiency="sufficient",
        dedup_key="projected_breach:1",
        status="resolved",
    )
    s2 = Signal(
        signal_id="SIG-000002",
        signal_type="po_overdue",
        severity="critical",
        product_id=2,
        raised_at=now,
        detected_from="overdue delivery",
        sufficiency="sufficient",
        dedup_key="po_overdue:2",
        status="open",
    )
    db.add_all([s1, s2])

    # Decisions
    d1 = Decision(
        decision_id="DEC-000001",
        signal_id="SIG-000001",
        action_type="raise_po",
        status="executed",
        actor="agent:replenishment",
        proposed_at=now,
        executed_at=now,
        policy_citation="manual §10 line 113",
        autonomy_mode="autonomous",
    )
    d2 = Decision(
        decision_id="DEC-000002",
        signal_id="SIG-000002",
        action_type="adjust_reorder_point",
        status="executed",
        actor="agent:replenishment",
        proposed_at=now,
        executed_at=now,
        policy_citation="manual §3 line 35",
        escalation_reason="config_change",
        autonomy_mode="assisted",
    )
    d3 = Decision(
        decision_id="DEC-000003",
        signal_id=None,
        action_type="no_action",
        status="insufficient_data",
        actor="agent:replenishment",
        proposed_at=now,
        autonomy_mode="off",
    )
    db.add_all([d1, d2, d3])

    # Approvals
    app1 = Approval(
        approval_id="APR-000001",
        decision_id="DEC-000002",
        requested_at=now,
        requested_from_role="manager",
        decided_by_user_id=1,
        decided_at=now,
        outcome="approved",
        expires_at=now,
    )
    db.add(app1)

    # Agent Run
    run1 = AgentRun(
        run_id="RUN-000001",
        trigger="scheduled",
        started_at=now,
        status="completed",
        llm_numeric_violation=False,
    )
    db.add(run1)

    db.commit()
