# Steward — Planning Package

**Autonomous Replenishment Control Tower.** A proposal for the next evolution of POC-07.

> **Status: PROPOSAL. Nothing in this package is approved.**
> No source code has been modified. Nothing has been committed or pushed. Every capability, workstream, and architecture decision here awaits a decision.

---

## What this is

A complete product + architecture + execution plan for turning POC-07 from a system that *describes* inventory into one that *acts on* it — under a policy, with a citation, and with a refusal path when the evidence is thin.

It is written to be built by **multiple Claude Code instances working in parallel**, which is why roughly a third of it is interface contracts and file-ownership rules rather than product design.

**Every factual claim about the current system was verified against the code, the schema, or the live database** — not against the existing documentation. Where the documentation and the code disagree, the code wins and the discrepancy is recorded (see [01](01-GROUNDING-BRIEF.md) §12).

---

## Reading order

Pick the path that matches what you are about to do.

### If you have 10 minutes — decide whether this is worth doing

1. **[00-EXECUTIVE-SUMMARY.md](00-EXECUTIVE-SUMMARY.md)** — the spine. Product thesis, the 15 locked architecture decisions, the wave plan
2. **[19-ROADMAP.md](19-ROADMAP.md)** §5 — the REJECT list. The fastest way to judge the quality of a plan is to read what it refused to build

### If you are approving the build

1. [00-EXECUTIVE-SUMMARY.md](00-EXECUTIVE-SUMMARY.md) — the spine
2. [03-CURRENT-STATE-WEAKNESSES.md](03-CURRENT-STATE-WEAKNESSES.md) — W1–W18, the verified problems this exists to solve
3. [19-ROADMAP.md](19-ROADMAP.md) — MUST BUILD / HIGH VALUE / OPTIONAL / REJECT
4. [20-RISKS-AND-CONSTRAINTS.md](20-RISKS-AND-CONSTRAINTS.md) — including §5.1, the strategic bet this package makes
5. [13-DEMO-SCENARIOS.md](13-DEMO-SCENARIOS.md) — what the audience actually sees

### If you are the human operator running the parallel build

1. **[15-SHARED-CONTRACTS.md](15-SHARED-CONTRACTS.md)** — read this yourself, end to end. It is the one document whose errors are expensive
2. [17-CLAUDE-CODE-EXECUTION-PLAN.md](17-CLAUDE-CODE-EXECUTION-PLAN.md) — worktrees, ports, bootstrap, launch prompts, wave gates
3. [14-PARALLEL-WORKSTREAMS.md](14-PARALLEL-WORKSTREAMS.md) — WS-0 … WS-17, who owns which files
4. [16-DEPENDENCY-GRAPH.md](16-DEPENDENCY-GRAPH.md) — what blocks what, and what to do when a stream is late
5. [18-INTEGRATION-AND-TESTING.md](18-INTEGRATION-AND-TESTING.md) — what "done" means

### If you are an implementing instance

Read only what your launch prompt tells you to. In order: [15](15-SHARED-CONTRACTS.md), then your section of [14](14-PARALLEL-WORKSTREAMS.md), then your one or two spec files. **[15](15-SHARED-CONTRACTS.md) is frozen — never edit it.**

---

## The 21 documents

### Grounding — what is actually true today

| # | Document | What it establishes |
|---|---|---|
| 00 | [EXECUTIVE-SUMMARY](00-EXECUTIVE-SUMMARY.md) | **The spine.** Product thesis, AD-1 … AD-15, the wave plan. Where documents conflict, this wins |
| 01 | [GROUNDING-BRIEF](01-GROUNDING-BRIEF.md) | Every verified fact about the existing system, with file and line. §12 lists doc-vs-code discrepancies |
| 03 | [CURRENT-STATE-WEAKNESSES](03-CURRENT-STATE-WEAKNESSES.md) | **W1 … W18.** Verified defects, not opinions — including the five fabricated numeric fields the codebase documents against itself |

### Product — what it should become

| # | Document | What it establishes |
|---|---|---|
| 02 | [PRODUCT-VISION](02-PRODUCT-VISION.md) | SENSE / ACT / PROVE + SIMULATE. The five principles P1–P5, each with a falsification test |
| 04 | [OPPORTUNITY-SPACE](04-OPPORTUNITY-SPACE.md) | The **full** inventory of possibilities before prioritisation, plus the self-challenge matrix |
| 05 | [DIFFERENTIATING-CAPABILITIES](05-DIFFERENTIATING-CAPABILITIES.md) | **C1 … C20.** Each one: business problem → behaviour → agent reasoning → action → human involvement → outcome → measurable impact |
| 06 | [PERSONA-JOURNEYS](06-PERSONA-JOURNEYS.md) | Store manager, procurement lead, ops director, auditor. Before and after, hour by hour |
| 10 | [IMPACT-METRICS](10-IMPACT-METRICS.md) | **M-1 … M-36**, tiered T1/T2/T3. Every T3 metric shows its formula and its missing input, and never a number |
| 19 | [ROADMAP](19-ROADMAP.md) | MUST BUILD / HIGH VALUE / OPTIONAL / **REJECT**, with the reason for each placement |

### Experience — what it looks like

| # | Document | What it establishes |
|---|---|---|
| 07 | [UX-ARCHITECTURE](07-UX-ARCHITECTURE.md) | 17 routes, the design language, the ~10 primitives, and the decomposition of a 1,136-line `App.jsx` |
| 13 | [DEMO-SCENARIOS](13-DEMO-SCENARIOS.md) | **D1 … D4.** Fixtures with `expected_signals` verification, not scripts. Plus the click path, pre-flight, and contingencies |

### Engineering — how it works

| # | Document | What it establishes |
|---|---|---|
| 08 | [AGENTIC-WORKFLOWS](08-AGENTIC-WORKFLOWS.md) | The 8-node graph, the state schema, the durable interrupt, and every failure path |
| 09 | [BUSINESS-WORKFLOWS](09-BUSINESS-WORKFLOWS.md) | **BW-1 … BW-6.** Complete closed loops from trigger to measured outcome |
| 11 | [TARGET-ARCHITECTURE](11-TARGET-ARCHITECTURE.md) | The module map, what each technology actually contributes, and what is deliberately not changed |
| 12 | [DATA-AND-API-CHANGES](12-DATA-AND-API-CHANGES.md) | The 8 new tables, every new endpoint, and why zero existing columns change |

### Execution — how it gets built in parallel

| # | Document | What it establishes |
|---|---|---|
| 14 | [PARALLEL-WORKSTREAMS](14-PARALLEL-WORKSTREAMS.md) | **WS-0 … WS-17.** Authoritative for file ownership. Peak parallelism 7; files with more than one owner: 0 |
| 15 | [SHARED-CONTRACTS](15-SHARED-CONTRACTS.md) | **FROZEN.** Authoritative for every interface. Real signatures, the status vocabularies, the schema traps |
| 16 | [DEPENDENCY-GRAPH](16-DEPENDENCY-GRAPH.md) | Contract vs implementation dependencies, the critical path, and the late-stream playbook |
| 17 | [CLAUDE-CODE-EXECUTION-PLAN](17-CLAUDE-CODE-EXECUTION-PLAN.md) | Worktrees, ports, bootstrap, the launch prompt, the four wave gates |
| 18 | [INTEGRATION-AND-TESTING](18-INTEGRATION-AND-TESTING.md) | The 210-test regression floor, the eight tests worth writing, and what is deliberately not tested |
| 20 | [RISKS-AND-CONSTRAINTS](20-RISKS-AND-CONSTRAINTS.md) | Hard constraints, honest unknowns, the strategic bet, and what this system will never do |

---

## Precedence

When two documents disagree:

| Question | Authoritative document |
|---|---|
| Product thesis, architecture decisions AD-1 … AD-15 | [00-EXECUTIVE-SUMMARY](00-EXECUTIVE-SUMMARY.md) |
| Any function signature, type, or status vocabulary | **[15-SHARED-CONTRACTS](15-SHARED-CONTRACTS.md)** — frozen |
| Who owns which file | **[14-PARALLEL-WORKSTREAMS](14-PARALLEL-WORKSTREAMS.md)** |
| What is true about the existing code | [01-GROUNDING-BRIEF](01-GROUNDING-BRIEF.md) — and if it disagrees with the code, **the code wins** |

---

## ID conventions

| Prefix | Range | Meaning | Defined in |
|---|---|---|---|
| **W** | W1 … W18 | Verified current-state weakness | [03](03-CURRENT-STATE-WEAKNESSES.md) |
| **C** | C1 … C20 | Capability | [05](05-DIFFERENTIATING-CAPABILITIES.md) |
| **AD** | AD-1 … AD-15 | Architecture decision | [00](00-EXECUTIVE-SUMMARY.md) §4 |
| **BW** | BW-1 … BW-6 | Business workflow | [09](09-BUSINESS-WORKFLOWS.md) |
| **M** | M-1 … M-36 | Impact metric | [10](10-IMPACT-METRICS.md) |
| **D** | D1 … D4 | Demo scenario | [13](13-DEMO-SCENARIOS.md) |
| **WS** | WS-0 … WS-17 | Workstream | [14](14-PARALLEL-WORKSTREAMS.md) |
| **P** | P1 … P5 | Product principle | [02](02-PRODUCT-VISION.md) |

> **One namespace collision, stated so it cannot confuse anyone.** [04-OPPORTUNITY-SPACE](04-OPPORTUNITY-SPACE.md) uses **file-local** prefixes for its brainstorm inventory — `A` (autonomy), `D` (detection), `Q` (decision quality), and others, one per section. Those IDs are referenced nowhere outside file 04 and are deliberately not part of the package's shared vocabulary. So `D4` in file 04 means *config drift*; `D4` everywhere else means *the refusal demo*.

Runtime ID formats, for reference: `SIG-000045`, `DEC-000123`, `APR-000012`, `RUN-000078`, `PO-2026-0042`.

---

## The four numbers that define done

| Measure | Target |
|---|---|
| Graded tests still passing | **210 / 210** |
| Demo scenarios verifying | **4 / 4** |
| Numbers that change when the LLM is disabled | **0** |
| T3 metrics displaying a value | **0** |

All four are checkable in under five minutes, and every one of them is falsifiable by anyone in the room. That is the point.

---

## What this package refuses to claim

No ROI percentage. No "X% stockout reduction." No "₹N saved annually." No FTE-hours figure.

Not because those outcomes are implausible, but because **the data to compute them does not exist** — 13 stock movements spanning 7 hours, all sales generated by a seeder. [10-IMPACT-METRICS](10-IMPACT-METRICS.md) gives the formula for each one, names the single missing input, and stops there.

A single invented figure would compromise every honest number beside it.

---

## Verification pass

Run 2026-08-25 across all 21 documents.

| Check | Result |
|---|---|
| Internal cross-links resolve | **19 / 19 OK** |
| ID ranges continuous, no gaps or duplicates | C1–C20, AD-1–AD-15, WS-0–WS-17, BW-1–BW-6, M-1–M-36, W1–W18, D1–D4 — all clean |
| `src/core/clock.py` claimed to exist | **Corrected.** It does not exist; `find` confirms no `clock.py` anywhere in the repo. File 11 said "← exists" |
| Graded test count | **Corrected.** File 00 said "110 graded test cases" (the *spec's* case count). The operational number is **210 test functions** — 65/34/38/33/40 |
| `inventory_service.py` defect ownership | **Corrected.** Was WS-4 (governance) in file 11 §3.1; reassigned to WS-9, which owns the file. Defect table unified to three rows across files 11 and 14 |
| `src/core/` module list | **Corrected.** Reconciled file 11's tree with files 14/15: `clock, events, ids, vocab, errors`. `idempotency.py` moved to `src/execution/` under WS-9, its only consumer |
| Model modules | **Corrected.** File 11's tree gained `models_sourcing.py` and `models_registry.py` to match WS-0's ownership list |
| Files with more than one owner | **0** |

Six corrections, all made by checking the repository rather than the documentation. That ratio is the argument for the rule in [01](01-GROUNDING-BRIEF.md): *do not assume the documentation is correct if the code says otherwise.*

---

## Before anything is built

| Step | Who |
|---|---|
| Approve or reject the plan | The human. **Nothing here is approved** |
| Read [15-SHARED-CONTRACTS.md](15-SHARED-CONTRACTS.md) end to end | The human. It is cheap now and expensive at Gate 1 |
| Create worktrees **outside** the OneDrive tree | The human — see [20](20-RISKS-AND-CONSTRAINTS.md) §2.2 |
| Run Wave 0 solo, land it on `main`, pass Gate 0 | One instance |
| Open Wave 1 — 7 instances | Only after Gate 0 passes |
