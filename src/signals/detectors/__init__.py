"""Signal detectors package (WS-3).

15-SHARED-CONTRACTS.md §6.
Exports all seven deterministic anomaly detectors.
"""
from src.signals.detectors import (
    capital_drag,
    config_drift,
    data_insufficient,
    po_overdue,
    projected_breach,
    supplier_drift,
    threshold_breach,
)
from src.signals.detectors.base import SignalCandidate

ALL_DETECTORS = {
    "threshold_breach": threshold_breach,
    "projected_breach": projected_breach,
    "po_overdue": po_overdue,
    "config_drift": config_drift,
    "supplier_drift": supplier_drift,
    "capital_drag": capital_drag,
    "data_insufficient": data_insufficient,
}

__all__ = [
    "SignalCandidate",
    "threshold_breach",
    "projected_breach",
    "po_overdue",
    "config_drift",
    "supplier_drift",
    "capital_drag",
    "data_insufficient",
    "ALL_DETECTORS",
]
