from dotenv import load_dotenv
load_dotenv()
import os
import sys
import logging
import contextlib
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

# Environment setup defaults.
# Only advertise tracing when a key is actually configured. Setting
# LANGCHAIN_TRACING_V2=true unconditionally makes the LangChain callback handler
# ship every span to api.smith.langchain.com, which 401s on every run and floods
# stderr with "Failed to send compressed multipart ingest ... 401 Unauthorized".
os.environ.setdefault("LANGCHAIN_PROJECT", "AI-Readiness-POC-07-P2")
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")

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
    from src.model_config import chat_model

    llm = ChatGoogleGenerativeAI(model=chat_model(), temperature=0.2)


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

    # OpenTelemetry span must WRAP the retrieval+generation work.
    # Previously the code did `span_context = tracer.start_as_current_span(...)`
    # without entering it, then called `__exit__` in a finally block. Creating a
    # generator-based context manager does not start a span; the un-entered
    # `__exit__` starts it and immediately raises "generator didn't stop", which
    # was swallowed. Net effect: the span reported 0.04ms for a 4000ms query --
    # 0.001% of the work -- and only ended when the generator was garbage
    # collected. ExitStack enters the span properly so its duration is real.
    with contextlib.ExitStack() as stack:
        try:
            from opentelemetry import trace
            tracer = trace.get_tracer("POC-07-RAG-Tracer")
            span = stack.enter_context(tracer.start_as_current_span("rag_retrieve_and_generate"))
            span.set_attribute("poc_id", "POC-07")
            span.set_attribute("phase", "P2")
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

            # Report a failure *as* a failure. This used to return
            # `answer=f"Error executing query: {e}"`, which put the provider's
            # raw payload into the field the UI renders as the assistant's reply
            # -- an operator asking about PO approval thresholds was shown a
            # Google 429 JSON blob quoting internal quota ids
            # ("EmbedContentRequestsPerDayPerUserPerProjectPerModel-FreeTier"),
            # a billing URL and a stack of RPC type names, styled as an answer.
            #
            # The structural problem is worse than the wording: with the error
            # text living in `answer`, a caller cannot tell a failure from a
            # reply. Anything checking "did I get a non-empty answer" scored a
            # quota outage as a successful response. `error` and `is_error` make
            # the distinction checkable; `answer` keeps a sentence fit to show a
            # user, and the diagnostic detail stays in `error` and the log.
            detail = str(e)
            lowered = detail.lower()
            if "resource_exhausted" in lowered or "429" in detail or "quota" in lowered:
                message = (
                    "The inventory manual is temporarily unavailable: the language model "
                    "provider's request quota is exhausted. This is a service limit, not a "
                    "gap in the manual — the same question should work once the quota resets."
                )
            else:
                message = (
                    "The inventory manual could not be searched because of a technical error. "
                    "No answer is available for this question right now — please retry, and "
                    "treat this as a failure rather than as 'the manual does not say'."
                )
            return {
                "answer": message,
                "source_documents": [],
                "query": question,
                "is_error": True,
                "error": detail,
            }
