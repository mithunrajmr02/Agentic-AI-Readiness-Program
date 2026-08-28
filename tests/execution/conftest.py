"""Fixtures for WS-9's own test suite (docs/implementation/14-PARALLEL-WORKSTREAMS.md
WS-9 "Tests: tests/execution/"). Fresh in-memory SQLite per test, exactly like
the graded suites' `db_session` fixture, but importing the WS-9 idempotency
table so `create_all` picks it up too.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.database import Base
from src.execution import clock
from src.execution import idempotency as idempotency_module  # noqa: F401 -- registers the table


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(autouse=True)
def _reset_clock():
    clock.reset()
    yield
    clock.reset()
