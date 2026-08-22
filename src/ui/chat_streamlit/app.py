import os
import sys
import uuid
import json
import requests
import structlog

class _SafeWriter:
    def write(self, s):
        try:
            if hasattr(sys, "__stdout__") and sys.__stdout__:
                sys.__stdout__.write(s)
        except Exception:
            pass
    def flush(self):
        pass

try:
    structlog.configure(
        logger_factory=structlog.PrintLoggerFactory(file=_SafeWriter()),
        cache_logger_on_first_use=False
    )
except Exception:
    pass

# Ensure repository root is on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import streamlit as st
from src.rag.rag_chain import build_rag_chain, ask_question
from src.mcp_server.chat_interface import process_message, ChatSession, build_chat_executor
from src.agents.multi_agent.graph import analyze_product

# Page Configuration
st.set_page_config(
    page_title="POC-07 — Retail Inventory & Procurement Assistant",
    page_icon="📦",
    layout="wide"
)

# Session state initialization
if "session_id" not in st.session_state:
    st.session_state["session_id"] = f"session-{uuid.uuid4().hex[:8]}"

if "mcp_messages" not in st.session_state:
    st.session_state["mcp_messages"] = [
        {
            "role": "assistant",
            "content": "👋 Hello! I am your **POC-07 Retail Inventory & Procurement Assistant** powered by FastMCP and Gemini 2.0 Flash.\n\nI can help you check real-time stock levels, view low-stock alerts, inspect supplier catalogs, generate purchase orders, and monitor overall inventory dashboard health."
        }
    ]

if "rag_messages" not in st.session_state:
    st.session_state["rag_messages"] = [
        {
            "role": "assistant",
            "content": "📚 Hello! I am your **POC-07 Inventory Operations Manual Assistant**. Ask me any policy, SKU format, PO lifecycle, or SOP question from the operational guidelines!"
        }
    ]

if "multi_agent_result" not in st.session_state:
    st.session_state["multi_agent_result"] = None

# Backend Health Check
api_base = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
backend_online = False
try:
    health_resp = requests.get(f"{api_base.replace('/api/v1', '')}/health", timeout=2)
    backend_online = health_resp.status_code == 200
except Exception:
    backend_online = False

# Sidebar metadata & settings
with st.sidebar:
    st.title("📦 System Metadata")
    st.markdown("**Program:** AI Readiness Training Program")
    st.markdown("**POC:** POC-07 — Inventory & Procurement")
    st.markdown("**Active Phases:** Phase 2 (RAG), Phase 4 (FastMCP), Phase 5 (LangGraph Multi-Agent)")
    st.markdown("---")
    
    st.subheader("🔌 Connection Status")
    if backend_online:
        st.success("🟢 FastAPI Backend: Connected (`localhost:8000`)")
    else:
        st.warning("🟡 FastAPI Backend: Offline / Mock Fallback")
    
    st.markdown("- **MCP Server:** FastMCP ('Inventory Management Server')")
    st.markdown("- **Multi-Agent Engine:** LangGraph (`StateGraph`)")
    st.markdown("- **Observability:** LangSmith (`AI-Readiness-POC-07-P5`)")
    st.markdown(f"- **Session ID:** `{st.session_state['session_id']}`")
    st.markdown("---")
    
    if st.button("🔄 Reset Conversation & Session", use_container_width=True):
        st.session_state["session_id"] = f"session-{uuid.uuid4().hex[:8]}"
        st.session_state["mcp_messages"] = [
            {
                "role": "assistant",
                "content": "👋 Conversation reset! How can I assist you with inventory and procurement today?"
            }
        ]
        st.session_state["rag_messages"] = [
            {
                "role": "assistant",
                "content": "📚 RAG Conversation reset! What would you like to know from the inventory manual?"
            }
        ]
        st.session_state["multi_agent_result"] = None
        st.rerun()

st.title("📦 Retail Inventory Management & Operations Platform")
st.caption("Integrated FastMCP Agentic Assistant, ChromaDB Vector RAG, and LangGraph Multi-Agent Orchestrator")

# Tab Navigation
tab_mcp, tab_rag, tab_multi = st.tabs([
    "🤖 Operations Chat Agent (Phase 4 MCP)",
    "📖 Inventory Manual & SOPs (Phase 2 RAG)",
    "🕸️ Multi-Agent Orchestrator (Phase 5 LangGraph)"
])

# ----------------------------------------------------
# TAB 1: Phase 4 FastMCP Operations Chat Agent
# ----------------------------------------------------
with tab_mcp:
    st.subheader("🤖 Conversational Inventory Operations Agent")
    st.markdown("Interact directly with the inventory database using natural language. The agent autonomously selects FastMCP tools to perform real-time queries and actions.")

    # Quick Action Preset Buttons
    col1, col2, col3, col4 = st.columns(4)
    quick_query = None
    with col1:
        if st.button("📊 Health Dashboard", use_container_width=True):
            quick_query = "What is the overall health of our inventory? Show me the dashboard metrics."
    with col2:
        if st.button("⚠️ Low Stock Alerts", use_container_width=True):
            quick_query = "Which products are currently at or below their reorder point?"
    with col3:
        if st.button("📋 Open Purchase Orders", use_container_width=True):
            quick_query = "List all current purchase orders and their status."
    with col4:
        if st.button("🏢 Supplier 1 Catalog", use_container_width=True):
            quick_query = "Show me the product catalog and prices for supplier ID 1."

    # Render Chat History
    for msg in st.session_state["mcp_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle User Input
    mcp_input = st.chat_input("Ask about stock levels, purchase orders, suppliers, or dashboard...")
    query_to_run = quick_query or mcp_input

    if query_to_run:
        st.session_state["mcp_messages"].append({"role": "user", "content": query_to_run})
        with st.chat_message("user"):
            st.markdown(query_to_run)

        with st.chat_message("assistant"):
            with st.spinner("🤖 Agent analyzing query and invoking FastMCP tools..."):
                resp = process_message(query_to_run, session_id=st.session_state["session_id"])
                agent_output = resp.get("output", "No response generated.")
                st.markdown(agent_output)
                st.session_state["mcp_messages"].append({
                    "role": "assistant",
                    "content": agent_output
                })

# ----------------------------------------------------
# TAB 2: Phase 2 RAG Assistant
# ----------------------------------------------------
with tab_rag:
    st.subheader("📖 Knowledge Base & Standard Operating Procedures (RAG)")
    st.markdown("Query the operational user manual stored in the ChromaDB vector database using Google Gemini embeddings.")

    # Initialize RAG Chain
    if "rag_chain" not in st.session_state:
        with st.spinner("Initializing ChromaDB vectorstore and LangChain Gemini 2.0 Flash RAG chain..."):
            try:
                st.session_state["rag_chain"] = build_rag_chain()
            except Exception as e:
                st.error(f"Error initializing RAG chain: {e}")
                st.session_state["rag_chain"] = None

    # Render RAG Chat History
    for msg in st.session_state["rag_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sources" in msg and msg["sources"]:
                with st.expander("📄 View Retrieved Source Document Chunks"):
                    for i, doc in enumerate(msg["sources"]):
                        st.markdown(f"**Chunk {i+1}:**")
                        st.caption(doc.page_content if hasattr(doc, "page_content") else str(doc))

    if rag_input := st.chat_input("Ask a question about inventory policies or SOPs...", key="rag_input_box"):
        st.session_state["rag_messages"].append({"role": "user", "content": rag_input})
        with st.chat_message("user"):
            st.markdown(rag_input)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving manual context and generating answer..."):
                chain = st.session_state.get("rag_chain")
                result = ask_question(rag_input, chain)
                answer = result.get("answer", "I don't have that information in the inventory manual.")
                sources = result.get("source_documents", [])

                st.markdown(answer)
                if sources:
                    with st.expander("📄 View Retrieved Source Document Chunks"):
                        for i, doc in enumerate(sources):
                            st.markdown(f"**Chunk {i+1}:**")
                            st.caption(doc.page_content if hasattr(doc, "page_content") else str(doc))

                st.session_state["rag_messages"].append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

# ----------------------------------------------------
# TAB 3: Phase 5 Multi-Agent Orchestrator (LangGraph)
# ----------------------------------------------------
with tab_multi:
    st.subheader("🕸️ Autonomous Multi-Agent Pipeline (LangGraph)")
    st.markdown("Execute the four-agent autonomous pipeline to audit inventory, forecast velocity, recommend replenishment, quote suppliers, and generate an executive report.")

    col_input, col_action = st.columns([3, 1])
    with col_input:
        target_product_id = st.number_input("Select Product ID for End-to-End Analysis:", min_value=1, max_value=100, value=1, step=1)
    with col_action:
        st.write("")
        st.write("")
        run_analysis = st.button("🚀 Run Multi-Agent Audit", use_container_width=True, type="primary")

    if run_analysis:
        with st.spinner(f"Executing LangGraph pipeline for Product #{target_product_id}..."):
            try:
                res = analyze_product(target_product_id)
                st.session_state["multi_agent_result"] = res
            except Exception as e:
                st.error(f"Multi-Agent execution failed: {e}")

    res = st.session_state.get("multi_agent_result")
    if res:
        st.success(f"✅ Pipeline Completed with Status: **{res.get('analysis_status', 'complete').upper()}**")
        
        # Overview KPI Cards
        p_data = res.get("product_data", {})
        d_forecast = res.get("demand_forecast", {})
        r_rec = res.get("reorder_recommendation", {})
        s_quote = res.get("supplier_quote", {})
        stock = p_data.get("stock_level", {}) if isinstance(p_data.get("stock_level"), dict) else {}

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("SKU / Product", f"{p_data.get('sku', 'SKU-001')}", p_data.get("name", "Product"))
        kpi2.metric("Available Stock", f"{stock.get('quantity_available', 0)} units", f"Reorder Pt: {p_data.get('reorder_point', 0)}")
        kpi3.metric("Stockout Risk", f"{str(d_forecast.get('stockout_risk', 'unknown')).upper()}", f"{d_forecast.get('days_of_stock_remaining', 0)} days runway")
        kpi4.metric("Reorder Urgency", f"{str(r_rec.get('urgency', 'None')).replace('_', ' ').title()}", f"{r_rec.get('recommended_quantity', 0)} units")

        st.markdown("---")
        
        # 4 Agent Outputs in Tabs / Accordions
        a1, a2, a3 = st.columns(3)
        with a1:
            st.markdown("#### 1️⃣ Demand Forecaster")
            st.json(d_forecast)
        with a2:
            st.markdown("#### 2️⃣ Reorder Agent")
            st.json(r_rec)
        with a3:
            st.markdown("#### 3️⃣ Supplier Coordinator")
            st.json(s_quote)

        st.markdown("#### 4️⃣ Inventory Auditor Executive Report")
        st.info(res.get("audit_report", "No report available."))

        with st.expander("📜 View Agent Execution Message Trail & State"):
            st.write("##### Step-by-Step Message Trail:")
            for m in res.get("messages", []):
                st.markdown(f"- `{m}`")
            if res.get("errors"):
                st.write("##### Error Log Trail:")
                for err in res.get("errors", []):
                    st.error(err)
            st.write("##### Full State Payload:")
            st.json(res)
