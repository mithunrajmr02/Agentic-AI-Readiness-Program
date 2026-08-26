"""Tests for deduplication and idempotency behavior (WS-3)."""
from src.backend.models_analytics import Signal
from src.signals.dedup import dedup_key_for
from src.signals.engine import raise_signal, resolve_signal


def test_dedup_key_generation_formats():
    """Verify dedup key scoping formats for various entities."""
    assert dedup_key_for("threshold_breach", product_id=42) == "threshold_breach:prod:42"
    assert dedup_key_for("supplier_drift", supplier_id=7) == "supplier_drift:supp:7"
    assert dedup_key_for("po_overdue", po_id=99) == "po_overdue:po:99"
    assert dedup_key_for("global_drift") == "global_drift:global"


def test_dedup_collision_updates_existing_open_signal(db, sample_data):
    """Re-raising an existing open signal updates the row without creating a duplicate."""
    p_rice = sample_data["products"]["rice"]

    sig1 = raise_signal(
        db,
        signal_type="threshold_breach",
        severity="medium",
        product_id=p_rice.id,
        detected_from="Initial breach detected at 40 units",
        evidence={"quantity": 40},
    )

    initial_sig_id = sig1.signal_id
    initial_raised_at = sig1.raised_at

    # Second detection of the same condition (now lower on-hand, higher severity)
    sig2 = raise_signal(
        db,
        signal_type="threshold_breach",
        severity="critical",
        product_id=p_rice.id,
        detected_from="Escalated breach detected at 0 units",
        evidence={"quantity": 0},
    )

    assert sig2.signal_id == initial_sig_id
    assert sig2.severity == "critical"
    assert sig2.detected_from == "Escalated breach detected at 0 units"

    # Verify database has exactly 1 row
    total_signals = db.query(Signal).filter(Signal.dedup_key == sig1.dedup_key).count()
    assert total_signals == 1


def test_dedup_allows_new_signal_after_resolution(db, sample_data):
    """When a previous signal is resolved, a subsequent detection creates a fresh open signal."""
    p_rice = sample_data["products"]["rice"]

    sig1 = raise_signal(
        db,
        signal_type="threshold_breach",
        severity="medium",
        product_id=p_rice.id,
        detected_from="First breach",
        evidence={"quantity": 40},
    )

    first_sig_id = sig1.signal_id

    # Resolve the first signal
    resolve_signal(db, first_sig_id, resolution="Replenished by PO-2026-0001")

    # A new breach occurs later
    sig2 = raise_signal(
        db,
        signal_type="threshold_breach",
        severity="medium",
        product_id=p_rice.id,
        detected_from="Second breach after replenishment",
        evidence={"quantity": 38},
    )

    assert sig2.signal_id != first_sig_id
    assert sig2.status == "open"

    # Database now contains 2 rows: one resolved, one open
    total_signals = db.query(Signal).filter(Signal.dedup_key == sig1.dedup_key).count()
    assert total_signals == 2
