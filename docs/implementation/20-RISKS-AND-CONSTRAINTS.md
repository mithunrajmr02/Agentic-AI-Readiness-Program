# 20 — Risks & Constraints

> **Status:** Proposal. Nothing here is approved.
> **Purpose:** What could go wrong, what is genuinely unknown, and what this system will never do.

---

## 1. Hard constraints — not risks, facts

These cannot be engineered away. Every design decision in the package is downstream of them.

| Constraint | Verified | Consequence |
|---|---|---|
| **Gemini free tier: 15 RPM / 1,500 RPD** | Documented in `.env.example` | Every business number must be LLM-free (AD-2). This constraint *produced* the architecture's best property |
| **No Alembic; `create_all` is additive at table granularity only** | `main.py:84`, `seed_demo_data.py:351` | New tables free. **New columns on existing tables impossible** |
| **SQLAlchemy `Enum` on SQLite → VARCHAR + CHECK** | `models.py:8-54` | `Category`, `MovementType`, `POStatus` can never gain a member |
| **13 stock movements, all within 7 hours on 2026-08-23** | Live DB | **Zero of five products have a computable daily demand.** Everything credible waits on the backfill |
| **`users` has exactly one row** | Live DB | RBAC and least-privilege agent identity are seed work, not schema work |
| **210 graded tests across 5 phases** | Counted | The regression floor. Read-only, always |
| **One store, one warehouse** | Schema | Multi-store is a rearchitecture, and an explicit non-goal |
| **No customer-order entity** | Schema | Fill rate (§13 line 138) is definable and **not computable** — M-25 |

The first row is worth restating: the rate limit is the reason the architecture is defensible. A project with unlimited LLM budget would have routed the numbers through the model and had no M-14 claim to make.

---

## 2. Technical risks

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| **WS-8's rewrite breaks a Phase 5 graded test** | High | **Medium** | The five assertions are in its brief; `pytest tests/phase5` after every change, not at the end |
| **A stream edits a graded test to make it pass** | **Critical** | Low | Prohibited three times in the launch prompt; every gate re-runs all 210 independently |
| **SQLite write contention** | Medium | **Medium** | See §2.1 |
| **OneDrive corrupts the database or a worktree** | **High** | **Medium** | See §2.2 |
| **`create_all` behaves differently on the populated DB than on a fresh one** | High | Low | Gate 0 tests against a **copy of the real `inventory.db`**, not a fresh file |
| **A WS-0 signature turns out wrong** | High | Medium | Wave 0 is solo and gated; file 15 is read end-to-end against files 08–12 before Wave 1 |
| **`App.jsx` decomposition takes longer than expected** | Medium | **High** | It is 1136 lines with `useState` tab switching. WS-6 ships routing + `screens/` skeleton first so four streams unblock before primitives are finished |
| **An idle instance "helps" in another stream's files** | High | **Medium** | Explicit prohibition + `git diff --name-only` in every DoD. Idle is cheaper than an unowned edit |
| **17 branches do not merge cleanly** | Medium | Low | Zero file overlap by construction. This is the payoff of the ownership rule |
| **The interrupt does not actually survive a restart** | High | Low | Tested with a genuine process restart. If it fails, LangGraph is unearned and should be removed |

### 2.1 SQLite write contention — the one that will actually happen

Three writers can be live at once: the APScheduler tick (WS-10), a manual pipeline trigger (WS-8), and the UI's approval mutations (WS-4). SQLite serialises writers and raises `database is locked` after a timeout.

| Measure | Why |
|---|---|
| **LangGraph checkpointer in a separate file** — `checkpoints.db`, not `inventory.db` | The checkpointer writes on every node transition. Sharing one file with business writes multiplies contention for no benefit |
| WAL mode on both | Readers stop blocking writers. Materially reduces the failure |
| Short transactions in WS-9 | The executor holds the only long write path |
| Scheduler **off by default**, env-gated | A scheduler firing during another stream's test run presents as flakiness in an unrelated stream |
| `next_id` is concurrency-safe (AD-15) | WS-3 and WS-9 both call it; a scheduled run overlapping a manual one is normal, not an edge case |

This risk is highest during the demo, because that is the only time the scheduler, the UI and a manual trigger are all live at once. It is the strongest argument for the WAL + separate-checkpoint-file pair being set up in Wave 0 rather than patched at Gate 3.

### 2.2 The repository lives inside OneDrive

> **Verified from the environment:** the working directory is `C:\Users\2mrmi\OneDrive\Documents\github-clone\Agentic-AI-Readiness-Program`.

OneDrive continuously syncs this tree. Three concrete problems:

| Problem | Effect |
|---|---|
| OneDrive holds a file handle while uploading | SQLite writes fail intermittently with permission or lock errors that look like application bugs |
| `node_modules/` and `venv/` sync | Thousands of small files; sync churn and real slowdowns. Four UI worktrees make it four times worse |
| Sibling worktrees inherit the problem | `git worktree add ../steward-ws03` puts the worktree inside `OneDrive\Documents\github-clone\` |

**Mitigation: create every worktree outside the OneDrive tree.**

```bash
git worktree add C:/steward/ws03 -b ws03-signals
```

`*.db`, `chroma_db/`, `node_modules/` and `venv/` are all gitignored, so the sync gains nothing by carrying them and loses a class of intermittent failures by not. This is cheap to do on day one and expensive to diagnose on day three — an intermittent SQLite lock error inside an agent's test run is close to indistinguishable from a concurrency bug in the code being tested.

---

## 3. Data risks

| Risk | Effect | Mitigation |
|---|---|---|
| **The backfill collapses onto one date** | Repeats the existing defect. Every demand number becomes uncomputable | Explicit `recorded_at=clock.now() - timedelta(days=n)` on every row. **Never the column default** |
| Synthetic demand rates get presented as measurements | Fabrication | File 13 §3.1 states all five rates openly. A fixture designed to hit a branch is normal engineering; a fixture presented as a measurement is not |
| Seeded demand contradicts the manual's category descriptions | An observant reviewer finds an inconsistency | Three contradictions are already documented (file 13 §3.2) and turned into **findings** for the D3 audit rather than hidden |
| A T3 metric acquires a value | Destroys the credibility of every honest number beside it | CI check: every T3 metric returns `None` |
| The scenario reset is available in production | A time machine and a database wipe are not inventory features | `DEMO_MODE` env gate on every simulation endpoint |

The third row is a genuine design choice worth naming. The customer's manual §12 says Household demand is *"highly predictable"* and Personal Care has *"high sales velocity"* — and the data shows neither. Rather than quietly reconciling the seed to the manual, the contradiction becomes something the audit surfaces. **A system that checks the client's data against the client's own written assumptions is doing something more useful than arithmetic.**

---

## 4. Demo risks

| Risk | Mitigation | Fallback |
|---|---|---|
| LLM quota exhausted live | **This is a scripted moment.** Numbers are unchanged; the narrative disappears | Show it deliberately. It proves AD-2 better than asserting it (M-36) |
| Scenario does not produce the expected signals | `GET /api/simulation/scenarios/:key/verify` in pre-flight | Reset and reload; verify again before presenting |
| Timing overrun | The click path totals ~4:15 with a documented cut order (file 13 §9.4) | Cut in the stated order, not improvised |
| Interrupt does not resume | Tested at Gate 2 with a real restart | Pre-flight check 4 |
| A number on screen looks wrong | Every number has an evidence block with its arithmetic and citation | Open the evidence block. **Being able to answer "where did that come from" is the demo** |
| Audience asks for ROI | Answered by design | *"Here is the formula, here is the one input we don't have, and here is what we'd need from you."* That is the Impact screen's closing section |

The pattern across this table: **every failure mode degrades into something worth showing.** That is not luck; it is the result of designing the demo as a fixture with verification rather than as a script.

---

## 5. Honest unknowns

Things I do not know and cannot determine from the code, the data, or the brief. Listed because a plan that presents its unknowns as settled is the failure this package is built to avoid.

| Unknown | Why it matters | How it gets resolved |
|---|---|---|
| **Whether WS-8's rewrite can keep all 40 Phase 5 tests green** | Two of them inspect source. I have read the assertions but not attempted the rewrite | Only by attempting it. First thing WS-8 does |
| **How long this actually takes** | 18 workstreams, 5 waves. **I have deliberately given no hour estimates** — I have no calibration for how fast these instances complete streams of this shape | Measured after Wave 1. Wave 1's actual duration is the only useful predictor of Waves 2–3 |
| **Whether seven parallel instances converge** | The contract-first partition is sound in principle and I have not run it | Gate 1. If stub replacement turns into signature negotiation, Wave 0 was rushed — worth recording either way |
| **Whether Gemini's output is stable enough for the narrative node** | Prose only, no numbers, so a bad generation is cosmetic | Wave 2. Low stakes by construction |
| **Whether the audience rewards honesty over polish** | See §5.1 |  Only by presenting |
| Whether `reserved` should be wired up | It is `0` for all five products. C17 may be solving a problem nobody has | Deferred to OPTIONAL, correctly |

### 5.1 The product bet, stated plainly

This build wagers that a technical audience rewards **verifiable honesty** over **impressive-sounding breadth**. The Impact screen's *"WHAT WE CANNOT MEASURE YET"* section, the refusal demo, and *"five fabricated fields → zero"* are all bets on that.

If the audience instead rewards flash, a competitor who ships ML forecasting with a confident chart and a fabricated 40%-improvement figure wins the room.

I think the bet is correct — an unfalsifiable number is worth less than nothing to anyone who has evaluated a POC before, and ~100 people building from the same baseline means differentiation has to come from somewhere other than feature count. But it is a bet, it is the central strategic choice in this package, and it should be made knowingly rather than discovered afterwards.

The hedge, such as it is: **the honest version is also the more capable version.** Deterministic arithmetic with a refusal path is not a smaller product than ML forecasting on 13 rows — it is the one that works.

---

## 6. What this system will never do

Non-goals, stated so they cannot be mistaken for gaps.

| Never | Why |
|---|---|
| Order without authority | Every action passes the policy engine. Value, evidence, supplier and config changes all have explicit authority rules |
| Present a number it cannot derive | `value is None` when sufficiency is insufficient. T3 metrics show formula and missing input, never a figure |
| Let an agent approve its own decision | AD-12. Least-privilege agent identity, enforced at the API |
| Act on an approval whose preconditions have changed | Seven preconditions re-checked at execution, not at proposal |
| Hide that its data is synthetic | `data_disclosure` is a stored column, not a UI convention. A figure cannot be exported stripped of its caveat |
| Scale to multiple stores | Single-store schema. An explicit non-goal, not an omission |
| Negotiate with, or message, a supplier | Outward-facing actions whose failure mode is a commercial relationship |
| Set prices | Inventory and procurement. No elasticity data, no mandate |
| Silently overwrite a human's decision | A counter-proposal records the system's objection **and** that the human overrode it |

The last row is the one that most distinguishes this from a system with an approval button. **A ledger in which the system never disagreed is a ledger of a system nobody was governing** — so the disagreement is recorded, including the times the system loses.

---

## 7. The single biggest risk

Not SQLite, not the rate limit, not the schedule.

> **A workstream edits a graded test to make its own change pass.**

It is silent. It looks like progress. It applies cleanly. And it destroys the one claim that separates this build from every other POC in the room: that a substantial redesign kept all 210 inherited tests green.

Everything else in this package is recoverable. A schedule slip cuts Wave 3, which costs nothing the demo needs. A signature error costs an integration pass. A locked database costs a retry. **An edited graded test costs the entire credibility of the result**, and nobody would notice until someone else ran the suite.

Which is why the prohibition appears three times in the launch prompt, why every wave gate re-runs all five phases independently rather than trusting the streams' reports, and why the rule is stated as a design principle rather than a policy: *a stream that cannot make its change without editing a graded test has found a design error, not a test error.*

---

**Next:** [README.md](README.md) is the index to this package.
