# 12 — Data and API Changes

> **Status:** Proposal. Nothing here is approved.
> **Purpose:** Specify every table, column, endpoint, and contract in enough detail that parallel workstreams can build against it without talking to each other.
> **Governing decision:** **AD-3** — zero migrations on existing tables. New relationships point new → old.
> **All schema facts below were read from `src/backend/models.py`, not from documentation.**

---

## 1. The constraint, mechanically

`Base.metadata.create_all` is additive **at table granularity only**. It creates tables that do not exist and touches nothing else. There is no Alembic in this project. Therefore:

| Change | Possible via `create_all`? |
|---|---|
| New table | **Yes** — free |
| New column on an existing table | **No** — silently ignored on an existing DB |
| New member on an existing `Enum` column | **No** — and worse than ignored. See §1.1 |
| New index on an existing table | No |
| Widened column | No |

### 1.1 Three frozen enums — the constraint that is easy to miss

This is stricter than "no new columns", and it is the finding most likely to trip an implementer.

SQLAlchemy renders `Column(Enum(PyEnum))` on SQLite as `VARCHAR` **plus a `CHECK` constraint enumerating the permitted values.** Adding a member to the Python enum does not alter the constraint on an existing database — so the new value is rejected at write time by the CHECK, producing an `IntegrityError` that looks nothing like a schema problem.

Three enums are therefore frozen:

| Enum | Location | Members | Frozen consequence |
|---|---|---|---|
| `POStatus` | `models.py:49-54` | `draft`, `submitted`, `acknowledged`, `received`, `cancelled` | **No `partially_received`.** Derived predicate instead — §3.1 |
| `MovementType` | `models.py:25-47` | `receipt`, `sale`, `adjustment`, `transfer`, `returnm`(=`"return"`) | No new movement kinds. Agent receipts use `receipt` |
| `Category` | `models.py:8-13` | `grocery`, `electronics`, `clothing`, `household`, `personal_care` | Autonomy policies scope to these five, no others |

`MovementType.returnm` deserves a note because an implementer will see it and want to "fix" it. **Do not.** The odd member name is deliberate (`return` is a Python keyword) and `models.py:27-46` carries a long comment recording that a duplicate-valued sibling member was already removed after it leaked an invalid `enum` array into the published OpenAPI schema and into 422 error bodies. That comment is institutional memory. Leave it, and leave the member alone.

### 1.2 The design rule this produces

> **Every status-like column on a new table is `String`, never `Enum`.**

Validation happens in the Pydantic layer, where it can evolve freely. This is the single most important schema decision in the package, because the new tables carry lifecycles that *will* change during implementation — `decision_status` alone has twelve values and will likely gain more. Encoding those in a SQLite CHECK constraint would recreate, in brand-new code, exactly the constraint that is currently blocking us.

The existing enums are a reasonable choice that has aged into a cage. The new tables should not enter the same cage.

---

## 2. The eight new tables

All in new modules per **AD-4**, so `models.py` is never a merge conflict:

| Module | Tables |
|---|---|
| `models_governance.py` | `signals`, `decisions`, `approvals`, `autonomy_policies` |
| `models_analytics.py` | `agent_runs`, `metric_snapshots`, `supplier_products` |
| `models_simulation.py` | `demo_scenarios` |

### 2.1 `signals` — C1

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `signal_ref` | String(20) unique | `SIG-000045` |
| `signal_type` | String(40) | One of 7. **String, not Enum** |
| `severity` | String(20) | `critical` / `warning` / `info` |
| `product_id` | Integer FK → `products.id` | Nullable — supplier signals have no product |
| `supplier_id` | Integer FK → `suppliers.id` | Nullable |
| `po_id` | Integer FK → `purchase_orders.id` | Nullable — `po_overdue` only |
| `dedup_key` | String(120) indexed | `{type}:{scope_id}` — collapses repeats |
| `status` | String(20) | `open` / `investigating` / `resolved` / `superseded` / `expired` |
| `detected_value` | Float | What tripped the detector |
| `threshold_value` | Float | What it was compared against |
| `detail` | Text JSON | Full detector evidence |
| `raised_at` | DateTime | **Explicit, from `clock.now()`** — never a server default |
| `resolved_at` | DateTime nullable | The field `stock_alerts` lacks |
| `resolved_by_decision_id` | Integer FK → `decisions.id` | Nullable |
| `source_event_at` | DateTime nullable | Enables M-2 detection latency |

`dedup_key` is what makes the tick idempotent: a breach that persists for six days produces one open signal updated six times, not six signals. Without it the Signals inbox becomes unusable by day two, which is the failure mode that makes most alerting systems get ignored.

`source_event_at` exists solely so detection latency (M-2) is measurable rather than asserted.

### 2.2 `decisions` — C6, the ledger

Append-only. **No update path in the service layer.** Corrections are new rows referencing `supersedes_id`.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `decision_ref` | String(20) unique | `DEC-000123` |
| `signal_id` | Integer FK → `signals.id` | Nullable — manual invocations |
| `run_id` | Integer FK → `agent_runs.id` | |
| `product_id` | Integer FK → `products.id` | |
| `decision_type` | String(40) | `reorder` / `reorder_point_change` / `resource_switch` / `consolidate` / `decline` |
| `decision_status` | String(30) | The 12-value lifecycle — §2.2.1 |
| `analysis_status` | String(20) | The graded projection. **Both stored** |
| **Computed inputs** | | |
| `avg_daily_demand` | Float | |
| `demand_variance` | Float | |
| `computed_reorder_point` | Float | |
| `stored_reorder_point` | Integer | Snapshot — drift is provable later |
| `days_on_hand` | Float | |
| `proposed_quantity` | Integer | |
| `eoq_reference` | Float nullable | Displayed as reference only |
| `data_sufficiency` | String(20) | `sufficient` / `thin` / `insufficient` |
| `sufficiency_detail` | Text JSON | Sale count, span, thresholds applied |
| **Sourcing** | | |
| `selected_supplier_id` | Integer FK → `suppliers.id` | |
| `unit_price_used` | Float | **From `supplier_products`, never an LLM** |
| `order_value` | Float | |
| `alternatives_considered` | Text JSON | The full ranked set |
| **Authority** | | |
| `authority` | String(30) | `within_authority` / `requires_approval` / `forbidden` |
| `escalation_reason` | String(60) nullable | Powers M-8's breakdown |
| `policy_limit` | Float nullable | |
| `policy_citation` | Text nullable | **Verbatim, snapshotted at decision time** |
| `policy_section` | String(80) nullable | `§10 PO Approval Threshold` |
| `autonomy_mode_at_decision` | String(20) | |
| **LLM** | | |
| `narrative` | Text nullable | Null when unavailable — **legitimate, not an error** |
| `hypotheses` | Text JSON nullable | Ranked causes |
| `llm_available` | Boolean | |
| **Outcome** | | |
| `actor_type` | String(20) | `agent` / `human` |
| `actor_user_id` | Integer FK → `users.id` nullable | |
| `po_id` | Integer FK → `purchase_orders.id` nullable | **Direction is deliberate — §3** |
| `idempotency_key` | String(80) unique nullable | |
| `refusal_reason` | Text nullable | |
| `error` | Text nullable | |
| `supersedes_id` | Integer FK → `decisions.id` nullable | |
| `created_at` / `pending_at` / `decided_at` / `executed_at` | DateTime | All explicit, all clock-sourced. Powers M-1 and M-10 |

`stored_reorder_point` is worth its column: recording what the configuration *was* at decision time means C10's drift claim is evidenced by the ledger itself rather than recomputed against a value that may since have changed.

`policy_citation` is snapshotted for the same reason. Resolving it on read would let a later edit to the manual silently rewrite the governance of a past decision.

#### 2.2.1 The two status fields

Both are stored. `analysis_status` is the graded contract (four permitted values, `tests/phase5/test_e2e.py:102`); `decision_status` is the domain lifecycle. The projection table is in [08-AGENTIC-WORKFLOWS.md](08-AGENTIC-WORKFLOWS.md) §4.2. Storing both — rather than deriving one on read — means the graded value is inspectable in the database and cannot drift from what the test sees.

### 2.3 `approvals` — C5

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `approval_ref` | String(20) unique | `APR-000012` |
| `decision_id` | Integer FK → `decisions.id` | |
| `requested_at` | DateTime | |
| `sla_due_at` | DateTime nullable | Inferred, not manual policy — §12 |
| `status` | String(20) | `pending` / `approved` / `rejected` / `approved_with_modification` / `expired` |
| `decided_at` | DateTime nullable | |
| `decided_by_user_id` | Integer FK → `users.id` nullable | |
| `decision_note` | Text nullable | Required on reject |
| `modified_quantity` | Integer nullable | Counter-proposal |
| `modified_supplier_id` | Integer FK nullable | |
| `system_objection` | Text nullable | **What the system said when it disagreed** |
| `objection_overridden` | Boolean default false | |

`system_objection` + `objection_overridden` are the two columns that make governance more than a form. "Approved" and "approved over a stated objection" are materially different ledger entries, and the difference has to be storable to be meaningful.

### 2.4 `autonomy_policies` — C4 / C3

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `scope_type` | String(20) | `global` / `category` / `product` |
| `scope_value` | String(40) nullable | Must be one of the five frozen `Category` values when `scope_type = category` |
| `mode` | String(20) | `off` / `shadow` / `assisted` / `autonomous` |
| `max_order_value` | Float nullable | Override; default comes from **retrieval**, not this column |
| `max_orders_per_hour` | Integer | Blast radius |
| `max_value_per_day` | Float | Blast radius |
| `min_sale_events` | Integer default 10 | Sufficiency threshold — **configurable and displayed** |
| `min_history_days` | Integer default 30 | |
| `safety_stock_days` | Integer default 2 | §3 line 35's worked example uses 2 |
| `drift_tolerance_pct` | Float default 20.0 | C10 |
| `kill_switch_engaged` | Boolean default false | |
| `kill_switch_reason` | Text nullable | |
| `kill_switch_by_user_id` | Integer FK nullable | |
| `consecutive_failures` | Integer default 0 | Circuit breaker |
| `updated_at` / `updated_by_user_id` | | Policy changes are themselves attributed |

`max_order_value` is an *override*, deliberately nullable. The default path retrieves §10's ₹50,000 from the policy collection. If this column became the primary source, C4's central claim — that the threshold is retrieved and cited rather than hardcoded — would quietly become false. The UI shows the retrieved value with its citation and marks the column as an override when set.

### 2.5 `supplier_products` — C11, the table that unblocks sourcing

`products.supplier_id` is a single nullable FK (`models.py:86`), so today a product has exactly one supplier and multi-supplier comparison is **structurally impossible.** This table is what makes `supplier_coordinator` mean something.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `supplier_id` | Integer FK → `suppliers.id` | |
| `product_id` | Integer FK → `products.id` | |
| `unit_price` | Float | **The only legitimate source of a price** |
| `lead_time_days` | Integer | Per product-supplier pair — `suppliers.lead_time_days` is supplier-wide |
| `min_order_quantity` | Integer default 1 | |
| `pack_size` | Integer default 1 | Solves the rounding question without a column on `products` |
| `is_preferred` | Boolean | |
| `last_price_update` | DateTime | |
| — unique constraint on (`supplier_id`, `product_id`) | | |

Two of these columns exist specifically to avoid touching `products`:

- **`lead_time_days`** — supplier-level lead time is too coarse. §12 line 128 notes *"Electronics: … longer supplier lead times typical"*, i.e. lead time varies by product line, not just by supplier.
- **`pack_size`** — [08-AGENTIC-WORKFLOWS.md](08-AGENTIC-WORKFLOWS.md) §12 item 4 flagged this as needing either a hardcoded default or a new column on `products`. It belongs here instead: pack size is a property of *how this supplier ships this product*, which is more accurate than a product-global value **and** requires no migration. The constraint produced the better model.

Reliability is **computed, not stored** — derived from `purchase_orders.order_date`, `expected_delivery`, and `received_date`, so it cannot go stale.

### 2.6 `agent_runs`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `run_ref` | String(20) unique | `RUN-000078` |
| `trigger` | String(20) | `scheduled` / `event` / `manual` / `backtest` |
| `triggered_by_user_id` | Integer FK nullable | |
| `signal_id` | Integer FK nullable | |
| `graph_thread_id` | String(60) nullable | The checkpointer key |
| `started_at` / `completed_at` | DateTime | |
| `status` | String(20) | `running` / `suspended` / `completed` / `failed` |
| `node_trace` | Text JSON | Per-node timings and outputs |
| `llm_calls` | Integer | |
| `llm_tokens` | Integer | |
| `llm_errors` | Integer | |
| `llm_numeric_violation` | Boolean default false | **M-15** |
| `violation_detail` | Text nullable | The offending token |
| `messages_count` | Integer | Guards the `>= 4` invariant in dev |
| `error` | Text nullable | |

`llm_numeric_violation` converts the hallucination class recorded at `agents.py:389-406` from an anecdote into a tracked rate.

### 2.7 `metric_snapshots`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `metric_key` | String(20) | `M-7`, `M-14`, … |
| `value` | Float | |
| `computed_at` | DateTime | Clock-aware |
| `window_start` / `window_end` | DateTime | |
| `scope_type` / `scope_value` | String | |
| `tier` | String(4) | `T1` / `T2` / `T3` |
| `data_disclosure` | String(12) | `synthetic` / `mixed` / `real` |

`tier` and `data_disclosure` are columns rather than UI conventions so a figure cannot be exported stripped of its caveat. The caveat travels with the value.

### 2.8 `demo_scenarios` — C8

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `scenario_key` | String(40) unique | `D1_autonomous`, `D2_escalation`, … |
| `name` / `description` | String / Text | |
| `seed_spec` | Text JSON | Deterministic definition |
| `clock_offset_days` | Integer | Paired with AD-9 |
| `expected_signals` | Text JSON | **What should fire — makes the demo self-testing** |
| `is_loaded` | Boolean | |
| `loaded_at` | DateTime nullable | |

`expected_signals` is the difference between a demo and a rehearsal: loading a scenario asserts which signals should appear, so a broken demo is detected before the room sees it.

---

## 3. Columns we wanted and cannot have

Every one of these has a workaround that requires no migration. Several of the workarounds are genuinely better than the column would have been.

| Wanted | On | Workaround | Verdict |
|---|---|---|---|
| `decision_id` | `purchase_orders` | `decisions.po_id` points forward instead | **Better** — the governance layer stays deletable without touching the base system |
| `approved_by` | `purchase_orders` | `approvals.decided_by_user_id` | **Better** — one PO can have a full approval history |
| `submitted_at` | `purchase_orders` | `order_date` exists; precise timing from `decisions.executed_at` | Adequate — §3.2 |
| `resolved_at` | `stock_alerts` | `signals.resolved_at` on the new table | Neutral — `stock_alerts` is left in place, unchanged |
| `pack_size` | `products` | `supplier_products.pack_size` | **Better** — §2.5 |
| `safety_stock_days` | `products` | `autonomy_policies.safety_stock_days` | Adequate — per-scope, not per-product |
| `partially_received` | `POStatus` | Derived predicate — §3.1 | **Better** — carries quantities, not just a label |
| Agent attribution | `stock_movements` | **`recorded_by` already exists** — §3.3 | No workaround needed |

The pattern is worth naming: **four of eight constraints produced a better model than the column would have.** That is not luck — pointing new tables at old ones forces you to ask where a fact actually belongs, and "on the join between supplier and product" is more often right than "on the product".

### 3.1 Partial receipt as a derived predicate

```
partially_received  ⟺  status ∈ {submitted, acknowledged}
                       AND ∃ item : 0 < quantity_received < quantity_ordered
```

`po_items.quantity_received` already exists as a nullable Integer (`models.py:161`). Status advances to `received` only when every line is complete. The UI renders "Partially received — 180 of 240" from the predicate, which is strictly more informative than a status label.

### 3.2 Lead time from existing columns

`purchase_orders` has `order_date`, `expected_delivery`, `received_date`, `created_at` — and no `submitted_at`. So:

```
actual_lead_time_days = received_date − order_date
lateness_days         = received_date − expected_delivery
```

Both computable today. **The blocker is not the schema — it is `inventory_service.py:137`**, where `received_date = date.today()` destroys the measurement. One line gates the entire supplier-reliability capability.

### 3.3 Attribution already works

`stock_movements.recorded_by` is `String(100), default="system"` (`models.py:135`). So agent attribution needs **no schema change at all** — the agent writes its own identity into a column that already exists.

What is broken is not the column but the identity: `src/service_auth.py` logs in as `admin@retail.com`, so every agent write is currently attributed to a human administrator. AD-12's `agent@retail.com` fix makes the existing column tell the truth. **A governance defect with a zero-schema fix.**

---

## 4. The clock and `server_default`

Four existing columns use `server_default=func.now()`:

| Column | Consequence |
|---|---|
| `stock_movements.recorded_at` | **The important one** — see below |
| `products.created_at` | Cosmetic |
| `purchase_orders.created_at` | Cosmetic |
| `stock_levels.last_updated` | `onupdate=func.now()` too |

`func.now()` is evaluated by SQLite, so **`clock.now()` cannot influence it.** Two hard implementation rules follow:

1. **The 90-day backfill seeder must pass `recorded_at` explicitly** on every `StockMovement`, overriding the server default. If it does not, all 90 days of history collapses to the seeding instant — which is precisely the current state of the database: all 13 existing movements fall between `2026-08-23 08:50:18` and `15:56:44`, one calendar day, because nothing ever passed an explicit timestamp.
2. **All new tables use explicit clock-sourced timestamps**, never `server_default`. Otherwise C8's controllable clock cannot drive `po_overdue` detection, and BW-3 becomes undemoable.

This is a small detail with a large blast radius: it is the difference between a system that appears to have history and one that has it.

---

## 5. API surface

New router modules only. **AD-5: `inventory.py` and `auth.py` are frozen; `main.py` registration is owned solely by the integration workstream.**

Path namespaces are pre-allocated so two workstreams can never collide on a route.

### 5.1 `/api/signals` — WS-2

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/api/signals` | any | Filter by type, severity, status, product |
| GET | `/api/signals/{ref}` | any | Detail with full detector evidence |
| POST | `/api/signals/scan` | manager | Run detection now |
| POST | `/api/signals/{ref}/dismiss` | manager | Dismiss with a reason |

### 5.2 `/api/decisions` — WS-5

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/api/decisions` | any | Filter by status, type, actor, date |
| GET | `/api/decisions/{ref}` | any | The full case, inputs, citation, narrative |
| GET | `/api/decisions/{ref}/run` | any | Node trace from `agent_runs` |

No POST. **Decisions are created by the graph, never by a client** — the ledger has no external write path, which is what makes "append-only" a property of the API rather than a convention.

### 5.3 `/api/approvals` — WS-5

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/api/approvals` | manager | The queue |
| GET | `/api/approvals/{ref}` | manager | Full case with the "if you do nothing" projection |
| POST | `/api/approvals/{ref}/approve` | **manager** | Resume the graph at `executor` |
| POST | `/api/approvals/{ref}/reject` | **manager** | Reason required |
| POST | `/api/approvals/{ref}/counter` | **manager** | Re-enter `reorder_agent`; returns the recomputed case *and any objection* before committing |

`/counter` returning the recomputed case **before** committing is the API-level expression of the counter-proposal design: the manager sees the system's objection, then decides again. A single-shot endpoint that just accepted the new quantity would erase the most interesting interaction in the product.

### 5.4 `/api/policies` — WS-3

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/api/policies/autonomy` | any | Current modes, caps, kill-switch state |
| PATCH | `/api/policies/autonomy` | **manager** | Change mode or caps |
| POST | `/api/policies/kill-switch` | **manager** | Engage or release, reason required |
| GET | `/api/policies/threshold` | any | **The retrieved threshold + verbatim citation + section** |
| GET | `/api/policies/reload` | manager | Re-ingest the policy collection |

`GET /api/policies/threshold` is the endpoint to open in front of a technical reviewer. It returns the value *and* the sentence it came from, which is the whole of C4 in one response.

### 5.5 `/api/agent` — WS-4

| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/api/agent/evaluate/{product_id}` | manager | Invoke a run manually |
| GET | `/api/agent/runs` | any | Run history |
| GET | `/api/agent/runs/{ref}` | any | Node-level trace |
| GET | `/api/agent/status` | any | Mode, last tick, in-flight, breaker state |
| POST | `/api/agent/copilot` | any | Co-pilot turn, MCP-backed, session-scoped |

### 5.6 `/api/impact` — WS-7

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/api/impact/summary` | any | T1 metrics with tier + disclosure |
| GET | `/api/impact/detection` | any | M-2 … M-6 |
| GET | `/api/impact/decision` | any | M-7 … M-13 |
| GET | `/api/impact/method` | any | **M-14 … M-17 — the reviewer's block** |
| GET | `/api/impact/gaps` | any | **T3 metrics with formula and missing input** |

`/api/impact/gaps` is an endpoint that returns what the system *cannot* measure. Unusual, and deliberate: it makes the honesty machine-readable rather than a UI flourish, so it cannot be quietly dropped from an export.

### 5.7 `/api/suppliers` — WS-8

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/api/suppliers/{id}/scorecard` | any | Reliability, lateness variance, history |
| GET | `/api/suppliers/compare/{product_id}` | any | Ranked options from `supplier_products` |
| GET | `/api/suppliers/{id}/products` | any | Catalog |
| POST | `/api/purchase-orders/{id}/acknowledge` | staff+ | **Reaches `POStatus.acknowledged`** (§5 #3) |
| POST | `/api/purchase-orders/{id}/receive` | **staff** | Partial + backdated receipt (BW-6) |

The receive endpoint is new rather than a change to `inventory.py`, which keeps the frozen router frozen while fixing the two defects behind a new contract.

### 5.8 `/api/simulation` — WS-9

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/api/simulation/scenarios` | any | Available scenarios |
| POST | `/api/simulation/load/{key}` | manager | Load deterministically |
| POST | `/api/simulation/clock` | manager | Set or advance the offset (AD-9) |
| GET | `/api/simulation/clock` | any | Current effective time |
| POST | `/api/simulation/backtest` | manager | 90-day replay, **no LLM** |
| GET | `/api/simulation/backtest/{id}` | any | Results |

---

## 6. Frozen endpoints

Nobody edits these. Listed so the boundary is unambiguous.

| Router | Rule |
|---|---|
| `auth.py` — `/api/auth/*` | **Frozen.** Login, token, current user |
| `inventory.py` — products, stock, movements, POs, alerts | **Frozen.** New behaviour goes in new routers |

If a new capability appears to require editing a frozen router, that is a design error in the new capability. The escape hatch is a new endpoint in a new module, not an edit.

---

## 7. Response conventions

Uniform across every new endpoint, so six UI workstreams can build without coordinating.

| Convention | Rule |
|---|---|
| References | `signal_ref`, `decision_ref`, `approval_ref`, `run_ref` are the public identifiers. Integer PKs never appear in a URL |
| Provenance | Every LLM-authored string field is named `*_narrative` or `*_rationale`. The UI marks these **◈**; nothing else is marked |
| Numbers | Every computed number ships with `basis` — the formula and its inputs — so the UI can show the arithmetic |
| Citations | `{ text, section, source }`. Never a bare string |
| Tier | Every metric carries `tier` and `data_disclosure` |
| Nullability | `narrative: null` is **valid and expected**. Clients must render the LLM-unavailable state, not an error |
| Time | ISO-8601 UTC, always from `clock.now()` |
| Errors | `{ error: { code, message, detail } }`. Refusals are **200 with a refusal body**, not 4xx — a refusal is an outcome |
| Money | Float rupees, formatted at the edge. Tabular numerals in the UI |

Two of these carry real weight. **Naming LLM-authored fields by convention** means the UI's provenance marking is mechanical rather than per-field judgment — a new field is marked correctly by construction. And **refusals as 200** encodes C6's central claim in the transport: a decision not to act is a decision, and an HTTP error would classify it as a failure.

---

## 8. RBAC

Enforced at the endpoint, not in the UI.

| Role | May | May not |
|---|---|---|
| `staff` | Receive goods, acknowledge POs, view everything | Approve, change policy, engage kill switch, load scenarios |
| `manager` | Everything | — |
| `agent` | Detect, decide, execute **within policy** | **Approve its own decision**, change policy, alter autonomy, set the clock |

The `agent` row's first prohibition is the one that matters. Without it the approval mechanism is decoration. It is enforced by the approval service requiring `actor_type = human` **and** `role = manager` on `decided_by_user_id` — not by omitting a UI button.

`User.role` is `String(50), default="staff"` (`models.py:185`), so adding the `agent` role is a **data change, not a schema change.**

---

## 9. Seed and simulation data

C8's requirements. All additive; the existing seeder's ledger invariant `sum(stock_movements.quantity) == quantity_on_hand` must continue to hold, verified by its existing `verify(db)`.

| Requirement | Detail |
|---|---|
| 90-day backfill | Explicit `recorded_at` per movement — §4. Weekday/weekend shape |
| Per-product profiles | Distinct velocity and variance so detection has signal |
| Deliberate insufficiency | ≥2 products with almost no sales, to make BW-5 real |
| Supplier variance | One reliable, one drifting, one cheap-but-late — so scoring discriminates |
| Multi-supplier coverage | ≥2 `supplier_products` rows for demo SKUs |
| An overdue PO | `expected_delivery` in the past, no receipt |
| A partial receipt | `quantity_received < quantity_ordered` |
| Config drift | ≥1 product whose stored `reorder_point` contradicts §3's formula |
| Drifted `reorder_quantity` | `products.reorder_quantity` (default 50) is also unaudited — C10 should check both |
| Named scenarios | D1–D4, each with `expected_signals` |

`products.reorder_quantity` is worth calling out: it is a *second* stored configuration value that nothing re-derives, sitting beside `reorder_point`. C10's audit should cover both, which roughly doubles that capability's surface for no additional mechanism.

---

## 10. RAG changes

**AD-13.** `src/rag/data/inventory_manual.md` is **not modified.**

| Collection | Contents | Status |
|---|---|---|
| Graded | `inventory_manual.md`, 600-char chunks, `k=4` | **Byte-identical. Do not touch** |
| **Policy (new)** | Policy documents with **section-level metadata** | New — C4 |

The graded assertions are `len(chunks) >= 20` (`tests/phase2/test_phase2.py:44`) and `len(c.page_content) <= 600` (`:33`) — looser than a fixed count, so the manual *could* be extended safely. AD-13 stands anyway on citation-quality grounds: the policy engine needs `{ text, section, source }` per chunk to quote §10 line 113 with a section reference, and retrofitting that metadata onto the graded collection would mean re-ingesting it. **A separate collection is cheaper and carries zero test risk.**

---

## 11. What is deliberately not added

| Not added | Why |
|---|---|
| Alembic | The additive design removes the need; adding migrations across parallel streams invites schema churn |
| Any column on any existing table | AD-3 |
| Any member on any existing enum | §1.1 — CHECK constraint |
| A customer-order entity | Would make M-25 computable, but it is a whole new domain with no grounding in the manual |
| `unit_margin` as a stored column | Derivable as `unit_price − cost_price`. Storing it invites drift |
| Notification tables | Outbound integration rejected in [04-OPPORTUNITY-SPACE.md](04-OPPORTUNITY-SPACE.md) §8.4 |
| Multi-warehouse | Rejected — complexity multiplier, no agency demonstrated |
| A second frontend | One is being rebuilt |

---

## 12. Open items for implementation

Flagged rather than buried, with a recommendation for each.

1. **Approval SLA duration.** §10 item 3's 24 hours governs *raising* a PO, not *approving* one. Reusing it for approval ageing is an **inference and must be labelled as one** — not cited as manual policy. Recommendation: default 24h, configurable, UI copy reads "internal target", never "policy".
2. **Sufficiency thresholds.** `min_sale_events = 10`, `min_history_days = 30`. Judgment calls, not derived. Stored in `autonomy_policies` and **displayed**, so the product says so rather than implying derivation.
3. **`ordering_cost` and `holding_cost_per_unit`.** Not in the manual; needed for EOQ (§9 line 98). Configured assumptions, labelled wherever EOQ appears.
4. **`drift_tolerance_pct = 20`.** Same category. Configurable and displayed.
5. **Checkpoint database location.** Separate SQLite file from the business DB, so a checkpoint reset never risks business data.

Items 1–4 share a shape: **a number the manual does not supply.** The rule for all of them is the same and it is the package's rule — put it in configuration, show it in the UI, and never let it look derived.

---

**Next:** [13-DEMO-SCENARIOS.md](13-DEMO-SCENARIOS.md) specifies the four demo scenarios, their seed states, and the click paths that exercise them.
