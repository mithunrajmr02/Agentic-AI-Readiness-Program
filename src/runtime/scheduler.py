from __future__ import annotations

import os
from typing import Any

from src.runtime.triggers import on_scheduled_tick


def scheduler_enabled() -> bool:
    return os.getenv("SCHEDULER_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    } or os.getenv("RUNTIME_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def build_scheduler() -> Any | None:
    if not scheduler_enabled():
        return None

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "SCHEDULER_ENABLED requires the predeclared 'apscheduler' package"
        ) from exc

    scheduler = BackgroundScheduler()
    interval_seconds = os.getenv("SCHEDULER_INTERVAL_SECONDS")
    common = {
        "id": "steward-runtime-tick",
        "replace_existing": True,
        "coalesce": True,
        "max_instances": 1,
    }

    if interval_seconds is not None:
        seconds = int(interval_seconds)
        if seconds <= 0:
            raise ValueError("SCHEDULER_INTERVAL_SECONDS must be positive")
        scheduler.add_job(on_scheduled_tick, "interval", seconds=seconds, **common)
    else:
        hour = int(os.getenv("SCHEDULER_HOUR", "8"))
        minute = int(os.getenv("SCHEDULER_MINUTE", "0"))
        scheduler.add_job(on_scheduled_tick, "cron", hour=hour, minute=minute, **common)

    return scheduler


def shutdown_scheduler(scheduler: Any) -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)