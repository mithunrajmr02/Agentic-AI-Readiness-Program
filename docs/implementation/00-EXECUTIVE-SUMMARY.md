# 00 — Executive Summary & Decision Spine

> **Status:** AUTHORITATIVE for all product, architecture, and scope decisions.
> **Companion:** [01-GROUNDING-BRIEF.md](01-GROUNDING-BRIEF.md) is authoritative for current-state facts.
> **Rule for every other document in this package:** expand and detail these decisions. Do **not** re-litigate them, propose alternatives to them, or contradict them. If you find a decision technically impossible, flag it explicitly as `⚠️ SPINE CONFLICT` rather than silently changing it.

---

## 1. The verdict in one paragraph

The current POC is a **well-executed baseline** — genuinely above spec in places (7 tools against a spec'd 5; 1136 lines of finished React CRUD). Its problem is not quality; it is that **every one of its capabilities is mandated by the programme brief, so ~100 associates will demo the same thing.** The stack is right. The *shape* is wrong: the system senses only when asked, computes demand figures the LLM invents, decides nothing, acts almost nowhere, records nothing it did, and splits its AI and its business UI across two separate applications. The differentiated product is not "more AI." It is **the same domain, closed into a loop, governed by policy the system retrieves rather than hardcodes, and able to prove what it did.**

---

## 2. Product decision

### Name

**Primary: `Steward`** — subtitle **"Autonomous Replenishment Control Tower."**

Rationale: a steward manages resources on an owner's behalf, *within delegated authority*. That is exactly the product. Alternates if the user prefers: `Sentinel`, `Control Tower`, `Replenish`. **Naming is a reversible taste call — the user may override it; do not build anything that depends on the string.**

### Vision statement (canonical — quote this verbatim in other docs)

> **Steward is a policy-governed autonomous replenishment layer for retail inventory.**
>
> It watches stock continuously instead of waiting to be asked. When a product breaches — or is projected to breach — its reorder point, Steward investigates on its own: real consumption from the movement ledger, purchase orders already in flight, supplier lead time and delivery reliability. It reasons over the company's own operations manual to decide what to do. Low-risk replenishment it executes itself, in seconds. High-value decisions it prepares, explains, and hands to a Store Manager with the policy it is obeying attached. It then tracks each order to delivery and escalates when reality diverges from the promise. Every decision it makes — **and every one it declines to make** — is recorded and attributable.

### Tagline

> **"Inventory that runs itself — within the limits you set."**

### The three product pillars (use these as the organising frame everywhere)

| Pillar | What it means | Why it differentiates |
|---|---|---|
| **SENSE** | Continuous multi-signal detection, not a single "low stock" check | Turns slide-7's *"reactive → proactive"* from an assertion into a demonstration |
| **ACT** | Governed autonomy — investigate, reason over retrieved policy, decide, execute or escalate | Moves from *Insight → Recommendation* to *Insight → Decision → Action → Outcome* |
| **PROVE** | Decision ledger, policy citations, enforced RBAC, shadow-mode backtest, live impact meter | Auditability is the precondition an enterprise buyer applies before autonomy |

Cross-cutting fourth concern, deliberately elevated: **SIMULATE** — a deterministic demo/simulation harness. Without it the demo is not reliable, and half the differentiators have no data to run on.

---

## 3. Scope decision — the locked capability set

### MUST BUILD — the spine of the product

| ID | Capability | One-line definition |
|---|---|---|
| **C1** | **Signal Engine** | Seven deterministic detectors over the ledger, replacing the inert write-only alerts side effect |
| **C2** | **Grounded Analytics Core** | Deterministic demand, days-of-cover, reorder point, EOQ, supplier reliability — plus a **data-sufficiency score** |
| **C3** | **Governed Autonomy Loop** | LangGraph: investigate → policy → decide → **durable interrupt for approval** → execute → record |
| **C4** | **Policy Engine** | Thresholds and SLAs *retrieved and cited from the operations manual*, plus a manager-controlled **Autonomy Policy** |
| **C5** | **Approval & Governance Workspace** | Approval inbox, counter-proposal, enforced RBAC, kill switch, blast-radius limits |
| **C6** | **Decision Ledger & Impact Meter** | Append-only record of every decision **and every refusal**; live metrics computed from it |
| **C7** | **Unified Product UI** | One application. Control-tower home. The two-app split is retired. |
| **C8** | **Simulation & Demo Harness** | 90-day backdated history, named deterministic scenarios, controllable clock, one-command reset |

### HIGH VALUE — build after the spine holds

| ID | Capability | One-line definition |
|---|---|---|
| **C9** | **Root-Cause Analyst** | Classifies *why* a breach happened: demand shift / supplier drift / configuration error / one-off |
| **C10** | **Reorder Point Auditor** | Finds reorder points that contradict the manual's own formula; batch-fixes on approval |
| **C11** | **Supplier Intelligence** | Multi-supplier catalog, reliability scoring, sourcing choice with an explicit price-vs-reliability tradeoff |
| **C12** | **PO Consolidation** | Batches same-supplier lines into one PO — real procurement practice, and the manual's EOQ formula has an `ordering_cost` term |
| **C13** | **Shadow Mode & Backtest** | Replays 90 days deterministically: *"here is what Steward would have done, and what it would have prevented"* |
| **C14** | **Embedded Co-pilot** | One conversational agent, context-scoped to the current screen, **with memory** (fixes the stateless Phase 4 defect) |

### OPTIONAL — only if the spine and high-value set are complete

| ID | Capability |
|---|---|
| **C15** | Dead-stock / working-capital release (activates the spec'd-but-never-generated `overstock` signal) |
| **C16** | Shrinkage & adjustment anomaly watch |
| **C17** | Reservation semantics — activate the dead `quantity_reserved` column so decisions can soft-allocate |
| **C18** | Executive one-pager export (PDF/PNG of the impact view) |
| **C19** | Real MCP over stdio — make the protocol genuinely spoken, with a client config |
| **C20** | Wire a real OpenTelemetry exporter so the existing spans stop being no-ops |

### REJECT — with reasons, stated so they are not re-proposed

| Rejected | Reason |
|---|---|
| Voice interface | Zero business value; pure novelty |
| ARIMA / Prophet / ML forecasting | A trailing average is defensible in one sentence; ARIMA is an unexplainable dependency risk. The manual **gives you the formula** — use theirs. |
| Multi-warehouse / stock transfers | Requires a **new column on an existing table** with no Alembic, and dilutes a focused procurement story |
| **ABC analysis** | **Not in the manual.** A grounded agent will correctly refuse. Grounding a feature in policy you do not have is precisely the credibility trap we are escaping. |
| Supplier email / portal integration | No SMTP, webhook, or outbound channel exists anywhere in the stack. It would be theatre. |
| Product substitution suggestions | Requires product-similarity data that does not exist |
| Kafka / Celery / Redis / streaming | Single-node SQLite deployment with 5 products. Operational weight with no demonstrable benefit. |
| Fine-tuning, embeddings retraining | Absurd at this scale; Gemini is locked by the programme |
| Mobile app | Out of scope |
| Blockchain / cryptographic audit chain | The ledger needs to be *append-only and attributable*, not distributed |

---

## 4. Architecture decisions (locked)

Numbered so other documents can cite them as `AD-n`.

### AD-1 — Is the current architecture sufficient? No. The stack is right; the shape is wrong.

Keep: FastAPI, SQLAlchemy, SQLite, Pydantic, LangChain, LangGraph, ChromaDB, Gemini, structlog, React/Vite.
**Add** the seven layers that do not exist: event/trigger, background runtime, analytics, policy, governance, decision ledger, simulation.
**Redesign** the LangGraph. **Replace** the alert mechanism and the UI split. **Combine** the two near-duplicate chat agents at the product surface.

### AD-2 — LLM placement is a hard architectural boundary

> **The LLM belongs in investigation, explanation, and judgment. It is deliberately kept out of arithmetic and out of execution.**

| Deterministic code — **never** an LLM | LLM contributes |
|---|---|
| Signal detection | Investigation synthesis across sources |
| Demand, days-of-cover, reorder point, EOQ | Root-cause hypothesis |
| Supplier reliability scoring | Policy interpretation narration |
| Authority-envelope evaluation | Human-readable rationale for a decision |
| Order execution | Escalation narrative |
| Metric computation | The conversational co-pilot |
| Backtest replay | — |

Three payoffs, all real: it is correct engineering; it is the strongest available answer to *"how do you stop it hallucinating a purchase order?"*; and it protects the demo from the **Gemini free tier's 15 RPM / 1,500 RPD** limit. **If the model is slow or rate-limited mid-demo, the loop still detects, still computes, still executes — you only lose the prose.** That is a genuine resilience story, not a hedge.

### AD-3 — Zero migrations on existing tables. New relationships point new → old.

`create_all` is additive, so new tables are free; new columns are not. Therefore:

- **New tables:** `signals`, `decisions`, `approvals`, `autonomy_policies`, `supplier_products`, `agent_runs`, `metric_snapshots`, `demo_scenarios`.
- **Zero changes to the eight existing tables.**
- `decisions` holds `po_id`; `purchase_orders` does **not** gain a `decision_id`.
- Approval attribution lives in `approvals`, not on `purchase_orders`.
- The unreachable `POStatus` values (`submitted`, `acknowledged`, `cancelled`) are reached by **new endpoints**, not by schema change.

### AD-4 — New models live in new modules, not in `models.py`

`src/backend/models_governance.py`, `models_analytics.py`, `models_simulation.py` — each importing the same `Base`. `create_all` picks them up once imported. **This removes `models.py` as a parallel-development conflict point entirely.** The single import line that registers them is owned by the integration workstream.

### AD-5 — New routers are new modules. Existing routers are frozen.

Nobody edits `src/backend/routers/inventory.py` or `auth.py`. New surfaces go in new router modules under a **pre-allocated path namespace** (see §5). `main.py` registration is owned solely by the integration workstream.

### AD-6 — LangGraph earns its place through durable human-in-the-loop interrupt

Today the graph has no reason to exist beyond the rubric — it is a serial chain with one error escape hatch. Give it a real one:

> **The approval gate means the run must suspend and resume.** Use a checkpointer with `interrupt_before=["executor"]`. When a decision exceeds the authority envelope, the graph **literally pauses**; when a manager approves, it **resumes from the interrupt** and executes.

That is genuine, non-gratuitous LangGraph value and the correct answer to *"why LangGraph?"*

**Mandatory fallback** (specify it so a parallel developer never blocks): if `langgraph-checkpoint-sqlite` proves fragile, persist the full graph state as JSON on the `decisions` row and re-enter the graph at the `executor` node on approval. Same observable behaviour, no new dependency.

### AD-7 — Node topology: extend the mandated four, do not replace them

Separation is by **authority and data source**, never by prompt.

| Existing node (name preserved — test constraint) | Becomes |
|---|---|
| `demand_forecaster` | Grounded analytics + data-sufficiency assessment — **and the entry point** |
| `reorder_agent` | Quantity computation per §9, and the re-entry point for counter-proposals |
| `supplier_coordinator` | Sourcing node — real scoring + tradeoff narration |
| `inventory_auditor` | Post-write verification — ledger invariant, PO state, idempotency |

**New nodes:** `investigator`, `policy_gate`, `executor`, `recorder`.

Test compliance: the four names remain in `build_inventory_graph`'s source ✓; `messages >= 4` on **every** terminal path ✓; terminal `analysis_status` stays inside `("complete","reorder_required","healthy","analyzing")` ✓.

> **REFINED 2026-08-25 — [08-AGENTIC-WORKFLOWS.md](08-AGENTIC-WORKFLOWS.md) supersedes this table in detail.** Three changes from the first draft of AD-7, each for a stated reason:
> 1. **Authority evaluation moved out of `reorder_agent` into `policy_gate`.** Mixing quantity arithmetic with authority evaluation in one node makes the escalation logic hard to audit and hard to test. `reorder_agent` computes; `policy_gate` judges. `reorder_agent` then doubles as the counter-proposal re-entry point, which it could not do if it also owned the verdict.
> 2. **`monitor` renamed `recorder`,** because its actual job is writing the append-only ledger row on **every** terminal path, not watching anything. The name should say what it does.
> 3. **`inventory_auditor` became post-write verification rather than the ledger writer** — separating "did the write do what it claimed" from "record what happened" means a failed verification is itself recorded, which a combined node cannot do.
>
> Node count is unchanged at 8 (4 preserved + 4 new), and all graded constraints still hold.

The story upgrades from *"I have four agents"* to **"my agents decide and act, and they know what they are not allowed to do"** — same node names, real substance, zero graded-test risk.

### AD-8 — Triggers: an in-process event bus plus two entry points

`src/core/events.py` — a synchronous in-process bus with named domain events and **persisted run records** in `agent_runs` for traceability. No broker.

Two entry points into the same `SignalEngine.scan()`:
1. **Post-commit hook on stock writes** — gives a sub-second demo response to a human action.
2. **APScheduler tick — env-gated, default OFF** — gives the "it runs unattended" claim without breaking the Phase 1 test suite.

Justification to state out loud: a single-node deployment with persisted run records gets traceability without operational weight.

### AD-9 — A controllable clock is a cross-cutting contract

`src/core/clock.py` exposes `now()` and `today()`, offsettable via env and an admin endpoint. **Every date comparison in new code must use it** — otherwise overdue-PO detection cannot be demonstrated without waiting days. This is a Wave-1 dependency for almost everything.

### AD-10 — The React SPA becomes the product. Streamlit is demoted.

React already has working CRUD, real auth, and is where a business user would live. Streamlit cannot deliver a credible enterprise experience (no routing, no design system, full rerun on every interaction).

- **React** = the product: Control Tower, Signals, Approvals, Decisions, Inventory, Suppliers, Impact.
- **Streamlit** = retained as an internal **Agent Console** / engine-room view, and as the intact home of the graded Phase 3/4/5 demo tabs. It is **not** part of the product demo path.
- The 1136-line `App.jsx` **must be decomposed before parallel UI work begins** — it is otherwise the worst conflict point in the repo.

### AD-11 — Preserve graded artifacts; unify only the product surface

The Phase 3 ReAct executor is **frozen at exactly 7 tools** (`assert len(agent.tools) == 7`). The Phase 4 MCP layer is open (`>= 6`).

Therefore: **do not touch `build_agent_executor`.** The product co-pilot is built on the **MCP toolset**, which is freely extensible. Both executors continue to exist for the graders; the product exposes one co-pilot.

### AD-12 — The agent gets its own least-privilege identity

Today `src/service_auth.py` logs in as `admin@retail.com` / `admin`, so **every agent action runs with full manager privilege attributed to "Admin".** Create a distinct `agent@retail.com` with role `agent` (free-text column — zero migration). The ledger then attributes honestly, and least-privilege becomes a demonstrable governance property rather than a claim.

### AD-13 — Policy retrieval uses a separate Chroma collection

Extending `inventory_manual.md` changes the graded corpus chunk count. **Do not touch it.** Policy documents for the Policy Engine go into a **separate Chroma collection** with **section-level metadata** (fixing the weak-citation problem) while the graded 21-chunk collection stays byte-identical.

**Gate:** before any change to the graded corpus, verify the actual assertion in `tests/phase2`. Default answer: don't.

> **VERIFIED 2026-08-25.** The graded assertions are `len(chunks) >= 20` (`tests/phase2/test_phase2.py:44`) and `len(c.page_content) <= 600` for every chunk (`:33`) — **not** `== 21`. The lock is therefore looser than assumed: the manual could be extended without breaking the tests, provided it still yields ≥20 chunks. AD-13 stands anyway, on citation-quality grounds rather than test-safety grounds — a separate collection is what buys section-level metadata. Risk downgraded from *blocker* to *low*.

### AD-14 — Dependencies are pre-declared once, in Wave 1

New Python deps: **`apscheduler`**, **`langgraph-checkpoint-sqlite`**. That is all. *(Both verified absent from `requirements.txt` on 2026-08-25; `langgraph>=1.2.0` and all 32 other packages are already declared.)*

New JS deps: **`react-router-dom`**, **`@tanstack/react-query`**, **`recharts`**. Three, not four.

> **VERIFIED 2026-08-25 — correction to an earlier claim.** `src/ui/web_react/package.json` declares exactly four runtime dependencies: `axios ^1.7.2`, `lucide-react ^0.395.0`, `react ^18.3.1`, `react-dom ^18.3.1`. So `lucide-react` and an HTTP client are **already present and need no addition**. More importantly: **there is no router, no charts library, and no server-state library today.** The existing app navigates via `const [activeTab, setActiveTab] = useState('dashboard')` (`App.jsx:160`). WS-6 must therefore *introduce* routing, not merely reorganise it — scope accordingly.

All of them are added by a **single owner in Wave 1**, before any other stream starts, so `requirements.txt` and `package.json` are never a merge conflict. *(Worth noting in the deck: an ambitious redesign needs two new Python packages.)*

### AD-15 — Safety rails on an autonomous writer

Non-negotiable, because a background process now writes to the business:

- **Idempotency keys** on every agent-initiated write — an agent retrying after a timeout must not create a duplicate PO.
- **Duplicate-order guard** — check for an in-flight PO covering the SKU before ordering. *(A real business rule no baseline POC will implement.)*
- **Blast-radius limits** — max POs per hour, max ₹ per day, circuit breaker on consecutive failures.
- **Kill switch** — pause autonomy globally, with a reason recorded.
- `_next_sequence` is documented as not concurrency-safe; the executor must serialise PO-number allocation.

---

## 5. Locked technical contracts (summary — detailed in `15-SHARED-CONTRACTS.md`)

### Signal types — seven

`threshold_breach` · `projected_breach` · `po_overdue` · `config_drift` · `supplier_drift` · `capital_drag` · `data_insufficient`

### Decision lifecycle

```
detected → investigating → decided → awaiting_approval → approved → executing → executed
                                  ↘ rejected      ↘ expired    ↘ failed
                        → shadow (backtest / shadow mode, never executes)
                        → superseded
```

### Autonomy modes — four

`off` · `shadow` (decide, record, never execute) · `assisted` (always require approval) · `autonomous` (execute within the envelope, escalate outside it)

### Human-readable ID conventions

`SIG-000045` · `DEC-000123` · `APR-000012` · `RUN-000078`

### API path namespace allocation (prevents route collisions between parallel streams)

| Namespace | Owner |
|---|---|
| `/analytics/*` | Analytics Core |
| `/signals/*` | Signal Engine |
| `/decisions/*`, `/approvals/*`, `/autonomy/*` | Governance |
| `/policy/*` | Policy Engine |
| `/sourcing/*`, `/suppliers/{code}/scorecard` | Supplier Intelligence |
| `/agent/*` | Autonomy Loop + Co-pilot |
| `/impact/*` | Metrics |
| `/simulation/*` | Simulation Harness |
| `/inventory-ext/*` (incl. the new `PATCH /products/{id}`) | Executor / inventory extensions |
| **`/products`, `/orders`, `/suppliers`, `/stock`, `/dashboard`, `/auth`** | **FROZEN — do not modify** |

### Test-directory ownership

Every stream writes to `tests/product/<stream>/`. **Nobody touches `tests/phase1` … `tests/phase5`.** That is the cleanest available conflict boundary and it doubles as the regression guarantee.

---

## 6. UI/UX direction (locked)

### Information architecture

```
Control Tower (home)  →  Signals  →  Approvals  →  Decisions
                      →  Inventory  →  Suppliers  →  Impact
                      →  Agent Console (internal)
```

Plus: a **⌘K command palette**, and the **co-pilot as a right-side drawer available on every screen, scoped to the current context** — not a separate tab.

**The home screen is an exception-first control tower, not a CRUD dashboard.** What needs a human comes first; totals come second.

### Design language — specified concretely so the result does not look AI-generated

**Light-first, dense, neutral.** This is a data-operations domain, not a consumer app.

| Rule | Value |
|---|---|
| Palette | Neutral grey scale + **exactly one** accent hue |
| Status colours | **Exactly four** semantic colours (critical / warning / ok / info) — nothing else is coloured |
| Type | System stack or Inter; **max two weights per screen**; `font-variant-numeric: tabular-nums` on every number |
| Grid | 8px spacing scale, strictly |
| Radius | **One** border radius across the entire app |
| Density | Tables are the primary primitive. Rows, not cards, for anything countable. |

**Explicitly banned:** gradient heroes; purple-to-blue gradients; glassmorphism; emoji as production iconography; more than one border radius; a card for every single stat; drop shadows used decoratively; centred marketing copy inside an operations tool.

### How agent actions are communicated

Four consistent surfaces, and the same vocabulary in all of them:
1. **Signal card** — what was detected, when, how severe, how much time is left.
2. **Decision record** — what it decided, the numbers it used, **the policy sentence it cited**, what it did or why it stopped.
3. **Approval request** — ordered as: *what I want to do → why → the policy I am obeying → expected impact → **what happens if you do nothing***. That last line is what makes it read as an enterprise workflow rather than a confirm dialog.
4. **Activity timeline** — plain-language, chronological, with each step's duration.

---

## 7. Measurable impact (locked — the honesty boundary)

### Genuinely computable from this application

Detection→action latency (against the manual's documented 24h SLA) · % of breaches detected unattended (**today: 0% — nothing runs without an inbound request**) · manual interaction count (today ≈ 8 UI interactions + 1 hand calculation → 1 approval click) · days-of-cover at detection · count and ₹ exposure of reorder points contradicting the manual's formula · duplicate POs avoided · policy-compliance rate (100% by construction) · autonomy rate (auto vs escalated) · supplier on-time % and average delay · PO cycle time (`order_date` → `received_date`) · working capital in dead stock · **shadow-mode counterfactual: stockout-days avoided across a 90-day replay**

### Requires real client data — say so explicitly rather than inventing it

₹ revenue protected by avoided stockouts · FTE hours or headcount saved in absolute terms · human error-rate reduction · **anything shaped like "14 days → 3 days" or "95% time saved"**

### The one honest before/after that can be staged live

**Time a human doing the replenishment task in the UI, then time Steward doing it.** Both measured in the room, both real, no counterfactual required. Per slide 9, *"Let me follow up with data" is a strength, not a weakness* — distinguishing "this is arithmetic on our data" from "this needs yours" reads as rigour.

### Two disclosures to make voluntarily

1. The 90-day demand history is **synthetic**, generated to exercise the math. The math is real; the volumes are illustrative.
2. Supplier reliability figures derive from **seeded** PO history.

---

## 8. Demo decision

Four scenarios are designed; **three are recommended for the live run.**

| # | Name | Beat | Verdict |
|---|---|---|---|
| **D1** | **The Refusal** — high-value breach → agent investigates, computes, finds the value exceeds ₹50,000, **refuses**, cites manual §10 → approval inbox → staff gets 403 → manager approves → **the graph resumes from its interrupt** → PO created → ledger entry | **Trust** | **PRIMARY** |
| **D2** | **The Root Cause** — a stockout that was not a demand problem: supplier drift plus a reorder point that assumes the contractual lead time → agent proposes both a re-source and a config fix → manager approves both | **Intelligence** | **PRIMARY** |
| **D3** | **The Audit** — nothing is alerting; the config audit finds N reorder points contradicting the manual, quantifies stockout risk and trapped capital → batch approve → applied | **Discovery** | **CLOSER if time** |
| **D4** | **The Honest Agent** — a cold-start SKU with no history: the agent declares insufficient data, **refuses to auto-order**, states exactly what it needs, and offers a conservative option for a human | **Credibility** | **Q&A ammunition** |

**Recommended live flow: D1 → D2 → close on the Impact meter.** D3 if time allows; D4 is the answer to *"what about bad data?"*

D4 deserves a note: the live DB has **two products with zero movements**. Rather than hide that, the agent **names it**. This converts the biggest credibility weakness in the project into a demonstration of rigour — and no baseline POC will do it, because everyone else's demo pretends to certainty.

---

## 9. Parallel execution decision

Four waves. Full detail in `14-PARALLEL-WORKSTREAMS.md`, `16-DEPENDENCY-GRAPH.md`, `17-CLAUDE-CODE-EXECUTION-PLAN.md`.

### Wave 0 — Foundations (single instance, must finish first)

**WS-0 Foundations & Contracts** — `src/core/clock.py`, `src/core/events.py`, `src/core/errors.py`, `src/core/ids.py`, the new SQLAlchemy model modules, shared Pydantic contract schemas, **all** dependency pre-declaration, and the frozen contract docs. Everything depends on this; it must be short and sharp.

### Wave 1 — Fully parallel, no interdependencies

| WS | Responsibility | Owns |
|---|---|---|
| **WS-1** | Analytics Core | `src/analytics/` |
| **WS-2** | Simulation & Data Harness | `src/simulation/` |
| **WS-3** | Signal Engine | `src/signals/` |
| **WS-4** | Governance Backend | `src/governance/` |
| **WS-5** | Policy Engine | `src/policy/` |
| **WS-6** | UI Foundation — **sole owner of the existing `App.jsx` decomposition** | `src/ui/web_react/src/` shell, routes, tokens |
| **WS-7** | Supplier Intelligence | `src/sourcing/` |

### Wave 2 — Depends on Wave 1

WS-8 Autonomy Loop (LangGraph) · WS-9 Executor & Inventory Extensions · WS-10 Background Runtime · WS-11 UI Control Tower + Signals · WS-12 UI Approvals + Decisions · WS-13 UI Impact + Executive · WS-14 Co-pilot · WS-15 Root-Cause Analyst · WS-16 Shadow Mode & Backtest · WS-17 Metrics & Impact API

### Wave 3 — Central integration (single owner, never parallel)

Router registration in `main.py` · lifespan wiring · model-module imports · event-bus subscriptions · UI route registration · seed orchestration · the demo runbook.

### Wave 4 — Validation

**Regression first:** all **210 graded test functions** must still pass — 65/34/38/33/40 across phases 1–5, verified by count. (The graded *spec* enumerates 110 test **cases**, 20/20/20/25/25; the implemented suites contain 210 functions. The 210 is the number that has to stay green.) Phase 3's `len(agent.tools) == 7` is the canary. Then per-stream unit tests, deterministic end-to-end demo runs from a clean database, a Gemini quota check on the loop, a security review of RBAC and idempotency, and a UI review against the design rules in §6.

### The three conflict rules that make this safe

1. **Never edit a file another stream owns.** New capability → new module.
2. **`main.py`, `models.py`, `requirements.txt`, `package.json`, and existing routers are owned centrally.** A stream that needs a line added there *requests* it; it does not add it.
3. **`tests/phase1`–`phase5` are read-only for everyone.**

---

## 10. Implementation order (recommended)

1. **WS-0 Foundations** — nothing else can start safely.
2. **WS-2 Simulation + WS-1 Analytics** — together they end the fabricated-numbers problem. **Everything credible depends on these two.**
3. **WS-3 Signals + WS-4 Governance + WS-5 Policy + WS-6 UI Foundation** — in parallel.
4. **WS-8 Autonomy Loop + WS-9 Executor + WS-10 Runtime** — the loop closes here; this is the first moment the product exists.
5. **WS-11/12 UI Control Tower + Approvals** — the first moment the product is *demonstrable*.
6. **WS-7 Supplier Intelligence + WS-15 Root Cause** — unlocks demo D2.
7. **WS-17 Metrics + WS-13 UI Impact** — unlocks the closing frame.
8. **WS-16 Shadow Mode + WS-14 Co-pilot** — depth and polish.
9. **Optional C15–C20** only if everything above is complete and green.

**Cut line if time runs short:** stop after step 5. D1 alone, with a working ledger and impact meter, already beats the baseline decisively. Steps 6–7 add D2 and the closing metric. Everything after step 7 is upside.

---

## 11. Risks acknowledged up front

| Risk | Mitigation |
|---|---|
| Graded tests regress | `tests/phase*` frozen; Phase 3 executor untouched; regression suite is the first gate in Wave 4 |
| Gemini 15 RPM quota exhausted mid-demo | AD-2 — deterministic detection/decision/execution; LLM only for narration; backtest is LLM-free |
| Scheduler starts during Phase 1 tests | Env-gated, default OFF (AD-8) |
| Synthetic history read as a real claim | Disclosed voluntarily on the slide and in the UI (§7) |
| `App.jsx` merge hell | WS-6 is the sole owner and decomposes it before any other UI stream starts (AD-10) |
| Duplicate POs from an autonomous writer | Idempotency keys + in-flight duplicate guard + serialised PO numbering (AD-15) |
| LangGraph checkpointer fragility | Documented fallback: state JSON on the decision row, re-enter at `executor` (AD-6) |
| Complexity outruns explainability (rubric §6 requires walking through every part) | Deterministic core keeps the explanation short: *"code decides, the model explains"* |
| Committed-credential exposure already on record | Out of scope for this package; rotation remains the repository owner's open item (`01-GROUNDING-BRIEF.md` §15) |
