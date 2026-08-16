# 📦 Retail Inventory Management & Procurement System (POC-07)
### Agentic AI Readiness Program — Enterprise Architecture & Code Documentation

![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)
![LangChain](https://img.shields.io/badge/LangChain-ReAct%20Agent-orange.svg)
![Gemini](https://img.shields.io/badge/Google%20Gemini-Flash%20%26%20Embeddings-8E75B2.svg)
![SonarQube](https://img.shields.io/badge/SonarQube-Quality%20Gate%20Passed-4E9BCD.svg)
![Coverage](https://img.shields.io/badge/Coverage-91%25%20%2B-brightgreen.svg)

---

## 🌟 Executive Overview
**POC-07** is an end-to-end retail supply chain and inventory management platform that evolves across 5 distinct modernization phases:
1. **Phase 1: Full-Stack CRUD & Database Engine** — RESTful API built with FastAPI, SQLAlchemy 2.0 ORM, SQLite with Foreign Key constraints, JWT authentication, and structured `structlog` telemetry.
2. **Phase 2: Enterprise RAG Knowledge Base** — Retrieval-Augmented Generation utilizing ChromaDB vector store, Google Generative AI Embeddings (`gemini-embedding-2`), Gemini Flash LLMs, and OpenTelemetry/LangSmith tracing.
3. **Phase 3: Autonomous ReAct Decision Agent** — LangChain ReAct agent equipped with context engineering, automatic output summarization, and custom REST API & RAG tool bindings.
4. **Phase 4: MCP (Model Context Protocol) Server & Chat Interface** — Standardized tool exposure and interactive AI interfaces.
5. **Phase 5: Multi-Agent Collaboration Engine** — Supervisor-worker multi-agent coordination for complex supply chain replenishment workflows.

---

## 📂 Repository Layout

```
Agentic-AI-Readiness-Program/
│
├── README.md                           # Master Project Documentation & Quickstart
├── DEVLOG.md                           # Chronological Engineering & Bug Fix Log
├── verify_all_phases.py                # Unified Multi-Phase Smoke & Test Runner
│
├── phase1/                             # Phase 1: Full-Stack CRUD Application
│   ├── app/
│   │   ├── main.py                     # FastAPI Application Initialization & Middleware
│   │   ├── database.py                 # SQLAlchemy Engine, SessionLocal, PRAGMA setup
│   │   ├── models.py                   # Relational DB Models (Product, StockLevel, etc.)
│   │   ├── schemas.py                  # Pydantic v2 ConfigDict Request/Response Models
│   │   ├── logging_config.py           # Structured JSON Logging (structlog)
│   │   ├── services/
│   │   │   └── inventory_service.py    # Core Business Logic (SKU/PO gen, alerts, receive)
│   │   └── routers/
│   │       ├── auth.py                 # JWT Authentication & User Registration
│   │       └── inventory.py            # REST Endpoints for Products, POs, Suppliers
│   ├── frontend/                       # React 18 + Vite Web Dashboard
│   ├── tests/                          # 20 Pytest Unit, API & DB Persistence Tests
│   └── submission/                     # SonarQube & Pytest XML Artifacts
│
├── phase2/                             # Phase 2: RAG Application
│   ├── rag/
│   │   ├── inventory_manual.md         # 15-Section Standard Operating Procedure Manual
│   │   ├── ingest.py                   # Vector Store Ingestion & Google Embeddings
│   │   ├── rag_chain.py                # RetrievalQA LangChain Pipeline with Tracing
│   │   └── app.py                      # Streamlit Interactive Knowledge Assistant
│   ├── chroma_db/                      # Persistent ChromaDB Vector Store
│   ├── tests/                          # Automated RAG Retrieval & Prompt Unit Tests
│   ├── verify_rag.py                   # Live CLI Verification Script
│   └── submission/                     # Quality Reports & Dashboard Screenshots
│
└── phase3/                             # Phase 3: Autonomous ReAct Agent
    ├── agent/
    │   ├── agent.py                    # LangChain ReAct Agent Initialization & Runner
    │   ├── tools.py                    # 5 Agent Tools (API integration & RAG bridge)
    │   ├── summarizer.py               # Document & List Summarization Middleware
    │   └── prompts.py                  # Structured System Prompts & Guardrails
    ├── run_agent.py                    # Interactive CLI Terminal for ReAct Agent
    ├── tests/                          # 21 Pytest Test Cases (91% Line Coverage)
    ├── generate_submission_artifacts.py# Automated Report & XML Exporter
    └── submission/
        ├── MY_SCORES.md                # Phase 3 Score Breakdown
        ├── TEST_REPORT.md              # Detailed Test Execution Summary
        ├── SONARQUBE_REPORT.md         # SonarQube Metric Evidence
        └── sonarqube_ss-phase3.png     # Real SonarQube Dashboard Screenshot
```

---

## 🔍 In-Depth Technical Walkthrough

### 1. Phase 1 — Data Model & Service Layer
Located in [`phase1/app/`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase1/app):

| Component / Function | File | Description & Behavior |
|---|---|---|
| `generate_sku(category, db)` | [`inventory_service.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase1/app/services/inventory_service.py) | Formats SKU as `SKU-{PREFIX}-{NNNN}` using category prefixes (`GRO`, `ELC`, `CLO`, `HHD`, `PRC`). |
| `generate_po_number(db)` | [`inventory_service.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase1/app/services/inventory_service.py) | Formats Purchase Order numbers as `PO-{YEAR}-{NNNN}` (e.g. `PO-2026-0001`). |
| `check_stock_alerts(product, stock, db)` | [`inventory_service.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase1/app/services/inventory_service.py) | Calculates `quantity_available` (`quantity_on_hand - quantity_reserved`). Triggers `low_stock` or `out_of_stock` alerts and auto-resolves existing alerts when stock recovers. |
| `receive_purchase_order(po_id, db)` | [`inventory_service.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase1/app/services/inventory_service.py) | Transitions PO to `received`, increases inventory stock on hand, logs `StockMovement` (type `receipt`), and clears active alerts. |
| `get_dashboard_data(db)` | [`inventory_service.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase1/app/services/inventory_service.py) | Computes total valuation (`quantity_on_hand * cost_price`), out of stock count, and open PO count. |

### 2. Phase 2 — RAG Knowledge Pipeline
Located in [`phase2/rag/`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase2/rag):

| Component / Function | File | Description & Behavior |
|---|---|---|
| `ingest_documents()` | [`ingest.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase2/rag/ingest.py) | Reads `inventory_manual.md`, applies `MarkdownHeaderTextSplitter` + `RecursiveCharacterTextSplitter` (chunk size: 800, overlap: 100), generates vectors using `GoogleGenerativeAIEmbeddings`, and stores them in ChromaDB. |
| `build_rag_chain()` | [`rag_chain.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase2/rag/rag_chain.py) | Constructs a LangChain `RetrievalQA` pipeline with custom `INVENTORY_RAG_PROMPT` and `ChatGoogleGenerativeAI`. |
| `ask_question(query)` | [`rag_chain.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase2/rag/rag_chain.py) | Queries the vector store with k=4, executes the prompt, records telemetry in OpenTelemetry/LangSmith, and returns answers with source documents. |

### 3. Phase 3 — Autonomous ReAct Agent & Tools
Located in [`phase3/agent/`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase3/agent):

| Tool / Function | File | Description & Behavior |
|---|---|---|
| `get_product_stock(sku)` | [`tools.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase3/agent/tools.py) | Fetches real-time quantity on hand, unit cost, and category from `GET /api/v1/products`. |
| `get_low_stock_alerts()` | [`tools.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase3/agent/tools.py) | Fetches products at or below reorder threshold from `GET /api/v1/stock/low-alerts` and applies `_summarize_if_long` to prevent LLM context explosion. |
| `create_purchase_order(...)` | [`tools.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase3/agent/tools.py) | Validates supplier codes, resolves SKU-to-ID mappings, auto-computes expected delivery date from supplier lead time, and raises a formal PO via `POST /api/v1/orders`. |
| `get_supplier_info(code)` | [`tools.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase3/agent/tools.py) | Retrieves lead times, payment terms, and status for suppliers from `GET /api/v1/suppliers`. |
| `rag_knowledge_base(query)` | [`tools.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase3/agent/tools.py) | Direct bridge to Phase 2 `ask_question()` for policy, formula, and manual inquiries. |
| `_summarize_if_long(data)` | [`summarizer.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase3/agent/summarizer.py) | Condenses long response arrays using Gemini Flash summarize chains or safe fallback truncation. |
| `run_agent(query)` | [`agent.py`](file:///c:/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/phase3/agent/agent.py) | Executes multi-step ReAct thought-action-observation cycles to fulfill natural language user objectives. |

---

## 🚀 How to Run the Entire System

### 1. Environment Setup
```powershell
# Activate Python Virtual Environment
. .\phase1\venv\Scripts\Activate.ps1

# Configure Environment Variables (.env)
GOOGLE_API_KEY=your_google_ai_studio_key
GEMINI_CHAT_MODEL=gemini-2.5-flash-lite
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-2
```

### 2. Start Phase 1 REST API Backend
```powershell
cd phase1
python -m app.main
# Server runs on: http://127.0.0.1:8000
# OpenAPI Docs at: http://127.0.0.1:8000/docs
```

### 3. Start Phase 2 RAG Streamlit App or CLI Verification
```powershell
cd phase2
# CLI Verification:
python verify_rag.py

# Interactive Streamlit Web UI:
streamlit run rag/app.py
```

### 4. Run Phase 3 ReAct Agent CLI
```powershell
cd phase3
python run_agent.py
```

### 5. Execute Test Suites & Quality Analysis
```powershell
# Phase 1 Test Suite (20/20 Passing)
cd phase1
pytest tests/ -v --cov=app

# Phase 2 Test Suite
cd phase2
pytest tests/ -v

# Phase 3 Test Suite (21/21 Passing, 91.0% Coverage)
cd phase3
pytest tests/ -v --cov=agent --cov-report=term-missing

# Run SonarQube Scanner (Port 9001)
npx.cmd sonar-scanner "-Dsonar.host.url=http://localhost:9001" "-Dsonar.projectKey=POC-07-Inventory-Phase3" "-Dsonar.login=YOUR_TOKEN"
```

---

## 📊 Quality & Compliance Evidence
- **Phase 1 Quality Gate**: Passed (20/20 tests passed, full CRUD integrity).
- **Phase 2 Quality Gate**: Passed (RAG ChromaDB embeddings verified).
- **Phase 3 Quality Gate**: Passed (21/21 tests passed, 91.0% code coverage, 0 Bugs, 0 Vulnerabilities, 0 Code Smells).
- **SonarQube Evidence**: Verified on `http://localhost:9001/dashboard?id=POC-07-Inventory-Phase3`.
