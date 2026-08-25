"""WS-0 contract tests — the two frozen HTTP envelopes (doc 15 §12.2 / §12.3).

These envelopes are published once by WS-0 so every stream's router and the UI's
API client share one shape. The tests pin the exact field names and the mapping
from the src.core.errors taxonomy into the error envelope.
"""
from datetime import datetime

import pytest

from src.backend.contracts import (
    ErrorDetail,
    ErrorEnvelope,
    Meta,
    ResponseEnvelope,
    error_envelope,
    success_envelope,
)
from src.core import clock
from src.core.errors import InsufficientData, PolicyDenied, StewardError


# --- §12.2 response envelope -------------------------------------------------

def test_meta_has_exactly_the_four_frozen_keys():
    meta = Meta(
        computed_at=datetime(2026, 8, 25, 8, 0, 0),
        clock_offset_days=0,
        provenance={"recommended_qty": "computed"},
        data_disclosure="synthetic",
    )
    assert set(meta.model_dump().keys()) == {
        "computed_at",
        "clock_offset_days",
        "provenance",
        "data_disclosure",
    }


def test_success_envelope_shape_is_data_plus_meta():
    env = success_envelope(
        {"recommended_qty": 120},
        provenance={"recommended_qty": "computed"},
        data_disclosure="synthetic",
    )
    assert isinstance(env, ResponseEnvelope)
    dumped = env.model_dump()
    assert set(dumped.keys()) == {"data", "meta"}
    assert dumped["data"] == {"recommended_qty": 120}
    assert dumped["meta"]["provenance"] == {"recommended_qty": "computed"}
    assert dumped["meta"]["data_disclosure"] == "synthetic"


def test_success_envelope_defaults_timestamps_from_the_clock():
    clock.reset()
    env = success_envelope({}, provenance={}, data_disclosure="synthetic")
    assert isinstance(env.meta.computed_at, datetime)
    assert env.meta.clock_offset_days == clock.offset_days()


def test_success_envelope_accepts_explicit_timestamps():
    when = datetime(2026, 1, 2, 3, 4, 5)
    env = success_envelope(
        {"x": 1},
        provenance={},
        data_disclosure="real",
        computed_at=when,
        clock_offset_days=7,
    )
    assert env.meta.computed_at == when
    assert env.meta.clock_offset_days == 7


def test_response_envelope_serialises_computed_at_as_iso_naive():
    env = success_envelope(
        {},
        provenance={},
        data_disclosure="synthetic",
        computed_at=datetime(2026, 8, 25, 8, 0, 0),
        clock_offset_days=0,
    )
    assert env.model_dump(mode="json")["meta"]["computed_at"] == "2026-08-25T08:00:00"


# --- §12.3 error envelope ----------------------------------------------------

def test_error_detail_has_exactly_the_five_frozen_keys():
    detail = ErrorDetail(
        code="insufficient_data",
        message="Cannot compute demand for SKU-PRC-0001",
        needed="14 sale events across 21 days",
        have="0 sale events",
        citation="manual §3 line 35",
    )
    assert set(detail.model_dump().keys()) == {
        "code",
        "message",
        "needed",
        "have",
        "citation",
    }


def test_error_envelope_wraps_detail_under_error_key():
    env = error_envelope(StewardError("boom"))
    assert isinstance(env, ErrorEnvelope)
    dumped = env.model_dump()
    assert set(dumped.keys()) == {"error"}
    assert dumped["error"]["code"] == "steward_error"
    assert dumped["error"]["needed"] is None
    assert dumped["error"]["have"] is None
    assert dumped["error"]["citation"] is None


def test_error_envelope_maps_insufficient_data_needed_and_have():
    exc = InsufficientData(
        what="demand for SKU-PRC-0001",
        needed="14 sale events across 21 days",
        have="0 sale events",
    )
    dumped = error_envelope(exc).model_dump()
    assert dumped["error"]["code"] == "insufficient_data"
    assert dumped["error"]["needed"] == "14 sale events across 21 days"
    assert dumped["error"]["have"] == "0 sale events"
    assert dumped["error"]["citation"] is None


def test_error_envelope_maps_policy_denied_citation():
    exc = PolicyDenied(rule="R4: value_threshold", citation="manual §10 line 113")
    dumped = error_envelope(exc).model_dump()
    assert dumped["error"]["code"] == "policy_denied"
    assert dumped["error"]["citation"] == "manual §10 line 113"
    assert dumped["error"]["needed"] is None
    assert dumped["error"]["have"] is None


def test_error_envelope_message_is_the_exception_text():
    exc = InsufficientData(what="X", needed="N", have="H")
    dumped = error_envelope(exc).model_dump()
    assert dumped["error"]["message"] == str(exc)
