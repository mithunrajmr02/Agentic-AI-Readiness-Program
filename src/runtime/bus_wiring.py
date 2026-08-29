from __future__ import annotations

from typing import Any

import structlog

from src.runtime.triggers import on_event_trigger, on_scheduled_tick

logger = structlog.get_logger()


def _handle_signal_raised(payload: dict[str, Any]) -> None:
    try:
        on_event_trigger(payload)
    except Exception as exc:
        logger.exception("runtime_event_trigger_failed", error=str(exc))


def _handle_clock_advanced(payload: dict[str, Any]) -> None:
    try:
        on_scheduled_tick()
    except Exception as exc:
        logger.exception("runtime_clock_trigger_failed", error=str(exc))


def wire_event_triggers() -> None:
    from src.core.events import subscribe

    subscribe("signal.raised", _handle_signal_raised)
    subscribe("clock.advanced", _handle_clock_advanced)