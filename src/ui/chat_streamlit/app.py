import os
import sys
import uuid
import json
import logging
import requests
import structlog
from datetime import date, timedelta

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
    # Every argument here is passed deliberately, including the two that look
    # redundant. `structlog.configure()` is a *partial* update: keys you omit keep
    # whatever value the process already had. This call used to pass only
    # `logger_factory` and `cache_logger_on_first_use`, which meant it inherited its
    # processor chain and wrapper class from whoever configured structlog first.
    #
    # Inherit them from src/backend/logging_config.py and the result is a
    # configuration that cannot log at all: that chain starts with
    # `structlog.stdlib.filter_by_level`, which reads `logger.disabled` and
    # `logger.isEnabledFor` off the underlying logger, and the PrintLogger built by
    # the factory below has neither. Every `logger.info(...)` anywhere in the
    # process then raises `AttributeError: 'PrintLogger' object has no attribute
    # 'disabled'` -- the backend's own MCP tools included.
    #
    # `start_app.py` runs the backend and this dashboard as separate processes, so
    # the two configurations never met and the app worked. They meet the moment
    # anything imports both into one process, which is exactly what
    # tests/phase3/test_ui_integration.py does. Stating the full configuration makes
    # it order-independent instead of relying on that separation holding.
    #
    # The renderer matches the backend's (JSON, sorted keys) so the dashboard's
    # events join the same structured stream rather than being the one component
    # emitting a different shape.
    structlog.configure(
        processors=[
            # The non-stdlib variants: these read the method name off the event, so
            # they work with any logger factory.
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(sort_keys=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=_SafeWriter()),
        cache_logger_on_first_use=False,
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
from src.agents.agent import build_agent_executor, run_agent, AGENT_ERROR_PREFIX
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

if "p3_messages" not in st.session_state:
    st.session_state["p3_messages"] = [
        {
            "role": "assistant",
            "content": (
                "🧠 Hello! I am the **Phase 3 ReAct reasoning agent**. Unlike the other tabs I can "
                "combine the *inventory manual* with *live stock data* in a single reasoning loop — "
                "so you can ask me not just what the numbers are, but what the policy says to do "
                "about them.\n\nTry: _\"Is SKU-GRO-0001 below its reorder point, and what does the "
                "manual say I should do about it?\"_"
            ),
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
    st.markdown("**Active Phases:** Phase 2 (RAG), Phase 3 (ReAct Agent), Phase 4 (FastMCP), Phase 5 (LangGraph Multi-Agent)")
    st.markdown("---")
    
    st.subheader("🔌 Connection Status")
    if backend_online:
        st.success("🟢 FastAPI Backend: Connected (`localhost:8000`)")
    else:
        st.warning("🟡 FastAPI Backend: Offline / Mock Fallback")
    
    st.markdown("- **MCP Server:** FastMCP ('Inventory Management Server')")
    st.markdown("- **ReAct Agent:** LangChain (7 REST + RAG tools)")
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
        st.session_state["p3_messages"] = [
            {
                "role": "assistant",
                "content": "🧠 Reasoning agent reset! Ask me about live stock, suppliers, dashboard totals, or what the manual says to do.",
            }
        ]
        st.session_state["multi_agent_result"] = None
        st.rerun()

st.title("📦 Retail Inventory Management & Operations Platform")
st.caption("Integrated FastMCP Agentic Assistant, ChromaDB Vector RAG, and LangGraph Multi-Agent Orchestrator")

# Tab Navigation
tab_mcp, tab_react, tab_rag, tab_multi = st.tabs([
    "🤖 Operations Chat Agent (Phase 4 MCP)",
    "🧠 Reasoning Agent (Phase 3 ReAct)",
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
# TAB 2: Phase 3 LangChain ReAct Reasoning Agent
#
# Why this tab exists.
#
# The Phase 3 agent was fully implemented and fully unreachable: `run_agent` had
# exactly two callers, its own pytest suite and a standalone CLI
# (`phase3/run_agent.py`). Nothing a user could open ever invoked it, and this
# sidebar did not even list Phase 3 among the active phases.
#
# It is not a duplicate of the Phase 4 chat tab above. That agent holds six MCP
# tools, none of which can read the inventory manual; the Phase 2 tab can read the
# manual but cannot see a single live stock figure. So the combination -- "what is
# true right now, and what does policy say to do about it" -- had no surface
# anywhere in the application. That is the capability this tab adds, and it is the
# reason it is worth adding rather than decoration.
# ----------------------------------------------------
with tab_react:
    st.subheader("🧠 ReAct Reasoning Agent — live data *and* written policy")
    st.markdown(
        "This agent reasons step by step over **7 tools**: six REST endpoints on the live "
        "inventory database plus the Phase 2 vector search over the operations manual. It is "
        "the only surface here that can answer a question needing both."
    )

    # Built once and kept. The Phase 4 chat rebuilds its executor on every single
    # message, which re-instantiates the LLM client and re-binds every tool for no
    # gain; there is no reason to copy that here.
    if "p3_executor" not in st.session_state:
        with st.spinner("Initializing LangChain ReAct agent and registering tools..."):
            try:
                st.session_state["p3_executor"] = build_agent_executor()
                st.session_state["p3_executor_error"] = None
            except Exception as e:
                st.session_state["p3_executor"] = None
                st.session_state["p3_executor_error"] = str(e)

    if st.session_state.get("p3_executor_error"):
        st.error(
            "The reasoning agent could not be initialized: "
            f"{st.session_state['p3_executor_error']}"
        )
        st.caption(
            "This usually means `GOOGLE_API_KEY` is missing or the configured chat model "
            "is unavailable. The other tabs are unaffected."
        )

    executor = st.session_state.get("p3_executor")
    if executor is not None:
        with st.expander(f"🔧 Registered tools ({len(executor.tools)})"):
            for t in executor.tools:
                st.markdown(f"- **`{t.name}`** — {(t.description or '').strip().splitlines()[0]}")

    # Quick actions chosen to exercise what only this agent can do: the first two
    # need policy *and* live data in one loop; the third reaches the endpoint that
    # had no caller anywhere in the codebase before this release.
    q1, q2, q3 = st.columns(3)
    p3_quick = None
    with q1:
        if st.button("📐 Check a SKU against policy", use_container_width=True):
            p3_quick = ("Is SKU-GRO-0001 below its reorder point right now? "
                        "Check the manual for what the reorder policy says I should do, "
                        "and tell me both.")
    with q2:
        if st.button("💰 Total inventory value", use_container_width=True):
            p3_quick = "What is the total value of our current inventory?"
    with q3:
        if st.button("🏢 Supplier catalog + terms", use_container_width=True):
            p3_quick = ("List everything supplier SUP-0001 sells with cost prices, "
                        "and tell me their lead time and payment terms.")

    for msg in st.session_state["p3_messages"]:
        with st.chat_message(msg["role"]):
            # An agent failure stays looking like a failure across reruns instead of
            # settling into the transcript as if it were a considered answer.
            if msg.get("is_error"):
                st.error(msg["content"])
            else:
                st.markdown(msg["content"])

    p3_input = st.chat_input(
        "Ask about live stock, suppliers, totals — or what the manual says to do...",
        key="p3_input_box",
    )
    p3_query = p3_quick or p3_input

    if p3_query:
        if executor is None:
            st.error("The reasoning agent is not available; see the initialization error above.")
        else:
            st.session_state["p3_messages"].append({"role": "user", "content": p3_query})
            with st.chat_message("user"):
                st.markdown(p3_query)

            with st.chat_message("assistant"):
                with st.spinner("🧠 Reasoning and calling tools..."):
                    answer = run_agent(p3_query, executor)

                # `run_agent` signals failure by *returning* a string rather than
                # raising, so without this check a stack trace would be rendered as
                # the agent's answer -- the same defect that was fixed in the RAG
                # tab below.
                is_error = answer.startswith(AGENT_ERROR_PREFIX)
                if is_error:
                    st.error(answer)
                else:
                    st.markdown(answer)

                st.session_state["p3_messages"].append({
                    "role": "assistant",
                    "content": answer,
                    "is_error": is_error,
                })

# ----------------------------------------------------
# TAB 3: Phase 2 RAG Assistant
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
            # Keep a past failure looking like a failure on rerun, rather than
            # letting it settle into the transcript as if it were an answer.
            if msg.get("is_error"):
                st.error(msg["content"])
            else:
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

                # A retrieval failure is not an answer. Rendering it with
                # st.markdown made a provider outage look like the manual's
                # considered reply, and it was then appended to the transcript
                # where it became context for the next question.
                if result.get("is_error"):
                    st.error(answer)
                    with st.expander("🔧 Technical detail"):
                        st.code(result.get("error", "no detail recorded"))
                else:
                    st.markdown(answer)
                if sources:
                    with st.expander("📄 View Retrieved Source Document Chunks"):
                        for i, doc in enumerate(sources):
                            st.markdown(f"**Chunk {i+1}:**")
                            st.caption(doc.page_content if hasattr(doc, "page_content") else str(doc))

                st.session_state["rag_messages"].append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "is_error": bool(result.get("is_error")),
                })

# ----------------------------------------------------
# TAB 4: Phase 5 Multi-Agent Orchestrator (LangGraph)
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

        # Never substitute a plausible-looking placeholder for a missing identity.
        # `p_data.get('sku', 'SKU-001')` rendered a *real-looking* SKU whenever the
        # inventory_auditor failed to fetch the product, so a pipeline run that had
        # loaded nothing still presented a confident-looking header -- and the four
        # agent outputs below it would then be read as if they described SKU-001.
        # An em dash is unmistakably "not available"; a valid SKU format is not.
        if not p_data.get("sku"):
            st.warning(
                f"The inventory auditor returned no product record for ID #{target_product_id}, "
                "so SKU, name and stock figures below are unavailable. Treat the agent "
                "outputs as unanchored."
            )

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("SKU / Product", p_data.get("sku") or "—", p_data.get("name") or "unavailable")
        kpi2.metric(
            "Available Stock",
            f"{stock['quantity_available']} units" if "quantity_available" in stock else "—",
            f"Reorder Pt: {p_data.get('reorder_point', 0)}" if p_data.get("sku") else "Reorder Pt: —",
        )
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

        # ----------------------------------------------------------------
        # Act on the recommendation.
        #
        # Without this the pipeline stops at advice: it would work out that
        # SKU-ELC-0001 needs 25 units from Apex Logistics at Rs 550,000 and then
        # render that in an st.json box, leaving the operator to retype it into
        # the Phase 1 screen. The backend has had POST /api/v1/orders all along.
        #
        # Deliberately human-approved rather than autonomous: committing spend to
        # a vendor is a buyer's decision, and the quantity comes from an LLM. The
        # button states exactly what will be created before it is created, and
        # the resulting PO lands in `draft` status, which is the same state the
        # Phase 1 UI creates and still requires a separate Receive step.
        # ----------------------------------------------------------------
        st.markdown("---")
        st.markdown("#### ✅ Act on this recommendation")

        quote_supplier_id = s_quote.get("supplier_id")
        rec_qty = int(r_rec.get("recommended_quantity") or 0)
        unit_cost = float(s_quote.get("quoted_unit_cost") or 0)
        product_id_for_po = p_data.get("id")

        if not r_rec.get("reorder_required"):
            st.caption(
                "The reorder agent did not recommend replenishment, so there is nothing to raise."
            )
        elif not product_id_for_po:
            st.warning(
                "No product record was loaded, so a purchase order cannot be raised against it."
            )
        elif not quote_supplier_id:
            # The honest blocker, not a disabled-looking button.
            st.warning(
                f"**Cannot raise a purchase order:** {s_quote.get('cost_basis', 'no supplier available')}. "
                f"Link a supplier to {p_data.get('sku') or 'this product'} in the Products screen, "
                "then re-run this analysis."
            )
        elif rec_qty <= 0 or unit_cost <= 0:
            st.warning(
                f"**Cannot raise a purchase order:** the recommendation resolved to "
                f"{rec_qty} units at {unit_cost:,.2f} per unit. Both must be greater than zero."
            )
        else:
            lead_days = s_quote.get("estimated_lead_time_days")
            expected = None
            if isinstance(lead_days, (int, float)) and lead_days >= 0:
                expected = (date.today() + timedelta(days=int(lead_days))).isoformat()

            supplier_label = (
                f"{s_quote.get('supplier_code')} — {s_quote.get('supplier_name')}"
                if s_quote.get("supplier_code") else f"supplier #{quote_supplier_id}"
            )
            st.markdown(
                f"This will create a **draft** purchase order for **{rec_qty} × "
                f"{p_data.get('sku')}** from **{supplier_label}** at "
                f"₹{unit_cost:,.2f} per unit — total **₹{rec_qty * unit_cost:,.2f}**"
                + (f", expected delivery **{expected}** ({int(lead_days)}-day lead time)." if expected
                   else ", with no expected delivery date (lead time unknown).")
            )
            st.caption(
                f"Cost basis: {s_quote.get('cost_basis', 'unspecified')}. "
                "The order is created in `draft` status and still needs to be received."
            )

            if st.button("📝 Create draft purchase order", type="primary", key="create_po_from_p5"):
                payload = {
                    "supplier_id": int(quote_supplier_id),
                    "order_date": date.today().isoformat(),
                    "items": [{
                        "product_id": int(product_id_for_po),
                        "quantity_ordered": rec_qty,
                        "unit_cost": unit_cost,
                    }],
                }
                if expected:
                    payload["expected_delivery"] = expected
                try:
                    from src import service_auth

                    po_resp = requests.post(
                        f"{api_base}/orders",
                        json=payload,
                        headers=service_auth.auth_headers(),
                        timeout=15,
                    )
                    if po_resp.status_code == 401:
                        service_auth.invalidate()
                        po_resp = requests.post(
                            f"{api_base}/orders",
                            json=payload,
                            headers=service_auth.auth_headers(force_refresh=True),
                            timeout=15,
                        )
                    if po_resp.status_code == 201:
                        po = po_resp.json()
                        st.success(
                            f"Created **{po.get('po_number')}** — {rec_qty} × {p_data.get('sku')} "
                            f"from {supplier_label}, total ₹{float(po.get('total_amount', 0)):,.2f}, "
                            f"status `{po.get('status')}`. It is now visible in the Purchase Orders "
                            "screen of the inventory app."
                        )
                        st.json(po)
                    else:
                        st.error(
                            f"The backend rejected the purchase order (HTTP {po_resp.status_code}): "
                            f"{po_resp.text[:500]}"
                        )
                except Exception as e:
                    st.error(f"Could not reach the backend to create the purchase order: {e}")

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
