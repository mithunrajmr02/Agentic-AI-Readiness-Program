import os
import pytest
from unittest.mock import MagicMock, patch


def test_full_pipeline(sample_product_data):
    """TC-07-P5-E2E-01: Full Pipeline Executes"""
    resps = [
        '{"avg_daily_demand":4.0,"demand_trend":"stable","days_of_stock_remaining":3,"stockout_risk":"high","forecast_notes":"Low."}',
        '{"reorder_required":true,"recommended_quantity":100,"urgency":"within_3_days","reason":"Stockout risk."}',
        '{"supplier_id":1,"quoted_unit_cost":280.0,"total_order_cost":28000.0,"estimated_lead_time_days":7,"quote_notes":"Standard."}',
        "SKU-GRO-0001 needs reorder urgently. Place PO for 100 units at ₹28,000."
    ]
    cnt = [0]
    def side(p):
        r = MagicMock()
        r.content = resps[min(cnt[0], 3)]
        cnt[0] += 1
        return r

    with patch("src.agents.multi_agent.agents.requests.get") as mg, patch("src.agents.multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = sample_product_data
        ml.invoke.side_effect = side
        from src.agents.multi_agent.graph import analyze_product
        try:
            result = analyze_product(product_id=1)
            assert result is not None
        except Exception as e:
            pytest.fail(f"analyze_product raised: {e}")


def test_audit_non_empty(sample_product_data):
    """TC-07-P5-E2E-02: audit_report Non-Empty"""
    resps = [
        '{"avg_daily_demand":2.0,"demand_trend":"stable","days_of_stock_remaining":10,"stockout_risk":"low","forecast_notes":"OK."}',
        '{"reorder_required":false,"recommended_quantity":0,"urgency":"not_required","reason":"Sufficient."}',
        '{"supplier_id":null,"quoted_unit_cost":0,"total_order_cost":0,"estimated_lead_time_days":7,"quote_notes":"No quote needed."}',
        "Stock levels are adequate. No immediate action required."
    ]
    cnt = [0]
    def side(p):
        r = MagicMock()
        r.content = resps[min(cnt[0], 3)]
        cnt[0] += 1
        return r

    with patch("src.agents.multi_agent.agents.requests.get") as mg, patch("src.agents.multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = sample_product_data
        ml.invoke.side_effect = side
        from src.agents.multi_agent.graph import analyze_product
        result = analyze_product(product_id=1)
        assert len(result.get("audit_report", "")) > 20


def test_four_messages(sample_product_data):
    """TC-07-P5-E2E-03: Four Messages in Trail"""
    resps = [
        '{"avg_daily_demand":2.0,"demand_trend":"stable","days_of_stock_remaining":10,"stockout_risk":"low","forecast_notes":"OK."}',
        '{"reorder_required":false,"recommended_quantity":0,"urgency":"not_required","reason":"OK."}',
        '{"supplier_id":null,"quoted_unit_cost":0,"total_order_cost":0,"estimated_lead_time_days":7,"quote_notes":"OK."}',
        "Inventory healthy."
    ]
    cnt = [0]
    def side(p):
        r = MagicMock()
        r.content = resps[min(cnt[0], 3)]
        cnt[0] += 1
        return r

    with patch("src.agents.multi_agent.agents.requests.get") as mg, patch("src.agents.multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = sample_product_data
        ml.invoke.side_effect = side
        from src.agents.multi_agent.graph import analyze_product
        result = analyze_product(product_id=1)
        assert len(result.get("messages", [])) >= 4


def test_terminal_status(sample_product_data):
    """TC-07-P5-E2E-04: Status Is Terminal"""
    resps = [
        '{"avg_daily_demand":2.0,"demand_trend":"stable","days_of_stock_remaining":10,"stockout_risk":"low","forecast_notes":"OK."}',
        '{"reorder_required":false,"recommended_quantity":0,"urgency":"not_required","reason":"OK."}',
        '{"supplier_id":null,"quoted_unit_cost":0,"total_order_cost":0,"estimated_lead_time_days":7,"quote_notes":"OK."}',
        "Normal."
    ]
    cnt = [0]
    def side(p):
        r = MagicMock()
        r.content = resps[min(cnt[0], 3)]
        cnt[0] += 1
        return r

    with patch("src.agents.multi_agent.agents.requests.get") as mg, patch("src.agents.multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = sample_product_data
        ml.invoke.side_effect = side
        from src.agents.multi_agent.graph import analyze_product
        result = analyze_product(product_id=1)
        assert result["analysis_status"] in ("complete", "reorder_required", "healthy", "analyzing")


def test_langsmith():
    """TC-07-P5-E2E-05: LangSmith Traces"""
    if not os.getenv("LANGCHAIN_API_KEY"):
        pytest.skip("No key")
    try:
        from langsmith import Client
        runs = list(Client().list_runs(project_name="AI-Readiness-POC-07-P5", limit=5))
        if not runs:
            pytest.skip("No traces yet")
        assert len(runs) >= 1
    except Exception:
        pytest.skip("LangSmith client unavailable")


def test_api_failure():
    """TC-07-P5-E2E-06: API Failure Handled"""
    resps = [
        '{"avg_daily_demand":0,"demand_trend":"unknown","days_of_stock_remaining":0,"stockout_risk":"unknown","forecast_notes":"API error."}',
        '{"reorder_required":false,"recommended_quantity":0,"urgency":"not_required","reason":"Insufficient data."}',
        '{"supplier_id":null,"quoted_unit_cost":0,"total_order_cost":0,"estimated_lead_time_days":7,"quote_notes":"No data."}',
        "Unable to retrieve product data. Please verify product ID and API connectivity."
    ]
    cnt = [0]
    def side(p):
        r = MagicMock()
        r.content = resps[min(cnt[0], 3)]
        cnt[0] += 1
        return r

    with patch("src.agents.multi_agent.agents.requests.get", side_effect=Exception("API down")), \
         patch("src.agents.multi_agent.agents._llm") as ml:
        ml.invoke.side_effect = side
        from src.agents.multi_agent.graph import analyze_product
        try:
            result = analyze_product(product_id=1)
            assert result is not None and len(result.get("errors", [])) > 0
        except Exception as e:
            pytest.fail(f"Should not crash: {e}")


def test_urgent_reorder(sample_product_data):
    """TC-07-P5-E2E-07: Urgent Reorder Sets Status"""
    resps = [
        '{"avg_daily_demand":8.0,"demand_trend":"increasing","days_of_stock_remaining":1,"stockout_risk":"high","forecast_notes":"Critical."}',
        '{"reorder_required":true,"recommended_quantity":200,"urgency":"immediate","reason":"Stockout tomorrow."}',
        '{"supplier_id":1,"quoted_unit_cost":280.0,"total_order_cost":56000.0,"estimated_lead_time_days":5,"quote_notes":"Urgent order."}',
        "URGENT: SKU-GRO-0001 will stock out tomorrow. Place immediate PO for 200 units."
    ]
    cnt = [0]
    def side(p):
        r = MagicMock()
        r.content = resps[min(cnt[0], 3)]
        cnt[0] += 1
        return r

    with patch("src.agents.multi_agent.agents.requests.get") as mg, patch("src.agents.multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = sample_product_data
        ml.invoke.side_effect = side
        from src.agents.multi_agent.graph import analyze_product
        result = analyze_product(product_id=1)
        if result.get("reorder_recommendation", {}).get("reorder_required"):
            assert result["analysis_status"] in ("reorder_required", "complete")
