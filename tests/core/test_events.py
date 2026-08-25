"""Contract tests for src/core/events.py.

Asserts the synchronous in-process event bus (15-SHARED-CONTRACTS.md §2.3):
ordered delivery, exact-type matching, and the critical invariant that a handler
which raises must not abort delivery to the others or propagate out of emit().
"""
from src.core import events


def setup_function():
    events.reset()


def teardown_function():
    events.reset()


def test_subscriber_receives_emitted_payload():
    received = []
    events.subscribe("stock.movement_recorded", lambda p: received.append(p))
    payload = {"product_id": 1, "movement_type": "sale", "quantity": 5}
    events.emit("stock.movement_recorded", payload)
    assert received == [payload]


def test_handlers_fire_in_subscription_order():
    order = []
    events.subscribe("signal.raised", lambda p: order.append("first"))
    events.subscribe("signal.raised", lambda p: order.append("second"))
    events.subscribe("signal.raised", lambda p: order.append("third"))
    events.emit("signal.raised", {"signal_id": "SIG-000001"})
    assert order == ["first", "second", "third"]


def test_emit_to_type_with_no_subscribers_is_a_noop():
    # Must not raise.
    events.emit("decision.executed", {"decision_id": "DEC-000001"})


def test_handler_exception_does_not_abort_delivery_or_propagate():
    ran = []

    def bad_handler(_payload):
        raise ValueError("handler blew up")

    def good_handler(_payload):
        ran.append("good")

    events.subscribe("po.received", bad_handler)
    events.subscribe("po.received", good_handler)

    # emit must swallow the handler error (wrap + log) and still call good_handler.
    events.emit("po.received", {"po_id": 1})
    assert ran == ["good"]


def test_event_types_are_isolated():
    a_calls, b_calls = [], []
    events.subscribe("clock.advanced", lambda p: a_calls.append(p))
    events.subscribe("decision.refused", lambda p: b_calls.append(p))
    events.emit("clock.advanced", {"from_offset": 0, "to_offset": 7})
    assert len(a_calls) == 1
    assert b_calls == []


def test_reset_clears_subscribers():
    calls = []
    events.subscribe("signal.resolved", lambda p: calls.append(p))
    events.reset()
    events.emit("signal.resolved", {"signal_id": "SIG-000001"})
    assert calls == []
