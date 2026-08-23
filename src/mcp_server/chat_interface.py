from dotenv import load_dotenv
load_dotenv()

import os
from typing import List, Dict, Any, Optional
import structlog
from langchain_google_genai import ChatGoogleGenerativeAI

try:
    from langchain_classic.agents import AgentExecutor, create_react_agent
except ImportError:  # pragma: no cover
    try:
        from langchain.agents import AgentExecutor, create_react_agent
    except ImportError:
        from langchain.agents.agent import AgentExecutor
        from langchain.agents.react.agent import create_react_agent

from langchain_core.prompts import PromptTemplate
from langchain_core.tools import StructuredTool

try:
    from langchain import hub
except Exception:  # pragma: no cover
    hub = None

try:
    from langsmith import traceable
except Exception:  # pragma: no cover
    def traceable(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator

from src.mcp_server.mcp_app import (
    update_stock,
    create_purchase_order,
    get_low_stock_products,
    get_supplier_catalog,
    get_purchase_orders,
    get_inventory_dashboard,
)

logger = structlog.get_logger()

# Fallback ReAct prompt template in case LangChain Hub is unreachable offline
DEFAULT_REACT_PROMPT_TEMPLATE = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""


class ChatSession:
    """Manages chat message history and context window for a conversational session."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def get_history_for_llm(self) -> List[Dict[str, str]]:
        return self.history[-10:]


def build_chat_executor() -> AgentExecutor:
    """Constructs and returns the LangChain ReAct agent executor wired to FastMCP tools."""
    # Model name and key resolution are centralised so the five call sites that
    # read GEMINI_CHAT_MODEL cannot drift apart again. See src/model_config.py.
    from src.model_config import api_key as resolve_api_key, chat_model

    llm = ChatGoogleGenerativeAI(
        model=chat_model(),
        temperature=0.1,
        google_api_key=resolve_api_key()
    )

    tools = [
        StructuredTool.from_function(
            func=update_stock,
            name="update_stock",
            description="Record a stock movement for a product (receipt, sale, adjustment, transfer, return)."
        ),
        StructuredTool.from_function(
            func=create_purchase_order,
            name="create_purchase_order",
            description="Create a purchase order for a supplier with line items (product_id, quantity_ordered, unit_cost)."
        ),
        StructuredTool.from_function(
            func=get_low_stock_products,
            name="get_low_stock_products",
            description="Get all low stock and out-of-stock products currently at or below their reorder point."
        ),
        StructuredTool.from_function(
            func=get_supplier_catalog,
            name="get_supplier_catalog",
            description="Get supplier product catalog with SKUs, product names, and prices."
        ),
        StructuredTool.from_function(
            func=get_purchase_orders,
            name="get_purchase_orders",
            description="List purchase orders by status or supplier."
        ),
        StructuredTool.from_function(
            func=get_inventory_dashboard,
            name="get_inventory_dashboard",
            description="Get inventory dashboard metrics and health summary."
        ),
    ]

    prompt = None
    if hub is not None:
        try:
            prompt = hub.pull("hwchase17/react")
        except Exception:
            prompt = None

    if prompt is None:
        prompt = PromptTemplate.from_template(DEFAULT_REACT_PROMPT_TEMPLATE)

    agent = create_react_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5
    )


@traceable(project_name="AI-Readiness-POC-07-P4")
def process_message(message: str, session_id: str = "default") -> dict:
    """Processes a user chat message using the MCP agent executor and returns a structured response."""
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
        try:
            logger.error("chat_error", poc_id="POC-07", phase="P4", error=str(e))
        except Exception:
            pass
        return {"output": f"Error: {str(e)}", "session_id": session_id}
