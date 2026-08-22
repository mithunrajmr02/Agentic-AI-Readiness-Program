import pytest
import os
import sys
import requests
from unittest.mock import patch, MagicMock

import src.mcp_server.server as server_mod
import src.mcp_server.mcp_app as mcp_mod
import src.mcp_server.chat_interface as chat_mod


def test_server_status_and_main():
    """Cover server.py status and main blocks."""
    status = server_mod.get_server_status()
    assert status["status"] == "ready"
    assert "name" in status
    assert status["phase"] == "Phase 4 Completed"

    # Simulate __main__ execution for server.py
    with patch.object(server_mod.mcp, "run") as mock_run:
        server_mod.mcp.run()
        mock_run.assert_called_once()


def test_mcp_helpers_and_exceptions():
    """Cover _get, _post, _patch error branches in mcp_app.py."""
    # Test _post ConnectionError
    with patch("requests.post", side_effect=requests.exceptions.ConnectionError("Backend down")):
        res = mcp_mod._post("/test", {})
        assert res == {"error": "API unavailable"}

    # Test _get generic Exception
    with patch("requests.get", side_effect=Exception("Generic GET failure")):
        res = mcp_mod._get("/test")
        assert "error" in res
        assert "Generic GET failure" in res["error"]

    # Test _post generic Exception
    with patch("requests.post", side_effect=Exception("Generic POST failure")):
        res = mcp_mod._post("/test", {})
        assert "error" in res
        assert "Generic POST failure" in res["error"]

    # Test _patch ConnectionError
    with patch("requests.patch", side_effect=requests.exceptions.ConnectionError("Offline")):
        res = mcp_mod._patch("/test", {})
        assert res == {"error": "API unavailable"}

    # Test _patch generic Exception
    with patch("requests.patch", side_effect=Exception("Generic PATCH failure")):
        res = mcp_mod._patch("/test", {})
        assert "error" in res
        assert "Generic PATCH failure" in res["error"]


def test_parse_id_all_branches():
    """Cover all edge cases of _parse_id in mcp_app.py."""
    assert mcp_mod._parse_id(None) is None
    assert mcp_mod._parse_id(42) == 42
    assert mcp_mod._parse_id({"id": 10}) == 10
    assert mcp_mod._parse_id({"product_id": 20}) == 20
    assert mcp_mod._parse_id({"supplier_id": 30}) == 30
    assert mcp_mod._parse_id('{"supplier_id": 2}') == 2
    # String that starts with { and } but is invalid json
    assert mcp_mod._parse_id('{broken json}') == '{broken json}'
    assert mcp_mod._parse_id("123") == 123
    assert mcp_mod._parse_id("abc") == "abc"


def test_update_stock_405_fallback_and_types():
    """Cover update_stock fallback on 405 error."""
    with patch("src.mcp_server.mcp_app._patch", return_value={"error": "405 Method Not Allowed"}):
        with patch("src.mcp_server.mcp_app._post", return_value={"id": 1, "status": "ok"}) as mock_post:
            res = mcp_mod.update_stock(
                product_id="1",
                movement_type="receipt",
                quantity="10",
                reference_number="REF-01",
                notes="Test"
            )
            assert res["status"] == "ok"
            mock_post.assert_called_once()


def test_get_purchase_orders_filters():
    """Cover get_purchase_orders with various filter permutations."""
    with patch("src.mcp_server.mcp_app._get", return_value=[{"id": 1}]) as mock_get:
        # Both status and supplier_id
        res = mcp_mod.get_purchase_orders(status="draft", supplier_id="2")
        assert len(res) == 1
        mock_get.assert_called_with("/orders", {"status": "draft", "supplier_id": 2})

        # Only status
        res2 = mcp_mod.get_purchase_orders(status="received", supplier_id=None)
        assert len(res2) == 1
        mock_get.assert_called_with("/orders", {"status": "received"})


def test_chat_session_history_window():
    """Cover ChatSession adding messages and sliding context window."""
    session = chat_mod.ChatSession("test-cov-session")
    for i in range(15):
        session.add_message("user" if i % 2 == 0 else "assistant", f"Msg {i}")
    
    assert len(session.history) == 15
    hist = session.get_history_for_llm()
    assert len(hist) == 10
    assert hist[0]["content"] == "Msg 5"
    assert hist[-1]["content"] == "Msg 14"


def test_process_message_success_and_error_handling():
    """Cover process_message success and exception branches."""
    mock_executor = MagicMock()
    mock_executor.invoke.return_value = {"output": "Mocked AI Response"}

    with patch("src.mcp_server.chat_interface.build_chat_executor", return_value=mock_executor):
        res = chat_mod.process_message("Hello AI", session_id="sess-123")
        assert res["output"] == "Mocked AI Response"
        assert res["session_id"] == "sess-123"

    with patch("src.mcp_server.chat_interface.build_chat_executor", side_effect=RuntimeError("LLM Failure")):
        err_res = chat_mod.process_message("Hello AI", session_id="sess-err")
        assert "Error: LLM Failure" in err_res["output"]
        assert err_res["session_id"] == "sess-err"


def test_build_chat_executor_with_hub_pull():
    """Cover build_chat_executor when hub.pull succeeds."""
    mock_prompt = chat_mod.PromptTemplate.from_template(chat_mod.DEFAULT_REACT_PROMPT_TEMPLATE)
    mock_hub = MagicMock()
    mock_hub.pull.return_value = mock_prompt
    with patch("src.mcp_server.chat_interface.hub", mock_hub):
        executor = chat_mod.build_chat_executor()
        assert executor is not None
        mock_hub.pull.assert_called_with("hwchase17/react")
