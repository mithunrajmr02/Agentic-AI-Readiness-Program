"""Sourcing and supplier intelligence package (WS-7).

15-SHARED-CONTRACTS.md §10 / 14-PARALLEL-WORKSTREAMS.md §WS-7.
Exports supplier selection, scorecard derivation, and drift detection capabilities.
"""
from src.sourcing.drift import (
    compute_supplier_drift,
    detect_supplier_drift,
    list_supplier_drifts,
)
from src.sourcing.scorecard import Scorecard, scorecard
from src.sourcing.selection import SupplierChoice, select_supplier

__all__ = [
    "Scorecard",
    "scorecard",
    "SupplierChoice",
    "select_supplier",
    "compute_supplier_drift",
    "detect_supplier_drift",
    "list_supplier_drifts",
]
