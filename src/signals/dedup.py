"""Deduplication key generation for signals (WS-3).

15-SHARED-CONTRACTS.md §3.1 / §6.
Generates deterministic, collision-resistant dedup keys so repeated
detections of an ongoing condition update the existing open signal rather
than spamming the signals inbox.
"""
from typing import Optional


def dedup_key_for(
    signal_type: str,
    product_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    po_id: Optional[int] = None,
) -> str:
    """Generate a canonical deduplication key for a signal condition.

    Keys are scoped by the primary entity causing the signal:
      - PO signals: ``{signal_type}:po:{po_id}``
      - Product signals: ``{signal_type}:prod:{product_id}``
      - Supplier signals: ``{signal_type}:supp:{supplier_id}``
      - Global signals: ``{signal_type}:global``
    """
    if po_id is not None:
        return f"{signal_type}:po:{po_id}"
    if product_id is not None:
        return f"{signal_type}:prod:{product_id}"
    if supplier_id is not None:
        return f"{signal_type}:supp:{supplier_id}"
    return f"{signal_type}:global"
