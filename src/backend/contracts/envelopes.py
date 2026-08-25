"""The two frozen HTTP envelopes every Steward router shares (doc 15 §12).

WS-0 publishes these once so the UI's API client is written against a single
shape and no stream hand-rolls its own. Nothing here computes a business number
— it only carries one, together with the provenance and disclosure marks that
stop a synthetic figure being exported stripped of its caveat (§12.2).
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.core import clock
from src.core.errors import StewardError


# --- §12.2 response envelope -------------------------------------------------

class Meta(BaseModel):
    """The four keys that accompany every payload (doc 15 §12.2)."""

    computed_at: datetime
    clock_offset_days: int
    provenance: dict[str, str] = Field(default_factory=dict)
    data_disclosure: str


class ResponseEnvelope(BaseModel):
    """``{"data": ..., "meta": {...}}`` — the success shape."""

    data: Any
    meta: Meta


def success_envelope(
    data: Any,
    *,
    provenance: Optional[dict[str, str]] = None,
    data_disclosure: str,
    computed_at: Optional[datetime] = None,
    clock_offset_days: Optional[int] = None,
) -> ResponseEnvelope:
    """Wrap ``data`` in the frozen envelope.

    ``computed_at`` and ``clock_offset_days`` default from ``src.core.clock`` so
    every response reports the demo clock it was computed under. ``provenance``
    and ``data_disclosure`` are the caller's to state — they know their numbers.
    """
    return ResponseEnvelope(
        data=data,
        meta=Meta(
            computed_at=computed_at if computed_at is not None else clock.now(),
            clock_offset_days=(
                clock_offset_days if clock_offset_days is not None else clock.offset_days()
            ),
            provenance=provenance or {},
            data_disclosure=data_disclosure,
        ),
    )


# --- §12.3 error envelope ----------------------------------------------------

class ErrorDetail(BaseModel):
    """The five keys of an error body (doc 15 §12.3).

    ``needed`` and ``have`` turn "cannot compute" into a finding; they are
    required on ``insufficient_data`` and null elsewhere.
    """

    code: str
    message: str
    needed: Optional[str] = None
    have: Optional[str] = None
    citation: Optional[str] = None


class ErrorEnvelope(BaseModel):
    """``{"error": {...}}`` — the failure shape."""

    error: ErrorDetail


def error_envelope(exc: StewardError) -> ErrorEnvelope:
    """Map a :class:`~src.core.errors.StewardError` into the frozen error body.

    ``code`` comes from the exception's ``code`` class attribute; ``needed`` /
    ``have`` / ``citation`` are pulled off whichever subclass carries them
    (InsufficientData, PolicyDenied) and are null on the rest.
    """
    return ErrorEnvelope(
        error=ErrorDetail(
            code=exc.code,
            message=str(exc),
            needed=getattr(exc, "needed", None),
            have=getattr(exc, "have", None),
            citation=getattr(exc, "citation", None),
        )
    )
