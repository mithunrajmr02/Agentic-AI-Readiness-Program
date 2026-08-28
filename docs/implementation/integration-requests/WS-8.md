# Integration requests — WS-8 (Autonomy Loop)

Filed per the runbook: things WS-8 needs but does not own, so does not
change. Each entry names the local stand-in shipped in the meantime and
exactly what should replace it.

## 1. `src/core/` does not exist (owned by WS-0)

None of `clock.py`, `ids.py`, `events.py`, `vocab.py`, `errors.py`
(15-SHARED-CONTRACTS.md §2) exist in this worktree. WS-8 cannot create
`src/core/` itself — it is not in section 14's ownership list for this
stream, and doing so would be exactly the "small necessary fix in a shared
file" the runbook warns against.

Stand-ins shipped:

- `src/agents/multi_agent/_clock.py` — mirrors `now()` / `today()` exactly.
  One `datetime.now()` call, in one place, for a documented reason.
- `run_id` generation uses `uuid.uuid4().hex[:8]`, not `next_id()`'s
  concurrency-safe counter — fine for a single-process demo, not for
  concurrent scheduled + manual runs (AD-15 territory).

**Ask:** land `src/core/clock.py` (and, before Wave 2 needs it more
broadly, `ids.py`/`events.py`). Every call site in
`src/agents/multi_agent/` importing `_clock` is then a one-line swap.

## 2. WS-1 analytics (`compute_daily_demand`, `derive_reorder_point`,
`score_sufficiency`, …) does not exist

`investigator.py`'s `_sufficiency_from_forecast` is a weak local proxy
derived from `demand_forecast` fields already produced by the *unmodified*
`demand_forecaster` (which still asks the LLM, per the Phase-5 tests it is
graded against — see §5 below). It does not implement
15-SHARED-CONTRACTS.md §5.4's real thresholds (≥14 sale events / ≥21 days,
etc.) because it has no access to `stock_movements` from a graph node that
only ever talks to the REST API, and doing a second, differently-shaped
`requests.get` call risks breaking the Phase-5 mocks that return one fixed
payload for every URL.

**Ask:** once `compute_daily_demand` / `score_sufficiency` land, replace
`_sufficiency_from_forecast` with a real call, and give `demand_forecaster`
(or a step ahead of `investigator`) DB or service access to call it.

## 3. WS-5 policy (`evaluate`, `PolicyVerdict`, `DecisionContext`) does not
exist

`nodes/policy_gate.py` hardcodes the one rule this build can source
honestly — the manual's ₹50,000 threshold (§10 line 113) — plus the
data-sufficiency escalation rule. Kill switch, blast-radius caps, autonomy
mode, and "non-cheapest supplier always escalates" are **not**
implemented; there is no `autonomy_policies` table and no `SupplierChoice`
to read `is_cheapest` from.

**Ask:** replace `policy_gate`'s body with a call to WS-5's `evaluate()`
once it exists. The node's shape (reads state, writes `authority` /
`policy_citation` / `policy_limit` / `order_value`) should not need to
change.

## 4. WS-7 sourcing (`select_supplier`, `Scorecard`) does not exist

`supplier_coordinator` is **unmodified** (see §5) and still resolves a
single supplier by product FK, not a real multi-supplier comparison —
`supplier_products` (owned by WS-0, written by WS-2/WS-7) does not exist
either.

**Ask:** once both land, `supplier_coordinator` becomes WS-8's one
sanctioned rewrite candidate — but only after confirming the Phase-5
prompt-content tests (`test_agent_data_flow.py`) are re-graded against the
new behaviour, since today they assert on this function's *current*
prompt text by substring.

## 5. WS-9 execution (`execute_decision`, `check_preconditions`,
`inventory_service` fixes) does not exist

`nodes/executor.py` does **not** call `inventory_service` or any write
endpoint — WS-9 is the sole owner of that path and it is not built yet.
Instead it simulates the write to `src/agents/multi_agent/ledger.py`
(a local JSON-lines file, not a database table) and returns a
`PO-SIM-######` number that is deliberately **not** in the real
`PO-YYYY-NNNN` format, so it can never be mistaken for a genuine PO.

Preconditions actually re-checked: idempotency key (via the ledger) and
"a supplier is on file". **Not** re-checked, because they need modules
this stream does not own: kill switch, autonomy mode, in-flight PO guard,
supplier `active` state, blast-radius caps (15-SHARED-CONTRACTS.md §9,
preconditions 1–4 and 7).

**Ask:** once `execute_decision(db, decision)` exists, `executor` should
call it in place of `ledger.consume_and_record`, and the four unchecked
preconditions above should move from "named gap" to "re-checked here".

## 6. `decisions` / `approvals` / `agent_runs` tables do not exist (owned
by WS-0, written by WS-4)

`recorder` and `executor` both write to `src/agents/multi_agent/ledger.py`
— an append-only JSON-lines file — instead of those tables. This is not a
database and provides none of `decisions`' query surface (no `GET
/api/decisions`, no ledger UI). It exists only so every terminal path in
the graph has *somewhere* durable to record to.

**Ask:** once `models_governance.py` / `models_analytics.py` land and
WS-4 publishes `create_decision` / `request_approval`, `ledger.py` should
be deleted and `recorder`/`executor` should call those instead.

## 7. `langgraph-checkpoint-sqlite` is not in `requirements.txt`

WS-8 does not own `requirements.txt` and did not add it. AD-6's own
mandated fallback ("if `langgraph-checkpoint-sqlite` proves fragile,
persist the full graph state as JSON… no new dependency") is what shipped
instead: `src/agents/multi_agent/checkpoint.py`'s `DurableFileSaver`,
`InMemorySaver` (bundled with `langgraph` core) plus a pickle flush to
disk after every write. Verified durable across a real process restart —
see `tests/autonomy/test_restart.py`.

**Ask:** no action required unless a future stream wants Postgres/SQLite
concurrency guarantees this single-writer file cannot give (e.g. WS-10's
scheduler running concurrent ticks). If so, add the package to
`requirements.txt` and swap `DurableFileSaver` for the real thing —
`build_inventory_graph()`'s `checkpointer=` line is the only call site.

## 8. `apscheduler` / WS-10's runtime does not exist

`run_pipeline` / `resume_pipeline` are implemented and manually callable,
but nothing calls them on a schedule or from a stock-write hook — that is
WS-10's `register_runtime(app)`, which does not exist yet. No action
needed from WS-8; noted so the gap is visible.

## What was *not* stubbed, and why

`demand_forecaster`, `reorder_agent`, `supplier_coordinator`,
`inventory_auditor` are **unmodified** — not because AD-7's "implementations
change beyond recognition" framing (08-AGENTIC-WORKFLOWS.md §1) was wrong in
principle, but because `tests/phase5/test_agents.py`,
`test_agent_data_flow.py`, `test_state.py`, and `test_coverage_boost.py`
assert on their exact LLM-call and prompt-content behaviour **by source**
(patched-call assertions, substring checks on the literal prompt text sent
to `_llm.invoke`). Rewriting them to be deterministic, as file 08 describes,
would fail all four of those files. 00-EXECUTIVE-SUMMARY.md's own AD-7 text
— *"extend the mandated four, do not replace them"* — is what this build
follows; file 08 is marked `Status: Proposal` and is superseded here by the
executive summary's literal instruction plus the graded tests' actual
behaviour, which is ground truth this runbook says to trust over
documentation.
