import os
import sys

# Ensure repository root and phase2 directory are on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
phase2_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if phase2_dir not in sys.path:
    sys.path.insert(0, phase2_dir)

import streamlit as st
from phase2.rag.rag_chain import build_rag_chain, ask_question

# Page Configuration
st.set_page_config(
    page_title="POC-07 — Inventory Management RAG Assistant",
    page_icon="📦",
    layout="wide"
)

# Sidebar metadata & settings
with st.sidebar:
    st.title("📦 System Metadata")
    st.markdown("**Program:** AI Readiness Training Program")
    st.markdown("**POC:** POC-07 — Inventory & Procurement")
    st.markdown("**Phase:** Phase 2 (RAG Application)")
    st.markdown("---")
    st.subheader("🤖 Model & Architecture Specs")
    st.markdown("- **LLM Model:** Gemini 2.0 Flash")
    st.markdown("- **Embedding Model:** `models/text-embedding-004`")
    st.markdown("- **Vector Store:** ChromaDB (`collection: inventory_manual`)")
    st.markdown("- **Observability Project:** `AI-Readiness-POC-07-P2`")
    st.markdown("- **Retrieval Top-K:** 4 Document Chunks")
    st.markdown("---")
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

st.title("📦 Inventory Management & Operations RAG Assistant")
st.caption("Ask questions about SKU formats, stock levels, PO lifecycles, supplier rules, and inventory valuation.")

# Initialize session state for chain and messages
if "rag_chain" not in st.session_state:
    with st.spinner("Initializing ChromaDB vectorstore and LangChain Gemini 2.0 Flash RAG chain..."):
        try:
            st.session_state["rag_chain"] = build_rag_chain()
        except Exception as e:
            st.error(f"Error initializing RAG chain: {e}")
            st.session_state["rag_chain"] = None

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": "Hello! I am your POC-07 Inventory Operations Assistant. Ask me any question about the inventory operations manual!"
        }
    ]

# Display existing chat messages
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("📄 View Retrieved Source Document Chunks"):
                for i, doc in enumerate(msg["sources"]):
                    st.markdown(f"**Chunk {i+1}:**")
                    st.caption(doc.page_content if hasattr(doc, "page_content") else str(doc))

# Handle new question input
if user_input := st.chat_input("Ask a question about inventory operations..."):
    # Display user query
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process answer via RAG chain
    with st.chat_message("assistant"):
        with st.spinner("Retrieving manual context and generating answer..."):
            chain = st.session_state.get("rag_chain")
            result = ask_question(user_input, chain)
            answer = result.get("answer", "I don't have that information in the inventory manual.")
            sources = result.get("source_documents", [])
            
            st.markdown(answer)
            if sources:
                with st.expander("📄 View Retrieved Source Document Chunks"):
                    for i, doc in enumerate(sources):
                        st.markdown(f"**Chunk {i+1}:**")
                        st.caption(doc.page_content if hasattr(doc, "page_content") else str(doc))

            st.session_state["messages"].append({
                "role": "assistant",
                "content": answer,
                "sources": sources
            })
