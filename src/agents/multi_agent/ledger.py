"""Local, append-only decision ledger.

Stand-in for the `decisions` / `agent_runs` tables
(15-SHARED-CONTRACTS.md §3.2, §8) -- both owned by WS-0/WS-4, both absent
from this worktree (no `models_governance.py`, no `models_analytics.py`).
WS-8 does not own `src/backend/models.py` and does not create new model
modules on WS-0's behalf, so `recorder` and `executor` append JSON lines to
a local file instead of writing rows to a table that does not exist.

Nothing here touches the application database. Replace wholesale once the
real tables and WS-4's `create_decision` / `request_approval` land -- see
docs/implementation/integration-requests/WS-8.md.
"""
import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from src.agents.multi_agent._clock import now as clock_now

_LOCK = threading.Lock()


def _path() -> Path:
    p = Path(os.getenv("STEWARD_LEDGER_PATH", "data/agent_ledger.jsonl"))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def append(record: Dict[str, Any]) -> None:
    """Append one JSON line. Never rewrites a previous line -- append-only,
    matching the real `decisions` table's own rule (§3.2: "No update path.
    Corrections are new rows")."""
    record = {"recorded_at": clock_now().isoformat(), **record}
    with _LOCK:
        with open(_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")


def is_key_consumed(idempotency_key: str) -> bool:
    """Precondition 6 (15-SHARED-CONTRACTS.md §9): has this key already
    produced a write? Re-checked at execution time, not trusted from
    proposal time."""
    p = _path()
    if not idempotency_key or not p.exists():
        return False
    with _LOCK:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if rec.get("kind") == "execution" and rec.get("idempotency_key") == idempotency_key:
                    return True
    return False


def consume_and_record(
    idempotency_key: str,
    *,
    product_id: Optional[int],
    quantity: Optional[int],
    supplier_id: Optional[int],
    total_cost: Optional[float],
) -> str:
    """Record a simulated execution and return a simulated PO number.

    Deliberately not `PO-YYYY-NNNN` (15-SHARED-CONTRACTS.md §2.2) -- that
    format is the real sequence WS-9's `next_id` owns, and this stream must
    not mint a number that could collide with or be mistaken for one.
    """
    po_number = f"PO-SIM-{abs(hash(idempotency_key)) % 1_000_000:06d}"
    append({
        "kind": "execution",
        "idempotency_key": idempotency_key,
        "product_id": product_id,
        "quantity": quantity,
        "supplier_id": supplier_id,
        "total_cost": total_cost,
        "po_number": po_number,
        "simulated": True,
    })
    return po_number
