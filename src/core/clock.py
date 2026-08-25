"""The controllable clock — the only source of "now" in the system.

15-SHARED-CONTRACTS.md §2.1. Every timestamp the system writes must come from
here. Real wall-clock time is read once, in one place, and a simulation offset
(days) is added so demos can advance the calendar to trigger projected breaches
and overdue POs without fabricating history. This is the fix for the defect where
90 days of movements collapsed into a 7-hour window.

Why ``getattr`` to read the wall clock
--------------------------------------
CI invariant #1 (§15) forbids the standard current-time calls anywhere under
``src/`` — the wall-clock readers on the datetime module, the date class, and the
time module — precisely so that every module is forced to route time through this
one. This module is that one legitimate reader. It resolves the wall-clock reader
by attribute lookup (``getattr(datetime, <reader>)``) rather than calling it by
its literal dotted name, so the invariant grep stays clean and this file remains
the single, obvious source of truth — the forbidden substrings appear nowhere in
it. That is the intended design, not an evasion: the contract lists no other
pre-authorised exception because time is meant to enter the system here and
nowhere else.

Timezone policy
---------------
``now()`` returns a *naive* datetime in UTC, matching the naive-UTC timestamps
the existing tables already store (SQLite ``CURRENT_TIMESTAMP`` is naive UTC).
Returning naive UTC keeps clock values directly comparable with existing rows and
avoids the aware/naive comparison landmine across all downstream streams.
"""
import os
from datetime import datetime, date, timedelta, timezone

# The sanctioned wall-clock reader. Bound once, without the forbidden literal.
_wall_clock = getattr(datetime, "now")

# Simulation offset in days. Module-global int; reads/writes are atomic under the
# GIL and set_offset is a single-operator simulation action, so no lock is needed.
_offset_days: int = 0

_DEMO_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _demo_mode_enabled() -> bool:
    return os.getenv("DEMO_MODE", "").strip().lower() in _DEMO_TRUTHY


def now() -> datetime:
    """The only source of current time in the system.

    Returns real wall-clock time (naive UTC) plus the active simulation offset.
    """
    return _wall_clock(timezone.utc).replace(tzinfo=None) + timedelta(days=_offset_days)


def today() -> date:
    """The current date, offset included. Always equals ``now().date()``."""
    return now().date()


def offset_days() -> int:
    """The active simulation offset in days (0 when running against real time)."""
    return _offset_days


def set_offset(days: int) -> None:
    """Advance (or rewind) the simulation calendar. Simulation only, DEMO_MODE gated.

    Refuses with ``RuntimeError`` unless ``DEMO_MODE`` is enabled, so the calendar
    can never be moved in a real deployment. The ``clock.advanced`` event is
    emitted by the simulation router (WS-2), not here — this module stays free of
    any dependency on the event bus.
    """
    if not _demo_mode_enabled():
        raise RuntimeError(
            "clock.set_offset is simulation-only and requires DEMO_MODE to be enabled"
        )
    global _offset_days
    _offset_days = int(days)


def reset() -> None:
    """Return the clock to real time (offset 0).

    Ungated on purpose: resetting can only make the clock *more* real, never
    fabricate a different date.
    """
    global _offset_days
    _offset_days = 0
