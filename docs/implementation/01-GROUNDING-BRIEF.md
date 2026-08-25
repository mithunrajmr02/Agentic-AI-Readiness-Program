# 01 — Grounding Brief (Verified Current-State Facts)

> **Status:** AUTHORITATIVE for current-state facts.
> **Method:** Every statement below was verified by reading source, grepping the tree, running SQL against the live `inventory.db`, or reading the test files. Where the documentation and the code disagree, **the code wins** and the disagreement is recorded.
> **Purpose:** This is the shared evidence base. Any document in this package that makes a claim about "what exists today" must be consistent with this file. If you believe a fact here is wrong, verify against the codebase and flag it — do not silently contradict it.

---

## 1. Repository shape

| Area | Location | Size / shape |
|---|---|---|
| Backend API | `src/backend/` | FastAPI, SQLAlchemy 2.0, Pydantic v2, SQLite (`inventory.db`) |
| Auth | `src/backend/routers/auth.py` | PyJWT HS256, Passlib (pbkdf2_sha256 / bcrypt) |
| Domain models | `src/backend/models.py` | 188 lines, 8 tables |
| Business logic | `src/backend/services/inventory_service.py` | 203 lines, 6 functions |
| Inventory routes | `src/backend/routers/inventory.py` | 13 routes |
| RAG | `src/rag/` | ChromaDB + Gemini embeddings, 21 chunks |
| RAG corpus | `src/rag/data/inventory_manual.md` | 168 lines, 10,016 bytes, 15 sections |
| ReAct agent | `src/agents/` | LangChain `initialize_agent`, 7 tools |
| Multi-agent | `src/agents/multi_agent/` | LangGraph `StateGraph`, 4 nodes, 537 + 104 lines |
| MCP server | `src/mcp_server/mcp_app.py` | FastMCP 3.4.7, stdio, 6 tools |
| MCP chat | `src/mcp_server/chat_interface.py` | 165 lines, ReAct over the 6 MCP functions |
| Streamlit UI | `src/ui/chat_streamlit/app.py` | 600 lines, 4 tabs — **all AI lives here** |
| React SPA | `src/ui/web_react/src/App.jsx` | **1136 lines, single file, zero AI** |
| Seeder | `src/backend/seed_demo_data.py` | 386 lines, idempotent |
| Service auth | `src/service_auth.py` | 125 lines, shared login for non-browser clients |
| Model config | `src/model_config.py` | Central Gemini model/embedding selection |
| Tests | `tests/` | 22 files, 3,215 lines, **210 test functions** |

React tree contains exactly three source files: `App.jsx`, `index.css`, `main.jsx`.

---

## 2. Data model — the complete action surface

Eight tables: `Supplier`, `Product`, `StockLevel`, `StockMovement`, `PurchaseOrder`, `POItem`, `StockAlert`, `User`.

### Facts that constrain design

| Fact | Location | Consequence |
|---|---|---|
| `StockMovement.recorded_at = Column(DateTime, server_default=func.now())` | `models.py:132` | **A plain column with a server default.** Passing an explicit value overrides it. **Backdating movements requires ZERO schema change** — only a seeder code change. |
| `StockMovement.recorded_by = Column(String(100), default="system")` | `models.py:133` | Attribution exists but receipts are written as `"system"`. |
| `PurchaseOrder.order_date` / `received_date` are plain `Date` columns | `models.py` | Fully settable. Realistic delivery history costs zero migrations. |
| `StockAlert.alert_type = Column(String(50), nullable=False)` | `models.py:171` | **Free text, not an enum.** New signal types need no migration. |
| `User.role = Column(String(50), default="staff")` | `models.py:186` | Free text. An `agent` role can be created with no migration. |
| `quantity_available = quantity_on_hand - quantity_reserved`, deliberately not clamped at 0 | `models.py:107-121` | `quantity_reserved` is **never written anywhere**. `quantity_available == quantity_on_hand`, always. |
| `POStatus` declares 5 states: `draft, submitted, acknowledged, received, cancelled` | `models.py` | **Only `draft` and `received` are reachable via the API.** `submitted` / `acknowledged` / `cancelled` have no code path. |
| No `Warehouse` entity; `StockLevel.warehouse_id` is spec'd in the programme docs but absent | `models.py` | Multi-warehouse would require a **new column on an existing table**. |
| `Product.supplier_id` is a single FK; **no supplier-price entity exists** | `models.py` | **Multi-supplier price comparison is impossible today.** This is why `supplier_coordinator` cannot coordinate. |
| No Alembic, no migrations directory, no version table | verified across tree | Schema comes from `Base.metadata.create_all` in the lifespan hook. |

### The migration rule this implies

`Base.metadata.create_all` is **additive** — it creates missing tables and leaves existing ones untouched.

- **New tables are free.** No migration needed.
- **New columns on existing tables are not free.** They require dropping the DB or hand-writing SQL.
- **Therefore: all new relationships must point new → old.** A new `decisions` table may hold `po_id`; `purchase_orders` may **not** gain a `decision_id`.

---

## 3. API surface — verified route list

### `src/backend/routers/inventory.py` (13 routes)

| Method | Path | Line |
|---|---|---|
| POST | `/products` | 28 |
| GET | `/products` | 72 |
| GET | `/products/{id}` | 91 |
| PATCH | `/products/{id}/stock` | 134 |
| GET | `/stock/low-alerts` | 181 |
| POST | `/suppliers` | 194 |
| GET | `/suppliers` | 218 |
| GET | `/suppliers/{id}/catalog` | 223 |
| POST | `/orders` | 232 |
| GET | `/orders` | 295 |
| GET | `/orders/{id}` | 310 |
| PATCH | `/orders/{id}/receive` | 318 |
| GET | `/dashboard` | 330 |

**There is no product-update endpoint.** A reorder point is set at creation and is immutable thereafter. An agent cannot tune it.

Other verified facts:
- PO status is hard-coded to `POStatus.draft` at `inventory.py:281`. No endpoint can produce any other status except `received`.
- The `low_stock` filter is applied **in Python**, not SQL, at `inventory.py:86`.
- **All 11 authenticated inventory routes are role-blind.** A `staff` token can create and receive purchase orders.

### `src/backend/routers/auth.py`

`verify_password:51`, `get_password_hash:60`, `create_access_token:64`, `ensure_default_user:71`, `get_current_user:96`, `get_optional_user:188`, `POST /register:205`, `POST /login:278`.

- JWT TTL is **1440 minutes (24h)**.
- `SECRET_KEY` reads from env with a hardcoded fallback: `"secret-key-poc-07-inventory-management-2026"`.
- **The only role check in the entire backend is at `auth.py:234`** — creating a non-`staff` account requires a caller with role `manager`.
- The `role` claim is present in the JWT and **is never read for any authorization decision**.
- Bootstrap user `admin@retail.com` / `admin`, role `manager`, created by the lifespan hook at `main.py:85`.

---

## 4. Business logic — `inventory_service.py`

Six functions: `_next_sequence:15`, `generate_sku:54`, `generate_po_number:59`, `check_stock_alerts:64`, `receive_purchase_order:125`, `get_dashboard_data:171`.

| Function | Verified behaviour | Consequence |
|---|---|---|
| `check_stock_alerts` | **Resolves-then-reinserts.** Every stock movement while below the reorder point marks the previous alert `is_resolved=True` and inserts a new row. Only two types are ever generated: `"out_of_stock"`, `"low_stock"`. | `is_resolved` means **"superseded"**, not "remediated". Unbounded row growth, no dedup, no idempotency. |
| `receive_purchase_order` | `po.status = POStatus.received` (`:136`); `received_date = date.today()` **hard-coded** (`:137`); `qty = item.quantity_received or item.quantity_ordered` (`:140`) → always `quantity_ordered`. Note `:133` is a `POStatus.cancelled` guard — `cancelled` is *read* here but never *written* anywhere, so it stays unreachable. | **Receipts cannot be backdated and partial receipt is impossible.** Movements are attributed `recorded_by="system"`. |
| `get_dashboard_data` | `open_po_count` counts `[draft, submitted, acknowledged]` (`:193`). | Two of the three counted statuses can never exist. |
| `_next_sequence` | Documented in-code as **not concurrency-safe**. | Two concurrent `POST /orders` can collide on the PO number. Matters more once a background writer exists. |

**`stock_alerts` has no read path.** No endpoint queries it. `StockAlertResponse` is dead code. `/stock/low-alerts` recomputes from `products` in Python. Alerts fire only as a synchronous side effect of a write.

`suppliers.contact_email` is stored and never used anywhere.

---

## 5. Agents — what is genuinely agentic

### Phase 3 ReAct agent — `src/agents/`

`initialize_agent(AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, max_iterations=10, temperature=0.0)`.

**Exactly 7 tools** in `src/agents/tools.py` (261 lines):

| Tool | Mutates? |
|---|---|
| `get_product_stock(sku)` | no |
| `get_low_stock_alerts()` | no |
| `create_purchase_order(supplier_code, items)` | **YES** |
| `get_supplier_info(supplier_code)` | no |
| `get_supplier_catalog(supplier)` | no |
| `get_dashboard_stats()` | no |
| `rag_knowledge_base(query)` | no |

**1 of 7 tools can change the world.**

This is the architectural high point of the repo: `rag_knowledge_base` sits alongside the live API tools, so **one reasoner can read the policy manual and the live database in the same trajectory.** The programme spec only asked for 5 tools; this implementation has 7.

- No conversational memory.
- `AGENT_ERROR_PREFIX = "Error executing query:"` (`agent.py:27`) is what the UI keys off to render `st.error`.
- `_tool_span()` emits `logger.info("tool_called", poc_id="POC-07", phase="P3", tool=...)`.
- Latent inconsistency: `tools.py:23` defaults `API_BASE` to `127.0.0.1` while every other client uses `localhost`.

### Phase 5 "multi-agent system" — `src/agents/multi_agent/`

`graph.py` (104 lines): 4 nodes, entry `demand_forecaster`, **one** conditional edge `should_skip_to_audit()` firing on `len(errors) >= 3 or status == "error"`, then serial edges to `END`. Public entrypoint `analyze_product(product_id)`.

**This is a serial prompt chain, not a multi-agent system.** Honest assessment:

| Node | Verified behaviour | Problem |
|---|---|---|
| `demand_forecaster` | Asks the LLM for `avg_daily_demand`, `days_of_stock_remaining`, `stockout_risk` **from a single product snapshot with no sales history in the input** | The numbers are **fabricated**, then rendered to the operator via `st.json` |
| `reorder_agent` | LLM computes a reorder quantity | No policy grounding, no threshold awareness |
| `supplier_coordinator` | Fetches the real catalog + supplier at `agents.py:318`, then **overwrites every LLM-supplied fact** | The code comment at `:389-406` records the model inventing `supplier_id: 101` and a ₹580.0 price against a real ₹600.0, with a fabricated *"Bulk discount… Price valid for 30 days"* caption, **3/3 runs**. `cost_basis` honestly reads `"product.cost_price (standard cost) x recommended_quantity"` because no supplier-price entity exists. |
| `inventory_auditor` | Produces a 3–4 sentence prose report, sets `analysis_status="complete"` | Terminal |

**No node takes any action. The graph is read-only and terminates in prose.** The only branch is an error escape hatch, not a business decision.

---

## 6. MCP layer

`src/mcp_server/mcp_app.py` (253 lines) — FastMCP 3.4.7, stdio transport, helpers `_send:31`, `_get:59`, `_post:68`, `_patch:77`, `_parse_id:86`.

**Exactly 6 tools:**

| Line | Tool | Mutates? |
|---|---|---|
| 110 | `update_stock` | **YES** |
| 146 | `create_purchase_order` | **YES** |
| 176 | `get_low_stock_products` | no |
| 193 | `get_supplier_catalog` | no |
| 211 | `get_purchase_orders` | no |
| 236 | `get_inventory_dashboard` | no |

**The MCP protocol is never actually spoken.** There is no `.mcp.json`, no `mcpServers` block, no Claude Desktop config, no compose service anywhere in the tree. `chat_interface.py:34-41` imports the six tool functions **directly, in-process** and rewraps them as LangChain `StructuredTool`s at `:80-142` — which works because `@mcp.tool()` in fastmcp 3.4.7 returns the plain function. Then `create_react_agent` + `AgentExecutor(max_iterations=5)`.

**Phase 4 chat is stateless.** `ChatSession.get_history_for_llm()` returns `history[-10:]` but `process_message` **never calls it**. The UI shows a transcript; the model sees one turn.

---

## 7. RAG

- Corpus: `src/rag/data/inventory_manual.md` — 168 lines, 15 sections.
- `RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=50)` → **21 chunks**, verified live in `chroma_db/chroma.sqlite3`.
- Retriever `k=4`, plain similarity — **no MMR, no score threshold, no metadata filter**.
- `RetrievalQA`, `chain_type="stuff"`.
- **Citations are weak:** chunks carry **no section or heading metadata**, so a "source" is an anonymous 600-character window. No inline `[1]` markers.
- Grounding prompt forces the refusal string `"I don't have that information in the inventory manual."`
- `rag_chain.py:131-139` enters the OTel span via `contextlib.ExitStack`; the comment records a prior bug where *"the span reported 0.04ms for a 4000ms query."*
- Ingestion is idempotent by force (`drop_collection()` + `reset=True`) after a prior bug grew the collection to 1323 vectors over 21 distinct chunks.

### Policy rules that actually exist in the corpus (verbatim, load-bearing)

| § | Rule |
|---|---|
| 2 | `reorder_point = (average daily demand × supplier lead time in days) + safety stock`; worked example `(10 × 5) + (10 × 2) = 70` |
| 3 | Alert when `quantity_available <= reorder_point`; *"action should be taken within 24-48 hours"*; `= 0` is *"critical priority"* |
| 5 | *"The system must verify a supplier is active before raising a purchase order."* |
| 8 | `EOQ = √((2 × annual_demand × ordering_cost) / holding_cost_per_unit)`; worked example `(5 × 7) + (5 × 14) = 105` |
| 9 | *"Raising POs within 24 hours of a low_stock alert trigger"* — Anita Singh, Procurement Officer |
| **10 (line 113)** | **"PO Approval Threshold: Purchase Orders with a total value above ₹50,000 require formal Store Manager approval prior to supplier submission."** |
| 11 | Weekly cycle counts for high-value; positive adjustment = found stock, negative = shrinkage/damage |
| 13 | Slow-moving = no sale in 30+ days; `stock turn = COGS / average inventory value`; fill rate; days on hand |
| 14 | Notional POS / Supplier Portal / Finance integrations |

**Notable absences — do not build features grounded in policy that does not exist:**
- **No ABC analysis anywhere in the manual.** An agent asked about it will correctly hit the refusal path.
- **No explicit safety-stock formula.** Safety stock appears only as an input term, expressed in "days of demand".

---

## 8. Observability

| Layer | Reality |
|---|---|
| structlog | **Real**, but **stdout only** — no sink, no persistence |
| OpenTelemetry | **Instrumented but inert.** Span names are everywhere; **no `TracerProvider` or exporter is configured anywhere under `src/`**. Providers exist only in test files. At runtime `trace.get_tracer()` returns no-op spans. |
| LangSmith | The **only real trace sink**. Projects P2, P4, P5 — **there is no P3 project**, so the best agent in the repo is the one with no tracing. |

---

## 9. UI

### Streamlit — `src/ui/chat_streamlit/app.py` (600 lines)

Four tabs:
1. **Operations Chat** — Phase 4 MCP agent, write-capable
2. **Reasoning Agent** — Phase 3, displays `f"🔧 Registered tools ({len(executor.tools)})"` = 7
3. **Inventory Manual RAG** — with a *"📄 View Retrieved Source Document Chunks"* expander
4. **Multi-Agent Orchestrator** — `number_input` 1–100 → *"🚀 Run Multi-Agent Audit"* → 4 `st.metric` cards → 3 `st.json` panels → `st.info(audit_report)` → **"✅ Act on this recommendation"** with 4 explicit blocker branches → **"📝 Create draft purchase order"** → real `POST /orders`

**That final button is the ONLY human-in-the-loop write gate in the entire system.**

### React — `src/ui/web_react/src/App.jsx` (1136 lines)

- `activeTab` defaults to `'dashboard'`; 5 nav items; 4 stat cards; 4 `<table className="custom-table">`; 5 modals (`showProductModal`, `showStockModal`, `showPOModal`, `showSupplierModal`, `showHistoryModal`); all 6 write operations wired.
- `identityFromToken` decodes `sub` / `role` **"for display only… not used for any access decision."**
- **Zero AI.**

### The single biggest structural fact about the UX

**All AI lives in Streamlit. All business UX lives in React. Two apps, two URLs.**

---

## 10. Live database state (probed directly)

| Table | Rows |
|---|---|
| suppliers | 4 — SUP-0001, SUP-0002, SUP-0003, **SUP-0005** |
| products | 5 |
| stock_levels | 5 |
| stock_movements | **13** |
| purchase_orders | 4 — 1 received, 1 submitted, 2 draft |
| po_items | 4 |
| stock_alerts | 3 — all unresolved |
| users | 1 |

| Product | On hand | Reorder point | State |
|---|---|---|---|
| Rice | 167 | 15 | healthy |
| Headphones | 4 | 10 | low_stock |
| TV | 0 | 5 | out_of_stock |
| Detergent | 50 | 20 | healthy |
| Toothpaste | 0 | 30 | out_of_stock |

### The credibility problem, stated precisely

- **All 13 movements fall between `2026-08-23 08:50:18` and `2026-08-23 15:56:44` — ONE calendar day.**
- Product 1 has 11 movements. Products 2 and 4 have 1 each. **Products 3 and 5 have ZERO.**
- **Only 3 sale movements exist in the entire database** (−83 units, all product 1).

There is no demand history. This is why `demand_forecaster` fabricates. The cause is a code choice, not a schema limit — see §2.

**One real signal already present:** a seeded PO arrived **2 days later** than its promised 5-day lead time.

`seed_demo_data.py` is idempotent on natural keys, reuses `receive_purchase_order()` and `check_stock_alerts()`, verifies the invariant **`sum(stock_movements.quantity) == stock_levels.quantity_on_hand`** via `verify(db)`, and deliberately skips SUP-0004 so React supplier attribution stays honest. **No historical date backfill.**

---

## 11. Test constraints — the hard feasibility envelope

**22 test files, 3,215 lines, 210 test functions.** The graded spec counts **110 test cases** (20/20/20/25/25).

| Constraint | Location | Verdict |
|---|---|---|
| **`assert len(agent.tools) == 7`** | `tests/phase3/test_phase3.py:15` | **HARD LOCK.** Adding a tool to `build_agent_executor()` breaks a graded test. |
| `assert len(tools) >= 6` | `tests/phase4/test_integration.py:9` | MCP layer is **freely extensible**. |
| `test_4_nodes` does `src = inspect.getsource(build_inventory_graph)` and asserts each of the 4 names is `in src` | `tests/phase5/test_routing.py` | **It does NOT assert exactly 4 nodes.** The graph is extensible as long as the 4 original names remain in the source. |
| `test_entry_point` requires `"demand_forecaster" in src and ("set_entry_point" in src or "entry_point" in src.lower())` | `tests/phase5/test_routing.py` | Entry point name is fixed. |
| `assert len(result.get("messages", [])) >= 4` | `tests/phase5/test_e2e.py` | **`>=`, not `==`.** More messages are fine. |
| `assert result["analysis_status"] in ("complete","reorder_required","healthy","analyzing")` | `tests/phase5/test_e2e.py` | Terminal status must stay inside this set. |
| Phase 5 tests patch `src.agents.multi_agent.agents.requests.get` and `..._llm` via `ml.invoke.side_effect` | `tests/phase5/` | New nodes must not bypass these seams, or must tolerate the patches. |
| **`tests/phase2` hits the LIVE Gemini API with no `skipif` guard** | `tests/phase2/` | The aggregate test run is already quota-dependent. |
| Three tautological tests | `tests/phase2/` | `test_irrelevant_low_score` asserts on a MagicMock's own return value; `test_otel_spans` ends in `assert True`; `test_log_poc_id` asserts `len(out) >= 0`. |

**Additional constraint:** any scheduler or background task must be **env-gated and default OFF**, or it will start during the Phase 1 API test suite.

---

## 12. Programme constraints (from `docs/program/`)

| Constraint | Source | Note |
|---|---|---|
| `Total Score = (P1×0.15)+(P2×0.20)+(P3×0.20)+(P4×0.25)+(P5×0.20)` | `SCORING_RUBRIC.md` | — |
| `Phase_Score = (Tests_Passed / Total_Tests) × 100`; pass ≥70% | `SCORING_RUBRIC.md` | **No feature you add can raise the graded score.** |
| *"Tier is determined solely by number of phases cleared."* | `SCORING_RUBRIC.md` | — |
| **There is no stand-out, bonus, or stretch-goal rubric anywhere in the corpus.** | verified across `docs/program/` | Only three "optional" mentions: HTML coverage report, RAGAS, reviewer XML scripts. Reviewer red flags can only *reduce* a score. |
| LLM-as-Judge thresholds | `SCORING_RUBRIC.md` | Faithfulness ≥0.7, Answer Relevance ≥0.7, Context Precision ≥0.6, Context Recall ≥0.6 |
| Phase 5 extra qualitative pass | `SCORING_RUBRIC.md` | *"Are the 4 agents performing distinct, specialized tasks? … Is the final output richer than what a single agent could produce? Are agent handoffs visible in LangSmith traces?"* |
| Mandatory Phase 4/5 code walkthroughs; *"Associates must be able to explain every part of their implementation"*; *"Code similarity checks will be run against submissions from the same cohort."* | `SCORING_RUBRIC.md` §6 | Complexity must be explainable. |
| **Gemini is locked.** *"No — Gemini 2.0 Flash via Google AI Studio is the standardized LLM for this program… Using other LLMs may affect test case scoring."* Pins `MODEL_NAME = "gemini-2.0-flash"`, `EMBEDDING_MODEL = "models/text-embedding-004"` | `TECH_STACK_REFERENCE.md` | — |
| **Free tier: 15 RPM / 1,500 RPD** | `TECH_STACK_REFERENCE.md` | **A background loop making LLM calls per tick can exhaust the quota mid-demo.** |
| Copilot mandatory for ≥60% of Phase 1 code | `TECH_STACK_REFERENCE.md` | — |
| 4 personas | `overview.md` | **Priya Sharma / Store Manager: "Monitor stock levels, approve purchase orders"**; Raj Patel / Inventory Analyst; Anita Singh / Procurement Officer; Dev Kumar / Warehouse Staff |
| Baseline scope | `Phasewise - Userstories/` | P1 = 8 user stories; P2 = RAG ≥20 chunks; **P3 = exactly 5 tools**; **P4 = exactly 6 MCP tools**; P5 = 9-field state + 4 fixed-order agents + `should_skip_to_audit` |

**The phase user-story docs ship near-complete reference implementations** — full models, full agent code, full prompt strings, the full manual text. Anyone following them lands on identical code. That is why similarity checks exist, and it is the entire reason differentiation matters.

---

## 13. Presentation constraints

### `presentation meeting/ppt-ocr.txt` — the authoritative contract

| Slide | Content |
|---|---|
| 2 | Audience: Account Delivery Heads / SMEs / business-outcomes focused |
| 4 | *"Teams spent X hours weekly on Y with Z accuracy."* |
| 6 | *"Highlight 2-3 key capabilities"*; *"One clean diagram — Input → Process → Output"*; *"Avoid deep technical layers — show the flow, not the plumbing"*; *"Narrate the 'so what' at every step."* |
| 7 | Before/After: *"Reactive operations — issues caught late in the cycle"* → *"Proactive insights — issues surfaced before they escalate"*. Pillars: SLA Adherence, Cost Efficiency, Client Satisfaction |
| 9 | *"'Let me follow up with data' is a strength, not a weakness."* |
| 10 | Internal precedent: **"Supply Chain Optimizer — ICD Pilot / Associate-built tool cut procurement cycle from 14 days → 3 days. −79%"** |

### `presentation meeting/Present with Impact - Agentic AI -transcription.txt`

**INCOMPLETE — jumps 11:38 → 39:22, ~28 minutes missing.** The only hard requirements stated: **3–4 slides max**, containing **Problem + Solution + Impact + an architecture diagram**. **No time limit is stated anywhere** — the "8 min" figure is a cited Mayo Clinic example, not a rule.

**The grading reviewers and the presentation judges are different people.** `docs/program/` never mentions the presentation at all.

---

## 14. Doc-vs-code contradictions on record

| Documentation says | Code does |
|---|---|
| Programme mandates `gemini-2.0-flash` + `models/text-embedding-004` | `src/model_config.py` runs **`gemini-3.1-flash-lite`** + **`models/gemini-embedding-2`** (3072-dim) |
| `docs/DEVLOG.md` describes a pre-`src/` layout | Code is under `src/` |
| `overview.md` reserves PO approval for the Store Manager | No authorization exists; `auth.py:217` has a code comment acknowledging this |
| `StockLevel.warehouse_id` is spec'd | Absent |
| `overstock` and `reorder_suggested` alert types are spec'd | Never generated |
| Graded spec counts 110 test cases | 210 test functions exist |

---

## 15. Security items on record (must not regress; not this package's scope to fix)

`docs/TECHNICAL_HANDOVER_GUIDE.md` §8 and `docs/learning/11_OBSERVABILITY_AND_SECURITY.md:129` self-document that:

- A live `GOOGLE_API_KEY` was committed in a tracked `phase3/.env`.
- Live SonarQube user tokens were present in older commit history (offending commits `cb5c5c1`, `6c5eaa0`).
- `docs/DEVLOG.md` §9 states these **must be revoked/rotated by the repository owner** in SonarQube and Google AI Studio — *"the one open item that cannot be closed from inside the repository."*

Additionally:
- `SECRET_KEY` has a hardcoded fallback.
- **`src/service_auth.py` defaults to `admin@retail.com` / `admin`** — so **every agent action today runs with full manager privilege, attributed to "Admin".**

---

## 16. Assets that make differentiation cheap

These are the levers. Every one was verified.

1. **`recorded_at`, `order_date`, `received_date` are all settable.** Realistic history costs **zero migrations**.
2. **The movement ledger invariant** (`sum(movements) == on_hand`, enforced by `verify(db)`) makes any backfilled history arithmetically trustworthy.
3. **`expected_delivery` + `received_date` + `lead_time_days` all exist.** Supplier reliability and overdue detection are computable with **zero schema change** — they just need data. Today `expected_delivery` is **never compared to today anywhere in the codebase**.
4. **The ₹50,000 approval threshold and the 24-hour PO SLA are already in the RAG corpus.** Policy can be *retrieved and cited*, not hardcoded.
5. **`manager` / `staff` roles exist on `User`; the JWT already carries the claim.** An approval gate is already authorizable — it just needs enforcing.
6. **`create_all` is additive → new tables are free.**
7. **The action rail already works end-to-end:** agent → `create_purchase_order` → `POST /orders` → DB. Agents can already act; they lack something worth doing.
8. **`receive_purchase_order()` and `check_stock_alerts()` are reusable service functions**, already exercised by the seeder.
9. **`POStatus` already declares a 5-state lifecycle** to hang a workflow on. Reaching the unreachable states needs no schema change.
10. **`StockAlert.alert_type` and `User.role` are free-text `String` columns** — new signal types and an `agent` identity need no migration.
11. **The tests permit extension** — see §11. The graph and the MCP layer are both open.
12. **structlog + OTel + LangSmith are already instrumented** — a decision ledger is a natural extension of an existing story, not a new concern.
13. **`rag_knowledge_base` alongside live API tools** — the policy-plus-data reasoning pattern already exists and works.
