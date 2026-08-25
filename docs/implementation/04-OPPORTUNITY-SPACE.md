# 04 — Opportunity Space

> **Status:** Proposal input. Nothing here is approved.
> **Purpose:** Enumerate the *full* space of things this product could become — deliberately wider than what will be built — then prune it with stated tests. The locked outcome is in [00-EXECUTIVE-SUMMARY.md](00-EXECUTIVE-SUMMARY.md) §3; this document shows the work behind it.
> **Reading order:** §1–§7 are the wide space. §8 is the prioritisation. §9 is the self-challenge. §10 is the reject rationale.

---

## 1. Autonomy & Control

| # | Idea | One-line description |
|---|---|---|
| A1 | Scheduled sense loop | A background tick that evaluates inventory state without human initiation. |
| A2 | Event-driven trigger | A stock write immediately raises evaluation for the affected SKU. |
| A3 | Autonomy dial | Per-category modes: off / shadow / assisted / autonomous. |
| A4 | Value-threshold authority | The agent acts alone below a monetary limit, escalates above it. |
| A5 | Confidence-gated authority | The agent escalates when its own data-sufficiency score is low, regardless of value. |
| A6 | Blast-radius caps | Hard per-hour and per-day limits on orders and spend. |
| A7 | Kill switch | One control that halts all autonomous action instantly. |
| A8 | Circuit breaker | Auto-suspend autonomy after N consecutive failures or rejections. |
| A9 | Shadow mode | The agent decides but does not execute; decisions are recorded for comparison. |
| A10 | Progressive autonomy | Authority expands automatically as approval rates stay high. |
| A11 | Time-boxed autonomy | Autonomy active only during business hours. |
| A12 | Idempotent execution | Replay-safe actions keyed so a retry cannot double-order. |
| A13 | In-flight duplicate guard | Refuse a new order for a SKU that already has one in transit. |

## 2. Detection & Sensing

| # | Idea | One-line description |
|---|---|---|
| D1 | Threshold breach | Stock at or below reorder point. *(The only detection that exists today.)* |
| D2 | Projected breach | Stock will cross the reorder point within lead time, given measured velocity. |
| D3 | Overdue PO | `expected_delivery` has passed with no receipt. |
| D4 | Config drift | The configured reorder point disagrees with what measured demand implies. |
| D5 | Supplier drift | A supplier's delivery reliability is degrading over time. |
| D6 | Capital drag | Stock far above requirement — money sitting on a shelf. |
| D7 | Data insufficiency | Not enough history to decide responsibly. |
| D8 | Demand-shape change | A step change in velocity that invalidates the current profile. |
| D9 | Dead stock | No movement for N days. |
| D10 | Shrinkage | Adjustment movements exceeding a tolerance. |
| D11 | Margin erosion | Supplier cost rising against selling price. |
| D12 | Stockout post-mortem | Reconstruct why a stockout happened after the fact. |
| D13 | Seasonality detection | Recurring periodic demand patterns. |
| D14 | Category cannibalisation | One SKU's rise correlating with another's fall. |

## 3. Decision Quality

| # | Idea | One-line description |
|---|---|---|
| Q1 | Deterministic reorder maths | EOQ / safety stock / reorder point computed in code, not by an LLM. |
| Q2 | Data-sufficiency scoring | An explicit measure of whether history supports a decision. |
| Q3 | Root-cause investigation | The agent explains *why* a signal fired, not just that it did. |
| Q4 | Multi-supplier sourcing | Compare price, lead time, and reliability across suppliers. |
| Q5 | Reliability-weighted choice | Prefer a costlier supplier when reliability justifies it. |
| Q6 | PO consolidation | Combine SKUs from one supplier into a single order to amortise ordering cost. |
| Q7 | Reorder-point audit | Systematically re-derive every configured reorder point. |
| Q8 | Counter-proposal handling | Human edits quantity or supplier; system recomputes and re-explains. |
| Q9 | Backtest / counterfactual | Replay history to compare agent decisions against what happened. |
| Q10 | Statistical forecasting (ARIMA/Prophet) | Time-series models for demand. |
| Q11 | ML demand model | Trained regression on features. |
| Q12 | Substitution recommendation | Suggest an alternative SKU during a stockout. |
| Q13 | Scenario what-if | "What if demand rises 20%?" |
| Q14 | ABC classification | Segment SKUs by value contribution. |

## 4. Governance & Trust

| # | Idea | One-line description |
|---|---|---|
| G1 | Approval inbox | A queue of decisions awaiting human judgment. |
| G2 | Policy retrieval with citation | Thresholds read from the manual and quoted, not hardcoded. |
| G3 | Real RBAC enforcement | Role checked before every consequential action. |
| G4 | Least-privilege agent identity | The agent has its own account, not the admin's. |
| G5 | Append-only decision ledger | Every decision, its inputs, its reasoning, its outcome. |
| G6 | Refusal as a first-class outcome | Declining to act is recorded and explained, not silent. |
| G7 | Attribution | Every write traceable to a human or the agent. |
| G8 | Approval SLA timers | Escalate when an approval sits too long. |
| G9 | Delegation | A manager temporarily grants authority. |
| G10 | Policy simulation | Preview what a policy change would have done. |
| G11 | Four-eyes approval | Two approvers above a higher threshold. |
| G12 | Immutable reasoning snapshot | Store the exact inputs the decision was made on. |

## 5. Impact Measurement

| # | Idea | One-line description |
|---|---|---|
| M1 | Decision latency | Time from signal raised to action executed. |
| M2 | Autonomy rate | Share of decisions resolved without a human. |
| M3 | Approval outcome rate | Approved / rejected / modified proportions. |
| M4 | Signals detected by class | Volume by detector, including those a human would have missed. |
| M5 | Overdue POs caught | Count of late deliveries surfaced that previously were invisible. |
| M6 | Config drift corrected | Reorder points brought in line with measured demand. |
| M7 | Human-vs-agent timing race | Live, in-room, measured. |
| M8 | Shadow-mode counterfactual | Agent decisions vs actual history over the replay window. |
| M9 | Stockout days avoided (simulated) | Derived from replay, on disclosed synthetic data. |
| M10 | Capital efficiency | Value of stock above requirement. |
| M11 | ₹ revenue protected | **Requires real client data.** |
| M12 | FTE hours saved | **Requires real client data.** |
| M13 | Order-cost savings from consolidation | Computable from the manual's own ordering-cost term. |

## 6. Experience

| # | Idea | One-line description |
|---|---|---|
| X1 | Unified product surface | One application, not two. |
| X2 | Exception-first home | What needs a human, before totals. |
| X3 | Approval detail view | The full case for a decision, in business language. |
| X4 | Decision timeline | A readable history of everything the agent did. |
| X5 | Impact / executive view | Outcomes, not activity. |
| X6 | Embedded co-pilot | Context-scoped assistant in a drawer, not a separate tab. |
| X7 | Command palette | Keyboard-driven navigation and action. |
| X8 | Signal inbox | Triage surface for detections. |
| X9 | Supplier scorecard | Reliability and price history per supplier. |
| X10 | Insufficient-data state as a feature | The agent visibly declining, with what it needs. |
| X11 | Blast-radius visualisation | Show the caps and how close autonomy is to them. |
| X12 | Live agent activity stream | What the agent is doing right now. |
| X13 | Mobile approvals | Approve from a phone. |
| X14 | Voice interface | Spoken queries. |
| X15 | Email/Slack notifications | Push approvals to where people already are. |
| X16 | Executive PDF export | A shareable summary. |

## 7. Data & Simulation

| # | Idea | One-line description |
|---|---|---|
| S1 | 90-day backfilled history | Realistic movement history with weekday/weekend shape. |
| S2 | Per-product demand profiles | Distinct velocity and variance per SKU. |
| S3 | Supplier delivery variance | Seeded reliability differences so scoring has signal. |
| S4 | Multi-supplier price entity | The missing table that makes sourcing possible. |
| S5 | Named demo scenarios | Deterministic, loadable starting states. |
| S6 | Controllable clock | Advance time to demonstrate overdue detection without waiting. |
| S7 | Deterministic replay | Backtest without LLM calls — fast and quota-free. |
| S8 | Partial-receipt support | Record 80 of 100 units delivered. |
| S9 | Reservation semantics | Make `quantity_reserved` mean something. |
| S10 | Multi-warehouse | Stock across locations. |
| S11 | Real supplier integration | Email or portal submission. |
| S12 | External signal ingest | Weather, holidays, promotions. |

**Total enumerated: 84 candidate ideas.**

---

## 8. Prioritisation

The locked set from [00-EXECUTIVE-SUMMARY.md](00-EXECUTIVE-SUMMARY.md) §3, with the ideas above mapped into it.

### 8.1 MUST BUILD — C1–C8

Without all eight, there is no product — only a better demo.

| C | Capability | Absorbs | Why it is non-negotiable |
|---|---|---|---|
| **C1** | Signal Engine | A2, D1–D7 | Replaces the inert alert table with real detection. Without it nothing initiates. |
| **C2** | Grounded Analytics Core | Q1, Q2 | Ends the fabricated-numbers problem (W2). Every credible claim depends on this. |
| **C3** | Governed Autonomy Loop | A4, A12, A13, D-lifecycle | The loop that actually closes. This is the product. |
| **C4** | Policy Engine | A3, G2 | Retrieved-and-cited thresholds. The differentiator competitors cannot fake. |
| **C5** | Approval & Governance Workspace | G1, G3, G6, A6, A7 | Where the human exercises authority. Also where RBAC becomes real. |
| **C6** | Decision Ledger & Impact Meter | G5, G7, G12, M1–M6 | Accountability. The precondition for anyone believing the rest. |
| **C7** | Unified Product UI | X1, X2, X3, X4, X5, X8 | Ends the two-app split (W17). |
| **C8** | Simulation & Demo Harness | S1, S2, S3, S5, S6 | Makes every number defensible and every demo repeatable. |

### 8.2 HIGH VALUE — C9–C14

Each materially strengthens the story; none blocks the loop.

| C | Capability | Absorbs | Value |
|---|---|---|---|
| **C9** | Root-Cause Analyst | Q3, D12 | Turns "stock is low" into "stock is low *because*". The clearest showcase of genuine LLM value. |
| **C10** | Reorder Point Auditor | D4, Q7, M6 | Agent improving the *configuration*, not just operating within it. Unblocks W9. |
| **C11** | Supplier Intelligence | D3, D5, Q4, Q5, S4, X9, M5 | Makes `supplier_coordinator` mean something (W8) and overdue detection possible (W7). |
| **C12** | PO Consolidation | Q6, M13 | Justified by the manual's own EOQ ordering-cost term — not invented. |
| **C13** | Shadow Mode & Backtest | A9, Q9, S7, M8, M9 | The only honest counterfactual available without client data. |
| **C14** | Embedded Co-pilot with memory | X6, X7 | Fixes stateless chat (W14) and folds the AI into the product surface. |

### 8.3 OPTIONAL — C15–C20

Build only if the cut lines in [19-ROADMAP.md](19-ROADMAP.md) are cleared early.

| C | Capability | Absorbs | Condition |
|---|---|---|---|
| **C15** | Dead-stock release | D9, D6, M10 | If capital-efficiency framing is wanted for the exec view. |
| **C16** | Shrinkage watch | D10 | Cheap detector; low narrative value. |
| **C17** | Reservation semantics | S9, W16 | Only if allocation becomes part of a workflow. |
| **C18** | Executive export | X16 | Nice-to-have; the screen itself is the deliverable. |
| **C19** | Real MCP over stdio | W13 | Technical honesty fix. Matters only to a reviewer who probes it. |
| **C20** | Real OTel exporter | W15 | Activates dead instrumentation. |

### 8.4 REJECT

| Idea | Reason for rejection |
|---|---|
| X14 Voice interface | Pure novelty. Adds a failure mode to a live demo and no business value. Textbook AI-for-AI's-sake. |
| Q10 ARIMA/Prophet | A statistical model on a 90-day *synthetic* series produces false precision. Deterministic velocity + variance is more honest and fully explainable. Also adds a heavy dependency. |
| Q11 ML demand model | Same objection, worse: unexplainable, and the rubric requires associates to explain every part of their implementation. |
| S10 Multi-warehouse | Multiplies schema and UI complexity to demonstrate nothing new about agency. |
| Q14 ABC analysis | **Not in `inventory_manual.md`.** Grounding it would require inventing policy, which breaks the retrieved-policy principle. A grounding trap dressed as a feature. |
| S11 Supplier email/portal | Outbound side effects to third parties in a POC. Unsafe, unverifiable, undemoable. |
| Q12 Substitution | Requires product-similarity data the model does not have. Would be pure LLM guesswork on identifiers — exactly the failure recorded at `agents.py:389-406`. |
| Kafka / Celery / Redis | Infrastructure for a scale that does not exist. A single-node SQLite deployment with persisted run records needs an in-process bus. |
| Fine-tuning | No training data, no evaluation set, and the programme locks the model. |
| X13 Mobile app | A second frontend when the first one is being rebuilt. |
| Blockchain audit | An append-only SQL table with attribution is the correct answer. |
| Q13 Scenario what-if | Cut reluctantly — genuinely useful, but overlaps C13's replay and costs a whole UI surface. Revisit only after C13 lands. |
| D13 Seasonality | 90 days of synthetic data cannot evidence a seasonal cycle. Claiming otherwise would be dishonest. |
| D14 Cannibalisation | Requires a product catalogue with real category relationships and far more history. |
| S12 External signals | No credible data source in scope; would be a hardcoded fixture pretending to be a feed. |
| G11 Four-eyes approval | Only one manager persona exists. Ceremony without substance at this scale. |
| A10 Progressive autonomy | Attractive, but needs a decision history longer than the demo window to be anything but a hardcoded rule. |
| A11 Time-boxed autonomy | A config flag masquerading as a capability. |
| G9 Delegation | Adds an RBAC edge case with no narrative payoff. |
| X15 Email/Slack notifications | Outbound integration risk; the approval inbox is the demonstrable surface. |
| M11 ₹ revenue protected | **Not rejected as an idea — rejected as a claim.** See [10-IMPACT-METRICS.md](10-IMPACT-METRICS.md) §2. |
| M12 FTE hours saved | Same. Named, with the client data required to compute it. |

### 8.5 Surfaced but not in the locked set

Ideas the enumeration produced that are **not part of the plan**, recorded so they are not re-proposed as discoveries:

| Idea | Verdict |
|---|---|
| A5 Confidence-gated authority | **Folded into C4**, not separate — data-sufficiency already gates escalation. |
| A8 Circuit breaker | **Folded into C3/AD-15** as a safety rail. |
| D8 Demand-shape change | Deferred. C10's config-drift detector covers the actionable half. |
| D11 Margin erosion | Deferred — needs selling-price history the model lacks. |
| G8 Approval SLA timers | **Partially in C5** via the manual's 24h language; full escalation chains are stretch. |
| G10 Policy simulation | Deferred to after C13. |
| X11 Blast-radius visualisation | **Folded into C5** as a panel, not a screen. |
| X12 Live activity stream | **Folded into C7** as a Control Tower zone. |
| S8 Partial receipt | **Folded into C8** as a seeder requirement. |

---

## 9. Self-challenge matrix

Nine tests applied to every MUST BUILD and HIGH VALUE capability. **✓** = passes, **~** = partial, **✗** = fails.

| Test | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | C13 | C14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Would a baseline POC have this? | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ~ |
| Genuinely agentic? | ~ | ✗ | ✓ | ✓ | ~ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ~ | ✓ | ✓ |
| Agent takes meaningful action? | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ~ | ✗ |
| Measurable value? | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ~ | ✓ | ✓ | ✓ | ✓ | ~ |
| Demonstrable live in minutes? | ✓ | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Believable to an enterprise audience? | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Feasible in this codebase? | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Complexity justified? | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ✓ |
| Strengthens the product story? | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ✓ |

### 9.1 Reading the failures honestly

The **✗** marks are the interesting part, and none of them is a reason to cut.

- **C2, C6, C7, C8 are not agentic and take no action.** Correct — and deliberate. They are the *substrate*: honest numbers, an audit record, a surface, and a world to operate in. Per AD-2, arithmetic and execution are explicitly kept away from the LLM. A capability that isn't agentic isn't automatically waste; C2 is what makes C3's agency defensible.
- **C1 is only partially agentic.** Detection is deterministic by design. An LLM-based detector would be slower, non-reproducible, and quota-bound. Determinism here is a feature.
- **C12's complexity is marked partial.** It is the weakest MUST/HIGH item — consolidation logic is fiddly and the payoff is a modest ordering-cost saving. It stays only because the manual's EOQ formula contains an `ordering_cost` term, which means the saving is *grounded* rather than invented. **First candidate to cut** if time compresses.
- **C7's feasibility is partial.** The 1,136-line `App.jsx` must be decomposed before parallel UI work, which is a genuine serialisation point (AD-10, WS-6). Acknowledged in the dependency graph rather than wished away.
- **C14 partially duplicates a baseline POC.** Every associate will have a chatbot. What differs is that this one is context-scoped, memory-bearing, and cannot act outside policy. Thin differentiation on its own — which is exactly why it is HIGH VALUE and not MUST BUILD.

### 9.2 The test that matters most

**"Would a baseline POC have this?"** — the answer is ✗ for twelve of fourteen capabilities. The two partials (C7, C14) are surfaces every POC will have in *some* form, differentiated by execution rather than existence.

This is the whole argument. The programme's phase documents ship near-complete reference implementations, so roughly 100 associates will converge on the same five phases. Differentiation cannot come from doing those phases better. It comes from **building the layer the phase documents never asked for**: detection, authority, governance, and proof.

---

## 10. Reject rationale — the standing record

If any of the following is proposed again during implementation, this is the answer. Recorded here so the reasoning does not have to be rediscovered.

| Rejected | The one-line answer |
|---|---|
| Voice | Adds a live-demo failure mode, adds no business value. |
| ARIMA / Prophet / ML forecasting | False precision on synthetic data, and unexplainable against a rubric that requires explanation. |
| ABC analysis | Not in the manual. Would require inventing policy. |
| Multi-warehouse | Complexity multiplier that demonstrates nothing about agency. |
| Supplier email / portal | Outbound third-party side effects in a POC. |
| Substitution | LLM guesswork on product identifiers — the exact failure already recorded in the code. |
| Kafka / Celery / Redis | Wrong scale. In-process bus + persisted runs is correct here. |
| Fine-tuning | No data, no eval set, model is programme-locked. |
| Mobile | Second frontend while the first is being rebuilt. |
| Blockchain | An append-only table with attribution already solves this. |
| Seasonality | 90 synthetic days cannot evidence a cycle. |
| Four-eyes approval | One manager persona. Ceremony without substance. |
| Invented ROI figures | See [10-IMPACT-METRICS.md](10-IMPACT-METRICS.md) §7. Refusing is a feature. |

---

**Next:** [05-DIFFERENTIATING-CAPABILITIES.md](05-DIFFERENTIATING-CAPABILITIES.md) specifies C1–C14 in the seven-part format.
