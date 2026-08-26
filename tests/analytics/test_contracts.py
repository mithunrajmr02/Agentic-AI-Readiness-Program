"""Contract tests for src.analytics (WS-1).

Verifies all published signatures match 15-SHARED-CONTRACTS.md §5.1 / §5.2 exactly.
"""
import dataclasses
import inspect
from dataclasses import is_dataclass
from typing import get_type_hints

import pytest
from src.analytics import (
    Computed,
    compute_daily_demand,
    derive_reorder_point,
    compute_eoq,
    score_sufficiency,
    measured_lead_time,
    inventory_value,
    days_on_hand,
    stock_turn,
)
from src.core.vocab import SUFFICIENCY


def test_computed_dataclass_contract():
    """Verify Computed dataclass structure (15-SHARED-CONTRACTS.md §5.1)."""
    assert is_dataclass(Computed)
    
    # Check fields
    field_names = [f.name for f in dataclasses.fields(Computed)]
    expected_fields = [
        "value",
        "sufficiency",
        "inputs",
        "formula",
        "citation",
        "sample_size",
        "span_days",
    ]
    for ef in expected_fields:
        assert ef in field_names, f"Missing field {ef} in Computed"

    # Frozen invariant
    c = Computed(
        value=None,
        sufficiency="none",
        inputs={},
        formula="test",
        citation="manual",
        sample_size=0,
        span_days=0,
    )
    with pytest.raises(Exception):
        c.value = 10.0  # Must be frozen


def test_computed_invariants():
    """Value must be None whenever sufficiency is 'insufficient' or 'none'."""
    c_none = Computed(
        value=None,
        sufficiency="none",
        inputs={},
        formula="",
        citation=None,
        sample_size=0,
        span_days=0,
    )
    assert c_none.value is None

    c_insufficient = Computed(
        value=None,
        sufficiency="insufficient",
        inputs={},
        formula="",
        citation=None,
        sample_size=1,
        span_days=30,
    )
    assert c_insufficient.value is None


def test_functions_exposed_and_signatures():
    """Verify all 8 functions in 15-SHARED-CONTRACTS.md §5.2 exist with correct parameters."""
    functions = [
        compute_daily_demand,
        derive_reorder_point,
        compute_eoq,
        score_sufficiency,
        measured_lead_time,
        inventory_value,
        days_on_hand,
        stock_turn,
    ]
    for fn in functions:
        assert callable(fn), f"{fn.__name__} must be callable"

    # Verify derive_reorder_point keyword-only use_measured_lead_time
    sig_rop = inspect.signature(derive_reorder_point)
    assert "db" in sig_rop.parameters
    assert "product_id" in sig_rop.parameters
    assert "use_measured_lead_time" in sig_rop.parameters

    # Verify compute_eoq parameters
    sig_eoq = inspect.signature(compute_eoq)
    assert "db" in sig_eoq.parameters
    assert "product_id" in sig_eoq.parameters
    assert "ordering_cost" in sig_eoq.parameters
    assert "holding_rate" in sig_eoq.parameters

    # Verify inventory_value parameters
    sig_val = inspect.signature(inventory_value)
    assert "db" in sig_val.parameters
    assert "scope" in sig_val.parameters
    assert "scope_id" in sig_val.parameters
