# WS-2 — Integration Requests & Reconciliation Notes

**Wave 1 · Simulation & Data Harness · status: COMPLETE, all gates green.**

This is the sanctioned channel (doc 14 §"IF YOU NEED SOMETHING YOU DO NOT OWN").
It records (A) what WS-2 published, (B) decisions taken where the planning docs
under-specified or disagreed, (C) the things WS-2 needs from files it does not own,
and (D) verification evidence.

Authority rule, unchanged from WS-0: **`15-SHARED-CONTRACTS.md` is frozen and wins
every conflict.** Doc 13 (`13-DEMO-SCENARIOS.md`) and doc 14 come next; where they
disagree with §15, §15 is what the code does and section B says so explicitly.

---

## A. What WS-2 published

| Area | File | Notes |
|---|---|---|
| Ninety-day history | `src/simulation/backfill.py` | Deterministic demand curves, backward receipt schedule, sufficiency arithmetic. Every `recorded_at` explicit. |
| Everything the history sits in | `src/simulation/seeder.py` | Users, supplier catalogue, autonomy policy, one overdue PO, one partially-received PO. |
| The four demo scenarios | `src/simulation/scenarios.py` | `demo_scenarios` rows + `load_scenario` / `verify_scenario`. |
| Return to baseline | `src/simulation/reset.py` | Removes only what this package wrote; positions rebuilt from the surviving ledger. |
| HTTP surface | `src/backend/routers/simulation.py` | Publishes a module-level `router` and **stops** — see C4. |
| Tests | `tests/simulation/` | 144 tests — backfill 35, scenarios 45, router 27, seeder 23, reset 14. |

Nothing outside these paths was modified. `src/backend/seed_demo_data.py` is
**imported**, never edited or restated: it owns the baseline (4 suppliers, 5
products, 4 POs, 11 opening movements) and the graded phases assert its numbers.

---

## B. Decisions taken (read before building against this)

### B1 — The defect this stream exists to fix
`stock_movements.recorded_at` carries `server_default=func.now()`, which SQLite
evaluates **at insert time**. Any writer that omits the value stamps wall-clock
now regardless of `clock.now()`, which is how the original ledger ended up with
ninety movements on a single date and every demand rate undefined.

**Rule for every stream that writes a movement:**

```python
recorded_at = clock.now() - timedelta(days=n)   # never the column default
```

`tests/simulation/test_backfill.py::test_no_backfilled_movement_lands_on_today`
asserts this directly rather than by counting dates, so a single omitted timestamp
fails loudly.

### B2 — Doc 13's severities are translated on the way in
Doc 13's scenario tables use `warning` and `info`. Neither is in
`vocab.SEVERITIES` (`critical|high|medium|low`), and §15 wins, so:

| Doc 13 | Stored |
|---|---|
| `critical` | `critical` |
| `warning` | `high` |
| `info` | `low` |

Applied once, in `scenarios.normalise_severity`. The stored `expected_signals`
contain only frozen values. **WS-3 should emit the right-hand column.**

### B3 — `demo_scenarios` has `is_loaded`/`loaded_at`, not `is_active`
Doc 13 §4 sketches an `is_active` column ("exactly one active at a time"). The
WS-0 model that exists carries `is_loaded` and `loaded_at`. WS-0 owns the schema
and this stream writes rows, never columns, so `is_loaded` is what is set —
`load_scenario` clears every other row, preserving the intended semantics.

### B4 — All four scenarios sit at clock offset 0
Doc 13 §13. The projected breaches are computed forward from a dense ninety-day
history rather than manufactured by moving the calendar, so the demo never has to
explain why "today" is not today. Consequence worth knowing: **`load_scenario`
never calls `clock.set_offset` and therefore needs no DEMO_MODE.** The HTTP
endpoint still gates it (C1); the function does not.

### B5 — `POST /api/simulation/clock` treats `days` as absolute
Doc 13 §4 specifies only `{days: n}`. Absolute is the default so pressing the same
button twice lands on the same date instead of drifting; `{"days": n, "relative":
true}` moves by a delta. A presenter who clicks "+14 days" twice because the first
click looked slow should not end up a month out with no way to tell.

### B6 — `verify_scenario` is a subset check, and reports extras
`passed` is true when nothing **expected** is missing. A dense ninety-day history
legitimately raises findings beyond the two or three a scenario is built to
demonstrate, so extras are reported under `unexpected` rather than failing the run.
A right-signal/wrong-severity case is reported separately as `severity_mismatch`
and **does** fail: "we found it but called it low" is a different defect from "we
did not find it", and a report that merged the two would send the reader to the
wrong place.

### B7 — `reset_simulation` deliberately does **not** call `events.reset()`
`events.reset()`'s docstring names WS-2's scenario reloads. This stream declines,
and the divergence is deliberate: subscriptions are application wiring registered
at startup, not scenario state. Clearing them mid-run would leave a live server
with every detector silently detached and no error to explain why. Asserted in
`test_reset.py::test_reset_does_not_unsubscribe_event_handlers`. **If WS-0 or WS-9
disagrees, this is the line to change and that test is where to argue it.**

### B8 — Positions are rebuilt from the ledger, not from a stored table
`reset._rebuild_stock_levels` recomputes each `quantity_on_hand` as the sum of the
surviving movements. A second hardcoded copy of numbers the ledger already
determines would eventually disagree with it. This is only correct because the
baseline seeder's own movements already sum to its documented positions —
verified, and guarded by
`test_reset.py::test_the_baseline_satisfies_the_ledger_invariant`:

| SKU | On hand | Ledger sum |
|---|---|---|
| SKU-GRO-0001 | 167 | 167 |
| SKU-ELC-0001 | 4 | 4 |
| SKU-ELC-0002 | 0 | 0 |
| SKU-HHD-0001 | 50 | 50 |
| SKU-PRC-0001 | 0 | 0 |

### B9 — Sufficiency is implemented here provisionally
`backfill.sufficiency_of` implements §5.4's floors (`sufficient` ≥14 events across
≥21 days; `thin` ≥5 across ≥7; `insufficient` ≥1; `none` 0) because the harness
must be able to prove its own dataset is dense enough to compute from. **WS-1 owns
sufficiency for the running system.** When it lands, this function should be
replaced by a call into it rather than left as a second implementation — the
boundary tests in `test_backfill.py` transfer directly.

### B10 — A latent bug found and fixed inside this stream's own code
`seed_supplier_products` can reach the same `(supplier, product)` pair twice in one
call — a scenario override that restates a product's **incumbent** terms is exactly
that, and D2 does it. Sessions here are `autoflush=False` (as is production's
`SessionLocal`), so the second lookup could not see the pending row and both
inserts hit the unique constraint at commit. Fixed with a `flush` in
`_upsert_supplier_product`; regression test
`test_seeder.py::test_an_override_naming_the_incumbent_supplier_updates_it`.
Recorded here because **any stream doing add-then-lookup within one uncommitted
unit of work has the same exposure.**

---

## C. Requests — files WS-2 does not own

### C1 — `.env` / `.env.example` have no `DEMO_MODE` key  *(blocks the demo)*
**Owner: WS-0 / WS-9.** `clock.set_offset` raises `RuntimeError` unless
`DEMO_MODE ∈ {1,true,yes,on}`, and every simulation endpoint refuses without it.
As shipped, the key is absent, so **the harness is unreachable in a running
server** — the tests set it via `monkeypatch`, which proves the code but not the
deployment. Please add to `.env.example`, and to `.env` for demo machines:

```
DEMO_MODE=true
```

### C2 — Please publish a public `clock.demo_mode_enabled()`
**Owner: WS-0.** The router needs to refuse *before* touching the clock, and
`clock`'s truthy set is private, so `routers/simulation.py` mirrors it in a local
`_DEMO_TRUTHY`. Two copies of one gate will drift. A public predicate on `clock`
removes the duplicate; `test_router.py::test_a_clock_refusal_from_the_core_becomes_a_409`
covers the case where they disagree today.

### C3 — Please register an app-level `StewardError` handler in `main.py`
**Owner: WS-9.** `HTTPException` renders its payload under `detail`, producing
`{"detail": {"error": {...}}}` and breaking the frozen §12.3 envelope. Until a
handler exists, these endpoints build an explicit `JSONResponse` from
`contracts.envelopes.ErrorEnvelope`. That works and is tested
(`test_the_error_body_is_not_nested_under_detail`), but every stream will
re-implement it. One handler translating `StewardError → error_envelope(exc)`
removes the duplication.

### C4 — Please wire the router  *(one line)*
**Owner: WS-9.** `src/backend/routers/simulation.py` publishes `router` and stops,
per doc 14 §"Integration only":

```python
from src.backend.routers import simulation
app.include_router(simulation.router)
```

Deliberately **not** asserted-absent anywhere in `tests/simulation/`: a test that
required the wiring to be missing would fail the day the wiring lands correctly.

### C5 — The `agent` role is not in `auth.VALID_ROLES`
**Owner: WS-0 / WS-6.** `seed_users` writes `agent@retail.com` with role `agent`
directly rather than through registration, because the endpoint would reject it.
§15 line 310 needs the identity to exist (AD-12's least-privilege agent subject).
Either add `agent` to `VALID_ROLES` or confirm that seeding directly is the
intended path — if it changes, `test_seeder.py::test_the_agent_role_is_not_self_registerable`
is where it surfaces.

### C6 — The exact signals WS-3 must raise  *(the contract, not a request)*
**Owner: WS-3.** `verify_scenario` matches on
`(signal_type, sku | supplier_code, severity)` — severities already translated per
B2. These are the triples, agreed here rather than discovered during integration:

**D1 — `D1_governed_order`** (3)

| signal_type | subject | severity |
|---|---|---|
| `threshold_breach` | SKU-ELC-0001 | `high` |
| `config_drift` | SKU-GRO-0001 | `critical` |
| `data_insufficient` | SKU-PRC-0001 | `low` |

**D2 — `D2_root_cause`** (3)

| signal_type | subject | severity |
|---|---|---|
| `projected_breach` | SKU-GRO-0001 | `critical` |
| `supplier_drift` | supplier `SUP-0005` | `high` |
| `config_drift` | SKU-GRO-0001 | `critical` |

**D3 — `D3_config_audit`** (5)

| signal_type | subject | severity |
|---|---|---|
| `config_drift` | SKU-GRO-0001 | `critical` |
| `config_drift` | SKU-HHD-0001 | `critical` |
| `config_drift` | SKU-ELC-0002 | `high` |
| `config_drift` | SKU-ELC-0001 | `medium` |
| `data_insufficient` | SKU-PRC-0001 | `low` |

**D4 — `D4_refusal`** (2)

| signal_type | subject | severity |
|---|---|---|
| `threshold_breach` | SKU-PRC-0001 | `critical` |
| `data_insufficient` | SKU-PRC-0001 | `low` |

Two notes for WS-3. `supplier_drift` is matched by **supplier**, not product —
`signals.supplier_id` must be set and `product_id` left null, or the subject will
not match. And a signal only counts while `status == "open"`; resolved and
superseded rows are history, not current findings.

### C7 — What the dataset guarantees you  *(for WS-1 and WS-3)*
After any `load_scenario`, on the five baseline products:

- **≥90 distinct `recorded_at` dates**, contiguous from day −90 to day −1. Today
  carries no backfilled movement; the opening adjustment sits before day −90.
- **≥3 of 5 products reach `sufficient`.** The full spectrum is present by design,
  so every branch of the sufficiency UI has a real subject: rice, detergent and
  headphones `sufficient`, the television `thin` (0.2/day), Colgate `none`
  (exactly zero — D4's refusal is indefensible otherwise).
- **M-16 holds per product**: `sum(stock_movements.quantity) ==
  stock_levels.quantity_on_hand`.
- Two operational POs no fixture ships with: `PO-2026-0005` overdue and never
  received (for `po_overdue`), `PO-2026-0006` received 40 of 100 (a short delivery,
  booked at 40).

Any `MetricValue`/`Computed` derived from a product whose sufficiency is
`insufficient` or `none` must return `value=None`, never `0.0` — Colgate is the
subject that will catch a violation.

---

## D. Verification

| Gate | Result |
|---|---|
| `pytest tests/simulation -q` | **144 passed** |
| `pytest tests/phase1..phase5 -q` | **232 passed, 2 skipped** — identical to the bootstrap baseline |
| `git diff --name-only` | empty; every WS-2 path is a new untracked file |
| Committed to `main` / pushed / merged | no |

The 2 skips are the LangSmith tests, skipped at baseline too. `HEAD` is
`2d4baf6` — the same commit this stream started from.

### A trap worth naming: the graded suite can fail for reasons that are not yours

An earlier run of the same command returned **7 failed** in phase 2, all of them
tests that call the embedding API:

```
Error embedding content (RESOURCE_EXHAUSTED): 429
Quota exceeded for metric: generativelanguage.googleapis.com/embed_content_free_tier_requests,
limit: 1000, model: gemini-embedding-2
quotaId: EmbedContentRequestsPerDayPerUserPerProjectPerModel-FreeTier
```

They present as logic failures — `AssertionError: Unexpected answer: the inventory
manual is temporarily unavailable...` — because what the assertion inspects is the
RAG chain's own fallback string, not the 429. The cap is **daily**, so unlike the
per-minute exhaustion seen during bootstrap it does not clear on a backoff; a
re-run 75 seconds later failed identically. It cleared when Google's daily window
rolled over, and the same 7 tests now pass untouched.

Affected: `test_sku_query`, `test_po_lifecycle`, `test_reorder_formula`,
`test_po_approval`, `test_movement_types`, `test_category_management`,
`test_ingest_build_vectorstore_default`.

**Do not chase these as regressions, and do not accept them as an excuse either.**
The way to tell the difference without waiting for the window is to prove the
graded suites cannot see your code at all:

1. **No tracked file modified** — `git status --porcelain` reports only `??` entries,
   so the graded suites' import graph is byte-identical to the baseline.
2. **Nothing outside `tests/simulation/` imports WS-2 code** — grep for
   `src.simulation` / `routers.simulation` across `src` and `tests` returns no hits.
   The package is unreachable from phases 1–5.
3. **The collected count is unchanged at 234** — nothing was added to or removed
   from the graded suites.

All three held then and hold now; the difference between that run and this one was
the clock at Google, not the code here.

### Two isolation guarantees worth naming

Getting either wrong would have corrupted a developer's working database or a later
suite:

- **Nothing in `src/simulation` opens its own session.** `database.py` rewrites
  relative SQLite URLs back to the real `inventory.db`, so a harness that reached
  for `SessionLocal()` during a test would seed ninety days of synthetic history
  into the developer's database. Every function takes an explicit `db`.
- **The clock offset is module-global**, so `tests/simulation/conftest.py` resets
  it before and after every test. A leaked offset would poison every suite that ran
  afterwards, including the graded ones.

Nothing in `tests/phase1..phase5/` was edited, and none of it was treated as
guidance: where a graded test and this stream disagreed, the design changed.
