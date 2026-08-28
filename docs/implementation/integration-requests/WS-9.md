# WS-9 Integration Requests

Filed by WS-9 (Executor & Inventory Extensions) against things it needed but
does not own. WS-9 did not modify any file outside its ownership; each item
below is a request for the owning workstream to review/reconcile, not a change
WS-9 made to a shared file.

## 1. `src/core/` (clock, ids, events, vocab, errors) — owned by WS-0

Not present in this worktree. WS-9's hard rule (`clock.now()` / `clock.today()`
only, no `datetime.now()`/`date.today()`/`time.time()`) is unenforceable without
it, and the `:137` defect fix (15-SHARED-CONTRACTS.md §2.1) specifically
requires a clock abstraction.

**What WS-9 did:** built a same-interface, same-behaviour shim at
`src/execution/clock.py` (`now`, `today`, `offset_days`, `set_offset` gated on
`DEMO_MODE`, `reset`) — inside WS-9's own package, not `src/core/`. All new
WS-9 code (`inventory_service.py`, `po_service.py`, the `src/execution/*`
modules) imports time only through this shim.

**Ask:** when WS-0 publishes `src/core/clock.py`, the fix is a one-line import
change in each of the files above (function names/signatures already match
the frozen contract). WS-9's shim can then be deleted.

## 2. `models_governance.py` — `Decision`, `Approval` ORM classes — owned by WS-0

Not present in this worktree. `execute_decision(db, decision) -> ExecutionResult`
and `check_preconditions(db, decision) -> list[str]` (15-SHARED-CONTRACTS.md §9)
are specified against a concrete `Decision` row.

**What WS-9 did:** `decision` is accepted duck-typed in
`src/execution/preconditions.py` and `src/execution/executor.py` — any object
exposing `product_id`, `supplier_id`, `quantity`, `unit_cost`,
`order_value`/`authority_limit`, `autonomy_mode`, `kill_switch_engaged`,
`idempotency_key`, `expected_delivery`. Tests use a `SimpleNamespace` stand-in.

**Ask:** once `models_governance.py` exists, WS-9 will drop the duck-typing
note and import the real `Decision` type; no signature change needed on WS-9's
side since attribute access is unchanged.

## 3. `decisions.idempotency_key` column — owned by WS-0

The frozen contract puts the idempotency key on the `decisions` table. Since
that table doesn't exist, consumed keys are tracked in a new WS-9-owned table
(`src/execution/idempotency.py::ConsumedIdempotencyKey`) instead — additive,
touches nothing WS-0 owns.

**Ask:** once `decisions.idempotency_key` exists, decide whether to keep both
(defence in depth) or consolidate onto the `decisions` column alone.

## 4. `autonomy_policies` (kill switch, autonomy mode) — owned by WS-5

`check_preconditions` reads `kill_switch_engaged` and `autonomy_mode` off the
`decision` object passed in (see #2) rather than querying `autonomy_policies`
directly, since that table does not exist here either.

**Ask:** WS-5 to confirm whether the executor should read current policy state
directly from `autonomy_policies` at execution time (re-check, not just what
was true when the decision was proposed) rather than trusting a value carried
on the decision object. If so, WS-9 needs `autonomy_policies`' read API.

## 5. `supplier_products` (WS-7's price/lead-time source) — not consumed here

`execute_decision` takes `unit_cost`/`quantity` from the caller (the decision)
rather than re-deriving them from `select_supplier` — WS-7's function is not
available in this worktree. No functional gap for WS-9's own tests, but the
real integration should confirm the executor is not meant to re-price at
execution time (only re-check preconditions, per its charter).
