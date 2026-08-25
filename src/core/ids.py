"""Concurrency-safe sequential business identifiers.

15-SHARED-CONTRACTS.md §2.2. Produces IDs like ``SIG-000045``, ``DEC-000123``,
``APR-000012``, ``RUN-000078`` — a prefix and a zero-padded counter that is
monotonic and gap-free per prefix.

Why not MAX(id)+1
-----------------
The existing ``inventory_service._next_sequence`` counts rows and adds one, which
is only correct while nothing is ever deleted: delete a row and the next call
reuses a live number, producing a duplicate and a permanent HTTP 500. This
function keeps a dedicated counter table instead, so the next value never depends
on how many rows currently exist.

Locking model
-------------
The whole system runs in one process (the event bus is in-process), so the
counter row is "locked" with a module-level ``threading.Lock``: it serializes the
read-modify-write across the FastAPI, agent and MCP threads, and each allocation
commits in its own transaction. On SQLite there is no row-level lock to take, so
the process-level lock *is* the row lock. Numbers may have gaps if a transaction
rolls back — that is fine; the contract requires uniqueness and monotonicity, not
density.

PO numbers (``PO-YYYY-NNNN``) are intentionally out of scope: they are generated
by WS-9's ``inventory_service.generate_po_number`` and must keep their existing
year-scoped shape.
"""
import threading

from sqlalchemy import Column, Integer, String

from src.backend.database import Base, SessionLocal

_lock = threading.Lock()


class IdSequence(Base):
    """One row per ID prefix, holding the last-issued counter value.

    Owned by WS-0. String primary key, no timestamps — nothing here needs
    a database-side timestamp default, and there is no status column to cage.
    """

    __tablename__ = "id_sequences"

    prefix = Column(String(10), primary_key=True)
    current_value = Column(Integer, nullable=False, default=0)


def next_id(prefix: str, width: int = 6) -> str:
    """Concurrency-safe sequential ID. Locks the counter row.

    Returns ``f"{prefix}-{n:0{width}d}"`` where ``n`` is the next value for that
    prefix. Safe to call concurrently from any thread.
    """
    with _lock:
        session = SessionLocal()
        try:
            row = session.get(IdSequence, prefix)
            if row is None:
                row = IdSequence(prefix=prefix, current_value=1)
                session.add(row)
            else:
                row.current_value += 1
            value = row.current_value
            session.commit()
        finally:
            session.close()
    return f"{prefix}-{value:0{width}d}"
