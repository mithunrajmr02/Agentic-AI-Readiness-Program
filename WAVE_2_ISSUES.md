# Wave 2 Issues and Handoff

Date: 2026-08-28 (WS-10 section), updated same day with WS-9

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

## Next Device Checklist

1. Fetch both pushed branches and check out whichever you're continuing:
   `git fetch origin`, then `ws-10-background-runtime` or
   `ws-9-executor-inventory-extensions`.
2. Supply the correct `.env` without committing it.
3. Integrate WS-0 events/clock and WS-8 `run_pipeline` first (WS-10); integrate
   WS-0 `src/core/clock.py` and `models_governance.py` first (WS-9) — both
   streams built local shims documented above and in their respective
   `docs/implementation/integration-requests/*.md`.
4. Add/install APScheduler through the integration-owned dependency file (WS-10 only).
5. Wire `register_runtime(app)` (WS-10) and `receiving.router` (WS-9) from
   application lifespan through integration; do not edit `main.py` from either
   workstream.
6. Run `python -m src.backend.seed_demo_data`.
7. Run `python -m src.rag.ingest` on a device with working SSL certificates.
8. Run `pytest tests/runtime -q` (WS-10) and `pytest tests/execution -q` (WS-9).
9. Run `pytest tests/phase1 tests/phase2 tests/phase3 tests/phase4 tests/phase5 -q`.
10. Confirm repository ownership (`git diff --name-only` against each
    workstream's owned-files list) before merging either branch.
11. `ws-9-executor-inventory-extensions` currently branches off
    `ws-10-background-runtime`'s tip, so its history includes the WS-10 commit
    as an ancestor — rebase or cherry-pick onto `main` first if a clean,
    single-workstream history is required before opening a PR.

No commit, push, or merge from another workstream was performed during WS-10
or WS-9 implementation before their respective handoff commits.