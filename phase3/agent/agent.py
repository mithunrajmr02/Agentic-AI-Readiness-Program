from dotenv import load_dotenv
load_dotenv()
import os
import logging
from typing import Optional, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import initialize_agent, AgentType, AgentExecutor

from phase3.agent.prompts import INVENTORY_AGENT_SYSTEM_PROMPT
from phase3.agent.tools import (
    get_product_stock,
    get_low_stock_alerts,
    create_purchase_order,
    get_supplier_info,
    rag_knowledge_base
)

logger = logging.getLogger("agent.core")

def get_llm():
    model_name = os.environ.get("GEMINI_CHAT_MODEL", "gemini-1.5-flash")
    return ChatGoogleGenerativeAI(
        model=model_name,
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
        return f"Error executing query: {str(e)}"
