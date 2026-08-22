import pytest
from unittest.mock import MagicMock, patch
from multi_agent.state import initial_state


def test_demand_fetches(sample_product_data):
    """TC-07-P5-AGENT-01: Demand Forecaster Fetches Data"""
    s = initial_state(1)
    with patch("multi_agent.agents.requests.get") as mg, patch("multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = sample_product_data
        ml.return_value.invoke.return_value = MagicMock(
            content='{"avg_daily_demand":4.0,"demand_trend":"stable","days_of_stock_remaining":3,"stockout_risk":"high","forecast_notes":"Low."}'
        )
        from multi_agent.agents import demand_forecaster
        result = demand_forecaster(s)
        mg.assert_called()
        assert result["product_data"].get("sku") == "SKU-GRO-0001"


def test_demand_api_error():
    """TC-07-P5-AGENT-02: Demand Forecaster Handles API Error"""
    s = initial_state(999)
    with patch("multi_agent.agents.requests.get", side_effect=Exception("down")), \
         patch("multi_agent.agents._llm") as ml:
        ml.return_value.invoke.return_value = MagicMock(
            content='{"avg_daily_demand":0,"demand_trend":"unknown","days_of_stock_remaining":0,"stockout_risk":"unknown","forecast_notes":"Error."}'
        )
        from multi_agent.agents import demand_forecaster
        result = demand_forecaster(s)
        assert len(result["errors"]) > 0


def test_forecast_fields(sample_product_data):
    """TC-07-P5-AGENT-03: Demand Forecast Has Required Fields"""
    s = initial_state(1)
    with patch("multi_agent.agents.requests.get") as mg, patch("multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = sample_product_data
        ml.return_value.invoke.return_value = MagicMock(
            content='{"avg_daily_demand":4.0,"demand_trend":"stable","days_of_stock_remaining":3,"stockout_risk":"high","forecast_notes":"High risk."}'
        )
        from multi_agent.agents import demand_forecaster
        result = demand_forecaster(s)
        for f in ["avg_daily_demand", "demand_trend", "stockout_risk"]:
            assert f in result["demand_forecast"]


def test_reorder_recommends(state_after_forecast):
    """TC-07-P5-AGENT-04: Reorder Agent Recommends for High Risk"""
    with patch("multi_agent.agents._llm") as ml:
        ml.return_value.invoke.return_value = MagicMock(
            content='{"reorder_required":true,"recommended_quantity":100,"urgency":"within_3_days","reason":"Stockout risk high."}'
        )
        from multi_agent.agents import reorder_agent
        result = reorder_agent(state_after_forecast)
        assert result["reorder_recommendation"]["reorder_required"] is True
        assert result["analysis_status"] == "reorder_required"


def test_reorder_no_action():
    """TC-07-P5-AGENT-05: Reorder Agent No Action for Low Risk"""
    s = {
        **initial_state(1),
        "product_data": {"sku": "SKU-ELC-0001"},
        "demand_forecast": {
            "avg_daily_demand": 1.0,
            "stockout_risk": "none",
            "days_of_stock_remaining": 60,
            "demand_trend": "stable"
        }
    }
    with patch("multi_agent.agents._llm") as ml:
        ml.return_value.invoke.return_value = MagicMock(
            content='{"reorder_required":false,"recommended_quantity":0,"urgency":"not_required","reason":"Ample stock."}'
        )
        from multi_agent.agents import reorder_agent
        result = reorder_agent(s)
        assert result["reorder_recommendation"]["reorder_required"] is False


def test_supplier_quote(state_after_reorder):
    """TC-07-P5-AGENT-06: Supplier Coordinator Generates Quote"""
    catalog = [{"sku": "SKU-GRO-0001", "name": "Basmati Rice", "cost_price": 280.0}]
    with patch("multi_agent.agents.requests.get") as mg, patch("multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = catalog
        ml.return_value.invoke.return_value = MagicMock(
            content='{"supplier_id":1,"quoted_unit_cost":280.0,"total_order_cost":28000.0,"estimated_lead_time_days":7,"quote_notes":"Standard rate."}'
        )
        from multi_agent.agents import supplier_coordinator
        result = supplier_coordinator(state_after_reorder)
        assert result["supplier_quote"]["total_order_cost"] > 0


def test_auditor_generates(state_after_reorder):
    """TC-07-P5-AGENT-07: Inventory Auditor Generates Report"""
    with patch("multi_agent.agents._llm") as ml:
        ml.return_value.invoke.return_value = MagicMock(
            content="SKU-GRO-0001 Basmati Rice has 12 units available against a reorder point of 20. Stockout expected in 3 days. Reorder of 100 units from supplier 1 is recommended at ₹28,000 total."
        )
        from multi_agent.agents import inventory_auditor
        result = inventory_auditor(state_after_reorder)
        assert len(result["audit_report"]) > 50
        assert result["analysis_status"] == "complete"


def test_all_append_messages(state_with_data, sample_product_data):
    """TC-07-P5-AGENT-08: All Agents Append Messages"""
    initial_count = len(state_with_data["messages"])
    with patch("multi_agent.agents.requests.get") as mg, patch("multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = sample_product_data
        ml.return_value.invoke.return_value = MagicMock(
            content='{"avg_daily_demand":4.0,"demand_trend":"stable","days_of_stock_remaining":3,"stockout_risk":"high","forecast_notes":"High risk."}'
        )
        from multi_agent.agents import demand_forecaster
        result = demand_forecaster(state_with_data)
    assert len(result["messages"]) == initial_count + 1
    assert "Demand Forecaster" in result["messages"][-1]
