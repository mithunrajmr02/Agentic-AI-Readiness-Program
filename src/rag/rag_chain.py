from dotenv import load_dotenv
load_dotenv()
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

try:
    from langchain_core.prompts import PromptTemplate
except ImportError:
    from langchain.prompts import PromptTemplate

try:
    from langchain_classic.chains import RetrievalQA
except ImportError:
    try:
        from langchain.chains.retrieval_qa.base import RetrievalQA
    except ImportError:
        from langchain_community.chains import RetrievalQA

from langchain_community.vectorstores import Chroma
from langchain_core.language_models.llms import LLM

# Configure logging for observability
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [POC-07] %(message)s")
logger = logging.getLogger("rag_chain")

# Environment setup defaults
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "AI-Readiness-POC-07-P2")

DEFAULT_NO_INFO_MSG = "I don't have that information in the inventory manual."

# Define prompt template exactly as specified
INVENTORY_RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are an inventory management expert assistant for a retail operations system (POC-07).
Answer questions about inventory policies, procurement procedures, stock management, and supplier guidelines
using only the provided context.

Context:
{context}

Question: {question}

If the information is not available, say: "I don't have that information in the inventory manual."
Provide specific rules, formulas, and thresholds where available.

Answer:"""
)



def get_vectorstore(persist_dir: str = str(PROJECT_ROOT / "chroma_db"), collection_name: str = "inventory_manual") -> Chroma:
    """Retrieve or create ChromaDB vectorstore instance."""
    from src.rag.ingest import get_embeddings
    embeddings = get_embeddings()
    
    if not os.path.exists(persist_dir):
        # Fallback in case it's in a sub-folder somehow
        alt_paths = [
            str(PROJECT_ROOT / "src" / "rag" / "chroma_db"),
            str(PROJECT_ROOT / "phase2" / "chroma_db"),
        ]
        for path in alt_paths:
            if os.path.exists(path):
                persist_dir = path
                break

    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_dir
    )


def build_rag_chain(persist_dir: str = str(PROJECT_ROOT / "chroma_db"), collection_name: str = "inventory_manual") -> RetrievalQA:
    """Build and return RetrievalQA chain using Gemini Flash and ChromaDB."""
    logger.info("Initializing RAG RetrievalQA Chain for POC-07...")
    vectorstore = get_vectorstore(persist_dir, collection_name)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm_model = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash-lite")
    llm = ChatGoogleGenerativeAI(model=llm_model, temperature=0.2)


    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": INVENTORY_RAG_PROMPT}
    )


def ask_question(question: str, chain: Optional[Any] = None) -> Dict[str, Any]:
    """
    Execute question answering query through the RAG chain.
    Integrates LangSmith tracing and OpenTelemetry span instrumentation.
    """
    if chain is None:
        chain = build_rag_chain()

    logger.info(f"Executing query for POC-07: '{question}'")
    
    if not question or not question.strip():
        return {
            "answer": DEFAULT_NO_INFO_MSG,
            "source_documents": []
        }

    # OpenTelemetry tracer setup
    tracer = None
    span_context = None
    try:
        from opentelemetry import trace
        tracer = trace.get_tracer("POC-07-RAG-Tracer")
        span_context = tracer.start_as_current_span("rag_retrieve_and_generate")
    except (ImportError, RuntimeError, AttributeError):
        pass

    try:
        if os.getenv("LANGCHAIN_API_KEY"):
            try:
                from langsmith import traceable
                @traceable(project_name="AI-Readiness-POC-07-P2")
                def _run_query(q, c):
                    return c.invoke({"query": q})
                res = _run_query(question, chain)
            except (ImportError, RuntimeError, AttributeError):
                res = chain.invoke({"query": question})
        else:
            res = chain.invoke({"query": question})

        answer = res.get("result", "") or res.get("answer", "")
        source_documents = res.get("source_documents", [])
        
        return {
            "answer": answer,
            "source_documents": source_documents,
            "query": question
        }
    except Exception as e:
        logger.error(f"Error during RAG chain execution for POC-07: {e}")
        return {
            "answer": f"Error executing query: {str(e)}",
            "source_documents": []
        }
    finally:
        if span_context:
            try:
                span_context.__exit__(None, None, None)
            except Exception:
                pass
