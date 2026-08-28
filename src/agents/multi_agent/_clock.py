"""Local clock shim -- WS-8 does not own and cannot create `src/core/clock.py`
(15-SHARED-CONTRACTS.md §2.1, owned by WS-0; not present in this worktree).

This module exists solely so this stream is not scattering bare
`datetime.now()` calls across `nodes/` and `ledger.py`. It mirrors the real
contract's two functions exactly, so every call site becomes a one-line
import swap the moment `src/core/clock.py` lands -- see
docs/implementation/integration-requests/WS-8.md, which asks for it.

Every other module in this package that needs "now" imports from here, not
from `datetime` directly, so this file is the only place in this stream's
code the grep-enforced ban on `datetime.now()` is technically touched, and it
is touched in exactly one place, for a documented reason, pending the real
clock.
"""
from datetime import datetime, date


def now() -> datetime:
    return datetime.now()


def today() -> date:
    return date.today()
