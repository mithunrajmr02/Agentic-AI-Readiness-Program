"""Phase 4 facade for chat_interface."""
import structlog
from typing import List, Dict, Any, Optional
from src.mcp_server.chat_interface import (
    ChatSession,
    build_chat_executor as _src_build_chat_executor,
    DEFAULT_REACT_PROMPT_TEMPLATE,
)
from src.mcp_server.mcp_app import (
    update_stock,
    create_purchase_order,
    get_low_stock_products,
    get_supplier_catalog,
    get_purchase_orders,
    get_inventory_dashboard,
)

try:
    from langsmith import traceable
except Exception:
    def traceable(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator

logger = structlog.get_logger()


def build_chat_executor():
    """Builds and returns the agent executor."""
    return _src_build_chat_executor()


@traceable(project_name="AI-Readiness-POC-07-P4")
def process_message(message: str, session_id: str = "default") -> dict:
    """Processes a user message and returns the response."""
    try:
        executor = build_chat_executor()
        logger.info(
            "chat_message",
            poc_id="POC-07",
            phase="P4",
            session_id=session_id,
            message_preview=message[:60]
        )
        result = executor.invoke({"input": message})
        output = result.get("output", "") if isinstance(result, dict) else str(result)
        return {"output": output, "session_id": session_id}
    except Exception as e:
        logger.error("chat_error", poc_id="POC-07", phase="P4", error=str(e))
        return {"output": f"Error: {str(e)}", "session_id": session_id}


__all__ = [
    "ChatSession",
    "build_chat_executor",
    "process_message",
    "update_stock",
    "create_purchase_order",
    "get_low_stock_products",
    "get_supplier_catalog",
    "get_purchase_orders",
    "get_inventory_dashboard",
]
