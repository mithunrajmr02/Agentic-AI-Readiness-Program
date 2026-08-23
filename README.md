# 📦 Retail Inventory Management & Procurement System (POC-07)
### Agentic AI Readiness Program — application, tests and phase submissions

![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)
![LangChain](https://img.shields.io/badge/LangChain-ReAct%20%26%20LangGraph-orange.svg)
![Gemini](https://img.shields.io/badge/Google%20Gemini-Flash%20%26%20Embeddings-8E75B2.svg)
![SonarQube](https://img.shields.io/badge/SonarQube-Quality%20Gate%20Passed-4E9BCD.svg)

---

## 🌟 What this is

One inventory-management application. It grew through the programme's five phases,
but it ships as a single system — the phases are capability layers inside it, not
separate deployables:

| Phase | Capability | Where it lives |
|---|---|---|
| P1 | Full-stack CRUD: FastAPI + SQLAlchemy 2.0 + SQLite, JWT auth, `structlog` telemetry, React operator SPA | `src/backend/`, `src/ui/web_react/` |
| P2 | RAG knowledge base: ChromaDB + Google embeddings over the inventory manual | `src/rag/` |
| P3 | ReAct decision agent: 7 tools over the live REST API plus a RAG bridge | `src/agents/` |
| P4 | MCP server and chat interface: the same operations exposed as MCP tools | `src/mcp_server/` |
| P5 | Multi-agent replenishment workflow on LangGraph | `src/agents/multi_agent/` |

Every layer talks to the same running backend and the same database. Nothing is
mocked or simulated at runtime.

---

## 📂 Repository layout

```
Agentic-AI-Readiness-Program/
│
├── start_app.py                 # single-command launcher for all three services
├── requirements.txt
├── pytest.ini
├── Dockerfile / docker-compose.yml / .dockerignore
├── .env.example                 # every variable the code actually reads
│
├── src/                         # THE APPLICATION -- the only runtime source tree
│   ├── backend/                 # FastAPI app, ORM models, schemas, services, routers
│   │   ├── main.py              #   app factory, middleware, exception handlers
│   │   ├── models.py            #   Product, StockLevel, PurchaseOrder, Supplier, ...
│   │   ├── services/            #   SKU/PO generation, stock alerts, PO receipt
│   │   ├── routers/             #   auth.py (JWT), inventory.py (REST endpoints)
│   │   └── seed_demo_data.py    #   idempotent demo dataset
│   ├── rag/                     # ingest.py, rag_chain.py, data/inventory_manual.md
│   ├── agents/                  # ReAct agent: agent.py, tools.py, prompts.py, summarizer.py
│   │   └── multi_agent/         #   LangGraph state, agents and graph
│   ├── mcp_server/              # FastMCP tool server + LangChain chat interface
│   ├── ui/
│   │   ├── web_react/           #   React + Vite operator dashboard (port 3000)
│   │   └── chat_streamlit/      #   Streamlit AI dashboard: MCP / ReAct / RAG / multi-agent
│   ├── model_config.py          # one place resolving Gemini model names
│   └── service_auth.py          # shared service-account login for non-browser clients
│
├── tests/                       # the five graded suites (232 tests)
│   ├── conftest.py              #   puts the repo root on sys.path for `src.*`
│   └── phase1/ … phase5/
│
├── submissions/                 # per-phase deliverables: scores, reports, XML, screenshots
│   └── phase1/ … phase5/
│
├── docs/
│   ├── ARCHITECTURE_AND_CODE_GUIDE.md   # architecture and function-level walkthrough
│   ├── RUN_GUIDE.md                     # step-by-step operational guide
│   ├── DEVLOG.md                        # chronological engineering and bug-fix log
│   └── program/                         # the programme's own briefs, rubric and test specs
│
└── scripts/
    ├── verify_rag.py            # live RAG retrieval smoke queries
    └── agent_cli.py             # interactive ReAct agent terminal
```

`src/` has no dependency on `tests/`, `submissions/` or `docs/`; the application
runs from `src/` alone.

---

## 🚀 Running it

### 1. Setup

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in `GOOGLE_API_KEY` (an AI Studio key) plus
`SECRET_KEY`. Everything else has a working default.

### 2. First run on a fresh clone

```bash
python start_app.py --seed --ingest
```

That seeds the demo dataset, builds the RAG vector store, then starts:

- FastAPI backend — http://localhost:8000 (OpenAPI docs at `/docs`)
- React operator SPA — http://localhost:3000
- Streamlit AI dashboard — http://localhost:8501

Afterwards `python start_app.py` is enough. `--no-web` and `--no-dashboard` skip
individual services. Default login: `admin@retail.com` / `admin`.

### 3. Individual pieces

```bash
uvicorn src.backend.main:app --reload --port 8000
```

```bash
python -m src.rag.ingest
```

```bash
streamlit run src/ui/chat_streamlit/app.py
```

```bash
python scripts/agent_cli.py
```

```bash
docker compose up backend streamlit-ui web
```

> Full operational detail, including the MCP server and troubleshooting, is in
> [docs/RUN_GUIDE.md](docs/RUN_GUIDE.md).

---

## 🧪 Tests

```bash
python -m pytest
```

Collects all five suites from `tests/` — 232 passing, 2 skipped (the two skips are
LangSmith checks that need a cloud API key). Scope one phase with
`python -m pytest tests/phase3`.

`--import-mode=importlib` is set in `pytest.ini` and is required: two suites
contain a `test_coverage_boost.py`, and the default import mode aborts collection
on the basename collision.

---

## 📊 Quality evidence

Per-phase scores, test reports, SonarQube reports and dashboard screenshots are in
[`submissions/`](submissions/). Coverage and JUnit XML for each phase sit alongside
them, together with the `sonar-project.properties` used for that phase's scan.
