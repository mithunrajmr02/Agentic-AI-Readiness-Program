"""Contract tests for src/core/errors.py.

Asserts the exception taxonomy (15-SHARED-CONTRACTS.md §2.6) and the attributes
the error envelope (§12.3) reads: ``needed``/``have`` for insufficient-data,
``citation`` for policy denials, and a stable ``code`` per type (§12.4).
"""
import pytest

from src.core import errors


def test_all_subclasses_of_steward_error():
    assert issubclass(errors.StewardError, Exception)
    for cls in (
        errors.InsufficientData,
        errors.PolicyDenied,
        errors.PreconditionFailed,
        errors.ExecutionFailed,
    ):
        assert issubclass(cls, errors.StewardError)


def test_insufficient_data_carries_what_needed_have():
    exc = errors.InsufficientData(what="demand_rate", needed="30 days history", have="1 day")
    assert isinstance(exc, errors.StewardError)
    assert exc.what == "demand_rate"
    assert exc.needed == "30 days history"
    assert exc.have == "1 day"
    assert exc.code == "insufficient_data"
    # The message must surface the three fields for logs / 422 bodies.
    text = str(exc)
    assert "30 days history" in text and "1 day" in text


def test_policy_denied_carries_rule_and_citation():
    exc = errors.PolicyDenied(rule="max_order_value", citation="Manual §4.2: orders above ₹50,000 require approval")
    assert isinstance(exc, errors.StewardError)
    assert exc.rule == "max_order_value"
    assert exc.citation == "Manual §4.2: orders above ₹50,000 require approval"
    assert exc.code == "policy_denied"


def test_policy_denied_citation_may_be_none():
    exc = errors.PolicyDenied(rule="kill_switch", citation=None)
    assert exc.rule == "kill_switch"
    assert exc.citation is None


def test_precondition_failed_carries_precondition_and_detail():
    exc = errors.PreconditionFailed(precondition="po_status==draft", detail="po PO-2026-0042 is already received")
    assert isinstance(exc, errors.StewardError)
    assert exc.precondition == "po_status==draft"
    assert exc.detail == "po PO-2026-0042 is already received"
    assert exc.code == "precondition_failed"


def test_execution_failed_is_a_steward_error():
    exc = errors.ExecutionFailed("supplier gateway returned HTTP 500")
    assert isinstance(exc, errors.StewardError)
    assert exc.code == "execution_failed"
    assert "supplier gateway" in str(exc)


def test_steward_error_is_raisable_and_catchable_as_base():
    with pytest.raises(errors.StewardError):
        raise errors.InsufficientData(what="x", needed="y", have="z")
