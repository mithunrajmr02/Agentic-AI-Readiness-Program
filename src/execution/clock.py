"""The only source of current time for WS-9's write path.

WS-0 owns the frozen `src/core/clock.py` (15-SHARED-CONTRACTS.md §2.1) with this
exact interface, but that module does not exist in this worktree yet. WS-9 may
not create files outside what it owns, so this is a same-interface, same-behaviour
shim living under `src/execution/` (WS-9's own package -- see the README
correction that moved `idempotency.py` here). Every WS-9 module imports time
through this file and NEVER calls `datetime.now()`, `date.today()`, `time.time()`
directly (hard rule, EXECUTION-RUNBOOK.md).

Filed as an integration request: docs/implementation/integration-requests/WS-9.md.
Once `src/core/clock.py` is published, the fix is a one-line import change in
each WS-9 module -- the function names and signatures already match.
"""
import os
from datetime import date, datetime, timedelta

_offset_days = 0


def now() -> datetime:
    """Real wall-clock time plus the active simulation offset."""
    return datetime.now() + timedelta(days=_offset_days)


def today() -> date:
    return now().date()


def offset_days() -> int:
    return _offset_days


def set_offset(days: int) -> None:
    """Simulation only. Gated by DEMO_MODE, matching the frozen contract."""
    if os.getenv("DEMO_MODE", "").lower() not in ("1", "true", "yes"):
        raise RuntimeError("clock.set_offset() requires DEMO_MODE to be enabled")
    global _offset_days
    _offset_days = days


def reset() -> None:
    global _offset_days
    _offset_days = 0
