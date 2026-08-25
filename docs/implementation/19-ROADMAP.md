# 19 — Roadmap & Prioritisation

> **Status:** Proposal. Nothing here is approved.
> **Purpose:** The full opportunity space, sorted into MUST BUILD / HIGH VALUE / OPTIONAL / REJECT, with the reason for each placement — and a sequenced plan.
> **Governing constraint (verbatim from the brief):** *"Reject anything that is merely 'AI for AI's sake.'"*

---

## 1. The test each capability had to pass

Four questions, in order. A capability that fails any of the first three does not get built regardless of how it scores on the fourth.

| # | Question | Fails if |
|---|---|---|
| 1 | **Does the data support it?** | It requires data that does not exist and cannot be honestly simulated |
| 2 | **Would ~100 other associates build it?** | It is CRUD, a dashboard, a chatbot, or a RAG lookup |
| 3 | **Does it re-introduce a fabricated number?** | Its output is a business figure an LLM or an untrained model produced |
| 4 | **Does it change what the system can *do*, or only what it can *say*?** | It only produces better text |

Question 3 is the sharpest filter and it eliminated the largest number of otherwise-attractive ideas. The current codebase already documents its own version of this failure at `agents.py:389-406` — in 3 of 3 runs the model invented `supplier_id: 101` and a ₹580.00 unit price against a real ₹600.00. **Any feature whose output is a number a model guessed re-creates that defect with a nicer wrapper.**

Question 4 is the one that separates this build from the baseline. A chatbot that explains a stockout better has improved what the system says. An agent that raises the purchase order, under a policy, with a citation, and stops when it lacks evidence, has changed what the system does.

---

## 2. MUST BUILD — C1 … C8

Without all eight, there is no product. Each is a hard dependency of the demo, not a nice-to-have.

| ID | Capability | Why it is not optional | Stream |
|---|---|---|---|
| **C1** | **Signal Engine** | Seven detectors. Six have a **verified baseline of zero** — no code path today could produce them. This is the entire M-4 impact claim | WS-3 |
| **C2** | **Grounded Analytics Core** | Every number, computed and cited. **Turns M-14 from 5 fabricated fields to 0.** Nothing else is trustworthy without it | WS-1 |
| **C3** | **Governed Autonomy Loop** | The durable interrupt. Propose → authorise → re-check → act. The one thing a chatbot cannot do | WS-8 |
| **C4** | **Policy Engine** | Ten ordered rules, first match wins. Authority has to be readable to be governance | WS-5 |
| **C5** | **Approval & Governance Workspace** | Three equally-weighted doors, with counter-proposal that recomputes and objects | WS-4 + WS-12 |
| **C6** | **Decision Ledger & Impact Meter** | Every decision with inputs, arithmetic, citation, actor. The audit artifact | WS-4 + WS-17 |
| **C7** | **Unified Product UI** | Currently one 1136-line `App.jsx` with `useState` tab switching. **A POC shell cannot carry this product** | WS-6, 11, 12, 13 |
| **C8** | **Simulation & Demo Harness** | **Zero of five products have a computable daily demand today.** Without this, every screen is correctly empty | WS-2 |

### 2.1 The two that look like infrastructure and are not

**C8 (Simulation)** reads like fixtures work. It is the gate on everything credible. Four of five products have no sale movements at all; the fifth has three sales sharing a single calendar day, because `server_default=func.now()` was evaluated by SQLite at insert time and the seeder never overrode it. Until C8 lands, C2 correctly returns `insufficient` for the entire catalogue, C1 has nothing to detect, and three of four demo scenarios cannot be reproduced.

**C2 (Analytics)** reads like a utility library. It is the single most defensible claim in the package, because M-14 — five fabricated numeric fields to zero — is checkable by reading the code in ninety seconds, needs no client data, and is already evidenced in the repository by the codebase's own comment. *"5 → 0"* beats *"40% fewer stockouts"* for a technical audience, because one is verifiable and the other is not checkable at all.

---

## 3. HIGH VALUE — C9 … C14

Each adds a distinct dimension. None is required for the loop to close.

| ID | Capability | What it adds | Cost | Stream |
|---|---|---|---|---|
| **C9** | Root-Cause Analyst | *Why*, not *what*. Ranked hypotheses **with unresolved competition preserved** | Low | WS-15 |
| **C10** | Reorder Point Auditor | **Zero of five stored reorder points are correct.** The audit nobody ran | Low | WS-1 + WS-3 |
| **C11** | Supplier Intelligence | Measured vs contract lead time. `PO-2026-0001` is late twice over and nothing has looked | Low | WS-7 |
| **C12** | PO Consolidation | Multi-SKU orders per supplier. Real ordering-cost saving | Medium | WS-9 |
| **C13** | Shadow Mode & Backtest | *"Run it for two weeks and compare."* The answer to the adoption objection | Medium | WS-16 |
| **C14** | Embedded Co-pilot | The agent inside the product rather than in a second app | Medium | WS-14 |

**C10 is the best value-to-cost ratio in the entire package.** It is arithmetic WS-1 already computes, and the finding is severe: every stored reorder point in the catalogue is wrong, in both directions, and the alerting mechanism is calibrated by the value being audited. Rice's stored ROP is 15 against a derived 28 at contract lead time and **44 at measured lead time** — so the dashboard reads green while the product is already four days past the point where ordering would have been on time.

**C13 is lowest priority and highest strategic value in a client conversation.** It is a product answer to *"how would we ever trust this?"* rather than a reassurance.

---

## 4. OPTIONAL — C15 … C20

Built only if Wave 3 completes early. None appears in the demo.

| ID | Capability | Why optional |
|---|---|---|
| **C15** | Dead-stock release | Real, but competes with C12 for the same capital narrative |
| **C16** | Shrinkage watch | Needs adjustment-movement history that does not exist |
| **C17** | Reservation semantics | `reserved` is `0` for all five products. No demand for it yet |
| **C18** | Executive PDF export | `metric_snapshots.data_disclosure` already makes it safe. Just not needed live |
| **C19** | Real MCP over stdio | **The protocol is currently never spoken** — the chat interface imports the tools in-process. Honest to fix, invisible in a demo |
| **C20** | Real OTel exporter | Structlog JSON already covers the observability requirement |

C19 deserves its phrasing. The MCP server exists, exposes six tools, and passes 33 graded tests — and the protocol is bypassed. That is worth *stating* plainly whether or not it is fixed; fixing it changes no visible behaviour.

---

## 5. REJECT — and why

The most useful section in this document. Each of these is a thing that could plausibly be built, would look impressive in a title, and is worse than not building it.

### 5.1 Rejected because they re-introduce a fabricated number

| Idea | Why rejected |
|---|---|
| **ML demand forecasting (Prophet / ARIMA / LSTM)** | There are 13 stock movements spanning 7 hours. A model fitted on that produces a confident number with no information in it — **exactly the defect at `agents.py:389-406`, with a library instead of an LLM.** The honest move is the manual's own formula plus a sufficiency verdict |
| **LLM-generated reorder recommendations** | The current system's actual bug. Removing it is the headline claim (M-14); adding it back anywhere is self-defeating |
| **Text-to-SQL "ask anything" analytics** | A generated query producing a number nobody can trace. The product's central rule is that every business number has a formula and a citation. Text-to-SQL is a fabrication engine with good manners |
| **Anomaly detection on movement history** | Unsupervised learning on 13 rows. Every output would be an artifact of the sample size |
| **Autonomous price optimisation** | No elasticity data, no margin targets, no competitor prices. Also out of scope — this is inventory and procurement, not pricing |
| **Confidence scores from LLM self-report** | Already one of the five fabricated fields. Self-reported confidence is not a measurement |

### 5.2 Rejected because the data does not exist and cannot be honestly simulated

| Idea | Why rejected |
|---|---|
| **Shelf-image recognition / planogram compliance** | No images. Would be pure theatre |
| **Supplier email sentiment / negotiation agent** | No email corpus, no supplier communication channel. Also: an agent that sends messages to real suppliers is an outward-facing action whose failure mode is a commercial relationship |
| **Customer demand-signal ingestion (weather, events, social)** | No integration, no history to validate against. A weather API call producing a demand multiplier is a fabricated number with a source URL |
| **Fill-rate optimisation** | §13 line 138 defines fill rate, and **no customer-order entity exists.** This is M-25 — reported as a named gap rather than fabricated |
| **Multi-store transfer optimisation** | One store. Modelling a second is inventing a business |

### 5.3 Rejected because it is agent theatre

The brief was explicit: *"Do not add multi-agent architecture just because it sounds impressive."*

| Idea | Why rejected |
|---|---|
| **More agents to raise the agent count** | Each agent is a failure point and an LLM call. The eight-node graph is the number of nodes the work needs. A "Negotiation Agent" with nobody to negotiate with is a slide, not a system |
| **An LLM critic/judge agent reviewing decisions** | No ground truth to judge against. Adds latency and a second opinion with no more information than the first. The **policy engine** is the reviewer, and it is deterministic and auditable |
| **Agent-to-agent debate** | Two LLMs disagreeing about a number that neither computed. The numbers come from arithmetic; there is nothing to debate |
| **A "digital twin" of the store** | The simulation harness is the honest version of this. "Digital twin" is the same thing with a claim attached |
| **Voice interface** | Zero information gain, nonzero demo failure risk, and it does not survive a noisy room |
| **Autonomous supplier onboarding** | Creating commercial relationships without human authorisation is the exact opposite of the governance thesis |

### 5.4 Rejected architecture and tooling

| Choice | Why rejected |
|---|---|
| **Alembic migrations** | Real cost, and the design avoids needing it: new tables only, `create_all` is additive at table granularity, every new status column is `String` |
| **PostgreSQL** | SQLite is sufficient for one store, and the checkpointer already uses it. Migrating buys nothing demonstrable |
| **Redis / Celery / a real broker** | An in-process synchronous bus is correct at this volume, and it is *debuggable* — a stack trace instead of a queue |
| **Next.js / a framework migration** | Vite + React works. Rewriting the build tooling is effort with no visible output |
| **A component library (MUI / Chakra / shadcn)** | The product needs ~10 primitives, several of them unusual (`<ProvenanceMark>`, `<RefusalCard>`, `<EmptyState reason formula missingInput>`). A library supplies the easy nine and none of the ones that matter, plus a design language that is not this product's |
| **WebSockets for live updates** | Polling at 30s is indistinguishable in a demo and cannot break mid-presentation |
| **Fine-tuning a model** | The LLM writes prose. Prose does not need fine-tuning, and every number bypasses the model entirely |
| **Removing LangGraph** | Genuinely considered. It earns its place through exactly one feature — the durable interrupt across a process restart (AD-6). That feature is the product's spine, so it stays. **If that test were dropped, LangGraph should be removed too** |

The last row is worth its space: it is the one place where the honest answer was "keep it", and the reason is a single testable property rather than momentum.

### 5.5 The three rejections that were hardest

**ML forecasting.** The single most requested feature in this problem domain, and the most tempting title on a slide. Rejected because it would put a fabricated number back at the centre of the product — undoing M-14, the strongest claim in the package — and because 13 movements across 7 hours cannot support any model. The defensible version is the manual's formula, computed, cited, with an explicit sufficiency verdict and a refusal when the evidence is thin. **That is a *better* answer, not a smaller one**: it is what an honest system does when it does not have enough data, and it is demonstrable today.

**A richer conversational interface.** Genuinely valuable, and it is C14 — but as a *drawer inside the product*, not as the product. A chatbot is what ~100 associates will build. The differentiator is not talking about inventory; it is acting on it under governance.

**Multi-store.** The natural "scale" story, and it would impress. Rejected because it is a rearchitecture with no demonstrable output: a second store is a second set of invented data, and the interesting problems (transfer optimisation, network allocation) all require demand history the project does not have. Naming it as an explicit non-goal is more credible than a half-built version.

---

## 6. Sequenced roadmap

| Wave | Streams | Capabilities delivered | Demo state after |
|---|---|---|---|
| **0** | WS-0 | — | Nothing visible. Everything unblocked |
| **1** | WS-1, 2, 3, 4, 5, 6, 7 | **C2, C8**, C1 partial, C4, C10, C11 | **Numbers become real.** M-14 achievable |
| **2** | WS-8, 9, 10, 11, 12, 17 | **C1, C3, C5, C6, C7** | **D1 + D2 work. The product exists** |
| **3** | WS-13, 14, 15, 16 | C9, C12, C13, C14 | D3 + D4 land. Depth |
| **Final** | Integration | — | 4/4 scenarios verify. 210/210 graded green |

### 6.1 The cut line

**Stop after Wave 2 if time is short.** That delivers:

- Every MUST BUILD capability, C1 through C8
- Demos D1 (governed high-value order) and D2 (the green dashboard that is wrong)
- A real ledger, a real durable interrupt, a working Impact screen
- All four honesty claims from file 18 §10

Wave 3 is depth. **If it is dropped entirely, the demo is unaffected** — which is the property the last wave should have, and it is why C13 and C14 sit there rather than earlier.

### 6.2 If there is spare capacity

In order:

1. **WS-10 (Background Runtime), if it slipped.** Small stream, one consumer, total dependency slack — and without it *"HANDLED WHILE YOU WERE AWAY"* is false and the product is a button someone presses. Cheapest severe failure in the plan
2. **C10's audit across `reorder_quantity` as well as `reorder_point`.** Same arithmetic, second unaudited field, more findings
3. **C13 Shadow Mode.** The best answer to the adoption question
4. **C19 real MCP transport.** Invisible, but it makes a currently-hedged claim unhedged

Not: another agent, another screen, another chart.

---

## 7. What this roadmap refuses to claim

| Claim not made | What is said instead |
|---|---|
| "X% stockout reduction" | The formula (M-26), and the one missing input: real demand history |
| "₹N saved annually" | The formula (M-23), margin **is** available, demand history is not |
| "N FTE hours saved" | The formula (M-24), and the missing time-and-motion baseline nobody has measured |
| "Production ready" | Single store, SQLite, synthetic data, one seeded user. All stated |
| "Full MCP integration" | Six tools exist; **the protocol is bypassed in-process.** C19 would fix it |
| "Forecasting" | Deterministic formulas from the client's manual, with a sufficiency verdict and a refusal path |

**A single invented figure would compromise every honest number beside it.** The Impact screen's value is that a reviewer can check any figure on it; one unfalsifiable claim destroys that property for the entire screen — and, by extension, for this roadmap.

---

## 8. One-paragraph summary

Build the eight MUST BUILD capabilities in three waves, in this order: **make the numbers real (C2, C8), then make the loop close (C1, C3, C4), then make it governable and visible (C5, C6, C7).** Add C9–C11 in the same waves because they are nearly free arithmetic on top of C2. Stop after Wave 2 if time is short — that is a complete product. Reject anything whose output is a number a model guessed, anything requiring data that does not exist, and anything whose value is that it sounds impressive. **The differentiator is not that the system talks about inventory; it is that it acts on inventory under a policy, cites the sentence that authorised it, and refuses when it cannot show its work.**

---

**Next:** [20-RISKS-AND-CONSTRAINTS.md](20-RISKS-AND-CONSTRAINTS.md) states what could go wrong, what is genuinely unknown, and what this system will never do.
