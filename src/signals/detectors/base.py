"""Base definitions for signal detectors (WS-3).

15-SHARED-CONTRACTS.md §6.
"""
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class SignalCandidate:
    """A detected anomaly ready to be recorded/updated in the database."""

    signal_type: str
    severity: str
    product_id: Optional[int]
    supplier_id: Optional[int]
    po_id: Optional[int]
    detected_from: str
    evidence: dict[str, Any]
    sufficiency: str
    dedup_key: str
