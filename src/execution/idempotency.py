"""Idempotency key derivation + consumption (AD-15).

Owned by WS-9 -- its only consumer (docs/implementation/README.md's correction
to file 11's tree, which originally placed this under `src/backend/execution/`).

The frozen contract (15-SHARED-CONTRACTS.md §3.2) puts `idempotency_key` on the
`decisions` table (`models_governance.py`, WS-0). That table does not exist in
this worktree, so consumed keys are tracked in a small new table owned by this
module instead -- a new table in a new module is additive under `create_all`
(AD-3) and touches nothing WS-0 owns. See
docs/implementation/integration-requests/WS-9.md for the reconciliation note.
"""
from __future__ import annotations

import hashlib
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import Session

from src.backend.database import Base
from src.execution import clock


class ConsumedIdempotencyKey(Base):
    """One row per idempotency key that has ever been used for a write.

    A replay with the same key must not write twice; it returns the original
    `execution_ref` instead.
    """
    __tablename__ = "execution_idempotency_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(128), unique=True, nullable=False, index=True)
    execution_ref = Column(String(50), nullable=True)
    consumed_at = Column(DateTime, nullable=False)


def derive_key(*, signal_id, product_id, quantity, supplier_id, decision_id) -> str:
    """`hash(signal_id, product_id, quantity, supplier_id, decision_id)` per
    15-SHARED-CONTRACTS.md §9 / 08-AGENTIC-WORKFLOWS.md §10.
    """
    raw = f"{signal_id}|{product_id}|{quantity}|{supplier_id}|{decision_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def is_key_consumed(db: Session, key: str) -> bool:
    if not key:
        return False
    return db.query(ConsumedIdempotencyKey).filter(ConsumedIdempotencyKey.key == key).first() is not None


def get_consumed(db: Session, key: str) -> Optional[ConsumedIdempotencyKey]:
    return db.query(ConsumedIdempotencyKey).filter(ConsumedIdempotencyKey.key == key).first()


def consume_key(db: Session, key: str, *, execution_ref: Optional[str]) -> ConsumedIdempotencyKey:
    """Record a key as used. Consuming an already-consumed key is a no-op that
    returns the original record -- callers must check `is_key_consumed` first
    if a replay should be refused rather than silently accepted.
    """
    existing = get_consumed(db, key)
    if existing:
        return existing
    record = ConsumedIdempotencyKey(key=key, execution_ref=execution_ref, consumed_at=clock.now())
    db.add(record)
    db.flush()
    return record
