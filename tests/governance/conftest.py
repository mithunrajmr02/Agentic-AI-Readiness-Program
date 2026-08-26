"""Fixtures and test setup for governance tests (WS-4)."""
from datetime import timedelta
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.database import Base, get_db
import src.backend.models  # register existing models
from src.backend import models_registry  # register new models
from src.backend.models import User
from src.backend.models_governance import Approval, Decision
from src.backend.routers.approvals import router as approvals_router
from src.backend.routers.auth import create_access_token, get_password_hash
from src.backend.routers.decisions import router as decisions_router
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
def users(db):
    """Seed test users: manager, staff, and agent."""
    manager = User(
        email="manager@retail.com",
        full_name="Store Manager",
        hashed_password=get_password_hash("pass123"),
        role="manager",
        is_active=True,
    )
    staff = User(
        email="staff@retail.com",
        full_name="Warehouse Staff",
        hashed_password=get_password_hash("pass123"),
        role="staff",
        is_active=True,
    )
    agent = User(
        email="agent@retail.com",
        full_name="Agent Replenisher",
        hashed_password=get_password_hash("pass123"),
        role="agent",
        is_active=True,
    )
    db.add_all([manager, staff, agent])
    db.commit()
    db.refresh(manager)
    db.refresh(staff)
    db.refresh(agent)
    return {"manager": manager, "staff": staff, "agent": agent}


@pytest.fixture
def manager_token(users):
    return create_access_token(
        data={"sub": users["manager"].email, "role": users["manager"].role},
        expires_delta=timedelta(hours=1),
    )


@pytest.fixture
def staff_token(users):
    return create_access_token(
        data={"sub": users["staff"].email, "role": users["staff"].role},
        expires_delta=timedelta(hours=1),
    )


@pytest.fixture
def agent_token(users):
    return create_access_token(
        data={"sub": users["agent"].email, "role": users["agent"].role},
        expires_delta=timedelta(hours=1),
    )


@pytest.fixture
def test_app(db):
    """Create a FastAPI test app with governance routers mounted."""
    app = FastAPI()
    app.include_router(decisions_router)
    app.include_router(approvals_router)

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)
