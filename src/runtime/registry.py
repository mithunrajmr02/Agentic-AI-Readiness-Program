from __future__ import annotations

from threading import Lock
from typing import Hashable


class InFlightRegistry:
    def __init__(self) -> None:
        self._active: set[Hashable] = set()
        self._lock = Lock()

    def try_start(self, key: Hashable) -> bool:
        with self._lock:
            if key in self._active:
                return False
            self._active.add(key)
            return True

    def finish(self, key: Hashable) -> None:
        with self._lock:
            self._active.discard(key)


in_flight = InFlightRegistry()


def register_runtime(app):
    """Wire and optionally start the runtime; integration calls this once."""
    if getattr(app.state, "runtime_registered", False):
        return getattr(app.state, "runtime_scheduler", None)

    from src.runtime.bus_wiring import wire_event_triggers
    from src.runtime.scheduler import build_scheduler, shutdown_scheduler

    wire_event_triggers()
    scheduler = build_scheduler()
    app.state.runtime_scheduler = scheduler
    app.state.runtime_registered = True

    if scheduler is not None:
        scheduler.start()
        app.add_event_handler("shutdown", lambda: shutdown_scheduler(scheduler))

    return scheduler