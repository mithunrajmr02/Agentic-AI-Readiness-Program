"""Tests for overdue purchase order detector (WS-3)."""
import os
from datetime import timedelta
from src.backend.models import POStatus, PurchaseOrder
from src.core import clock
from src.signals.detectors import po_overdue


def test_po_overdue_fires_when_expected_delivery_is_past(db, sample_data):
    """PO with expected_delivery in past and status submitted must fire po_overdue."""
    po1 = sample_data["pos"]["po1"]  # expected 3 days ago
    candidate = po_overdue.detect(db, po1.id)

    assert candidate is not None
    assert candidate.signal_type == "po_overdue"
    assert candidate.po_id == po1.id
    assert candidate.severity == "high" or candidate.severity == "critical"
    assert candidate.evidence["days_late"] == 3
    assert candidate.evidence["po_number"] == po1.po_number
    assert "manual §10 item 4" in candidate.evidence["citation"]


def test_po_overdue_does_not_fire_on_received_po(db, sample_data):
    """A completed/received PO must never be flagged as overdue."""
    po2 = sample_data["pos"]["po2"]  # received
    candidate = po_overdue.detect(db, po2.id)
    assert candidate is None


def test_po_overdue_does_not_fire_on_future_po(db, sample_data):
    """A PO expected in the future must not fire."""
    po5 = sample_data["pos"]["po5"]  # expected in 5 days
    candidate = po_overdue.detect(db, po5.id)
    assert candidate is None


def test_po_overdue_does_not_fire_on_cancelled_po(db, sample_data):
    """A cancelled PO must not fire overdue signals."""
    po = sample_data["pos"]["po1"]
    po.status = POStatus.cancelled
    db.commit()

    candidate = po_overdue.detect(db, po.id)
    assert candidate is None


def test_po_overdue_detect_all(db, sample_data):
    """detect_all finds only the active overdue POs."""
    results = po_overdue.detect_all(db)
    overdue_po_ids = {c.po_id for c in results}

    assert sample_data["pos"]["po1"].id in overdue_po_ids
    assert sample_data["pos"]["po2"].id not in overdue_po_ids
    assert sample_data["pos"]["po5"].id not in overdue_po_ids


def test_po_overdue_responds_to_controllable_clock(db, sample_data, monkeypatch):
    """Advancing the simulation clock makes future POs become overdue."""
    monkeypatch.setenv("DEMO_MODE", "true")
    po5 = sample_data["pos"]["po5"]  # expected in +5 days

    # At t=0, po5 is not overdue
    assert po_overdue.detect(db, po5.id) is None

    # Advance clock by 6 days
    clock.set_offset(6)
    candidate = po_overdue.detect(db, po5.id)

    assert candidate is not None
    assert candidate.po_id == po5.id
    assert candidate.evidence["days_late"] == 1
