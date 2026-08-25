"""Contract tests for src/core/clock.py.

Asserts the controllable clock (15-SHARED-CONTRACTS.md §2.1): a real wall-clock
base plus a simulation offset, with the offset gated behind DEMO_MODE. This is
the module that fixes the "90 days collapsed into 7 hours" defect — every
timestamp in the system must come from here.
"""
from datetime import datetime, timedelta

import pytest

from src.core import clock


@pytest.fixture(autouse=True)
def _clean_clock(monkeypatch):
    # Each test starts from real time with DEMO_MODE unset.
    monkeypatch.delenv("DEMO_MODE", raising=False)
    clock.reset()
    yield
    clock.reset()


def test_now_returns_naive_utc_datetime_close_to_real_time():
    n = clock.now()
    assert isinstance(n, datetime)
    # Naive (no tzinfo) so it compares cleanly with the existing func.now() columns.
    assert n.tzinfo is None


def test_today_is_the_date_of_now():
    assert clock.today() == clock.now().date()


def test_offset_defaults_to_zero():
    assert clock.offset_days() == 0


def test_set_offset_requires_demo_mode():
    with pytest.raises(RuntimeError):
        clock.set_offset(7)
    # Offset must be unchanged after a refused set.
    assert clock.offset_days() == 0


def test_set_offset_advances_now_by_exactly_that_many_days(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    clock.set_offset(0)
    a = clock.now()
    clock.set_offset(10)
    b = clock.now()
    delta = b - a
    # Both reads happen within milliseconds; the difference is the offset change.
    assert timedelta(days=10) - timedelta(seconds=2) <= delta <= timedelta(days=10) + timedelta(seconds=2)
    assert clock.offset_days() == 10


def test_set_offset_advances_today(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    base = clock.today()
    clock.set_offset(5)
    assert (clock.today() - base).days == 5


def test_reset_returns_to_real_time(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    clock.set_offset(30)
    assert clock.offset_days() == 30
    clock.reset()
    assert clock.offset_days() == 0


def test_demo_mode_truthy_variants(monkeypatch):
    for val in ("1", "true", "TRUE", "yes", "on"):
        clock.reset()
        monkeypatch.setenv("DEMO_MODE", val)
        clock.set_offset(3)
        assert clock.offset_days() == 3


def test_demo_mode_falsy_variants_are_refused(monkeypatch):
    for val in ("0", "false", "no", "off", ""):
        monkeypatch.setenv("DEMO_MODE", val)
        with pytest.raises(RuntimeError):
            clock.set_offset(3)
