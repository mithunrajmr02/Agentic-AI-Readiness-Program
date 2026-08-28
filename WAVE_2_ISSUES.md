# Wave 2 Issues and Handoff

Date: 2026-08-28

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

## Verification Completed

- `pytest tests/runtime -q`: **8 passed**.
- VS Code diagnostics for `src/runtime/` and `tests/runtime/`: **no errors**.
- Pylance syntax checks for all new Python files: **no syntax errors**.
- Forbidden-pattern scan: no `datetime.now()`, `date.today()`, `time.time()`, SQLAlchemy Enum, `server_default=func.now()`, or prohibited ports in `src/runtime/`.

## Next Device Checklist

1. Fetch the pushed WS-10 branch and check it out.
2. Supply the correct `.env` without committing it.
3. Integrate WS-0 events/clock and WS-8 `run_pipeline` first.
4. Add/install APScheduler through the integration-owned dependency file.
5. Wire `register_runtime(app)` from application lifespan through integration; do not edit `main.py` from WS-10.
6. Run `python -m src.backend.seed_demo_data`.
7. Run `python -m src.rag.ingest` on a device with working SSL certificates.
8. Run `pytest tests/runtime -q`.
9. Run `pytest tests/phase1 tests/phase2 tests/phase3 tests/phase4 tests/phase5 -q`.
10. Confirm repository ownership before merging.

No commit, push, or merge from another workstream was performed during WS-10 implementation before this handoff commit.