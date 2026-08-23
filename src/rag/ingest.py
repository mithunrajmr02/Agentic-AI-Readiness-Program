import os
import sys
import logging
from dotenv import load_dotenv
from typing import List, Optional
from langchain_community.document_loaders import TextLoader
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import Chroma

from pathlib import Path

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
COLLECTION_NAME = "inventory_manual"
DEFAULT_PERSIST_DIR = str(PROJECT_ROOT / "chroma_db")


def get_manual_path() -> str:
    """Find and return the absolute path to inventory_manual.md."""
    candidates = [
        str(PROJECT_ROOT / "src" / "rag" / "data" / "inventory_manual.md"),
        str(PROJECT_ROOT / "phase2" / "rag" / "data" / "inventory_manual.md"),
        str(PROJECT_ROOT / "phase2" / "rag" / "inventory_manual.md"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    # Default fallback
    return str(PROJECT_ROOT / "src" / "rag" / "data" / "inventory_manual.md")


def load_documents(file_path: Optional[str] = None) -> List[Document]:
    """Load the Markdown knowledge base document."""
    target_path = file_path or get_manual_path()
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"Inventory manual not found at: {target_path}")

    logger.info(f"Loading knowledge base document from {target_path}")
    loader = TextLoader(target_path, encoding="utf-8")
    docs = loader.load()
    logger.info(f"Successfully loaded document (character count: {len(docs[0].page_content)})")
    return docs


def split_documents(docs: List[Document], chunk_size: int = 600, chunk_overlap: int = 50) -> List[Document]:
    """Split documents into chunks of specified size and overlap."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(docs)
    
    logger.info(f"Generated {len(chunks)} text chunks.")
    if len(chunks) < 20:
        logger.warning(f"Chunk count ({len(chunks)}) is below recommended minimum of 20.")
        
    oversized = [i for i, c in enumerate(chunks) if len(c.page_content) > chunk_size]
    if oversized:
        logger.warning(f"Found {len(oversized)} chunks exceeding maximum character limit of {chunk_size}.")
        
    return chunks


def get_embeddings():
    """Return embedding function (GoogleGenerativeAIEmbeddings)."""
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from src.model_config import api_key as resolve_api_key, embedding_model

    model_name = embedding_model()
    logger.info(f"Initializing GoogleGenerativeAIEmbeddings (model: {model_name})")
    # Previously defaulted to the literal "dummy_fallback_key" and ignored
    # GEMINI_API_KEY, so a clone that set only GEMINI_API_KEY silently embedded
    # against an invalid credential.
    return GoogleGenerativeAIEmbeddings(model=model_name, google_api_key=resolve_api_key())


def drop_collection(persist_dir: str = DEFAULT_PERSIST_DIR, collection_name: str = COLLECTION_NAME) -> bool:
    """Delete a persisted collection if it exists. Returns True if one was removed."""
    if not os.path.exists(persist_dir):
        return False
    try:
        import chromadb
        client = chromadb.PersistentClient(path=persist_dir)
        if collection_name in [c.name for c in client.list_collections()]:
            client.delete_collection(collection_name)
            logger.info(f"Dropped existing collection '{collection_name}' before re-ingestion.")
            return True
    except Exception as e:
        logger.warning(f"Could not drop collection '{collection_name}': {e}")
    return False


def build_vectorstore(
    chunks: Optional[List[Document]] = None,
    persist_dir: str = DEFAULT_PERSIST_DIR,
    collection_name: str = COLLECTION_NAME,
    reset: bool = True
) -> Chroma:
    """Ingest document chunks into ChromaDB vectorstore.

    Ingestion is idempotent by default. Chroma.from_documents() APPENDS to an
    existing collection rather than replacing it, so without dropping first every
    run stores another copy of all chunks. Repeated runs had grown the live
    collection to 1323 vectors over only 21 distinct chunks. Duplicate points
    collapse the HNSW graph into a degenerate clique -- traversal enters it and
    cannot improve, so every query returns the same neighbours at an identical
    distance regardless of what was asked.

    Pass reset=False only to deliberately append to an existing collection.
    """
    if chunks is None:
        docs = load_documents()
        chunks = split_documents(docs)

    embeddings = get_embeddings()
    logger.info(f"Initializing ChromaDB vectorstore at '{persist_dir}' with collection '{collection_name}'")

    if reset:
        drop_collection(persist_dir, collection_name)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=persist_dir
    )

    logger.info(f"Successfully ingested {len(chunks)} chunks into ChromaDB collection '{collection_name}'.")
    return vectorstore


def main():
    """Main execution function for document ingestion."""
    docs = load_documents()
    chunks = split_documents(docs)
    build_vectorstore(chunks=chunks)
    logger.info("Ingestion completed successfully.")


if __name__ == "__main__":
    main()
