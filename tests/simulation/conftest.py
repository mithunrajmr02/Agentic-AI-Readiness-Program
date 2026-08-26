"""Fixtures for the simulation harness tests.

Two things here matter more than convenience.

**Every test gets its own in-memory database.** ``src.backend.database`` rewrites
relative SQLite URLs back to the real ``inventory.db``, so a test that reached for
``SessionLocal()`` would seed ninety days of synthetic history into the developer's
working database. Nothing in ``src/simulation`` opens its own session for exactly
this reason, and these fixtures are what make that discipline testable.

**The clock is reset around every test.** ``clock``'s offset is module-global. A
test that moved it and failed before restoring it would leak a shifted calendar
into every suite that ran afterwards, including the graded ones. The autouse
fixture makes that impossible.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


def make_session():
    """A fresh in-memory database with the full Steward schema."""
    from src.backend.database import Base
    import src.backend.models  # noqa: F401 -- the existing 8 tables
    from src.backend import models_registry  # noqa: F401 -- the WS-0 tables

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


@pytest.fixture
def db():
    session = make_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def real_clock():
    """Guarantee every test starts and ends at offset 0."""
    from src.core import clock

    clock.reset()
    yield
    clock.reset()


@pytest.fixture
def demo_mode(monkeypatch):
    """Enable the DEMO_MODE gate for tests that need the time machine.

    ``.env`` ships without a ``DEMO_MODE`` key, so this is also the only way the
    clock endpoints can currently be exercised at all — see the integration
    request filed in ``docs/implementation/integration-requests/WS-2.md``.
    """
    monkeypatch.setenv("DEMO_MODE", "true")
    return True


@pytest.fixture
def no_demo_mode(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    return False


@pytest.fixture
def raise_signals(db):
    """Write synthetic ``signals`` rows so ``verify_scenario`` has something to read.

    WS-3 owns detection. Until it lands, the only way to test the verification
    contract is to state the signals directly — which is also the cleanest way to
    test it afterwards, since a verifier should be exercised against inputs it did
    not produce.

    Entries use the same ``{signal_type, sku | supplier_code, severity}`` shape as a
    scenario's ``expected_signals``, so a test can hand ``expected_signals``
    straight back in and assert the round trip.
    """
    from src.backend.models import Product, Supplier
    from src.backend.models_analytics import Signal
    from src.core import clock

    def _raise(entries, *, status="open"):
        written = []
        for index, entry in enumerate(entries, start=1):
            product_id = None
            if entry.get("sku"):
                product = db.query(Product).filter(Product.sku == entry["sku"]).first()
                product_id = product.id if product else None
            supplier_id = None
            if entry.get("supplier_code"):
                supplier = (
                    db.query(Supplier)
                    .filter(Supplier.supplier_code == entry["supplier_code"])
                    .first()
                )
                supplier_id = supplier.id if supplier else None

            signal = Signal(
                signal_id=f"SIG-{index:06d}",
                signal_type=entry["signal_type"],
                severity=entry["severity"],
                product_id=product_id,
                supplier_id=supplier_id,
                raised_at=clock.now(),
                detected_from="synthetic test fixture",
                sufficiency=entry.get("sufficiency", "sufficient"),
                dedup_key=f"test:{entry['signal_type']}:{index}",
                status=status,
            )
            db.add(signal)
            written.append(signal)
        db.commit()
        return written

    return _raise
