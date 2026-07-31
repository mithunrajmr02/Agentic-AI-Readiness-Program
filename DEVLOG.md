# Developer Log (DEVLOG) — AI Readiness Program POC-07
## Retail Domain: Inventory Management & Procurement System

---

## 📌 Executive Summary
This log tracks developer decisions, architecture choices, bug fixes, implementation logs, and verification outputs across all 5 phases of **POC-07 (Inventory Management & Procurement System)**.

---

## 📑 Phase 1: Full-Stack CRUD Application Development

### 1. Requirements & Core Business Rules
- **POC ID**: `POC-07`
- **Domain**: Retail Operations & Supply Chain
- **Core Entities**: Product, StockLevel, StockMovement, PurchaseOrder, POItem, Supplier, StockAlert, User.
- **SKU Auto-Generation**: `SKU-{CAT_PREFIX}-{NNNN}`
  - Categories & Prefixes: `grocery` -> `GRO`, `electronics` -> `ELC`, `clothing` -> `CLO`, `household` -> `HHD`, `personal_care` -> `PRC`.
- **PO Number Auto-Generation**: `PO-{YEAR}-{NNNN}` (e.g. `PO-2026-0042`).
- **Stock Logic**:
  - `quantity_available` = `max(0, quantity_on_hand - quantity_reserved)`
  - Trigger `low_stock` alert when `quantity_available <= reorder_point`
  - Trigger `out_of_stock` alert when `quantity_available == 0`
- **PO Receive Logic**:
  - `PATCH /api/v1/orders/{id}/receive` updates PO status to `received`.
  - Creates `StockMovement` (type `receipt`) per line item.
  - Updates `quantity_on_hand` for each product.
  - Resolves active `StockAlert` records for received items.

---

### 🛠️ Tech Stack & Directory Structure
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, PyJWT, Passlib (Bcrypt), structlog, SQLite.
- **Frontend**: React 18, Vite, Axios, Modern Vanilla CSS design system.
- **Testing**: `pytest`, `httpx`, `pytest-cov`, `--junitxml` report generator.

```
c:\Users\2mrmi\OneDrive\Documents\github-clone\Agentic-AI-Readiness-Program\
├── DEVLOG.md (Root Dev Log)
├── README.md
├── Inventory-Management/ (Documentation & Specifications)
└── phase1/ (Phase 1 Full-Stack CRUD Implementation)
    ├── app/
    │   ├── database.py
    │   ├── models.py
    │   ├── schemas.py
    │   ├── logging_config.py
    │   ├── main.py
    │   ├── services/
    │   │   └── inventory_service.py
    │   └── routers/
    │       ├── auth.py
    │       └── inventory.py
    ├── tests/
    │   ├── conftest.py
    │   ├── test_unit.py
    │   ├── test_api.py
    │   └── test_db.py
    ├── frontend/
    │   ├── index.html
    │   ├── package.json
    │   └── src/
    │       ├── App.jsx
    │       └── index.css
    ├── results/
    │   └── phase1-results.xml
    ├── submission/
    │   ├── MY_SCORES.md
    │   └── phase1-results.xml
    ├── requirements.txt
    └── .env
```

---

### 📝 Development Log & Issue Tracker

#### Log Entry 001 - Project Setup & Architecture Initialization
- **Date**: 2026-07-31
- **Action**: Environment configured, directory structure initialized under `phase1/` and `Inventory-Management/phase1/`.
- **Status**: Complete.

#### Log Entry 002 - Database Schema & SQLAlchemy Models
- **Models Created**: `Supplier`, `Product`, `StockLevel`, `StockMovement`, `PurchaseOrder`, `POItem`, `StockAlert`, `User`.
- **Key Relationships**:
  - `Product.stock_level` (1-to-1 with `StockLevel`)
  - `Product.movements` (1-to-Many with `StockMovement`)
  - `Product.alerts` (1-to-Many with `StockAlert`)
  - `PurchaseOrder.items` (1-to-Many with `POItem`)
- **Status**: Implemented.

#### Log Entry 003 - Business Services & Helper Functions
- `generate_sku(category, db)`: Auto-counts category items and formats `SKU-{PREFIX}-{NNNN}`.
- `generate_po_number(db)`: Auto-counts current year's POs and formats `PO-{YEAR}-{NNNN}`.
- `check_stock_alerts(product, stock, db)`: Generates `low_stock` or `out_of_stock` alerts.
- `receive_purchase_order(po_id, db)`: Updates stock, creates `receipt` movements, resolves alerts.

#### Log Entry 004 - REST API Endpoints & Structured Logging
- Initialized FastAPI routers for `/products`, `/orders`, `/suppliers`, `/stock/low-alerts`, `/dashboard`, and `/auth`.
- Integrated `structlog` with mandatory fields: `poc_id="POC-07"`, `phase="P1"`, `operation`, `duration_ms`, `status`.

#### Log Entry 005 - Pytest Test Suite & Fix Log
- **Issue A**: `email-validator` was missing for Pydantic `EmailStr`.
  - **Fix**: Installed `email-validator` package.
- **Issue B**: In-memory SQLite (`sqlite:///:memory:`) was opening independent connections per fixture/client causing `OperationalError: no such table: products`.
  - **Fix**: Updated `tests/conftest.py` to use `StaticPool` (`from sqlalchemy.pool import StaticPool`).
- **Issue C**: Pydantic v2 deprecation warning for `class Config`.
  - **Fix**: Refactored `app/schemas.py` to use `model_config = ConfigDict(from_attributes=True)`.

---

### 🧪 Verification & Results Log

```
======================== 20 passed, 1 warning in 0.33s ========================
```

| Test Category | Total Cases | Target | Passed | Status |
|---------------|-------------|--------|--------|--------|
| Unit Tests    | 8           | 6      | 8      | ✅ PASSED (100%) |
| API Tests     | 8           | 6      | 8      | ✅ PASSED (100%) |
| DB Tests      | 4           | 2      | 4      | ✅ PASSED (100%) |
| **Total**     | **20**      | **14 (70%)** | **20** | ✅ PASSED (100%) |

**XML Report**: Generated at `phase1/results/phase1-results.xml` and copied to `phase1/submission/phase1-results.xml`.

---

### 🌁 Bridge to Phase 2 (RAG Application)
- **Phase 1 Baseline**: Fully functioning REST API with 100% test pass rate and populated SQLite database.
- **Phase 2 Requirements**:
  1. Prepare `rag/inventory_manual.md` with 15 sections covering inventory rules, SKU prefixes, PO lifecycles, and troubleshooting.
  2. Build RAG pipeline with ChromaDB vector store and Gemini 2.0 Flash LLM (`models/text-embedding-004` & `gemini-2.0-flash`).
  3. Streamlit Q&A interface and LangSmith tracing project `AI-Readiness-POC-07-P2`.
