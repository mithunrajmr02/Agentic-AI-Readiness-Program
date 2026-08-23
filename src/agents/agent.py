from dotenv import load_dotenv
load_dotenv()
import os
import logging
from typing import Optional, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import initialize_agent, AgentType, AgentExecutor

from src.agents.prompts import INVENTORY_AGENT_SYSTEM_PROMPT
from src.agents.tools import (
    get_product_stock,
    get_low_stock_alerts,
    create_purchase_order,
    get_supplier_info,
    get_supplier_catalog,
    get_dashboard_stats,
    rag_knowledge_base
)

logger = logging.getLogger("agent.core")

# `run_agent` reports failure by returning a string rather than raising, so a caller
# has no other way to tell an answer from an error. Naming the prefix here means the
# UI can render a failure as a failure instead of letting it settle into the chat
# transcript looking like something the agent concluded.
AGENT_ERROR_PREFIX = "Error executing query:"

def get_llm():
    # Was `os.environ.get("GEMINI_CHAT_MODEL", "gemini-1.5-flash")`. That default
    # names a model the API does not serve, so a clone without a .env failed here.
    # See src/model_config.py.
    from src.model_config import chat_model

    return ChatGoogleGenerativeAI(
        model=chat_model(),
        temperature=0.0
    )

def build_agent_executor() -> AgentExecutor:
    """Build and return the LangChain ReAct AgentExecutor for Phase 3."""
    logger.info("Initializing Phase 3 LangChain ReAct Agent...")
    
    # Initialize LLM
    llm = get_llm()

    # Define tools
    tools = [
        get_product_stock,
        get_low_stock_alerts,
        create_purchase_order,
        get_supplier_info,
        get_supplier_catalog,
        get_dashboard_stats,
        rag_knowledge_base
    ]

    # Initialize Agent
    agent_executor = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
        agent_kwargs={
            "prefix": INVENTORY_AGENT_SYSTEM_PROMPT
        }
    )
    
    return agent_executor

def run_agent(query: str, agent_executor: Optional[AgentExecutor] = None) -> str:
    """Execute a query against the ReAct agent."""
    if agent_executor is None:
        agent_executor = build_agent_executor()
        
    logger.info(f"Running Agent with query: {query}")
    try:
        response = agent_executor.invoke({"input": query})
        return response.get("output", str(response))
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return f"{AGENT_ERROR_PREFIX} {str(e)}"


if __name__ == "__main__":
    import sys
    agent = build_agent_executor()
    query = sys.argv[1] if len(sys.argv) > 1 else "Check stock for SKU-GRO-0001 and tell me if reorder is needed."
    print(f"\nUser Query: {query}\n" + "="*50)
    res = run_agent(query, agent)
    print(f"\nAgent Response:\n{res}\n" + "="*50)
