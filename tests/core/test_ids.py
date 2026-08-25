"""Contract tests for src/core/ids.py.

Asserts the sequential-ID contract (15-SHARED-CONTRACTS.md §2.2): the exact
zero-padded format, independent monotonic counters per prefix, and — the reason
this function exists instead of MAX()+1 — that concurrent callers never collide
or skip. PO numbers (PO-YYYY-NNNN) are deliberately NOT this function's job; they
stay in WS-9's inventory_service.
"""
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.backend.database import Base
from src.core import ids


@pytest.fixture
def ids_db(tmp_path, monkeypatch):
    # A real file-backed SQLite DB so concurrent threads use distinct connections.
    db_file = tmp_path / "ids_test.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)  # creates id_sequences (IdSequence registered on import)
    monkeypatch.setattr(ids, "SessionLocal", TestingSessionLocal)
    yield
    engine.dispose()


def test_format_is_prefix_dash_six_digits(ids_db):
    assert ids.next_id("SIG") == "SIG-000001"


def test_counter_is_monotonic_per_prefix(ids_db):
    assert ids.next_id("DEC") == "DEC-000001"
    assert ids.next_id("DEC") == "DEC-000002"
    assert ids.next_id("DEC") == "DEC-000003"


def test_counters_are_independent_across_prefixes(ids_db):
    assert ids.next_id("SIG") == "SIG-000001"
    assert ids.next_id("APR") == "APR-000001"
    assert ids.next_id("SIG") == "SIG-000002"
    assert ids.next_id("APR") == "APR-000002"


def test_width_is_configurable(ids_db):
    assert ids.next_id("RUN", width=4) == "RUN-0001"


def test_known_prefixes_render_as_documented(ids_db):
    # The four runtime formats from §2.2 (6-digit).
    assert ids.next_id("SIG") == "SIG-000001"
    assert ids.next_id("DEC") == "DEC-000001"
    assert ids.next_id("APR") == "APR-000001"
    assert ids.next_id("RUN") == "RUN-000001"


def test_concurrent_allocation_never_collides_or_skips(ids_db):
    threads, per_thread = 8, 25
    total = threads * per_thread

    def allocate_many(_):
        return [ids.next_id("SIG") for _ in range(per_thread)]

    with ThreadPoolExecutor(max_workers=threads) as pool:
        batches = list(pool.map(allocate_many, range(threads)))

    all_ids = [i for batch in batches for i in batch]
    # No duplicates.
    assert len(set(all_ids)) == total
    # Contiguous 1..total — no gaps, no lost updates.
    numbers = sorted(int(i.split("-")[1]) for i in all_ids)
    assert numbers == list(range(1, total + 1))
