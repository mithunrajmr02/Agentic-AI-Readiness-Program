# Wave 2 Issues and Handoff

Date: 2026-08-28 (WS-10 section), updated same day with WS-9, updated same day with WS-8

## Completion

### WS-10 Background Runtime

- Implementation: **100% complete**.
- Focused tests: **100% complete (8 passed)**.
- Integration readiness: **approximately 70%** because APScheduler and the upstream WS-0/WS-8 contracts are not available in this worktree.
- Definition-of-done gates: **2 of 4 satisfied**. WS-10 tests pass and no forbidden implementation patterns were found. The all-phase green gate and literal repository-wide ownership gate are blocked by external issues listed below.

Implemented files:

- `src/runtime/__init__.py`
- `src/runtime/registry.py`
- `src/runtime/triggers.py`
- `src/runtime/scheduler.py`
- `src/runtime/bus_wiring.py`
- `tests/runtime/test_runtime.py`
- `docs/implementation/integration-requests/WS-10.md`

Implemented behavior:

- Environment-gated APScheduler runtime, disabled by default.
- Scheduled, event, manual, and backtest pipeline triggers.
- Thread-safe in-flight deduplication by product scope.
- Safe subscriptions for `signal.raised` and `clock.advanced`.
- Idempotent module-level `register_runtime(app)` publication.
- No wiring into `src/backend/main.py`; integration still owns that step.

### WS-9 Executor & Inventory Extensions

- Implementation: **100% complete** for everything WS-9 owns.
- Own tests: **100% complete (23 passed)** — `tests/execution/`.
- Graded suite (`tests/phase1..5`): **unchanged** — 225 passed / 2 skipped / 7 failed, same 7 pre-existing Gemini-embedding SSL failures in Phase 2 as the pre-WS-9 baseline. No regression.
- Integration readiness: **approximately 60%**, because `src/core/` (clock/ids/events/vocab/errors) and `models_governance.py` (`Decision`/`Approval`) — both WS-0 — are not present in this worktree. WS-9 built local, same-interface stand-ins (below) so its own tests are self-contained, but the real cross-stream wiring is not done.
- Definition-of-done gates: **3 of 4 satisfied**. Own tests pass, graded suite still green, `git diff` scoped to a dedicated branch contains only WS-9 files. Not satisfied: full cross-stream integration (blocked on WS-0's `src/core/` and `models_governance.py` not existing yet).
- Branch: `ws-9-executor-inventory-extensions` (pushed to `origin`, based on top of `ws-10-background-runtime`'s tip — **not** rebased onto `main`, so its history currently includes the WS-10 commit as an ancestor. Cherry-pick or rebase onto `main` before merging if a clean history is required).

Implemented files:

- `src/backend/services/inventory_service.py` (modified — the 3 defect fixes)
- `src/backend/services/po_service.py` (new)
- `src/backend/routers/receiving.py` (new, not wired into `main.py`)
- `src/execution/__init__.py`, `clock.py`, `idempotency.py`, `preconditions.py`, `executor.py` (new)
- `tests/execution/conftest.py` + 3 test files (new)
- `docs/implementation/integration-requests/WS-9.md`

Implemented behavior:

- `:133` defect: `receive_purchase_order`'s status guard changed from a blacklist (only `cancelled`) to an explicit whitelist (`draft`/`submitted`/`acknowledged`). `draft` was deliberately kept receivable — the graded `tests/phase1/test_api.py::test_receive_po_updates_stock` receives directly from a draft-status PO (the only PO-creation path hard-codes `draft`), so narrowing further would break a frozen graded test.
- `:137` defect: `date.today()` replaced with a clock abstraction; an optional explicit `received_at` supports backdated/seeded receipts.
- `:140-141` defect: real partial receipt via `item_receipts` (per-item delta quantity, not cumulative); a PO only advances to `received` once every line item is fully received. Added `is_partially_received()` derived predicate (no new `POStatus` member, matches the SQLite CHECK-constraint constraint).
- Duplicate-open-PO guard and idempotency-safe PO creation in `po_service.create_purchase_order`.
- The 7 preconditions (`src/execution/preconditions.py`) re-checked at execution time, not proposal time, including `need_already_resolved` for the "delivery arrived during the approval window" scenario.
- `execute_decision`/`ExecutionResult` (`src/execution/executor.py`) — decides nothing, only re-verifies and writes.

### WS-8 Autonomy Loop

- Implementation: **100% complete** for everything WS-8 owns.
- Own tests: **100% complete (9 passed)** — `tests/autonomy/`, including a real two-subprocess process-restart test for the durable interrupt (not mocked).
- Graded suite (`tests/phase1..5`): **unchanged** — 234 passed / 2 skipped / 7 failed (225 baseline + these 9 new autonomy tests), same 7 pre-existing Gemini-embedding SSL failures in Phase 2. No regression. Ran `pytest tests/phase5 -q` after every change, per the highest-risk-stream instruction.
- Integration readiness: **approximately 55%**, because `src/core/` (WS-0), WS-1 analytics, WS-5 policy, WS-7 sourcing, and WS-9's `execute_decision` are not present/consumable in this worktree. WS-8 built local, clearly-labelled stand-ins (below) so its own tests are self-contained; the real cross-stream wiring is not done.
- Definition-of-done gates: **3 of 4 satisfied**. Own tests pass, graded suite still green (no regression), `git diff --name-only` scoped to a dedicated branch contains only WS-8 files. Not satisfied: full cross-stream integration (blocked on WS-0/WS-1/WS-5/WS-7/WS-9 not existing yet).
- Branch: `ws-8-autonomy-loop` (pushed to `origin`, based on top of `ws-9-executor-inventory-extensions`'s tip, which is itself on top of `ws-10-background-runtime` — **not** rebased onto `main`, same caveat WS-9 recorded about its own base. Rebase or cherry-pick onto `main` before merging if a clean, single-workstream history is required).

Implemented files:

- `src/agents/multi_agent/graph.py` (modified — 8-node topology, `run_pipeline`, `resume_pipeline`)
- `src/agents/multi_agent/state.py` (modified — extended `InventoryAnalysisState`)
- `src/agents/multi_agent/__init__.py` (modified — exports)
- `src/agents/multi_agent/nodes/` (new — `investigator.py`, `policy_gate.py`, `executor.py`, `recorder.py`)
- `src/agents/multi_agent/checkpoint.py` (new — `DurableFileSaver`)
- `src/agents/multi_agent/ledger.py` (new — local append-only decision ledger)
- `src/agents/multi_agent/_clock.py` (new — local clock shim)
- `tests/autonomy/` (new — `test_topology.py`, `test_interrupt.py`, `test_restart.py`)
- `docs/implementation/integration-requests/WS-8.md`
- `.gitignore` (modified — ignore the new local runtime artifacts)

Implemented behavior:

- 8-node LangGraph topology (AD-7): the four original nodes (`demand_forecaster`, `reorder_agent`, `supplier_coordinator`, `inventory_auditor`) are wired in **unmodified** — `tests/phase5/test_agents.py`, `test_agent_data_flow.py`, `test_state.py`, and `test_coverage_boost.py` assert their exact LLM-call and prompt-content behaviour by source, so AD-7's own instruction ("extend the mandated four, do not replace them" — `00-EXECUTIVE-SUMMARY.md`) was followed over `08-AGENTIC-WORKFLOWS.md`'s superseded rewrite framing. `agents.py` has **zero edits**, which preserves the `agents.py:389-406` hallucination-record evidence verbatim, as required.
- Four new nodes: `investigator` (LLM, ranks causal hypotheses, numeric-token validator against the recorded hallucination class), `policy_gate` (deterministic, ₹50,000 threshold + data-sufficiency escalation), `executor` (the sole write/interrupt target), `recorder` (terminal on every path, including refusals).
- A durable interrupt using LangGraph's dynamic `interrupt()`/`Command(resume=...)`, checkpointed via `DurableFileSaver` — an `InMemorySaver` with a pickle flush to disk after every write, because `langgraph-checkpoint-sqlite` is not declared in `requirements.txt` and WS-8 does not own that file. This is AD-6's own mandated no-new-dependency fallback, not an improvised substitute.
- Verified durable **across a real process restart**: `tests/autonomy/test_restart.py` runs two separate `python -c` subprocesses sharing only the checkpoint/ledger file paths — the first suspends at `executor` and exits; the second, a fresh interpreter, resumes and completes the write.
- Executor re-checks two preconditions at execution time rather than trusting proposal-time state: idempotency-key replay (ledger-backed) and "a supplier is on file". A resumed run with the same idempotency key a second time is blocked with `decision_status="failed"`.
- `≥4 messages` holds on every exercised path (graded `test_e2e.py:78`), including mid-suspension.

## Open Issues

### 1. APScheduler is unavailable

`requirements.txt` does not declare APScheduler and the package is not installed. The runtime remains import-safe while disabled. Enabling `SCHEDULER_ENABLED=true` raises a clear error until integration adds the dependency.

Requested action: process `docs/implementation/integration-requests/WS-10.md` through WS-0/integration.

### 2. Upstream contracts were initially absent

WS-10 expects these frozen contracts:

- `src.core.events.subscribe(event_type, handler)`
- `src.agents.multi_agent.graph.run_pipeline(trigger, *, product_ids=None, run_id=None)`

Concurrent WS-8 files now appear in the worktree, but they were not included in the WS-10 commit and must be integrated independently.

### 3. Graded suite is not green

Pre-WS-10 baseline:

- `225 passed, 2 skipped, 7 failed`
- All seven failures were Phase 2 RAG failures downstream of Gemini SSL certificate verification.

Latest post-WS-10 combined-worktree run:

- `223 passed, 2 skipped, 9 failed`
- Seven failures are the same SSL/RAG failures.
- Two Phase 5 source-inspection failures appeared after concurrent WS-8 edits to `build_inventory_graph`.
- Phase 1, Phase 3, and Phase 4 remained green.

The bootstrap RAG ingestion dropped the existing Chroma collection before the SSL failure prevented rebuilding it. Re-run ingestion from a device with working certificate trust before re-running the graded suite.

### 4. Required `.env` source did not exist

The requested source path under `C:\Users\2mrmi\...` does not exist on this device. An existing worktree `.env` was available and used. On the next device, copy the correct private `.env` before seeding or ingestion.

### 5. Concurrent uncommitted work must remain separate

The following non-WS-10 paths appeared while WS-10 was being implemented and were deliberately excluded from its commit:

- `src/agents/multi_agent/`
- `src/backend/services/inventory_service.py`
- `src/backend/services/po_service.py`
- `src/backend/routers/receiving.py`
- `src/execution/`
- `tests/execution/`

Do not discard these paths when cleaning or switching branches. They belong to other Wave 2 workstreams.

### 6. `src/core/` (WS-0) is still missing — WS-9 built a local shim

Same root cause as WS-10's item 2: `src/core/clock.py`, `events.py`, `ids.py`, `vocab.py`, `errors.py` do not exist in this worktree. WS-9's hard rule (`clock.now()`/`clock.today()` only) is unenforceable without a clock module.

What WS-9 did: a same-interface, same-behaviour shim at `src/execution/clock.py` (function names and signatures match the frozen contract exactly), used only inside WS-9's own files. See `docs/implementation/integration-requests/WS-9.md` item 1.

Requested action: once WS-0 publishes `src/core/clock.py`, swap the import in `inventory_service.py`, `po_service.py`, and the four `src/execution/*.py` files (one line each), then delete the shim.

### 7. `models_governance.py` (`Decision`, `Approval`) is missing — WS-9 accepts a duck-typed decision

`execute_decision(db, decision)` and `check_preconditions(db, decision)` are specified against a concrete `Decision` ORM row that does not exist here. WS-9's implementation reads `decision.product_id`, `.supplier_id`, `.quantity`, `.unit_cost`, `.order_value`/`.authority_limit`, `.autonomy_mode`, `.kill_switch_engaged`, `.idempotency_key`, `.expected_delivery` off any object with those attributes (tests use `SimpleNamespace`). Once WS-0/WS-4 publish the real type, drop the duck-typing note in `src/execution/preconditions.py` and `executor.py` and import it directly — no signature change needed.

### 8. `decisions.idempotency_key` (WS-0 column) does not exist — WS-9 tracks consumed keys in its own new table

`src/execution/idempotency.py::ConsumedIdempotencyKey` is a new, additive table (`execution_idempotency_keys`) used only because the frozen `decisions` table isn't here yet. Reconcile onto `decisions.idempotency_key` once it exists (see `docs/implementation/integration-requests/WS-9.md` item 3).

### 9. `autonomy_policies` (WS-5) and `select_supplier` (WS-7) are not consumed

`check_preconditions` reads kill-switch / autonomy-mode straight off the `decision` object rather than querying `autonomy_policies`, and `execute_decision` uses the price/quantity already on the decision rather than re-deriving them from WS-7. Flagged for WS-5/WS-7 to confirm this is the intended re-check boundary (see integration-requests/WS-9.md items 4-5).

### 10. `src/core/` (WS-0) is still missing — WS-8 built its own separate local shim

Same root cause as items 2 and 6: no `clock.py`, `ids.py`, `events.py` in this worktree. WS-8's shim lives at `src/agents/multi_agent/_clock.py` — deliberately not shared with WS-9's `src/execution/clock.py` shim, since neither stream owns the other's files. Both disappear once WS-0 publishes the real module (see `docs/implementation/integration-requests/WS-8.md` item 1).

### 11. WS-1 analytics, WS-5 policy, WS-7 sourcing, WS-9 execution are not consumed by the graph

`nodes/investigator.py`, `nodes/policy_gate.py`, and `nodes/executor.py` all contain local stand-ins instead of calling the real `compute_daily_demand`/`score_sufficiency` (WS-1), `evaluate`/`PolicyVerdict` (WS-5), or `execute_decision`/`check_preconditions` (WS-9) — none of which exist in this worktree. `policy_gate` only implements the ₹50,000 threshold and data-sufficiency escalation rules; kill switch, blast-radius caps, autonomy mode, and non-cheapest-supplier escalation are named gaps, not silently assumed clear. Full detail and swap-in points: `docs/implementation/integration-requests/WS-8.md` items 2, 3, 5.

### 12. `executor` writes to a local ledger file, not a real purchase order

`src/agents/multi_agent/ledger.py` is a JSON-lines file standing in for the not-yet-existing `decisions`/`agent_runs` tables (WS-0/WS-4). `executor` returns a `PO-SIM-######` number, deliberately not in the real `PO-YYYY-NNNN` format, so it can never be mistaken for a genuine purchase order. WS-9's `execute_decision` does not exist yet, so WS-8 could not call it instead. See `docs/implementation/integration-requests/WS-8.md` items 5-6.

### 13. `langgraph-checkpoint-sqlite` is not in `requirements.txt`

WS-8 does not own `requirements.txt` and did not add it. `src/agents/multi_agent/checkpoint.py`'s `DurableFileSaver` (an `InMemorySaver` plus a pickle flush to disk) is AD-6's own mandated no-new-dependency fallback, verified durable across a real process restart. No action required unless a future stream needs concurrent-writer guarantees a single file cannot give (e.g. WS-10's scheduler firing concurrent ticks) — see `docs/implementation/integration-requests/WS-8.md` item 7.

### 14. Three branches now stack on top of each other

`ws-8-autonomy-loop` is based on `ws-9-executor-inventory-extensions`'s tip, which is based on `ws-10-background-runtime`'s tip. None of the three is rebased onto `main`. This was a deliberate choice to avoid losing this file's WS-9/WS-10 sections (which only exist in this branch lineage, not on `main`) rather than an oversight — but it means a clean merge to `main` needs each branch cherry-picked or rebased in dependency order (WS-10, then WS-9, then WS-8), not merged as three parallel PRs.

### 15. WS-8's own node rewrite risk

`supplier_coordinator` was left unmodified rather than rewritten into a real multi-supplier comparison (as `08-AGENTIC-WORKFLOWS.md` describes), specifically because `tests/phase5/test_agent_data_flow.py` asserts on its current prompt text by substring. Once WS-7's `select_supplier`/`Scorecard` land, rewriting this node is the one place graded-test re-verification is needed before touching it — see `docs/implementation/integration-requests/WS-8.md` item 4.

## Verification Completed

- `pytest tests/runtime -q`: **8 passed**.
- VS Code diagnostics for `src/runtime/` and `tests/runtime/`: **no errors**.
- Pylance syntax checks for all new Python files: **no syntax errors**.
- Forbidden-pattern scan: no `datetime.now()`, `date.today()`, `time.time()`, SQLAlchemy Enum, `server_default=func.now()`, or prohibited ports in `src/runtime/`.

### WS-9 verification

- `pytest tests/execution -q`: **23 passed**.
- `pytest tests/phase1 tests/phase2 tests/phase3 tests/phase4 tests/phase5 -q`: **225 passed, 2 skipped, 7 failed** — identical to the pre-WS-9 baseline (same 7 Gemini SSL failures). No regression.
- `git status --porcelain` scoped to WS-9's owned paths on branch `ws-9-executor-inventory-extensions`: clean after commit `f169e57`.
- No `datetime.now()`, `date.today()`, `time.time()`, SQLAlchemy `Enum` on a new column, or `server_default=func.now()` on a new table in any WS-9 file.

### WS-8 verification

- `pytest tests/autonomy -q`: **9 passed**, including a real two-subprocess restart test (`test_restart.py`).
- `pytest tests/phase1 tests/phase2 tests/phase3 tests/phase4 tests/phase5 -q`: **234 passed, 2 skipped, 7 failed** (225 baseline + 9 new autonomy tests) — same 7 Gemini SSL failures as every prior baseline. No regression. Re-ran `tests/phase5` after every change during implementation, not just at the end.
- Fixed one transient Windows `PermissionError` found during full-suite runs: `checkpoint.py`'s disk flush now retries the atomic rename a few times before raising.
- `git status --short` on branch `ws-8-autonomy-loop`: only files under `src/agents/multi_agent/`, `tests/autonomy/`, `docs/implementation/integration-requests/WS-8.md`, and `.gitignore` — nothing in `tests/phase1..5`, `main.py`, `models.py`, or `requirements.txt`.
- `src/agents/multi_agent/agents.py`: **zero edits** — the `agents.py:389-406` hallucination-record comment is preserved verbatim, unmoved.
- No `datetime.now()`, `date.today()`, `time.time()`, SQLAlchemy `Enum` on a new column, or `server_default=func.now()` on a new table, outside the one documented shim call site (`_clock.py`).

## Next Device Checklist

1. Fetch all pushed branches and check out whichever you're continuing:
   `git fetch origin`, then `ws-10-background-runtime`,
   `ws-9-executor-inventory-extensions`, or `ws-8-autonomy-loop` (the latter
   already contains the other two's commits — see item 11 below).
2. Supply the correct `.env` without committing it.
3. Integrate WS-0 events/clock and WS-8 `run_pipeline` first (WS-10); integrate
   WS-0 `src/core/clock.py` and `models_governance.py` first (WS-9); integrate
   WS-0/WS-1/WS-5/WS-7/WS-9 first (WS-8) — all three streams built local shims
   documented above and in their respective
   `docs/implementation/integration-requests/*.md`.
4. Add/install APScheduler through the integration-owned dependency file (WS-10 only).
5. Wire `register_runtime(app)` (WS-10) and `receiving.router` (WS-9) from
   application lifespan through integration; do not edit `main.py` from any
   workstream.
6. Run `python -m src.backend.seed_demo_data`.
7. Run `python -m src.rag.ingest` on a device with working SSL certificates.
8. Run `pytest tests/runtime -q` (WS-10), `pytest tests/execution -q` (WS-9),
   and `pytest tests/autonomy -q` (WS-8).
9. Run `pytest tests/phase1 tests/phase2 tests/phase3 tests/phase4 tests/phase5 -q`.
10. Confirm repository ownership (`git diff --name-only` against each
    workstream's owned-files list) before merging any branch.
11. The three branches stack: `ws-9-executor-inventory-extensions` branches off
    `ws-10-background-runtime`'s tip, and `ws-8-autonomy-loop` branches off
    `ws-9-executor-inventory-extensions`'s tip. None is rebased onto `main` —
    rebase or cherry-pick each onto `main` in that order (WS-10, WS-9, WS-8)
    before opening PRs if a clean, single-workstream history is required.

No commit, push, or merge from another workstream was performed during WS-10,
WS-9, or WS-8 implementation before their respective handoff commits.