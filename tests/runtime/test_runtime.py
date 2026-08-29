from concurrent.futures import ThreadPoolExecutor
from threading import Event
from types import SimpleNamespace

import pytest

from src.runtime import bus_wiring, registry, scheduler, triggers


@pytest.mark.parametrize(
    ("invoke", "expected_trigger", "expected_ids", "expected_run_id"),
    [
        (lambda: triggers.on_scheduled_tick(product_ids=[2, 1]), "scheduled", [1, 2], None),
        (lambda: triggers.on_event_trigger({"product_id": 3}), "event", [3], None),
        (
            lambda: triggers.on_manual_trigger(product_ids=[4], run_id="RUN-000004"),
            "manual",
            [4],
            "RUN-000004",
        ),
        (
            lambda: triggers.on_backtest_trigger(product_ids=[5], run_id="RUN-000005"),
            "backtest",
            [5],
            "RUN-000005",
        ),
    ],
)
def test_each_trigger_fires_pipeline_once(
    monkeypatch, invoke, expected_trigger, expected_ids, expected_run_id
):
    calls = []

    def fake_pipeline(trigger, *, product_ids, run_id):
        calls.append((trigger, product_ids, run_id))
        return {"trigger": trigger}

    monkeypatch.setattr(triggers, "_load_run_pipeline", lambda: fake_pipeline)

    assert invoke() == {"trigger": expected_trigger}
    assert calls == [(expected_trigger, expected_ids, expected_run_id)]


def test_scheduler_is_off_by_default(monkeypatch):
    monkeypatch.delenv("SCHEDULER_ENABLED", raising=False)

    assert scheduler.build_scheduler() is None


def test_concurrent_triggers_do_not_double_execute(monkeypatch):
    entered = Event()
    release = Event()
    calls = []

    def blocking_pipeline(trigger, *, product_ids, run_id):
        calls.append((trigger, product_ids, run_id))
        entered.set()
        assert release.wait(timeout=2)
        return "completed"

    monkeypatch.setattr(triggers, "_load_run_pipeline", lambda: blocking_pipeline)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(triggers.on_manual_trigger, product_ids=[7])
        assert entered.wait(timeout=2)
        second = pool.submit(triggers.on_event_trigger, {"product_id": 7})
        assert second.result(timeout=2) is None
        release.set()
        assert first.result(timeout=2) == "completed"

    assert len(calls) == 1


def test_event_handler_does_not_raise(monkeypatch):
    def fail(_payload):
        raise RuntimeError("pipeline failed")

    monkeypatch.setattr(bus_wiring, "on_event_trigger", fail)

    bus_wiring._handle_signal_raised({"product_id": 1})


def test_register_runtime_is_idempotent(monkeypatch):
    app = SimpleNamespace(state=SimpleNamespace(), add_event_handler=lambda *args: None)
    wired = []

    monkeypatch.setattr(bus_wiring, "wire_event_triggers", lambda: wired.append(True))
    monkeypatch.setattr(scheduler, "build_scheduler", lambda: None)

    assert registry.register_runtime(app) is None
    assert registry.register_runtime(app) is None
    assert wired == [True]