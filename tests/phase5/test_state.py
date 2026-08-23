import typing
import pytest
from unittest.mock import MagicMock, patch
from src.agents.multi_agent.state import InventoryAnalysisState, initial_state


def test_state_fields():
    """TC-07-P5-STATE-01: TypedDict Has All Fields"""
    hints = typing.get_type_hints(InventoryAnalysisState)
    for f in [
        "product_id", "product_data", "demand_forecast", "reorder_recommendation",
        "supplier_quote", "audit_report", "analysis_status", "errors", "messages"
    ]:
        assert f in hints, f"Missing field in InventoryAnalysisState: {f}"


def test_initial_defaults():
    """TC-07-P5-STATE-02: initial_state Correct Defaults"""
    s = initial_state(42)
    assert s["product_id"] == 42
    assert s["product_data"] == {}
    assert s["demand_forecast"] == {}
    assert s["reorder_recommendation"] == {}
    assert s["supplier_quote"] == {}
    assert s["audit_report"] == ""
    assert s["analysis_status"] == "analyzing"
    assert s["errors"] == [] and s["messages"] == []


def test_no_mutation(state_with_data, sample_product_data):
    """TC-07-P5-STATE-03: No In-Place Mutation"""
    orig = state_with_data["messages"].copy()
    with patch("src.agents.multi_agent.agents.requests.get") as mg, \
         patch("src.agents.multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = sample_product_data
        ml.invoke.return_value = MagicMock(
            content='{"avg_daily_demand":4.0,"demand_trend":"stable","days_of_stock_remaining":3,"stockout_risk":"high","forecast_notes":"Low stock."}'
        )
        from src.agents.multi_agent.agents import demand_forecaster
        new = demand_forecaster(state_with_data)
    assert state_with_data["messages"] == orig
    assert len(new["messages"]) > len(orig)


def test_fields_persist(state_after_reorder):
    """TC-07-P5-STATE-04: Fields Persist Across Nodes"""
    assert state_after_reorder["demand_forecast"]["stockout_risk"] == "high"
    assert state_after_reorder["product_data"]["sku"] == "SKU-GRO-0001"
    assert state_after_reorder["reorder_recommendation"]["reorder_required"] is True
