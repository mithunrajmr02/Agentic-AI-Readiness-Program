"""Tests for Signal Engine orchestration and event bus integration (WS-3)."""
from src.core import events
from src.signals.engine import (
    get_signal,
    list_signals,
    raise_signal,
    resolve_signal,
    run_detectors,
    setup_event_handlers,
)


def test_run_detectors_full_scan(db, sample_data):
    """Full scan executes all seven detectors across products, POs, and suppliers."""
    signals = run_detectors(db)

    assert len(signals) > 0
    signal_types = {s.signal_type for s in signals}

    # Should detect threshold breach, po overdue, supplier drift, capital drag, data insufficient
    assert "threshold_breach" in signal_types
    assert "po_overdue" in signal_types
    assert "supplier_drift" in signal_types
    assert "capital_drag" in signal_types
    assert "data_insufficient" in signal_types

    # Every signal must have a valid SIG- prefix ID
    for sig in signals:
        assert sig.signal_id.startswith("SIG-")
        assert sig.status == "open"
        assert sig.raised_at is not None


def test_run_detectors_scoped_by_product_ids(db, sample_data):
    """Product-scoped scan runs only on specified product IDs."""
    p_colgate = sample_data["products"]["colgate"]
    signals = run_detectors(db, product_ids=[p_colgate.id])

    for sig in signals:
        assert sig.product_id == p_colgate.id


def test_get_and_list_signals(db, sample_data):
    """get_signal and list_signals filtering."""
    p_rice = sample_data["products"]["rice"]
    sig = raise_signal(
        db,
        signal_type="threshold_breach",
        severity="high",
        product_id=p_rice.id,
        detected_from="Test breach",
        evidence={"on_hand": 10},
    )

    # Lookup by business ID
    fetched = get_signal(db, sig.signal_id)
    assert fetched is not None
    assert fetched.id == sig.id

    # Lookup by primary key string
    fetched_pk = get_signal(db, str(sig.id))
    assert fetched_pk is not None
    assert fetched_pk.signal_id == sig.signal_id

    # Filtered list
    open_breaches = list_signals(db, signal_type="threshold_breach", status="open")
    assert any(s.signal_id == sig.signal_id for s in open_breaches)

    resolved_breaches = list_signals(db, signal_type="threshold_breach", status="resolved")
    assert not any(s.signal_id == sig.signal_id for s in resolved_breaches)


def test_resolve_signal_emits_event(db, sample_data):
    """Resolving a signal updates its state and emits signal.resolved event."""
    emitted_events = []

    def handler(payload):
        emitted_events.append(payload)

    events.subscribe("signal.resolved", handler)

    p_rice = sample_data["products"]["rice"]
    sig = raise_signal(
        db,
        signal_type="threshold_breach",
        severity="medium",
        product_id=p_rice.id,
        detected_from="Test breach",
        evidence={"on_hand": 10},
    )

    resolved = resolve_signal(db, sig.signal_id, resolution="Replenished from supplier")
    assert resolved is not None
    assert resolved.status == "resolved"
    assert resolved.resolution == "Replenished from supplier"

    assert len(emitted_events) == 1
    assert emitted_events[0]["signal_id"] == sig.signal_id
    assert emitted_events[0]["resolution"] == "Replenished from supplier"


def test_setup_event_handlers_and_po_received(db, sample_data):
    """po.received event automatically resolves open po_overdue signals."""
    setup_event_handlers()

    po1 = sample_data["pos"]["po1"]
    sig = raise_signal(
        db,
        signal_type="po_overdue",
        severity="high",
        po_id=po1.id,
        detected_from="PO is overdue",
        evidence={"po_id": po1.id},
    )
    assert sig.status == "open"

    # Emit po.received with active test db
    events.emit("po.received", {"po_id": po1.id, "po_number": po1.po_number, "db": db})

    # Signal should now be resolved in db
    refreshed = get_signal(db, sig.signal_id)
    assert refreshed.status == "resolved"
    assert "received" in refreshed.resolution.lower()
