"""Shared Pydantic contracts, owned by WS-0 (doc 14 §WS-0, doc 15 §12).

Import the two frozen HTTP envelopes and their builders from here::

    from src.backend.contracts import success_envelope, error_envelope
"""
from src.backend.contracts.envelopes import (
    ErrorDetail,
    ErrorEnvelope,
    Meta,
    ResponseEnvelope,
    error_envelope,
    success_envelope,
)

__all__ = [
    "Meta",
    "ResponseEnvelope",
    "success_envelope",
    "ErrorDetail",
    "ErrorEnvelope",
    "error_envelope",
]
