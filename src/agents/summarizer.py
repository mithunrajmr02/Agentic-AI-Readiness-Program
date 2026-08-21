import os
from dotenv import load_dotenv
load_dotenv()
import logging
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains.summarize import load_summarize_chain

logger = logging.getLogger("agent.summarizer")

def _summarize_if_long(data: List[Dict[str, Any]], max_items: int = 5) -> str:
    """Summarizes a long list of items using LangChain's summarize chain."""
    if not data:
        return "[]"
    if len(data) <= max_items:
        # If it's short, just return a formatted string
        return "\n".join([str(item) for item in data])
        
    logger.info(f"Data contains {len(data)} items, which exceeds {max_items}. Summarizing...")
    
    # Convert data to Documents
    docs = [Document(page_content=str(item)) for item in data]
    
    # Initialize LLM
    try:
        model_name = os.environ.get("GEMINI_CHAT_MODEL", "gemini-1.5-flash")
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
        chain = load_summarize_chain(llm, chain_type="stuff")
        summary = chain.invoke(docs)
        return f"Summary of {len(data)} items: " + summary.get("output_text", str(summary))
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        # Fallback to truncating
        truncated = data[:max_items]
        return f"Data too long to display. Showing first {max_items} items:\n" + "\n".join([str(item) for item in truncated]) + f"\n... and {len(data) - max_items} more items."
