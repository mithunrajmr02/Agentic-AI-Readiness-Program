# STEWARD: Enterprise Inventory Management & Autonomous Procurement System
### Autonomous Supply Chain Control Tower & Multi-Agent Operations (POC-07)

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141.1-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6F00?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![FastMCP](https://img.shields.io/badge/FastMCP-Model%20Context%20Protocol-8A2BE2?style=flat-square)](https://modelcontextprotocol.io)
[![ChromaDB](https://img.shields.io/badge/Vector%20DB-ChromaDB-blueviolet?style=flat-square)](https://trychroma.com)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy%202.0-D71F00?style=flat-square)](https://www.sqlalchemy.org/)

---

## Overview

**STEWARD** is a production-minded retail inventory management and autonomous procurement control tower. It coordinates end-to-end supply chain operations, from demand forecasting and supplier intelligence to governed replenishment, goods receiving, and human-in-the-loop financial control.

> **Inventory that runs itself, within the limits you set.**

Steward combines a reliable inventory system of record with grounded AI, deterministic operational analytics, policy-aware autonomy, and a decision trail that makes every action explainable.

The system unifies five operational layers into a single production architecture:
1. **Full-Stack Invariant CRUD:** FastAPI REST services backed by SQLAlchemy ORM and an append-only stock movement ledger with invariant verification.
2. **Domain Knowledge RAG:** Grounded semantic retrieval over standard operating procedures (SOPs) and manuals using ChromaDB.
3. **Agentic Tool Integration:** Dynamic context management and Pydantic-validated function calling for procurement reasoning.
4. **Standard Model Context Protocol (FastMCP):** Standardized tool reflection exposing inventory operations to LLM clients and chat interfaces.
5. **Multi-Agent LangGraph System:** Collaborative agent graph comprising Demand Forecaster, Reorder Agent, Supplier Coordinator, and Inventory Auditor nodes with deterministic state handoffs.

---

## Executive Showcase

### What makes this implementation stand out

Steward goes beyond a conventional CRUD application or standalone chatbot. It brings the operational loop together in one system:

| Capability | Implemented experience | Evidence in the repository |
|---|---|---|
| **Sense** | Seven operational detectors identify threshold breaches, projected stockouts, overdue purchase orders, configuration drift, supplier drift, capital drag, and insufficient data. | `src/signals/detectors/`, `src/signals/engine.py` |
| **Decide** | Deterministic demand, reorder, EOQ, lead-time, sufficiency, valuation, and supplier analytics support explainable decisions. | `src/analytics/`, `src/sourcing/`, `src/policy/` |
| **Act** | Eight-node LangGraph orchestration moves from investigation through policy evaluation, execution, verification, and recording. | `src/agents/multi_agent/graph.py`, `src/agents/multi_agent/nodes/` |
| **Govern** | Approval inbox, counter-proposals, role-based authorization, autonomy modes, policy limits, and kill-switch controls provide bounded autonomy. | `src/governance/`, `src/backend/routers/approvals.py`, `src/backend/routers/policies.py` |
| **Prove** | Decisions, approvals, signals, run records, provenance, and impact metrics make outcomes auditable. | `src/backend/models_governance.py`, `src/backend/models_analytics.py`, `src/metrics/` |
| **Simulate** | Reproducible 90-day history and named scenarios make the system demonstrable on demand. | `src/simulation/`, `src/backend/routers/simulation.py` |
| **Assist** | Grounded RAG, LangChain tools, FastMCP tools, and Streamlit chat expose operational intelligence naturally. | `src/rag/`, `src/agents/`, `src/mcp_server/`, `src/ui/chat_streamlit/` |

### The product story in one sentence

**Steward detects what needs attention, investigates the operational context, applies the store's policy, executes what it is authorized to do, escalates what needs a human decision, and records the outcome.**

### Built for an executive demonstration

The experience is designed around the decisions an operations leader cares about:

- What needs attention now?
- Why did the system raise it?
- What does the policy allow?
- What will happen if we act?
- Who approved or executed the action?
- What measurable operational impact followed?

Every answer is represented in the product through the Control Tower, Signals Inbox, Approval Workspace, Decision Ledger, Supplier Scorecards, Receiving Dock, Impact view, Autonomy settings, and deterministic Scenario Harness.

### Evidence-led delivery

- Five integrated capability phases: CRUD, RAG, tool reasoning, MCP/chat, and LangGraph orchestration.
- Seven signal detectors and dedicated analytics modules for demand, reorder quantity, EOQ, lead time, sufficiency, valuation, and supplier drift.
- Real React control-tower interface with 17 captured product views.
- FastAPI, SQLite, ChromaDB, LangChain, LangGraph, FastMCP, OpenTelemetry, and LangSmith working through shared application boundaries.
- Full local verification: **723 tests passed, 0 skipped, 0 failed** in the final evaluation run.

## Application Interface Gallery

The platform features a responsive React 18 single-page application built with Vite and custom CSS design tokens, coupled with an interactive Streamlit AI interface.

### Control Tower Dashboard (`/tower`)
Real-time operational monitoring across inventory valuation, active stock alerts, critical stockouts, purchase orders, and multi-agent health status.
![Control Tower Dashboard](screenshots/02_control_tower.png)

### Autonomous Signals & Anomaly Detection (`/signals`)
Live operational signals detecting runout risk, vendor lead-time drift, demand velocity spikes, and replenishment urgency.
![Signals Inbox](screenshots/03_signals_inbox.png)

### Human-in-the-Loop Governance & 3-Door Policy Gate (`/approvals`)
Enforces financial governance boundaries (e.g. monetary approval thresholds) with structured 3-door actions: Approve Proposal, Reject with mandatory rationale, or Counter-Propose with live simulation.
![Approvals Queue](screenshots/05_approvals_queue.png)
![Approval Detail](screenshots/06_approval_detail.png)

### Real-Time Inventory & Stock Ledger (`/inventory`)
Physical stock position tracking with continuous invariant verification: `quantity_on_hand == sum(stock_movements.quantity)`.
![Inventory Management](screenshots/07_inventory.png)

### Supplier Directory & Performance Scorecards (`/suppliers`)
Vendor reliability metrics, lead-time variance tracking, on-time delivery rates, and catalog pricing comparisons.
![Supplier Directory](screenshots/09_suppliers.png)
![Supplier Scorecard](screenshots/10_supplier_scorecard.png)

### Idempotent Purchase Order Receiving Dock (`/receiving`)
Goods receiving dock preventing duplicate entries while appending atomic stock movements for every line item received.
![Receiving Dock](screenshots/11_receiving.png)
![Receipt Entry](screenshots/12_receipt_entry.png)

### Decision Provenance & Audit Trails (`/decisions`)
Complete policy provenance tracking whether an action was executed autonomously within policy bounds or approved by a human operator.
![Decisions Log](screenshots/13_decisions.png)
![Decision Detail](screenshots/14_decision_detail.png)

### Financial Impact & Autonomy Bounds (`/impact`, `/settings/autonomy`)
Working capital analysis, carrying cost reductions, stockout prevention metrics, and configurable autonomous spending bounds.
![Financial Impact](screenshots/15_impact.png)
![Autonomy Settings](screenshots/16_autonomy.png)

### Deterministic Scenario Simulation (`/settings/scenarios`)
Interactive test harness for operational scenarios: D1 (Governed Order), D2 (Lead Time Spike), D3 (Config Audit), and D4 (Autonomy Threshold Refusal).
![Simulation Scenarios](screenshots/17_scenarios.png)

---

## 🏛️ System Architecture

All capability layers communicate with the same live backend services and database without mocks or disjoint states:

```
                          ┌───────────────────────────┐
                          │   React 18 Control Tower  │
                          │   Streamlit AI Interface  │
                          └─────────────┬─────────────┘
                                        │ REST / FastMCP
                                        ▼
    ┌───────────────────────────────────────────────────────────────────┐
    │                       FastAPI Application                         │
    │   ┌──────────────────────────┐    ┌───────────────────────────┐   │
    │   │  Core Inventory Routers  │    │ FastMCP Tool Server       │   │
    │   │  Auth / Products / POs   │    │ 6 Standardized MCP Tools  │   │
    │   └─────────────┬────────────┘    └─────────────┬─────────────┘   │
    │                 │                               │                 │
    │                 ▼                               ▼                 │
    │   ┌───────────────────────────────────────────────────────────┐   │
    │   │                  Domain Business Services                 │   │
    │   │     Ledger Invariants, Sourcing Drift, Stock Alerts       │   │
    │   └─────────────┬───────────────────────────────┬─────────────┘   │
    └─────────────────┼───────────────────────────────┼─────────────────┘
                      │                               │
                      ▼                               ▼
    ┌──────────────────────────────────┐  ┌─────────────────────────────┐
    │    SQLite Invariant Database     │  │   ChromaDB Vector Store     │
    │   `sum(movements) == on_hand`    │  │   Operations Manual RAG     │
    └──────────────────────────────────┘  └─────────────────────────────┘
                      ▲                               ▲
                      │                               │
    ┌─────────────────┴───────────────────────────────┴─────────────────┐
    │                 LangGraph Multi-Agent Orchestration               │
    │                                                                   │
    │   [Demand Forecaster] ──▶ [Reorder Agent] ──▶ [Supplier Coord]    │
    │                                                     │             │
    │   [START] ──────────────▶ [Inventory Auditor] ◀─────┘ ──▶ [END]   │
    └───────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Repository Structure

```
Agentic-AI-Readiness-Program/
├── start_app.py                    # Single-command orchestrator for all services
├── requirements.txt                # Python dependencies manifest
├── pytest.ini                      # Pytest configuration
├── Dockerfile / docker-compose.yml # Containerized deployment configs
├── .env.example                    # Environment configuration template
│
├── src/                            # Core application source
│   ├── backend/                    # FastAPI app, ORM models, schemas, routers
│   │   ├── main.py                 #   Application entry point, CORS, middleware
│   │   ├── models/                 #   SQLAlchemy models: Product, StockLevel, PO, Supplier
│   │   ├── services/               #   SKU/PO generators, stock alerts, PO receipt logic
│   │   ├── routers/                #   Auth (JWT), products, orders, stock, suppliers
│   │   └── seed_demo_data.py       #   Deterministic demo dataset seeder
│   ├── rag/                        # RAG pipeline: ingest.py, rag_chain.py, manual corpus
│   ├── agents/                     # LangChain ReAct agent, tool definitions, prompts
│   │   └── multi_agent/            #   LangGraph state, 4 specialized agents, state graph
│   ├── mcp_server/                 # FastMCP server exposing 6 standardized tools
│   ├── analytics/ & sourcing/      # Drift detection, demand velocity, lead time models
│   ├── governance/ & simulation/   # Autonomy limits, approval policies, D1-D4 scenarios
│   └── ui/
│       ├── web_react/              #   React 18 + Vite operator dashboard (port 3000)
│       └── chat_streamlit/         #   Streamlit multi-tab AI interface (port 8501)
│
├── screenshots/                    # Real application interface captures
├── tests/                          # Automated test suites
│   ├── phase1/ through phase5/     #   Unit, API, RAG, MCP, and Multi-Agent tests
│   ├── analytics/ & sourcing/      #   Sourcing drift and velocity tests
│   ├── governance/ & simulation/   #   Ledger invariants & scenario tests
│   └── ui/                         #   React screen contracts & layout tests
│
└── docs/                           # Architectural documentation and operational runbooks
```

---

## 🚀 Quick Start Guide

### 1. Environment Setup

```bash
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate   # On Windows
source venv/bin/activate # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

Initialize environment variables:
```bash
cp .env.example .env
```
*(Optionally provide `GOOGLE_API_KEY` for live Gemini 3.5 Flash queries. Offline deterministic fallbacks are built-in for all automated tests).*

### 2. Launch Stack with One Command

```bash
python start_app.py --seed --ingest
```

This command executes the following startup sequence:
1. Seeds the operational database with strict ledger invariants.
2. Ingests and embeds the operations manual into ChromaDB.
3. Launches the **FastAPI Backend** on `http://localhost:8000` (Swagger docs at `/docs`).
4. Launches the **React Control Tower** on `http://localhost:3000`.
5. Launches the **Streamlit AI Dashboard** on `http://localhost:8501`.

*Default Operator Credentials:* `admin@retail.com` / `admin` (Role: `manager`)

### 3. Individual Service Execution

```bash
# Backend REST API
uvicorn src.backend.main:app --reload --port 8000

# React Frontend (Development)
cd src/ui/web_react && npm run dev

# React Frontend (Production Build & Preview)
cd src/ui/web_react && npm run build && npm run preview -- --port 3000

# FastMCP Server (stdio mode)
python -m src.mcp_server.server

# Streamlit Multi-Agent Chat Interface
streamlit run src/ui/chat_streamlit/app.py
```

---

## 🧪 Automated Testing & Invariant Verification

Execute the complete automated test suite:

```bash
python -m pytest -v
```

Execute individual test suites:
```bash
python -m pytest tests/phase1/ -v   # Full Stack CRUD & Invariant Ledger
python -m pytest tests/phase2/ -v   # RAG Semantic Retrieval & ChromaDB
python -m pytest tests/phase3/ -v   # Context Engineering & Tool Integration
python -m pytest tests/phase4/ -v   # FastMCP Protocol & Streamlit Chat
python -m pytest tests/phase5/ -v   # Multi-Agent LangGraph Workflows
python -m pytest tests/simulation/  # Operational Simulation Scenarios D1-D4
```

---

## 🛡️ Governance Invariants & Business Rules

1. **Physical Ledger Invariant:**
   The relationship $\sum \text{StockMovement.quantity} \equiv \text{StockLevel.quantity\_on\_hand}$ is mathematically preserved across every goods receipt, manual adjustment, and outbound sale.
2. **Idempotent Purchase Order Receipts:**
   Subsequent attempts to receive already processed purchase orders are strictly idempotent, preventing double-counting or orphaned inventory adjustments.
3. **Autonomy Guardrails:**
   Procurement orders exceeding configurable monetary thresholds require explicit human manager approval via the 3-door policy gate.
4. **Traceable Decision Provenance:**
   Every automated or human action produces an immutable audit record linking root-cause operational signals to final execution outcomes.

---

## 📚 Documentation & Reference Reports

- **Technical Architecture & Code Guide:** [`docs/ARCHITECTURE_AND_CODE_GUIDE.md`](docs/ARCHITECTURE_AND_CODE_GUIDE.md)
- **Operational Run Guide:** [`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md)
- **Implementation Dossier:** [`docs/implementation/README.md`](docs/implementation/README.md)
- **Evaluation Reports:** [`Mithun_20696155.md`](Mithun_20696155.md) | [`Mithun_20696155.json`](Mithun_20696155.json)
