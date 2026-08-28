from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, Literal

from src.runtime.registry import in_flight

Trigger = Literal["scheduled", "event", "manual", "backtest"]


def _load_run_pipeline() -> Callable[..., Any]:
    from src.agents.multi_agent.graph import run_pipeline

    return run_pipeline


def _normalise_product_ids(product_ids: Iterable[int] | None) -> tuple[int, ...]:
    if product_ids is None:
        return ()
    return tuple(sorted(set(product_ids)))


def run_trigger(
    trigger: Trigger,
    *,
    product_ids: Iterable[int] | None = None,
    run_id: str | None = None,
):
    normalised_ids = _normalise_product_ids(product_ids)
    scope = normalised_ids or ("all",)
    if not in_flight.try_start(scope):
        return None

    try:
        return _load_run_pipeline()(
            trigger,
            product_ids=list(normalised_ids) or None,
            run_id=run_id,
        )
    finally:
        in_flight.finish(scope)


def on_scheduled_tick(*, product_ids: Iterable[int] | None = None):
    return run_trigger("scheduled", product_ids=product_ids)


def on_event_trigger(payload: dict[str, Any]):
    product_id = payload.get("product_id")
    product_ids = [product_id] if isinstance(product_id, int) else None
    return run_trigger("event", product_ids=product_ids)


def on_manual_trigger(
    *,
    product_ids: Iterable[int] | None = None,
    run_id: str | None = None,
):
    return run_trigger("manual", product_ids=product_ids, run_id=run_id)


def on_backtest_trigger(
    *,
    product_ids: Iterable[int] | None = None,
    run_id: str | None = None,
):
    return run_trigger("backtest", product_ids=product_ids, run_id=run_id)