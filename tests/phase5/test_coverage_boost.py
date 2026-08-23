import pytest
from unittest.mock import MagicMock, patch
from src.agents.multi_agent.state import initial_state
from src.agents.multi_agent.agents import (
    _safe_json, _extract_text, _invoke_llm,
    demand_forecaster, reorder_agent, supplier_coordinator, inventory_auditor
)
from src.agents.multi_agent.graph import _safe_log


def test_extract_text_variations():
    """Test _extract_text on all input types: str, list of strings/dicts/objects, None."""
    assert _extract_text(None) == ""
    assert _extract_text("hello") == "hello"
    
    mock_obj = MagicMock()
    mock_obj.content = "inner content"
    assert _extract_text(mock_obj) == "inner content"
    
    mock_text_obj = MagicMock()
    mock_text_obj.text = "custom text"
    
    list_input = [
        "part1 ",
        {"text": "part2 "},
        mock_text_obj
    ]
    assert _extract_text(list_input) == "part1 part2 custom text"
    
    dict_input = {"text": "dict text"}
    assert _extract_text(dict_input) == "dict text"


def test_safe_json_variations():
    """Test _safe_json handles markdown codeblocks, invalid text, whitespace, and empty strings."""
    assert _safe_json("") == {}
    assert _safe_json(None) == {}
    assert _safe_json("Not a json at all") == {}
    assert _safe_json('```json\n{"key": "value"}\n```') == {"key": "value"}
    assert _safe_json('Preamble text ```json\n{"reorder": true}\n``` trailing text') == {"reorder": True}
    assert _safe_json('Some text {"count": 42} more text') == {"count": 42}
    
    # Test invalid json candidate inside braces
    assert _safe_json('text {invalid: json, not standard} text') == {}
    
    # Test non-string object with .content
    mock_msg = MagicMock()
    mock_msg.content = '{"from_content": 123}'
    assert _safe_json(mock_msg) == {"from_content": 123}
    
    # Test un-parsable object
    assert _safe_json(12345) == {}


def test_invoke_llm_direct():
    """_invoke_llm passes the prompt to `_llm.invoke` and returns the response.

    There is no longer a "fallback" path to test: `_invoke_llm` used to branch on
    `hasattr(_llm, "return_value")` -- a unittest.mock attribute -- so production
    behaviour depended on whether a test was running. The prompt assertion below
    is what that branch made impossible to check.
    """
    mock_res = MagicMock()
    mock_res.content = "standard response"
    with patch("src.agents.multi_agent.agents._llm") as ml:
        ml.invoke.return_value = mock_res
        res = _invoke_llm("test prompt")
        assert res.content == "standard response"
        # The prompt actually reaches the model, wrapped in a single HumanMessage.
        ml.invoke.assert_called_once()
        (messages,), _ = ml.invoke.call_args
        assert len(messages) == 1
        assert messages[0].content == "test prompt"


def test_safe_log_resilience():
    """Test _safe_log handles logging exceptions gracefully."""
    with patch("src.agents.multi_agent.graph.logger") as mock_logger:
        mock_logger.info.side_effect = OSError(22, "Invalid argument")
        _safe_log("test_event", poc_id="POC-07")


def test_demand_forecaster_llm_exception(sample_product_data):
    """Test demand_forecaster handles LLM exception and logs errors."""
    s = initial_state(1)
    with patch("src.agents.multi_agent.agents.requests.get") as mg, patch("src.agents.multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = sample_product_data
        ml.invoke.side_effect = Exception("Demand LLM timeout")
        result = demand_forecaster(s)
        assert len(result["errors"]) > 0
        assert "Demand LLM error" in result["errors"][-1]


def test_reorder_agent_llm_exception():
    """Test reorder_agent handles LLM exceptions gracefully without crashing."""
    s = initial_state(1)
    with patch("src.agents.multi_agent.agents._llm") as ml:
        ml.invoke.side_effect = Exception("LLM connection timeout")
        result = reorder_agent(s)
        assert len(result["errors"]) > 0
        assert result["reorder_recommendation"]["reorder_required"] is False
        assert "LLM connection timeout" in result["errors"][-1]


def test_supplier_coordinator_api_error_and_llm_exception():
    """Test supplier_coordinator handles both supplier API errors and LLM failures."""
    s = {**initial_state(1), "product_data": {"supplier_id": 99}}
    with patch("src.agents.multi_agent.agents.requests.get", side_effect=Exception("Supplier API timeout")), \
         patch("src.agents.multi_agent.agents._llm") as ml:
        ml.invoke.side_effect = Exception("LLM error")
        result = supplier_coordinator(s)
        assert len(result["errors"]) >= 2
        assert result["supplier_quote"]["supplier_id"] == 99


def test_supplier_coordinator_without_supplier_id():
    """Test supplier_coordinator when product_data has no supplier_id."""
    s = {**initial_state(1), "product_data": {}}
    with patch("src.agents.multi_agent.agents._llm") as ml:
        ml.invoke.return_value = MagicMock(
            content='{"supplier_id": null, "quoted_unit_cost": 0, "total_order_cost": 0, "estimated_lead_time_days": 7, "quote_notes": "None"}'
        )
        result = supplier_coordinator(s)
        assert result["supplier_quote"]["supplier_id"] is None


def test_inventory_auditor_llm_exception():
    """Test inventory_auditor handles LLM failure and populates error report."""
    s = initial_state(1)
    with patch("src.agents.multi_agent.agents._llm") as ml:
        ml.invoke.side_effect = Exception("Audit LLM failure")
        result = inventory_auditor(s)
        assert "Audit error" in result["audit_report"]
        assert result["analysis_status"] == "complete"
