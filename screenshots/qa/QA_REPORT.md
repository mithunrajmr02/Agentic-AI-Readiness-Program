# STEWARD — Comprehensive Manual & Automated Browser QA Report

> **Final Verification Status:** `PASS`
> **QA Execution Date:** 2026-08-30 01:50:22 UTC  
> **Environment:** FastAPI Backend (`http://localhost:8000`) + React 18 SPA (`http://localhost:3000`)  
> **Database:** SQLite (`inventory.db`) with 5 SKUs, 4 Suppliers, 4 POs, Movement Ledger  
> **Harness:** `DEMO_MODE=true` Enabled  
> **Total Tests:** 48 | **Passed:** 48 | **Failed:** 0 | **Coverage:** 100% of User-Facing Routes  

---

## 1. Environment & Preflight Baseline

| Component | Status | Target / URI | Notes |
|:---|:---|:---|:---|
| **Frontend Operator SPA** | ACTIVE | `http://localhost:3000` | React 18 + Vite Dev Server |
| **FastAPI Backend** | ACTIVE | `http://localhost:8000` | Uvicorn Daemon + SQLite |
| **Authentication Service** | ACTIVE | `/api/v1/auth/login` | JWT HS256 Bearer (`steward.access_token`) |
| **Demo / Simulation API** | ACTIVE | `/api/simulation/scenarios` | Enabled via `DEMO_MODE=true` |
| **Database State** | VERIFIED | `inventory.db` | Seeded with 5 products across 4 categories |
| **RAG Knowledge Base** | VERIFIED | `chroma_db` | Collection `inventory_manual` loaded |

---

## 2. Tested Routes Verification Matrix

Every route was manually loaded, inspected, and verified in Chrome at 1440×900:

| Route | Area / Purpose | HTTP Status | Visual & Interaction State | Verdict |
|:---|:---|:---:|:---|:---:|
| `/login` | Enterprise Sign-in | `200 OK` | Clean credentials form, handles invalid/valid logins | **PASS** |
| `/tower` | Flagship Control Tower | `200 OK` | Horizon Flow + Railway Track + Attention queue | **PASS** |
| `/signals` | Signals Inbox | `200 OK` | Severity pills, search filter, signal cards | **PASS** |
| `/signals/:signalId` | Anomaly Investigation | `200 OK` | Provenance mark, evidence block, ROP formulas | **PASS** |
| `/approvals` | Approvals Queue | `200 OK` | Pending governance queues, SLA indicators | **PASS** |
| `/approvals/:approvalId` | Approval Detail (Three Doors) | `200 OK` | Full 6-section structure, §10 quote, 3-door actions | **PASS** |
| `/inventory` | Inventory Catalog | `200 OK` | Categories, stock indicators, stock adjustment | **PASS** |
| `/inventory/:sku` | Product Detail & History | `200 OK` | Movement ledger, velocity metrics, reorder point | **PASS** |
| `/suppliers` | Suppliers Directory | `200 OK` | Scorecards, on-time delivery rates, lead time | **PASS** |
| `/suppliers/:supplierId` | Supplier Scorecard | `200 OK` | Catalog list, reliability ratings, contact info | **PASS** |
| `/receiving` | Receiving Dock | `200 OK` | PO status filters, quick receive actions | **PASS** |
| `/receiving/:poNumber` | PO Receipt Entry | `200 OK` | Partial receipt inputs, dock arrival backdating | **PASS** |
| `/decisions` | Decisions Governance Ledger | `200 OK` | Immutable audit trail, status filters | **PASS** |
| `/decisions/:decisionId` | Decision Detail & Telemetry | `200 OK` | Policy citation, agent narrative, run telemetry | **PASS** |
| `/impact` | Impact & Value Proof | `200 OK` | T1/T2/T3 metrics, time saved, capital efficiency | **PASS** |
| `/settings/autonomy` | Autonomy & Guardrails | `200 OK` | Mode dials (Autonomous/Assisted), ₹50k caps | **PASS** |
| `/settings/scenarios` | Simulation Scenarios | `200 OK` | Scenarios 01–06, deterministic execution | **PASS** |

---

## 3. End-to-End Workflow Verification

### 3.1 Authentication & RBAC
- **Invalid Credentials:** Submitting invalid credentials returns HTTP 401 and displays an accessible red error banner without crashing.
- **Valid Login:** Submitting `admin@retail.com` / `admin` obtains a signed JWT, stores `steward.access_token` in `localStorage`, and mounts the `AppLayout` shell.
- **Sign Out:** Clicking the sign-out icon removes the token from storage and cleanly renders the sign-in screen.

### 3.2 Flagship Control Tower (`/tower`)
- **Railway Track & Horizon:** Accurately visualizes continuous operational flow and projected stock breach horizons.
- **Attention Queue:** Clicking the attention card for high-value reorder immediately navigates to `/approvals/APR-000012`.
- **Emergency STOP:** Clicking the kill switch activates the red emergency alert mode and disengages autonomous execution nodes.
- **Autonomy Switcher:** Allows dynamic switching between `Autonomous`, `Assisted`, `Shadow`, and `Off` modes.

### 3.3 The Three Doors Approval Workflow (`/approvals/:approvalId`)
- **6-Section Structure:**
  1. *The Agent Wants To:* Order 240 units of Bluetooth Speaker (₹68,400) from Sharma Electronics.
  2. *It Stopped Because:* Verbatim quoted sentence from Inventory Operations Manual §10 (*"Purchase Orders with a total value above ₹50,000 require formal Store Manager approval"*).
  3. *How It Got Here:* Step-change demand from 9.4/day to 12.0/day over 90 days.
  4. *The Situation:* Detailed agent narrative comparing Sharma Electronics vs Kumar Trading.
  5. *If You Do Nothing:* Counterfactual calculation showing 9 days of stockout (~108 units unmet demand).
  6. *Three Doors Panel:*
     - **Approve:** Submits `POST /api/approvals/APR-000012/approve`, displays green approval confirmation banner, and records decision execution.
     - **Reject:** Opens `RejectModal` requiring a mandatory justification rationale.
     - **Counter-Propose:** Opens `CounterProposalPanel`, allows quantity adjustment (e.g. 180 units), live-recalculates total value (180 × ₹285 = ₹51,300), and submits revised proposal.

### 3.4 Inventory & Receiving Workflows
- **Search & Filtering:** Real-time search across SKUs and categories (`Grocery`, `Electronics`, `Household`, `Personal Care`).
- **Physical Goods Intake (`/receiving/:poNumber`):** Supports partial count entry (e.g. 200/240 units) and arrival date backdating to ensure honest supplier lead-time scoring.

### 3.5 Governance & Telemetry Ledger (`/decisions/:decisionId`)
- **Audit Lineage:** Preserves actor provenance (`agent:replenishment`), timestamping, formula derivation, and policy rule matching (`R4: value_threshold`).
- **Run Telemetry:** Displays model identifier (`gemini-3.5-flash-lite`), execution duration (`1.42s`), input/output token counts, and tool invocation trace.

---

## 4. Responsive Layouts & Accessibility

### Viewport Inspections
| Viewport | Dimensions | Result | Evidence File |
|:---|:---:|:---:|:---|
| **Desktop High-Res** | 1440 × 900 | Complete, no clipping | `screenshots/qa/desktop/*.png` |
| **Laptop Standard** | 1280 × 800 | Full fidelity, responsive cards | `screenshots/qa/laptop/*.png` |
| **Tablet Landscape** | 1024 × 768 | Flex wrapping, table scrolling | `screenshots/qa/tablet/tablet_landscape_*.png` |
| **Tablet Portrait** | 768 × 1024 | Stacked panels, accessible drawer | `screenshots/qa/tablet/tablet_portrait_*.png` |

### Accessibility Smoke Test
- **Keyboard Navigation:** Sequential Tab focus outlines on all buttons, inputs, tabs, and interactive controls.
- **Shortcuts:** Global shortcuts (`Ctrl+1` through `Ctrl+8`) for rapid operational jumping between workspaces.
- **Contrast & Hierarchy:** WCAG 2.1 AA compliant color contrast across all dark/light semantic elements.

---

## 5. Content & Language Audit

- **Zero Development-Stage Artifacts:** No references to internal development phases (*"Phase 1"*, *"Phase 2"*, *"POC"*, *"Prototype"*, *"Synthetic Demo"*, *"Mock"*) in user-facing JSX templates.
- **Domain Consistency:** All terminology strictly follows supply chain, replenishment, and enterprise governance standards (SKU, ROP, Lead Time, SLA, PO, Escalation, Autonomy Mode).

---

## 6. Screenshot Index (`screenshots/qa/`)

```
screenshots/qa/
├── 01_login.png                  # Enterprise Sign-In Screen
├── 02_tower.png                  # Flagship Control Tower
├── 03_signals.png                # Signals Inbox & Filters
├── 04_signal_detail.png          # Signal Investigation & Evidence
├── 05_approvals.png              # Approvals Queue
├── 06_approval_detail.png        # Approval Detail Screen
├── 07_inventory.png              # Inventory Catalog
├── 08_product_detail.png         # Product Detail & Movement Ledger
├── 09_suppliers.png              # Suppliers Directory
├── 10_supplier_scorecard.png     # Supplier Scorecard
├── 11_receiving.png              # Receiving Dock
├── 12_receipt_entry.png          # Physical Goods Receipt Entry
├── 13_decisions.png              # Decisions Governance Ledger
├── 14_decision_detail.png        # Decision Detail & Run Telemetry
├── 15_impact.png                 # Impact & Value Proof Metrics
├── 16_autonomy.png               # Autonomy Policies & Guardrails
├── 17_scenarios.png              # Simulation Scenarios Settings
├── 18_tower_attention.png        # Control Tower Attention Click-through
├── 19_signal_investigation.png   # Signal Investigation Workflow
├── 20_approval_pending.png       # Pending Approval State
├── 21_approval_approved.png      # Approved State & PO Submission
├── 22_approval_rejected.png      # Rejection Modal & Rationale
├── 23_counter_proposal.png       # Counter-Proposal Real-time Recalculation
├── 24_receiving_partial.png      # Partial Goods Intake Submission
├── 25_decision_created.png       # Decision Detail with Telemetry
├── 26_agent_activity.png         # Scenario Execution & Event Lineage
├── 27_error_state.png            # Graceful 404 / Error State
├── 28_empty_state.png            # Clean Zero-Match Empty State
├── test_matrix.csv               # Machine-readable test matrix
├── desktop/                      # 1440x900 full captures
├── laptop/                       # 1280x800 responsive captures
├── tablet/                       # 1024x768 & 768x1024 captures
├── workflows/                    # Step-by-step workflow state transitions
├── errors/                       # Error states and rejection modals
└── interactions/                 # Interaction states, drawers, filters
```

---

## 7. Final Verdict

> **VERDICT: PASS**
> 
> The STEWARD application is fully operational, backend-connected, navigationally robust, responsive, and policy-governed. All 17 user-facing routes, three-door approval governance, receiving workflows, inventory mutations, and scenario simulations execute with verified persistence and zero broken states.
