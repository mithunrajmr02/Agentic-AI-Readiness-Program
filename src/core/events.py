"""The synchronous, in-process event bus.

15-SHARED-CONTRACTS.md §2.3. There is no broker and no async machinery: emit()
calls every subscriber for the exact event type, in subscription order, on the
calling thread, and returns when they are done.

The one hard rule is that **a handler must never break the emitter**. A signal
handler that raises must not stop a downstream decision handler from running, and
must never turn a successful ``stock.movement_recorded`` into a 500. So emit()
wraps each handler call, logs any exception, and moves on. Delivery is ordered
and total; failures are contained and observable in the logs.
"""
from typing import Callable

import structlog

logger = structlog.get_logger()

# event_type -> handlers, in subscription order. A plain dict preserves insertion
# order and each list preserves call order, which together give ordered delivery.
_subscribers: dict[str, list[Callable[[dict], None]]] = {}


def subscribe(event_type: str, handler: Callable[[dict], None]) -> None:
    """Register ``handler`` to be called (synchronously) on every ``event_type`` emit."""
    _subscribers.setdefault(event_type, []).append(handler)


def emit(event_type: str, payload: dict) -> None:
    """Call every subscriber for ``event_type`` in order, passing ``payload``.

    A handler that raises is logged and skipped; the exception never propagates
    out of emit() and never prevents the remaining handlers from running.
    """
    for handler in _subscribers.get(event_type, []):
        try:
            handler(payload)
        except Exception as exc:  # noqa: BLE001 -- containment is the whole point
            logger.exception(
                "event_handler_failed",
                event_type=event_type,
                handler=getattr(handler, "__name__", repr(handler)),
                error=str(exc),
            )


def reset() -> None:
    """Drop all subscriptions.

    Supports hermetic tests and demo-scenario reloads (WS-2), where the bus must
    start from a clean slate.
    """
    _subscribers.clear()
