# Execution Runbook

> **What this is:** the exact order in which to open new chats, which tool to send each prompt to, and the gate that must pass before the next wave opens. Copy prompts from here into fresh sessions.
>
> **Ground rules that never change:**
> - One **git worktree per stream**, created **outside OneDrive** (at `C:/steward/wsNN`). See [20](20-RISKS-AND-CONSTRAINTS.md) §2.2.
> - **One owner per file.** The table in [14-PARALLEL-WORKSTREAMS.md](14-PARALLEL-WORKSTREAMS.md) is the source of truth.
> - The **210 graded tests are read-only.** An agent that edits one has found a design error, not a test error.
> - Each stream = **one fresh session opened *in its worktree directory*** so the agent's working directory is the worktree, not the primary repo.
> - **Only the integration operator (you + Claude Code) ever commits to `main` or wires `main.py`.** Streams stay on their branch.

---

## Tool split (decided)

| Tool | Streams | Role |
|---|---|---|
| **Claude Code** | WS-0, WS-2, WS-8, WS-9 · **every gate** · **final integration** | Silent-failure, gameable-test, and whole-system-context work |
| **Antigravity** | WS-1, 3, 4, 5, 6, 7 · WS-10, 11, 12, 17 · WS-13, 14, 15, 16 | Bulk parallel, well-specified, mechanically verifiable |

---

## STEP 0 — One-time setup (you, once, in the primary repo)

The planning package is currently **untracked**. `git worktree` only checks out **committed** files, so if you don't commit it, none of your worktrees will contain `docs/implementation/` and every agent will be blind. Commit it first.

```bash
cd "/c/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program"
git add docs/implementation/ && git commit -m "docs: Steward planning package + runbook"
```

Then confirm the regression floor is green **before anyone touches anything** — this is the baseline every worktree inherits:

```bash
pytest tests/phase1 tests/phase2 tests/phase3 tests/phase4 tests/phase5 -q
```

Expect **210 passed**. If it is not 210, stop and fix that first — otherwise no stream can tell an inherited breakage from one it caused.

---

## The master launch prompt (reused for every stream)

This is the body you paste into each stream's fresh session. Fill the `{{...}}` from the **Stream table** below. It is deliberately short — the agent gets its detail by reading the docs.

```
You are implementing workstream {{WS-N}} of the Steward build. Your working
directory is this worktree.

BOOTSTRAP FIRST (before reading any spec):
  cp "/c/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/.env" .env
  python -m src.backend.seed_demo_data
  python -m src.rag.ingest
  pytest tests/phase1 tests/phase2 tests/phase3 tests/phase4 tests/phase5 -q
All five phases must be GREEN before you change anything. If they are not,
STOP and report — you are in a broken worktree and nothing you do is valid.

READ IN THIS ORDER:
  1. docs/implementation/15-SHARED-CONTRACTS.md      <- FROZEN. Never edit.
  2. docs/implementation/14-PARALLEL-WORKSTREAMS.md, section {{WS-N}}
     (this lists the exact files you own, consume, and publish)
  3. The spec files for your stream (see docs/implementation/README.md doc map)

YOU OWN ONLY the files listed for {{WS-N}} in section 14. You MAY NOT modify
anything else. In particular:
  - tests/phase1..phase5/       GRADED. Read-only. If your change breaks one,
                                you have a DESIGN error, not a test error.
  - src/backend/main.py         Integration only. Publish a module-level `router`
                                and STOP; do not wire it in.
  - src/backend/models.py       Frozen. New tables go in new modules.
  - requirements.txt, package.json   WS-0 already pre-declared what you need.
  - src/agents/executor, src/rag/*, src/mcp_server/*   Frozen.

HARD RULES:
  - clock.now() / clock.today() only. No datetime.now(), date.today(), time.time().
  - No SQLAlchemy Enum on any new column. String only.
  - No server_default=func.now() on any new table. Pass explicit timestamps.
  - Any Computed/MetricValue with sufficiency insufficient/none returns value=None,
    never 0.0.
  - Server port {{PORT}} (and Vite {{VITE}}) — do not use 8000/3000/8501.

DEFINITION OF DONE:
  1. Your own tests pass.
  2. All five graded phases still pass (run the pytest line above).
  3. `git diff --name-only` lists ONLY files you own. Verify this literally.
  4. You have NOT committed to main, NOT pushed, NOT merged another branch.

IF YOU NEED SOMETHING YOU DO NOT OWN:
  Do not change it. Append the request to
  docs/implementation/integration-requests/{{WS-N}}.md and continue.

Report when done: files created, files modified, tests added, graded status,
and any integration requests you filed.
```

**For Antigravity:** paste the same body into a new agent task, opened on that stream's worktree folder. The rules are tool-agnostic.

---

## Stream table (fill-ins for the template)

| Stream | Tool | Worktree | Branch | Port | Vite |
|---|---|---|---|---|---|
| WS-0 Foundations | **Claude** | `C:/steward/ws00` | `ws00-foundations` | 8000 | — |
| WS-1 Analytics | Antigravity | `C:/steward/ws01` | `ws01-analytics` | 8001 | — |
| WS-2 Simulation | **Claude** | `C:/steward/ws02` | `ws02-simulation` | 8002 | — |
| WS-3 Signals | Antigravity | `C:/steward/ws03` | `ws03-signals` | 8003 | — |
| WS-4 Governance | Antigravity | `C:/steward/ws04` | `ws04-governance` | 8004 | — |
| WS-5 Policy | Antigravity | `C:/steward/ws05` | `ws05-policy` | 8005 | — |
| WS-6 UI Foundation | Antigravity | `C:/steward/ws06` | `ws06-ui-foundation` | 8010 | 3010 |
| WS-7 Supplier | Antigravity | `C:/steward/ws07` | `ws07-supplier` | 8006 | — |
| WS-8 Autonomy Loop | **Claude** | `C:/steward/ws08` | `ws08-autonomy` | 8011 | — |
| WS-9 Executor | **Claude** | `C:/steward/ws09` | `ws09-executor` | 8012 | — |
| WS-10 Runtime | Antigravity | `C:/steward/ws10` | `ws10-runtime` | 8013 | — |
| WS-11 UI Tower | Antigravity | `C:/steward/ws11` | `ws11-ui-tower` | 8020 | 3020 |
| WS-12 UI Approvals | Antigravity | `C:/steward/ws12` | `ws12-ui-approvals` | 8021 | 3021 |
| WS-17 Metrics API | Antigravity | `C:/steward/ws17` | `ws17-metrics` | 8014 | — |
| WS-13 UI Impact | Antigravity | `C:/steward/ws13` | `ws13-ui-impact` | 8022 | 3022 |
| WS-14 Co-pilot | Antigravity | `C:/steward/ws14` | `ws14-copilot` | 8030 | 3030 |
| WS-15 Root Cause | Antigravity | `C:/steward/ws15` | `ws15-root-cause` | 8015 | — |
| WS-16 Shadow | Antigravity | `C:/steward/ws16` | `ws16-shadow` | 8016 | — |

---

# THE SEQUENCE

---

## WAVE 0 — Foundations (Claude Code, solo)

Everything depends on this being right. Do not open Wave 1 until Gate 0 passes.

**0a. You — create the worktree:**
```bash
cd "/c/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program"
git worktree add C:/steward/ws00 -b ws00-foundations
```

**0b. Send to Claude Code** (new session opened in `C:/steward/ws00`): the master prompt with `{{WS-N}}=WS-0`, `{{PORT}}=8000`, no Vite — **plus this addendum:**

```
ADDITIONAL (WS-0 only):
- You are the only instance running. Seventeen streams build against what you
  publish. A signature you change later breaks six of them. Publish exactly what
  15-SHARED-CONTRACTS.md specifies — no more.
- Your ONE sanctioned edit to a shared file: add
  `from src.backend import models_registry  # noqa: F401`
  to the import block of src/backend/main.py. Nothing else in that file.
- Verify on a COPY of the real database, not just a fresh one:
    cp "/c/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program/inventory.db" ./inventory.db
    python -c "from src.backend.main import app"
    sqlite3 inventory.db ".tables"
  All 8 new tables must appear AND the 8 existing tables must be unchanged.
```

**0c. Wait** until Claude Code reports done (its own tests green, 210 green, diff clean).

**0d. GATE 0 — send to a fresh Claude Code session in the PRIMARY repo:**

```
You are the integration operator. Verify and land Wave 0.
1. Merge branch ws00-foundations into main. Resolve nothing creatively — if it
   does not merge cleanly, stop and report.
2. cp a copy of the real inventory.db in and confirm additive creation:
   8 new tables appear, 8 existing tables unchanged.
3. Run: pytest tests/phase1..phase5 -q  -> must be 210 passed.
4. grep -rn "datetime.now()\|date.today()\|time.time()" src/ --include=*.py  -> nothing.
5. grep -rn "Enum(" src/backend/models_*.py  -> nothing.
6. Read 15-SHARED-CONTRACTS.md end to end against files 08-12. Confirm every
   signature Wave 1 will stub actually exists as published.
Report PASS/FAIL per check. On PASS, commit main. Do NOT push.
```

**Gate 0 passes when:** all six checks green and WS-0 is on `main`. Only now create Wave 1 worktrees — they branch from this updated `main`.

---

## WAVE 1 — Numbers become real (7 parallel)

**1a. You — create seven worktrees** (each branches from the WS-0 `main`):
```bash
cd "/c/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program"
git worktree add C:/steward/ws01 -b ws01-analytics
git worktree add C:/steward/ws02 -b ws02-simulation
git worktree add C:/steward/ws03 -b ws03-signals
git worktree add C:/steward/ws04 -b ws04-governance
git worktree add C:/steward/ws05 -b ws05-policy
git worktree add C:/steward/ws06 -b ws06-ui-foundation
git worktree add C:/steward/ws07 -b ws07-supplier
```

**1b. Fire all seven prompts** (order doesn't matter — they're independent):

| Send to | Stream | Prompt |
|---|---|---|
| **Claude Code** (in `C:/steward/ws02`) | WS-2 | master, `WS-2` / port 8002 + addendum below |
| Antigravity | WS-1 | master, `WS-1` / port 8001 + addendum below |
| Antigravity | WS-3 | master, `WS-3` / port 8003 |
| Antigravity | WS-4 | master, `WS-4` / port 8004 |
| Antigravity | WS-5 | master, `WS-5` / port 8005 |
| Antigravity | WS-6 | master, `WS-6` / port 8010 / Vite 3010 + addendum below |
| Antigravity | WS-7 | master, `WS-7` / port 8006 |

**WS-2 addendum (Claude Code):**
```
ADDITIONAL (WS-2): Every backfilled movement MUST carry an explicit timestamp:
  recorded_at = clock.now() - timedelta(days=n)   # NEVER the column default
Omit it and 90 days of history collapse onto today, silently invalidating every
downstream number. Target: >=90 distinct recorded_at dates, and >=3 of 5 products
reach `sufficient` demand once WS-1 lands. Also define the 4 demo_scenarios rows
with their expected_signals.
```

**WS-1 addendum (Antigravity):**
```
ADDITIONAL (WS-1): Write these two tests FIRST, before any implementation:
  assert (10*5)+(10*2) == 70    # manual §3 line 35
  assert (5*7)+(5*14) == 105    # manual §9 line 102
Make derive_reorder_point reproduce them. You will find NO product has enough
history yet — return `insufficient`, never 0.0. Write NOTHING to the database;
WS-1 is pure functions.
```

**WS-6 addendum (Antigravity):**
```
ADDITIONAL (WS-6): Ship routing + the screens/ skeleton FIRST (all 17 routes must
render, even as stubs), THEN the shared primitives. Four Wave-2 UI streams are
blocked on your skeleton, so unblock them before polishing.
```

**1c. Wait** until all seven report done.

**1d. GATE 1 — send to a fresh Claude Code session in the PRIMARY repo:**
```
You are the integration operator. Close Wave 1.
1. Merge ws01..ws07 into main, ONE at a time, running the 210 graded tests after
   each merge. A merge that breaks a graded phase is REVERTED, not fixed here —
   report which stream and stop.
2. Wire the routers those streams published into main.py (signals, policies,
   suppliers, etc.) in one pass.
3. Process any docs/implementation/integration-requests/*.md.
4. Verify: 210 passed; WS-6 App.jsx decomposed and all 17 routes render; WS-2
   backfill >=90 distinct dates; WS-1+WS-2 together return `sufficient` for >=3
   of 5 products.
Report PASS/FAIL. On PASS commit main. Do NOT push.
```

**Gate 1 passes when:** 210 green on merged main, the demand gate (≥3/5 `sufficient`) holds, and no integration-request is unresolved.

---

## WAVE 2 — The loop closes, the product exists (6 parallel)

**2a. You — create six worktrees** (branch from Wave-1 `main`):
```bash
cd "/c/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program"
git worktree add C:/steward/ws08 -b ws08-autonomy
git worktree add C:/steward/ws09 -b ws09-executor
git worktree add C:/steward/ws10 -b ws10-runtime
git worktree add C:/steward/ws11 -b ws11-ui-tower
git worktree add C:/steward/ws12 -b ws12-ui-approvals
git worktree add C:/steward/ws17 -b ws17-metrics
```

**2b. Fire six prompts:**

| Send to | Stream | Prompt |
|---|---|---|
| **Claude Code** (`C:/steward/ws08`) | WS-8 | master, `WS-8` / port 8011 + addendum below |
| **Claude Code** (`C:/steward/ws09`) | WS-9 | master, `WS-9` / port 8012 + addendum below |
| Antigravity | WS-10 | master, `WS-10` / port 8013 |
| Antigravity | WS-11 | master, `WS-11` / port 8020 / Vite 3020 |
| Antigravity | WS-12 | master, `WS-12` / port 8021 / Vite 3021 |
| Antigravity | WS-17 | master, `WS-17` / port 8014 |

> Start **WS-8 first** — it is the highest-risk stream and has no fallback. Give it your attention before the others.

**WS-8 addendum (Claude Code):**
```
ADDITIONAL (WS-8): Highest-risk stream. You rewrite three files graded tests
inspect BY SOURCE. Run `pytest tests/phase5 -q` after EVERY change, not at the end.
The five constraining assertions are in 17-CLAUDE-CODE-EXECUTION-PLAN.md §5.3.
The entry-point test is source-inspection and technically gameable. DO NOT game it —
demand_forecaster is genuinely first because deterministic computation precedes any
LLM call. Preserve the agents.py:389-406 fabrication evidence verbatim (as a comment
if the code around it changes). Test the durable interrupt across a REAL process
restart, not a mock.
```

**WS-9 addendum (Claude Code):**
```
ADDITIONAL (WS-9): You own the ONLY write path. Fix the three inventory_service.py
defects (:133 status guard, :137 date.today()->clock, :140-141 partial receipt) with
regression tests. Enforce: idempotency key blocks a replay; duplicate-order guard
blocks a second open PO for one SKU; sum(movements)==quantity_on_hand after every
write; the 7 preconditions re-checked at execution time, not at proposal. Decide
nothing — you execute a decision someone else authorised.
```

**2c. Wait** until all six report done.

**2d. GATE 2 — send to a fresh Claude Code session in the PRIMARY repo:**
```
You are the integration operator. Close Wave 2.
1. Merge ws08, ws09, ws10, ws11, ws12, ws17 into main one at a time; 210 graded
   tests after each; revert-don't-fix on breakage.
2. Wire remaining routers (agent, impact) and register the background runtime in
   lifespan after create_all.
3. Replace stubs with real imports (each should be a ~2-line diff).
4. Prove the whole loop end to end:
   a signal is raised with no human input -> a decision is created with a policy
   citation -> policy escalates -> an approval is created -> a manager approves ->
   the executor re-checks preconditions -> a PO is raised -> the decision appears
   in the ledger with arithmetic, citation, and actor.
5. D1 and D2 verify via GET /api/simulation/scenarios/:key/verify.
6. The interrupt survives an ACTUAL process restart between proposal and approval.
7. Kill switch halts mid-pipeline; sum(movements)==quantity_on_hand holds; 210 green.
Report PASS/FAIL per check. On PASS commit main. Do NOT push.
```

**Gate 2 passes when:** the end-to-end loop assertion holds, D1+D2 verify, the restart-durable interrupt is proven, and 210 are green. **This is a complete, demoable product** — if you are short on time, you may stop here.

---

## WAVE 3 — Depth (4 parallel, droppable)

Nothing here is required for the demo. Build it only if Wave 2 landed with time to spare.

**3a. You — create four worktrees:**
```bash
cd "/c/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program"
git worktree add C:/steward/ws13 -b ws13-ui-impact
git worktree add C:/steward/ws14 -b ws14-copilot
git worktree add C:/steward/ws15 -b ws15-root-cause
git worktree add C:/steward/ws16 -b ws16-shadow
```

**3b. Fire four prompts — all Antigravity:** WS-13 (8022/3022), WS-14 (8030/3030), WS-15 (8015), WS-16 (8016), each the master prompt.

**3c. Wait**, then **GATE 3 — send to fresh Claude Code in PRIMARY repo:**
```
You are the integration operator. Close Wave 3.
1. Merge ws13..ws16 into main one at a time; 210 graded tests after each;
   revert-don't-fix.
2. Wire their routers/screens.
Report PASS/FAIL. On PASS commit main.
```

---

## FINAL — Integration sign-off (Claude Code, PRIMARY repo)

Run whether you stopped at Wave 2 or completed Wave 3.

```
You are the integration operator. Final sign-off on main.
1. pytest tests/phase1..phase5 -q  -> 210 passed.
2. All built demo scenarios verify (4/4 if Wave 3 done, 2/2 D1+D2 if you stopped
   at Wave 2) via the scenario verify endpoint.
3. The 8-step demo click path completes with NO manual database edit.
4. Every T3 metric returns null with a named missing_input (0 T3 values shown).
5. LLM-OFF EQUIVALENCE: run the pipeline with GOOGLE_API_KEY="" and again with it
   set. Every number must be identical; only the narrative disappears.
6. CI invariants: clock grep clean, Enum grep clean, func.now() grep clean.
Report the four done-numbers: graded 210/210, scenarios N/N, LLM-off deltas = 0,
T3 values shown = 0. Do NOT push unless I tell you to.
```

**Done when:** `210/210` · scenarios `N/N` · LLM-off deltas `0` · T3 values shown `0`.

---

## Cleanup (you, after sign-off)

```bash
cd "/c/Users/2mrmi/OneDrive/Documents/github-clone/Agentic-AI-Readiness-Program"
git worktree list          # see them all
git worktree remove C:/steward/ws01   # repeat per stream once merged
```

---

## If something goes wrong

| Symptom | Do this |
|---|---|
| An agent says a graded test "needs" changing | **No.** It has a design error. Have it file an integration-request and route the real fix through the owning stream. |
| A gate merge breaks a graded phase | Claude Code **reverts that one merge** (not the others), names the stream, and that stream's session fixes it on its own branch. |
| A stream is late and blocking a gate | See [16-DEPENDENCY-GRAPH.md](16-DEPENDENCY-GRAPH.md) §7 — every stream has a named mitigation. WS-8 has none; WS-10 is the cheapest severe one. |
| `git diff` in a worktree shows files the stream doesn't own | Stop that stream. Something leaked. Revert the unowned files before continuing. |
| An idle agent offers to "help" in another stream | Decline. An idle instance is cheaper than an unowned edit ([14](14-PARALLEL-WORKSTREAMS.md) §9). |
| Intermittent SQLite "database is locked" | You created a worktree inside OneDrive. Move it to `C:/steward/...`. |

---

## At-a-glance

```
STEP 0  commit docs + confirm 210 green            (you)
WAVE 0  WS-0                                        (Claude)      -> GATE 0 -> main
WAVE 1  WS-1 3 4 5 6 7 (Antigravity) + WS-2 (Claude)              -> GATE 1 -> main
WAVE 2  WS-10 11 12 17 (Antigravity) + WS-8 9 (Claude)            -> GATE 2 -> main  [STOP-OK]
WAVE 3  WS-13 14 15 16 (Antigravity)                             -> GATE 3 -> main
FINAL   integration sign-off                        (Claude)     -> 210/210 · N/N · 0 · 0
```

Every gate is run by Claude Code, re-runs all 210 tests independently, and never trusts a stream's self-report. That single discipline is what protects the one claim that separates this build from every other POC: a substantial redesign that kept all 210 inherited tests green.
