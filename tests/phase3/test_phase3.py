import pytest
import requests
from unittest.mock import patch, MagicMock

from src.agents.agent import build_agent_executor, run_agent
from src.agents.tools import (
    get_product_stock, get_low_stock_alerts, create_purchase_order,
    get_supplier_info, get_supplier_catalog, get_dashboard_stats, rag_knowledge_base,
)

def test_agent_initialization():
    """Test that the agent executor can be built."""
    agent = build_agent_executor()
    assert agent is not None
    assert len(agent.tools) == 7

def test_tools_exist():
    """Test that all 7 tools are available."""
    assert get_product_stock.name == "get_product_stock"
    assert get_low_stock_alerts.name == "get_low_stock_alerts"
    assert create_purchase_order.name == "create_purchase_order"
    assert get_supplier_info.name == "get_supplier_info"
    assert get_supplier_catalog.name == "get_supplier_catalog"
    assert get_dashboard_stats.name == "get_dashboard_stats"
    assert rag_knowledge_base.name == "rag_knowledge_base"

def test_every_registered_tool_is_described_in_the_system_prompt():
    """A tool the prompt never mentions is a tool the model will not reach for.

    The two directions drift independently: a tool can be registered in the
    executor without being named in the prefix, or the prefix can advertise a tool
    that no longer exists and invite the model to hallucinate a call. Checking both
    ways is what makes this test worth having.
    """
    from src.agents.prompts import INVENTORY_AGENT_SYSTEM_PROMPT

    agent = build_agent_executor()
    registered = {t.name for t in agent.tools}

    for name in registered:
        assert f"`{name}(" in INVENTORY_AGENT_SYSTEM_PROMPT, \
            f"tool {name} is registered but the system prompt never describes it"

    # And nothing is advertised that cannot be called.
    import re
    advertised = set(re.findall(r"^- `(\w+)\(", INVENTORY_AGENT_SYSTEM_PROMPT, re.MULTILINE))
    assert advertised == registered, \
        f"prompt/executor mismatch: prompt-only={advertised - registered}, executor-only={registered - advertised}"

@patch("src.agents.tools.requests.get")
def test_tool_get_product_stock(mock_get):
    """Test get_product_stock tool calls the correct API endpoint."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = [{"id": 1, "sku": "SKU-123", "stock_level": {"quantity_on_hand": 50}}]
    mock_get.return_value = mock_resp

    result = get_product_stock.invoke({"sku": "SKU-123"})
    # The tool now authenticates as the service account, so the call carries a
    # `headers` kwarg. Asserting url + timeout positionally and checking `headers`
    # separately keeps this test pinned to the endpoint without re-pinning it to
    # the exact credential plumbing.
    mock_get.assert_called_once()
    call_args, call_kwargs = mock_get.call_args
    assert call_args == ("http://127.0.0.1:8000/api/v1/products",)
    assert call_kwargs["timeout"] == 10
    assert "headers" in call_kwargs
    assert "SKU-123" in result

@patch("src.agents.tools.requests.post")
@patch("src.agents.tools.requests.get")
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

@patch("src.agents.tools.ask_question")
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

@patch("src.agents.agent.get_llm")
def test_build_agent_executor_error(mock_get_llm):
    from src.agents.agent import build_agent_executor
    mock_get_llm.side_effect = Exception("LLM Error")
    with pytest.raises(Exception):
        build_agent_executor()

def test_summarize_if_long_short():
    """Test summarizer with short list."""
    from src.agents.summarizer import _summarize_if_long
    data = [{"id": 1}, {"id": 2}]
    res = _summarize_if_long(data, max_items=5)
    assert "id" in res

@patch("src.agents.summarizer.load_summarize_chain")
@patch("src.agents.summarizer.ChatGoogleGenerativeAI")
def test_summarize_if_long_long(mock_chat, mock_load):
    """Test summarizer with long list."""
    from src.agents.summarizer import _summarize_if_long
    data = [{"id": i} for i in range(10)]
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {"output_text": "Summarized text"}
    mock_load.return_value = mock_chain
    
    res = _summarize_if_long(data, max_items=5)
    assert "Summarized text" in res

@patch("src.agents.summarizer.ChatGoogleGenerativeAI")
def test_summarize_if_long_error(mock_chat):
    """Test summarizer fallback on error."""
    from src.agents.summarizer import _summarize_if_long
    data = [{"id": i} for i in range(10)]
    mock_chat.side_effect = Exception("API Error")
    res = _summarize_if_long(data, max_items=5)
    assert "Data too long to display" in res

@patch("src.agents.tools.requests.get")
def test_api_get_error(mock_get):
    from src.agents.tools import _api_get
    mock_get.side_effect = requests.RequestException("Network Error")
    res = _api_get("/test")
    assert "error" in res

@patch("src.agents.tools.requests.post")
def test_api_post_error(mock_post):
    from src.agents.tools import _api_post
    mock_post.side_effect = requests.RequestException("Network Error")
    res = _api_post("/test", {})
    assert "error" in res

@patch("src.agents.tools._api_get")
def test_get_low_stock_alerts_error(mock_get):
    mock_get.return_value = {"error": "API failed"}
    res = get_low_stock_alerts.invoke({})
    assert "API failed" in res

@patch("src.agents.tools._api_get")
def test_get_low_stock_alerts_list(mock_get):
    mock_get.return_value = [{"sku": "SKU-1"}, {"sku": "SKU-2"}]
    res = get_low_stock_alerts.invoke({})
    assert "SKU-1" in res

@patch("src.agents.tools._api_get")
def test_get_product_stock_error(mock_get):
    mock_get.return_value = {"error": "API failed"}
    res = get_product_stock.invoke({"sku": "SKU-1"})
    assert "API failed" in res

@patch("src.agents.tools._api_get")
def test_get_product_stock_not_found(mock_get):
    mock_get.return_value = [{"sku": "SKU-2"}]
    res = get_product_stock.invoke({"sku": "SKU-1"})
    assert "not found" in res

@patch("src.agents.tools._api_get")
def test_get_supplier_info_error(mock_get):
    mock_get.return_value = {"error": "API failed"}
    res = get_supplier_info.invoke({"supplier_code": "SUP-1"})
    assert "API failed" in res

@patch("src.agents.tools._api_get")
def test_get_supplier_info_success(mock_get):
    mock_get.return_value = [{"supplier_code": "SUP-1"}]
    res = get_supplier_info.invoke({"supplier_code": "SUP-1"})
    assert "SUP-1" in res

@patch("src.agents.tools._api_get")
def test_create_purchase_order_supplier_error(mock_get):
    mock_get.return_value = {"error": "API failed"}
    res = create_purchase_order.invoke({"supplier_code": "SUP-1", "items": []})
    assert "API failed" in res

@patch("src.agents.tools._api_get")
def test_create_purchase_order_product_error(mock_get):
    mock_get.side_effect = [[{"id": 1, "supplier_code": "SUP-1"}], {"error": "API failed"}]
    res = create_purchase_order.invoke({"supplier_code": "SUP-1", "items": []})
    assert "API failed" in res

@patch("src.agents.tools.ask_question")
def test_rag_knowledge_base_dict(mock_ask):
    mock_ask.return_value = "String answer"
    res = rag_knowledge_base.invoke({"query": "q"})
    assert res == "String answer"


# --- get_dashboard_stats -----------------------------------------------------
#
# This tool was added because the Phase 3 specification's own overview names
# "What is the total value of our current inventory?" as a query the agent must
# answer, and no tool reached `/dashboard` -- the one endpoint that knows. The
# agent could enumerate products but had no way to total them.

@patch("src.agents.tools._api_get")
def test_get_dashboard_stats_hits_the_dashboard_endpoint(mock_get):
    mock_get.return_value = {
        "total_products": 5, "low_stock_count": 1, "out_of_stock_count": 2,
        "open_po_count": 3, "total_stock_value": 203700.0,
    }
    res = get_dashboard_stats.invoke({})

    mock_get.assert_called_once_with("/dashboard")
    # Every field the endpoint returns has to survive into the answer; a tool that
    # quietly drops `total_stock_value` would still look like it worked.
    for expected in ("5", "1", "2", "3", "203700.0"):
        assert expected in res, f"{expected} missing from {res!r}"
    assert "total value of current inventory" in res

@patch("src.agents.tools._api_get")
def test_get_dashboard_stats_surfaces_api_errors(mock_get):
    mock_get.return_value = {"error": "API failed"}
    assert "API failed" in get_dashboard_stats.invoke({})


# --- get_supplier_catalog ----------------------------------------------------
#
# `GET /suppliers/{id}/catalog` was implemented and tested in Phase 1 and then had
# no caller anywhere -- not the React frontend, not the agent. This tool gives it
# one. `get_supplier_info` returns a supplier's *terms*, not what it sells.

@patch("src.agents.tools._api_get")
def test_get_supplier_catalog_resolves_a_supplier_code_to_an_id(mock_get):
    """A conversation names a supplier by code; the endpoint is keyed on the id."""
    mock_get.side_effect = [
        [{"id": 7, "supplier_code": "SUP-0002", "name": "Metro Wholesale"}],
        [{"sku": "SKU-GRO-0001", "name": "Basmati Rice", "cost_price": 280.0,
          "unit_of_measure": "box", "stock_level": {"quantity_on_hand": 12}}],
    ]
    res = get_supplier_catalog.invoke({"supplier": "SUP-0002"})

    assert mock_get.call_args_list[0].args == ("/suppliers",)
    assert mock_get.call_args_list[1].args == ("/suppliers/7/catalog",)
    assert "SKU-GRO-0001" in res and "Basmati Rice" in res
    assert "280.0" in res
    assert "Metro Wholesale" in res

@patch("src.agents.tools._api_get")
def test_get_supplier_catalog_accepts_a_numeric_id_without_a_lookup(mock_get):
    """A numeric argument must not cost a wasted round trip to /suppliers."""
    mock_get.return_value = [
        {"sku": "SKU-HOU-0001", "name": "Detergent", "cost_price": 90.0,
         "unit_of_measure": "pieces", "stock_level": {"quantity_on_hand": 4}}
    ]
    res = get_supplier_catalog.invoke({"supplier": "3"})

    mock_get.assert_called_once_with("/suppliers/3/catalog")
    assert "SKU-HOU-0001" in res

@patch("src.agents.tools._api_get")
def test_get_supplier_catalog_unknown_code(mock_get):
    mock_get.return_value = [{"id": 1, "supplier_code": "SUP-0001"}]
    res = get_supplier_catalog.invoke({"supplier": "SUP-9999"})

    assert "not found" in res
    # It must not go on to call the catalog endpoint with `None` as the id.
    assert mock_get.call_count == 1

@patch("src.agents.tools._api_get")
def test_get_supplier_catalog_empty_is_not_reported_as_an_error(mock_get):
    """No products on file is a real, sayable answer -- not a failure."""
    mock_get.side_effect = [
        [{"id": 2, "supplier_code": "SUP-0003", "name": "Sunrise Foods"}],
        [],
    ]
    res = get_supplier_catalog.invoke({"supplier": "SUP-0003"})

    assert "no products" in res.lower()
    assert "error" not in res.lower()

@patch("src.agents.tools._api_get")
def test_get_supplier_catalog_surfaces_api_errors(mock_get):
    mock_get.return_value = {"error": "API failed"}
    assert "API failed" in get_supplier_catalog.invoke({"supplier": "SUP-0001"})


# --- Mandated observability --------------------------------------------------

@pytest.mark.parametrize("tool_obj, payload", [
    (get_dashboard_stats, {}),
    (get_low_stock_alerts, {}),
    (get_product_stock, {"sku": "SKU-1"}),
    (get_supplier_info, {"supplier_code": "SUP-1"}),
    (get_supplier_catalog, {"supplier": "1"}),
])
@patch("src.agents.tools._api_get")
def test_every_tool_emits_the_mandated_tool_called_event(mock_get, tool_obj, payload):
    """Phase 3 requires a structured `tool_called` record naming the POC and phase.

    Before this, `grep -rn tool_called` over the agent package matched nothing: the
    tools opened spans but set no attributes and logged no structured event, so a
    trace showed that some tool ran without saying which POC, phase, or tool it was.
    """
    mock_get.return_value = {}
    with patch("src.agents.tools.logger") as mock_logger:
        tool_obj.invoke(payload)

    events = [c for c in mock_logger.info.call_args_list if c.args and c.args[0] == "tool_called"]
    assert len(events) == 1, f"{tool_obj.name} emitted {len(events)} tool_called events"
    kwargs = events[0].kwargs
    assert kwargs["poc_id"] == "POC-07"
    assert kwargs["phase"] == "P3"
    assert kwargs["tool"] == tool_obj.name

def test_tool_span_sets_the_mandated_span_attributes():
    """The span must carry poc_id/phase/tool, not just exist."""
    from src.agents import tools as tools_mod

    span = MagicMock()
    fake_tracer = MagicMock()
    fake_tracer.start_as_current_span.return_value.__enter__.return_value = span

    with patch.object(tools_mod, "tracer", fake_tracer):
        with tools_mod._tool_span("get_dashboard_stats"):
            pass

    fake_tracer.start_as_current_span.assert_called_once_with("tool_get_dashboard_stats")
    recorded = {c.args[0]: c.args[1] for c in span.set_attribute.call_args_list}
    assert recorded == {"poc_id": "POC-07", "phase": "P3", "tool": "get_dashboard_stats"}

def test_tool_span_still_runs_the_body_without_a_tracer():
    """OpenTelemetry is optional at import time; the tools must not depend on it."""
    from src.agents import tools as tools_mod

    ran = []
    with patch.object(tools_mod, "tracer", None):
        with tools_mod._tool_span("get_dashboard_stats"):
            ran.append(True)
    assert ran == [True]
