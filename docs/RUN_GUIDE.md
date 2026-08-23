# 🚀 Complete Step-by-Step Execution Guide
## POC-07: Retail Inventory Management & Procurement System (Unified Architecture)

This guide provides step-by-step instructions for setting up, running, testing, and interacting with all services in the newly unified codebase under `src/`.

---

## 📋 Table of Contents
1. [Prerequisites & Environment Setup](#1-prerequisites--environment-setup)
2. [Starting the FastAPI Backend Server](#2-starting-the-fastapi-backend-server)
3. [Running the RAG Ingestion Pipeline](#3-running-the-rag-ingestion-pipeline)
4. [Launching the Streamlit AI Assistant](#4-launching-the-streamlit-ai-assistant)
5. [Executing the LangChain ReAct Agent (CLI)](#5-executing-the-langchain-react-agent-cli)
6. [Launching the React Frontend Dashboard](#6-launching-the-react-frontend-dashboard)
7. [Running the Unified Test Verification Suite](#7-running-the-unified-test-verification-suite)
8. [Multi-Container Deployment with Docker Compose](#8-multi-container-deployment-with-docker-compose)
9. [Architecture Directory Mapping Reference](#9-architecture-directory-mapping-reference)

---

## 1. Prerequisites & Environment Setup

### 1.1 Install Python Dependencies
From the repository root, install all required dependencies:
```bash
pip install -r requirements.txt
```

### 1.2 Configure `.env` File
Ensure your `.env` file at the repository root contains the following variables:
```ini
# Database Configuration
DATABASE_URL=sqlite:///./inventory.db
SECRET_KEY=supersecretjwtkeyforpoc07inventorysystem
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Gemini API Keys (Required for RAG & Agents)
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_CHAT_MODEL=gemini-1.5-flash
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-2

# LangSmith Observability (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langchain_api_key_here
LANGCHAIN_PROJECT=AI-Readiness-POC-07
```

---

## 2. Starting the FastAPI Backend Server

The backend REST API provides full CRUD operations for Products, Stock Levels, Suppliers, Purchase Orders, and Stock Alerts.

### Run with Uvicorn (Hot Reload):
```bash
uvicorn src.backend.main:app --reload --port 8000
```

### Run via Python Module:
```bash
python -m src.backend.main
```

### Access URLs:
* **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 3. Running the RAG Ingestion Pipeline

To populate or refresh the ChromaDB vector database from `src/rag/data/inventory_manual.md`:

```bash
python -m src.rag.ingest
```

### What this does:
1. Loads the 15-section domain policy manual.
2. Recursively chunks text (chunk size: 500, overlap: 50).
3. Generates 3072-dimensional vector embeddings using Google Generative AI (`models/gemini-embedding-2`).
4. Persists the collection into `./chroma_db/`.

---

## 4. Launching the Streamlit AI Assistant

The Streamlit web UI provides a conversational chat interface connected to the ChromaDB vector database and Gemini 2.0 Flash RetrievalQA chain.

```bash
streamlit run src/ui/chat_streamlit/app.py
```

* **Local URL:** [http://localhost:8501](http://localhost:8501)
* **Features:** Natural language Q&A, automatic source chunk citation, chat history reset.

---

## 5. Executing the LangChain ReAct Agent (CLI)

The autonomous ReAct agent connects the LLM with backend APIs (Stock checking, PO creation, Alert polling, Supplier lookups, RAG knowledge retrieval).

### Run default test prompt:
```bash
python -m src.agents.agent
```

### Run with a custom question/command:
```bash
python -m src.agents.agent "Check stock for SKU-GRO-0001 and create a purchase order if it is low on stock."
```

```bash
python -m src.agents.agent "What is the policy threshold for Store Manager approval on purchase orders?"
```

---

## 6. Launching the React Frontend Dashboard

The React + Vite frontend dashboard allows users to manage products, suppliers, stock movements, and purchase orders visually.

```bash
cd src/ui/web_react
npm install
npm run dev
```

* **Local URL:** [http://localhost:5173](http://localhost:5173) (or port shown in terminal)

---

## 7. Running the Unified Test Verification Suite

`pytest.ini` points at `tests/`, so a bare invocation collects all five graded
suites (232 tests, 2 skipped):

```bash
python -m pytest
```

### Running Individual Test Suites:
* **Phase 1 Backend Tests:** `python -m pytest tests/phase1 -v`
* **Phase 2 RAG Tests:** `python -m pytest tests/phase2 -v`
* **Phase 3 Agent Tests:** `python -m pytest tests/phase3 -v`
* **Phase 4 MCP Tests:** `python -m pytest tests/phase4 -v`
* **Phase 5 Multi-Agent Tests:** `python -m pytest tests/phase5 -v`

---

## 8. Multi-Container Deployment with Docker Compose

To orchestrate the backend, frontend, Streamlit UI, and SonarQube quality scanner:

```bash
docker-compose up -d
```

### Container Endpoints:
* **FastAPI Backend:** [http://localhost:8000](http://localhost:8000)
* **Streamlit UI:** [http://localhost:8501](http://localhost:8501)
* **SonarQube Dashboard:** [http://localhost:9001](http://localhost:9001)

---

## 9. Architecture Directory Mapping Reference

The five phases were originally developed in per-phase directories. They were
consolidated into one application tree; the phase directories and the
backward-compatibility bridge packages inside them have since been removed, so the
"previous location" column below is history, not a path that still resolves.

| Previous Location | Current Location | Purpose |
|---|---|---|
| `phase1/app/` | `src/backend/` | Core FastAPI application, SQLAlchemy models, schemas, routers, and services |
| `phase2/rag/` | `src/rag/` | Document ingestion, ChromaDB vector store, Gemini embeddings & RetrievalQA chain |
| `phase3/agent/` | `src/agents/` | LangChain ReAct structured agent, custom tools, prompts, and payload summarizer |
| `phase1/frontend/` | `src/ui/web_react/` | React + Vite inventory management user interface |
| `phase2/rag/app.py` | `src/ui/chat_streamlit/app.py` | Streamlit conversational assistant interface |
| `phase4/mcp_server/` | `src/mcp_server/` | FastMCP server tools exposing backend endpoints |
| `phase5/multi_agent/` | `src/agents/multi_agent/` | Multi-agent supervisor and specialized worker workflows |
| `phaseN/tests/` | `tests/phaseN/` | The five graded test suites |
| `phaseN/submission/` | `submissions/phaseN/` | Per-phase scores, reports, XML artifacts and screenshots |
| `phase2/verify_rag.py` | `scripts/verify_rag.py` | Live RAG retrieval smoke queries |
| `phase3/run_agent.py` | `scripts/agent_cli.py` | Interactive ReAct agent terminal |

