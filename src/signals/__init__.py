"""Signal Engine package (WS-3).

15-SHARED-CONTRACTS.md §6 / 14-PARALLEL-WORKSTREAMS.md WS-3.
"""
from src.signals.dedup import dedup_key_for
from src.signals.engine import (
    get_signal,
    list_signals,
    raise_signal,
    resolve_signal,
    run_detectors,
    setup_event_handlers,
)

__all__ = [
    "run_detectors",
    "raise_signal",
    "resolve_signal",
    "get_signal",
    "list_signals",
    "dedup_key_for",
    "setup_event_handlers",
]
