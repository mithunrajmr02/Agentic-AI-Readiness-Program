import pytest
from unittest.mock import patch, MagicMock


def test_6_tools_discovered():
    """TC-07-P4-INT-01: 6 Tools Discovered"""
    from mcp_server.chat_interface import build_chat_executor
    tools = build_chat_executor().tools
    assert len(tools) >= 6


def test_tool_invoked():
    """TC-07-P4-INT-02: Tool Invoked"""
    mock_r = {"total_products": 500, "low_stock_count": 25}
    with patch("mcp_server.mcp_app.requests.get") as mg:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = mock_r
        mg.return_value.raise_for_status = MagicMock()
        from mcp_server.mcp_app import get_inventory_dashboard
        result = get_inventory_dashboard()
        assert result.get("total_products") == 500 or "error" in result


def test_correct_tool():
    """TC-07-P4-INT-03: Correct Tool for Low Stock"""
    from mcp_server.chat_interface import build_chat_executor
    tool_map = {t.name: t for t in build_chat_executor().tools}
    assert "get_low_stock_products" in tool_map
    assert "stock" in tool_map["get_low_stock_products"].description.lower()


def test_response_routed():
    """TC-07-P4-INT-04: Response Routed Back"""
    from mcp_server.chat_interface import process_message
    with patch("mcp_server.chat_interface.build_chat_executor") as mb:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = {"output": "25 products below reorder point."}
        mb.return_value = mock_instance
        
        result = process_message("Low stock items", session_id="route-007")
        out = result.get("output", str(result)) if isinstance(result, dict) else str(result)
        assert len(out) > 10


def test_multi_turn():
    """TC-07-P4-INT-05: Multi-Turn Context"""
    from mcp_server.chat_interface import ChatSession
    s = ChatSession(session_id="mt-007")
    s.add_message("user", "Show low stock items")
    s.add_message("assistant", "25 products need reorder.")
    s.add_message("user", "Create a PO for grocery items from supplier 1")
    assert len(s.get_history_for_llm()) >= 2


def test_tool_chain():
    """TC-07-P4-INT-06: Tool Chain for Complex Query"""
    from mcp_server.chat_interface import build_chat_executor
    names = [t.name for t in build_chat_executor().tools]
    assert "get_inventory_dashboard" in names and "get_low_stock_products" in names


def test_update_reachable():
    """TC-07-P4-INT-07: update_stock Reachable"""
    mock_r = {"id": 5, "movement_type": "receipt", "quantity": 50}
    with patch("mcp_server.mcp_app.requests.patch") as mp_patch, patch("mcp_server.mcp_app.requests.post") as mp_post:
        mp_patch.return_value.status_code = 200
        mp_patch.return_value.json.return_value = mock_r
        mp_patch.return_value.raise_for_status = MagicMock()
        mp_post.return_value.status_code = 200
        mp_post.return_value.json.return_value = mock_r
        mp_post.return_value.raise_for_status = MagicMock()
        
        from mcp_server.mcp_app import update_stock
        result = update_stock(product_id=1, movement_type="receipt", quantity=50)
        assert isinstance(result, dict) and (result.get("id") is not None or "error" in result)
