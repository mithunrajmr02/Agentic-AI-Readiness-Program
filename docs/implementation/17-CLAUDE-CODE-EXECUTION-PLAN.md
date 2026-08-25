# 17 — Claude Code Execution Plan

> **Status:** Proposal. Nothing here is approved. No code has been written.
> **Purpose:** The operational plan for running this build across multiple Claude Code instances — isolation, bootstrap, launch prompts, wave gates, and integration.

---

## 1. The problem file ownership does not solve

[14-PARALLEL-WORKSTREAMS.md](14-PARALLEL-WORKSTREAMS.md) guarantees no two streams write the same file. That prevents *edit* collisions. It does not prevent **filesystem** collisions, and those are worse because they present as impossible bugs.

Two Claude Code instances in one working directory share:

| Shared resource | Failure it produces |
|---|---|
| `inventory.db` | WS-2 resets the database mid-way through WS-9's test run. WS-9 sees phantom failures |
| `chroma_db/` | Two instances re-ingest concurrently; the collection is corrupt for both |
| `.pytest_cache/`, `__pycache__/` | Stale bytecode from another stream's half-written module |
| `node_modules/` | Two `npm install` runs racing |
| Ports 8000 / 3000 / 8501 | Second instance cannot start a server; concludes the code is broken |
| `git` index and `HEAD` | One instance's `git status` shows another's work as its own |

The last one is the dangerous one. An instance whose `git diff --name-only` shows another stream's files will either try to reconcile them or report a violation of its own ownership rule. Both waste a full context window.

**Resolution: one git worktree per workstream. Non-negotiable for any wave running more than one instance.**

```bash
git worktree add ../steward-ws03 -b ws03-signals
```

Each worktree is a full checkout with its own database, its own caches, its own `node_modules`, and its own index. With zero file overlap between streams, merging seventeen branches is close to trivial — **that is the payoff of the ownership rule, and worktrees are what let you collect it.**

### 1.1 Port allocation

Any stream running a server needs its own ports, or the second instance concludes the backend is broken.

| Stream | Backend | Vite | Streamlit |
|---|---|---|---|
| WS-0 | 8000 | — | — |
| WS-1 … WS-5, WS-7 | 8001–8006 | — | — |
| WS-6 | 8010 | 3010 | — |
| WS-8, 9, 10, 17 | 8011–8014 | — | — |
| WS-11, 12, 13 | 8020–8022 | 3020–3022 | — |
| WS-14 | 8030 | 3030 | 8531 |
| Integration | 8000 | 3000 | 8501 |

Integration keeps the canonical ports so `.claude/launch.json` (verified: `react-frontend` on 3000, `streamlit-chat` on 8501) needs no change.

---

## 2. Bootstrap — what every fresh worktree is missing

**Verified from `.gitignore`.** These are not tracked, so a new worktree has none of them:

| Missing | Consequence | Fix |
|---|---|---|
| `.env` | Every LLM and embedding call fails | `cp ../Agentic-AI-Readiness-Program/.env .env` |
| `inventory.db` (`*.db` ignored) | **No database at all.** Every query errors | Run the seeder |
| `chroma_db/` | RAG returns nothing | Run the ingest |
| `node_modules/` | `npm run dev` fails | `npm install` |
| `venv/` | Wrong interpreter | Reuse the primary venv, or create one |

Every instance runs this once, first, before reading any spec:

```bash
cp ../Agentic-AI-Readiness-Program/.env .env
python -m src.backend.seed_demo_data
python -m src.rag.ingest
pytest tests/phase1 tests/phase2 tests/phase3 tests/phase4 tests/phase5 -q
```

**The `pytest` line is the important one.** It establishes that all five graded phases were green *before* the stream touched anything. Without that baseline, a stream that later sees a failure cannot tell whether it caused it — and will spend a long time finding out. This is the single cheapest instruction in the whole plan.

`.env.example` is tracked and documents every variable the code actually reads, including the fallback behaviour when a variable is absent. An instance without a Gemini key can still complete every deterministic stream — WS-1, WS-2, WS-3, WS-4, WS-5, WS-9, WS-17 need no LLM at all, which is itself a consequence of AD-2.

---

## 3. Branch and merge strategy

| | |
|---|---|
| Branch naming | `ws00-foundations`, `ws01-analytics`, … `ws17-metrics` |
| Base | `main` for Wave 1; the previous wave's integration commit for Waves 2–3 |
| Merge direction | Always stream → integration. **Never stream → stream** |
| Who merges | Integration only, one stream at a time, tests green between each |
| Rebasing | Streams do not rebase mid-wave. Integration handles divergence |

**A stream never merges another stream's branch**, even to "get the latest contracts". Contracts are frozen in Wave 0 and land on `main` before Wave 1 starts, so there is nothing to pull. A stream that pulls a sibling branch has imported unreviewed code into its own test results and no longer knows what it verified.

### 3.1 Wave 0 lands on `main` before Wave 1 opens

This is the one place a serial step is worth its cost. WS-0's output — `src/core/`, the four model modules, `models_registry.py`, the one `main.py` import line, and the pinned `requirements.txt` / `package.json` — must be on `main` before any Wave 1 worktree is created. Otherwise seven instances each carry their own copy of the contracts and diverge.

---

## 4. The launch prompt

Each instance is started with exactly this, its `{{WS-N}}` filled in. Nothing else.

```
You are implementing workstream {{WS-N}} of the Steward build.

BOOTSTRAP FIRST (before reading any spec):
  cp ../Agentic-AI-Readiness-Program/.env .env
  python -m src.backend.seed_demo_data
  python -m src.rag.ingest
  pytest tests/phase1 tests/phase2 tests/phase3 tests/phase4 tests/phase5 -q
All five phases must be GREEN before you change anything. If they are not,
STOP and report — you are in a broken worktree and nothing you do is valid.

READ IN THIS ORDER:
  1. docs/implementation/15-SHARED-CONTRACTS.md   <- FROZEN. Never edit.
  2. docs/implementation/14-PARALLEL-WORKSTREAMS.md, section {{WS-N}}
  3. {{the 1-2 spec files for this stream}}

YOU OWN EXACTLY THESE FILES:
{{explicit list, including files you will create}}

YOU MAY NOT MODIFY ANYTHING ELSE. In particular:
  - tests/phase1..phase5/       GRADED. Read-only. If your change breaks one,
                                you have a design error, not a test error.
  - src/backend/main.py         Integration only.
  - src/backend/models.py       Frozen. New tables go in new modules.
  - requirements.txt, package.json   WS-0 pre-declared everything you need.
  - src/agents/agent.py, tools.py, src/rag/*, src/mcp_server/*   Frozen.

HARD RULES:
  - clock.now() only. No datetime.now(), date.today(), time.time().
  - No sqlalchemy Enum on any new column. String only.
  - No server_default=func.now() on any new table. Pass explicit timestamps.
  - Any Computed with sufficiency insufficient/none returns value=None, not 0.0.
  - Expose a module-level `router`. Do not wire it into main.py.

DEFINITION OF DONE:
  1. Your own tests pass.
  2. All five graded phases still pass.
  3. `git diff --name-only` lists ONLY files you own. Verify this literally.
  4. You have NOT committed to main. You have NOT pushed. You have NOT
     merged another workstream's branch.

IF YOU NEED SOMETHING YOU DO NOT OWN:
  Do not change it. Append the request to
  docs/implementation/integration-requests/{{WS-N}}.md
  and continue with the rest of your scope. An unowned edit in a parallel
  build is indistinguishable from a bug.

Report when done: files created, files modified, tests added, graded status,
and any integration requests you filed.
```

### 4.1 Why each unusual clause is there

| Clause | Prevents |
|---|---|
| Bootstrap **before** reading specs | An instance debugging a missing `.env` for twenty minutes with no idea the DB was never created |
| Baseline `pytest` | A stream inheriting a broken worktree and attributing the failure to its own work |
| "you have a design error, not a test error" | The most likely single act of damage: editing a graded test to make it pass |
| `git diff --name-only` **literally** | Silent scope creep. The check is mechanical for a reason |
| "have NOT merged another workstream's branch" | Untested sibling code contaminating a green test result |
| The integration-request path | An instance reasoning itself into a "small necessary fix" in a shared file |
| Report format | An integration pass that has to reverse-engineer what seventeen instances did |

---

## 5. Three worked launch prompts

The rest follow the same shape. These three are the ones with non-obvious framing.

### 5.1 WS-0 — Foundations

> Additional to the standard prompt:
>
> **You are the only instance running. Seventeen streams will build against what you publish. A signature you change later breaks six of them.**
>
> Your deliverable is plumbing and vocabulary. Not business logic. If you find yourself computing a reorder point, you have drifted into WS-1 and are blocking six streams while you do it.
>
> Publish exactly what [15-SHARED-CONTRACTS.md](15-SHARED-CONTRACTS.md) specifies — no more. Extra surface is extra promise.
>
> **Your one sanctioned edit to a shared file:** add `from src.backend import models_registry  # noqa: F401` to the import block of `src/backend/main.py`. Nothing else in that file. Without it, `create_all` at `main.py:84` never sees the eight new tables and every downstream stream's first query fails against a table that does not exist.
>
> **Verify on a copy of the real database, not just a fresh one:**
> ```bash
> cp ../Agentic-AI-Readiness-Program/inventory.db ./inventory.db
> python -c "from src.backend.main import app"
> sqlite3 inventory.db ".tables"
> ```
> All eight new tables must appear, and the eight existing ones must be unchanged. A fresh-database test proves nothing about additive creation — the whole AD-3 claim is that this works on a database that already has data.

### 5.2 WS-1 — Analytics

> Additional to the standard prompt:
>
> **Write these two tests first, before any implementation:**
> ```python
> assert (10 * 5) + (10 * 2) == 70     # manual §3 line 35
> assert (5 * 7) + (5 * 14) == 105     # manual §9 line 102
> ```
> Then make `derive_reorder_point` reproduce the first from those inputs. These are the client's own worked examples. If your arithmetic disagrees with them, every number in the product is wrong in the same direction, and nothing downstream can be trusted.
>
> **You will discover that no product has enough sales history to compute demand.** Four of five have zero sale movements; the fifth has three sales sharing one calendar day. That is correct and expected — the current `recorded_at` values were written by a column default, not by the seeder. WS-2 fixes it. **Do not work around it, and do not return `0.0` for it.** `insufficient` is the honest answer and it is the answer a downstream refusal depends on.
>
> **Write nothing to the database. Not one row.** WS-1 is pure functions. A single write makes you a stream that must be serialised against WS-4 and WS-9.

### 5.3 WS-8 — Autonomy Loop

> Additional to the standard prompt:
>
> **This is the highest-risk stream in the build.** You are rewriting three files that graded tests inspect by source.
>
> Run `pytest tests/phase5 -q` after **every** change, not at the end.
>
> The five assertions constraining you:
>
> | Test | Assertion |
> |---|---|
> | `test_routing.py:37-42` | Four node names appear in `inspect.getsource(build_inventory_graph)` |
> | `test_routing.py:45-48` | `"demand_forecaster"` present **and** an entry-point call |
> | `test_e2e.py:78` | `len(result["messages"]) >= 4` |
> | `test_e2e.py:102` | `analysis_status ∈ {complete, reorder_required, healthy, analyzing}` |
> | `test_e2e.py:167` | `analysis_status ∈ {reorder_required, complete}` |
>
> The entry-point test is source-inspection and technically gameable. **Do not game it.** `demand_forecaster` is genuinely first because deterministic computation genuinely precedes any LLM call. Satisfying a loose test dishonestly would undercut the one claim this entire product rests on.
>
> On the refusal path, the ≥4 messages are three real `demand_forecaster` steps plus the refusal. **No filler messages.**
>
> **Preserve `agents.py:389-406` verbatim, as a comment if the code around it goes.** That block records that in 3 of 3 runs the model invented `supplier_id: 101` and a ₹580.00 unit price against a real ₹600.00. It is the repository's own evidence for the architecture decision you are implementing, and it is the most persuasive artifact in the project.

---

## 6. Wave gates

Integration verifies each gate before the next wave's worktrees are created. **A wave does not open because the previous one's instances stopped talking; it opens because the gate passed.**

### Gate 0 → 1

```bash
cp <primary>/inventory.db ./inventory.db     # additive creation on real data
python -c "from src.backend.main import app"
sqlite3 inventory.db ".tables"               # 8 new + 8 existing
pytest tests/core tests/phase1 tests/phase2 tests/phase3 tests/phase4 tests/phase5 -q
grep -rn "datetime.now()\|date.today()\|time.time()" src/ --include=*.py
grep -rn "Enum(" src/backend/models_*.py
```

Last two must return nothing except the pre-authorised `inventory_service.py:137` (WS-9's to fix).

**Also required, and not automatable:** [15-SHARED-CONTRACTS.md](15-SHARED-CONTRACTS.md) is read end to end against files 08–12 for coherence. This is the last cheap moment to catch a wrong signature. After Wave 1 starts, changing one costs six streams.

### Gate 1 → 2

- Every Wave 1 stream's own tests green, in its own worktree
- All five graded phases green **on the merged result**
- WS-6: `App.jsx` decomposed; `screens/` exists with a settled convention; all 17 routes render
- WS-2: 90-day backfill produces ≥90 distinct `recorded_at` dates
- **WS-1 + WS-2 together: `compute_daily_demand` returns `sufficient` for at least three of five products.** This is the gate that matters — it is the moment the product stops having nothing to say
- No `integration-requests/` entry unresolved

### Gate 2 → 3

**One end-to-end assertion, and it is the product:**

> A signal is raised without human input → a decision is created with a policy citation → policy escalates it → an approval is created → a manager approves → the executor re-checks preconditions → a PO is raised → the decision appears in the ledger with its arithmetic, its citation, and its actor.

Plus:

- D1 and D2 verify via `GET /api/simulation/scenarios/:key/verify`
- The interrupt survives a **process restart** between proposal and approval. Not a mocked restart — an actual one. This is the sole architectural justification for LangGraph (AD-6) and the only way to know it is real
- Kill switch halts execution mid-pipeline
- `sum(movements) == quantity_on_hand` holds after every agent write
- All five graded phases green

### Gate 3 → Final

- All four scenarios verify
- The 8-step click path completes without a manual database edit
- Every T3 metric returns `null` with a named missing input
- LLM disabled: **every number is identical.** The narrative disappears; nothing else changes
- All five graded phases green

That LLM-off check is a correctness test disguised as a demo check. If any number moves when the model is removed, AD-2 is false and M-14 is unearned.

---

## 7. Integration procedure

One instance, serial, in the primary working directory.

```
1. Merge streams one at a time, in dependency order.
   Run the stream's own tests + all five graded phases after each merge.
   A merge that breaks a graded phase is reverted, not fixed in place.

2. Wire routers. One pass, all of them:
     main.py:12   import the new router modules
     main.py:177  app.include_router(...) for each
   This is the only file integration writes that no stream owns.

3. Register the runtime: register_runtime(app) in lifespan, after create_all.

4. Replace stubs with real imports. Each replacement is a two-line diff if the
   contract was honoured. If it is not, the producing stream is at fault and
   the fix belongs in that stream's file.

5. Process integration-requests/*.md. Each is a change to a file its requester
   did not own. Apply, or reject with a reason written back into the file.

6. Run the gate for the wave being closed.

7. Commit. Only integration commits to main.
```

Step 4 is the measurement of whether the contract discipline worked. If stub replacement is a series of two-line diffs, file 15 did its job. If it turns into signature negotiation, the lesson is that Wave 0 was rushed — worth recording either way.

**Step 1's revert rule matters.** An integration instance that starts fixing a stream's code has taken ownership of a file it does not understand, at the point of maximum context pressure. Revert, report, let the owner fix it.

---

## 8. What the human operator does

| When | Action |
|---|---|
| Before Wave 0 | Approve the plan. Nothing in this package is approved yet |
| Wave 0 | Read [15-SHARED-CONTRACTS.md](15-SHARED-CONTRACTS.md) yourself. It is the one document whose errors are expensive |
| Creating worktrees | `git worktree add ../steward-wsNN -b wsNN-name` per stream |
| Launching | Paste the §4 prompt with `{{WS-N}}` filled in. Resist adding context — extra context invites scope creep |
| During a wave | Answer questions. **Do not let an idle instance help elsewhere** |
| At each gate | Run the gate. Do not open the next wave on vibes |
| At Gate 2 | Decide whether to build Wave 3 at all. Wave 2 is a complete product |

The one judgment call is at Gate 2. Wave 0–2 delivers D1, D2, a real ledger, a durable interrupt, and the Impact screen. Wave 3 adds depth — shadow mode, the co-pilot, root-cause analysis — none of which the demo requires. **Deciding to stop is a legitimate outcome and the safest one**, which is exactly the property the last wave should have.

---

## 9. Honest assessment of this plan

| Property | Assessment |
|---|---|
| Peak parallelism | 7 instances (Wave 1) |
| Files with more than one owner | 0 |
| Serial bottlenecks | 2 — WS-0 entirely, WS-6's decomposition |
| Highest-risk stream | WS-8, and it has no mitigation |
| Most under-rated stream | WS-2. Looks like fixtures; gates everything credible |
| Cheapest severe failure | WS-10. Small stream; without it the Control Tower's core claim is false |
| Most likely actual failure | An instance edits a graded test to make it pass |

**The last row is the one to watch.** Every other risk here is scheduling — recoverable, visible, cheap to detect. Editing a graded test is silent, looks like progress, and destroys the only claim that distinguishes this build from every other POC in the room. It is why that prohibition appears three times in the launch prompt and why every wave gate re-runs all five phases rather than trusting the streams' own reports.

---

**Next:** [18-INTEGRATION-AND-TESTING.md](18-INTEGRATION-AND-TESTING.md) specifies what "verified" means for each layer, and which tests are worth writing at all.
