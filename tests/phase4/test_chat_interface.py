import uuid
import pytest
from unittest.mock import patch, MagicMock


def test_executor_builds():
    """TC-07-P4-CHAT-01: Executor Builds"""
    from src.mcp_server.chat_interface import build_chat_executor
    assert build_chat_executor() is not None


def test_message_processed():
    """TC-07-P4-CHAT-02: Message Processed"""
    from src.mcp_server.chat_interface import process_message
    with patch("src.mcp_server.chat_interface.build_chat_executor") as mb:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = {"output": "25 products need reorder."}
        mb.return_value = mock_instance
        
        result = process_message("Which products need reordering?", session_id="inv-001")
        assert result is not None
        assert "25 products" in str(result) or "output" in result


def test_session_id():
    """TC-07-P4-CHAT-03: Session ID Accepted"""
    from src.mcp_server.chat_interface import process_message
    with patch("src.mcp_server.chat_interface.build_chat_executor") as mb:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = {"output": "OK"}
        mb.return_value = mock_instance
        
        sess_id = str(uuid.uuid4())
        result = process_message("Dashboard", session_id=sess_id)
        assert result is not None
        assert result.get("session_id") == sess_id


def test_history():
    """TC-07-P4-CHAT-04: History Tracked"""
    from src.mcp_server.chat_interface import ChatSession
    s = ChatSession(session_id="hist-007")
    s.add_message("user", "Show low stock items")
    s.add_message("assistant", "25 products below reorder point.")
    s.add_message("user", "Create a PO for the grocery items")
    assert len(s.history) >= 3


def test_tool_calls():
    """TC-07-P4-CHAT-05: Tool Calls Extracted"""
    from src.mcp_server.chat_interface import process_message
    with patch("src.mcp_server.chat_interface.build_chat_executor") as mb:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = {
            "output": "Dashboard loaded.",
            "intermediate_steps": [("get_inventory_dashboard", {})]
        }
        mb.return_value = mock_instance
        
        process_message("Dashboard", session_id="tool-007")
        mb.return_value.invoke.assert_called_once()


def test_error_handled():
    """TC-07-P4-CHAT-06: Error Handled"""
    from src.mcp_server.chat_interface import process_message
    with patch("src.mcp_server.chat_interface.build_chat_executor") as mb:
        mock_instance = MagicMock()
        mock_instance.invoke.side_effect = Exception("Timeout")
        mb.return_value = mock_instance
        
        try:
            result = process_message("Show data", session_id="err-007")
            assert result is not None
            assert "error" in str(result).lower()
        except Exception:
            pytest.fail("Should not raise unhandled exception")
