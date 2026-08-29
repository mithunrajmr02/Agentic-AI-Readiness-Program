"""Re-export and wrap the system clock for WS-9 execution package.

Delegates directly to the unified frozen clock in src/core/clock.py, while
allowing test monkeypatching of clock.now() / clock.today().
"""
from datetime import date, datetime
from src.core import clock as _core_clock


def now() -> datetime:
    return _core_clock.now()


def today() -> date:
    return now().date()


def offset_days() -> int:
    return _core_clock.offset_days()


def set_offset(days: int) -> None:
    _core_clock.set_offset(days)


def reset() -> None:
    _core_clock.reset()


__all__ = ["now", "today", "offset_days", "set_offset", "reset"]

