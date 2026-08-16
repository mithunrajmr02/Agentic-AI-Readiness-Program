import os
import sys
import pytest
import requests
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from phase3.agent.agent import build_agent_executor, run_agent
from phase3.agent.tools import get_product_stock, get_low_stock_alerts, create_purchase_order, get_supplier_info, rag_knowledge_base

def test_agent_initialization():
    """Test that the agent executor can be built."""
    agent = build_agent_executor()
    assert agent is not None
    assert len(agent.tools) == 5

def test_tools_exist():
    """Test that all 5 tools are available."""
    assert get_product_stock.name == "get_product_stock"
    assert get_low_stock_alerts.name == "get_low_stock_alerts"
    assert create_purchase_order.name == "create_purchase_order"
    assert get_supplier_info.name == "get_supplier_info"
    assert rag_knowledge_base.name == "rag_knowledge_base"

@patch("phase3.agent.tools.requests.get")
def test_tool_get_product_stock(mock_get):
    """Test get_product_stock tool calls the correct API endpoint."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = [{"id": 1, "sku": "SKU-123", "stock_level": {"quantity_on_hand": 50}}]
    mock_get.return_value = mock_resp
    
    result = get_product_stock.invoke({"sku": "SKU-123"})
    mock_get.assert_called_once_with("http://127.0.0.1:8000/api/v1/products", timeout=10)
    assert "SKU-123" in result

@patch("phase3.agent.tools.requests.post")
@patch("phase3.agent.tools.requests.get")
def test_tool_create_purchase_order(mock_get, mock_post):
    """Test create_purchase_order tool calls the correct API endpoint."""
    mock_get_resp = MagicMock()
    # Mocking the two get calls: 1 for suppliers, 1 for products
    mock_get_resp.json.side_effect = [
        [{"id": 1, "supplier_code": "SUP-1"}],
        [{"id": 1, "sku": "SKU-123", "cost_price": 10.0}]
    ]
    mock_get.return_value = mock_get_resp
    
    mock_post_resp = MagicMock()
    mock_post_resp.json.return_value = {"status": "success"}
    mock_post.return_value = mock_post_resp
    
    result = create_purchase_order.invoke({"supplier_code": "SUP-1", "items": [{"sku": "SKU-123", "quantity": 10}]})
    assert mock_post.called
    assert "success" in result

@patch("phase3.agent.tools.ask_question")
def test_tool_rag_knowledge_base(mock_ask):
    """Test rag_knowledge_base tool calls Phase 2 ask_question."""
    mock_ask.return_value = {"answer": "This is a RAG answer."}
    result = rag_knowledge_base.invoke({"query": "What is a PO?"})
    mock_ask.assert_called_once_with("What is a PO?")
    assert result == "This is a RAG answer."

def test_run_agent_error():
    """Test run_agent exception handling."""
    mock_agent = MagicMock()
    mock_agent.invoke.side_effect = Exception("Test Error")
    result = run_agent("test", agent_executor=mock_agent)
    assert "Error executing query" in result

@patch("phase3.agent.agent.get_llm")
def test_build_agent_executor_error(mock_get_llm):
    from phase3.agent.agent import build_agent_executor
    mock_get_llm.side_effect = Exception("LLM Error")
    with pytest.raises(Exception):
        build_agent_executor()

def test_summarize_if_long_short():
    """Test summarizer with short list."""
    from phase3.agent.summarizer import _summarize_if_long
    data = [{"id": 1}, {"id": 2}]
    res = _summarize_if_long(data, max_items=5)
    assert "id" in res

@patch("phase3.agent.summarizer.load_summarize_chain")
@patch("phase3.agent.summarizer.ChatGoogleGenerativeAI")
def test_summarize_if_long_long(mock_chat, mock_load):
    """Test summarizer with long list."""
    from phase3.agent.summarizer import _summarize_if_long
    data = [{"id": i} for i in range(10)]
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {"output_text": "Summarized text"}
    mock_load.return_value = mock_chain
    
    res = _summarize_if_long(data, max_items=5)
    assert "Summarized text" in res

@patch("phase3.agent.summarizer.ChatGoogleGenerativeAI")
def test_summarize_if_long_error(mock_chat):
    """Test summarizer fallback on error."""
    from phase3.agent.summarizer import _summarize_if_long
    data = [{"id": i} for i in range(10)]
    mock_chat.side_effect = Exception("API Error")
    res = _summarize_if_long(data, max_items=5)
    assert "Data too long to display" in res

@patch("phase3.agent.tools.requests.get")
def test_api_get_error(mock_get):
    from phase3.agent.tools import _api_get
    mock_get.side_effect = requests.RequestException("Network Error")
    res = _api_get("/test")
    assert "error" in res

@patch("phase3.agent.tools.requests.post")
def test_api_post_error(mock_post):
    from phase3.agent.tools import _api_post
    mock_post.side_effect = requests.RequestException("Network Error")
    res = _api_post("/test", {})
    assert "error" in res

@patch("phase3.agent.tools._api_get")
def test_get_low_stock_alerts_error(mock_get):
    mock_get.return_value = {"error": "API failed"}
    res = get_low_stock_alerts.invoke({})
    assert "API failed" in res

@patch("phase3.agent.tools._api_get")
def test_get_low_stock_alerts_list(mock_get):
    mock_get.return_value = [{"sku": "SKU-1"}, {"sku": "SKU-2"}]
    res = get_low_stock_alerts.invoke({})
    assert "SKU-1" in res

@patch("phase3.agent.tools._api_get")
def test_get_product_stock_error(mock_get):
    mock_get.return_value = {"error": "API failed"}
    res = get_product_stock.invoke({"sku": "SKU-1"})
    assert "API failed" in res

@patch("phase3.agent.tools._api_get")
def test_get_product_stock_not_found(mock_get):
    mock_get.return_value = [{"sku": "SKU-2"}]
    res = get_product_stock.invoke({"sku": "SKU-1"})
    assert "not found" in res

@patch("phase3.agent.tools._api_get")
def test_get_supplier_info_error(mock_get):
    mock_get.return_value = {"error": "API failed"}
    res = get_supplier_info.invoke({"supplier_code": "SUP-1"})
    assert "API failed" in res

@patch("phase3.agent.tools._api_get")
def test_get_supplier_info_success(mock_get):
    mock_get.return_value = [{"supplier_code": "SUP-1"}]
    res = get_supplier_info.invoke({"supplier_code": "SUP-1"})
    assert "SUP-1" in res

@patch("phase3.agent.tools._api_get")
def test_create_purchase_order_supplier_error(mock_get):
    mock_get.return_value = {"error": "API failed"}
    res = create_purchase_order.invoke({"supplier_code": "SUP-1", "items": []})
    assert "API failed" in res

@patch("phase3.agent.tools._api_get")
def test_create_purchase_order_product_error(mock_get):
    mock_get.side_effect = [[{"id": 1, "supplier_code": "SUP-1"}], {"error": "API failed"}]
    res = create_purchase_order.invoke({"supplier_code": "SUP-1", "items": []})
    assert "API failed" in res

@patch("phase3.agent.tools.ask_question")
def test_rag_knowledge_base_dict(mock_ask):
    mock_ask.return_value = "String answer"
    res = rag_knowledge_base.invoke({"query": "q"})
    assert res == "String answer"
