# 15 — Shared Contracts

> **Status:** Proposal. Nothing here is approved.
> **Purpose:** The frozen interface between workstreams. Every cross-stream signature, vocabulary, and invariant, in one place.
> **Audience:** Every Claude Code instance, before it writes a line.

---

## 1. What "frozen" means

This file is published by **WS-0 in Wave 0** and does not change afterwards. Every other workstream builds against it and stubs what it does not own.

| | |
|---|---|
| **Who may edit** | WS-0, during Wave 0 only. After that, integration only |
| **Who may read** | Everyone. First thing, every stream |
| **What happens on a violation** | The consuming stream's integration fails. The producing stream is at fault |
| **What happens if a signature is wrong** | It is changed **once**, by integration, and every affected stream is told. This is expensive — hence Wave 0 is solo and gated |

**The rule that makes this work:** a signature in this file is a promise about *name, arguments, return type, and failure behaviour*. It is not a promise about implementation. WS-3 can be written, tested, and finished before WS-1 exists, because WS-3 depends on this document rather than on WS-1's code.

**The rule that makes it fail:** a stream that "improves" a signature it publishes. If `derive_reorder_point` gains a keyword argument in Wave 2, three streams' stubs are now wrong and nobody finds out until integration. **Publish, then live with it.**

---

## 2. Core primitives — `src/core/`, owned by WS-0

### 2.1 The clock — `src/core/clock.py`

```python
def now() -> datetime:
    """The only source of current time in the system.
    Returns real wall-clock time plus the active simulation offset.
    """

def today() -> date: ...
def offset_days() -> int: ...
def set_offset(days: int) -> None: ...   # simulation only, DEMO_MODE gated
def reset() -> None: ...
```

**Absolute prohibition, every stream, no exceptions:**

```python
datetime.now()      # FORBIDDEN
datetime.utcnow()   # FORBIDDEN
date.today()        # FORBIDDEN
time.time()         # FORBIDDEN
```

Grep-enforced in CI across `src/`. Two existing violations are pre-authorised for repair by their owners: `inventory_service.py:137` (WS-9) and any `server_default=func.now()` on a **new** table (WS-0 must not write one).

**Why this is rule number one.** The current database has thirteen stock movements whose `recorded_at` values all fall on 2026-08-23, between 08:50 and 15:56 — because `server_default=func.now()` was evaluated by SQLite at insert time and the seeder never overrode it. Ninety days of intended history collapsed into seven hours. Every demand calculation in the product is downstream of that mistake not recurring.

### 2.2 IDs — `src/core/ids.py`

```python
def next_id(prefix: str, width: int = 6) -> str:
    """Concurrency-safe sequential ID. Locks the counter row."""
```

| Entity | Format | Example |
|---|---|---|
| Signal | `SIG-` + 6 digits | `SIG-000045` |
| Decision | `DEC-` + 6 digits | `DEC-000123` |
| Approval | `APR-` + 6 digits | `APR-000012` |
| Agent run | `RUN-` + 6 digits | `RUN-000078` |
| Purchase order | `PO-YYYY-NNNN` | `PO-2026-0042` |

The PO format is **existing and must be matched exactly** — `PO-2026-0001` through `PO-2026-0004` are already in the database, and the graded Phase 1 tests read POs back.

`next_id` must be safe under concurrent callers (AD-15). WS-3 and WS-9 will both call it, and a scheduled run overlapping a manual one is the normal case, not the edge case.

### 2.3 Events — `src/core/events.py`

Synchronous, in-process, ordered. No broker.

```python
def emit(event_type: str, payload: dict) -> None: ...
def subscribe(event_type: str, handler: Callable[[dict], None]) -> None: ...
```

| Event | Emitted by | Payload keys |
|---|---|---|
| `stock.movement_recorded` | WS-9 | `product_id`, `movement_type`, `quantity`, `recorded_at` |
| `stock.level_changed` | WS-9 | `product_id`, `quantity_on_hand`, `previous` |
| `po.received` | WS-9 | `po_id`, `po_number`, `received_at`, `days_late` |
| `signal.raised` | WS-3 | `signal_id`, `signal_type`, `product_id`, `severity` |
| `signal.resolved` | WS-3 | `signal_id`, `resolution` |
| `decision.created` | WS-4 | `decision_id`, `signal_id`, `action_type` |
| `decision.pending_approval` | WS-4 | `decision_id`, `approval_id`, `escalation_reason` |
| `decision.executed` | WS-9 | `decision_id`, `execution_ref` |
| `decision.refused` | WS-4 | `decision_id`, `reason` |
| `clock.advanced` | WS-2 | `from_offset`, `to_offset` |

**Handlers must not raise.** A subscriber that throws inside a synchronous bus takes down the emitter's transaction. Every handler wraps its body and logs. This is a contract, not a suggestion — WS-3 subscribes to WS-9's events, and a signal-detection bug must not roll back a goods receipt.

### 2.4 Vocabularies — `src/core/vocab.py`

Frozen string constants. **Never `enum.Enum` on a new column** (§4.1).

```python
SIGNAL_TYPES = (
    "threshold_breach", "projected_breach", "po_overdue",
    "config_drift", "supplier_drift", "capital_drag", "data_insufficient",
)

SEVERITIES = ("critical", "high", "medium", "low")

DECISION_STATUS = (
    "proposed", "policy_checked", "auto_approved", "pending_approval",
    "approved", "rejected", "countered", "executing", "executed",
    "failed", "expired", "insufficient_data",
)

AUTONOMY_MODES = ("off", "shadow", "assisted", "autonomous")

ACTION_TYPES = (
    "raise_po", "adjust_reorder_point", "adjust_reorder_quantity",
    "switch_supplier", "consolidate_po", "expedite_po", "no_action",
)

ESCALATION_REASONS = (
    "value_threshold", "insufficient_evidence", "non_cheapest_supplier",
    "config_change", "blast_radius", "policy_off", "kill_switch",
)

SUFFICIENCY = ("sufficient", "thin", "insufficient", "none")

PROVENANCE = ("computed", "retrieved", "generated")

DATA_DISCLOSURE = ("synthetic", "mixed", "real")

METRIC_TIERS = ("T1", "T2", "T3")
```

### 2.5 The projection to the graded vocabulary

`DECISION_STATUS` has twelve values. The graded Phase 5 tests assert `analysis_status ∈ {complete, reorder_required, healthy, analyzing}`. Both must hold simultaneously, so the projection is a contract, owned by WS-0, consumed by WS-8:

```python
def project_analysis_status(decision_status: str, action_type: str) -> str:
    """Map the 12-value internal vocabulary onto the 4 graded values."""
```

| Internal status | Graded `analysis_status` |
|---|---|
| `proposed`, `policy_checked`, `executing` | `analyzing` |
| `pending_approval`, `approved`, `auto_approved`, `executed` where action ≠ `no_action` | `reorder_required` |
| `executed` where action = `no_action` | `healthy` |
| `rejected`, `expired`, `failed`, `countered` | `complete` |
| `insufficient_data` | `complete` |

Two things worth being explicit about. `insufficient_data` maps to `complete` because the *analysis* did complete — it completed with a refusal, which is a result. And this projection is a **display and compatibility mapping only**; nothing in the system branches on `analysis_status`. All internal logic reads the twelve-value column. Collapsing a refusal and a rejection into one graded label loses information, which is precisely why the internal vocabulary is not the graded one.

### 2.6 Errors — `src/core/errors.py`

```python
class StewardError(Exception): ...
class InsufficientData(StewardError):
    def __init__(self, what: str, needed: str, have: str): ...
class PolicyDenied(StewardError):
    def __init__(self, rule: str, citation: str | None): ...
class PreconditionFailed(StewardError):
    def __init__(self, precondition: str, detail: str): ...
class ExecutionFailed(StewardError): ...
```

`InsufficientData` is required to name **what** was missing, **what** was needed, and **what** was actually available. A refusal that cannot say "I needed 14 sale events across 30 days; I have 0" is not a demonstration of judgment — and D4's entire value is in that sentence.

---

## 3. The eight new tables

Column contracts only; full DDL is in [12-DATA-AND-API-CHANGES.md](12-DATA-AND-API-CHANGES.md). Every table below is a **new** table in a **new** module, so `Base.metadata.create_all` creates it additively without a migration (AD-3).

| Table | Module | Owner | Written by |
|---|---|---|---|
| `signals` | `models_analytics.py` | WS-0 | WS-3 |
| `decisions` | `models_governance.py` | WS-0 | WS-4, WS-8 |
| `approvals` | `models_governance.py` | WS-0 | WS-4 |
| `autonomy_policies` | `models_governance.py` | WS-0 | WS-5 |
| `supplier_products` | `models_sourcing.py` | WS-0 | WS-2 (seed), WS-7 |
| `agent_runs` | `models_analytics.py` | WS-0 | WS-8, WS-10 |
| `metric_snapshots` | `models_analytics.py` | WS-0 | WS-17 |
| `demo_scenarios` | `models_simulation.py` | WS-0 | WS-2 |

**"Owner" is WS-0 for every one.** Streams write *rows*, never *columns*. A stream that needs a column files an integration request; a stream that adds one has silently changed a table three others read.

### 3.1 `signals` — the columns other streams read

```python
signal_id: str          # SIG-000045, unique
signal_type: str        # ∈ SIGNAL_TYPES
severity: str           # ∈ SEVERITIES
product_id: int | None  # FK products.id
supplier_id: int | None
po_id: int | None
raised_at: datetime     # clock.now()
detected_from: str      # human-readable: "projected stockout in 4 days"
evidence: str           # JSON: the inputs, the arithmetic, the citation
sufficiency: str        # ∈ SUFFICIENCY
dedup_key: str          # indexed. Suppresses re-raise
status: str             # open | superseded | resolved | expired
resolution: str | None
```

`evidence` is JSON text, not prose. It must contain enough for the UI to render the arithmetic without recomputing it, because the Control Tower renders signals raised by a run that finished eight hours ago and the inputs have since moved.

### 3.2 `decisions` — the ledger

```python
decision_id: str            # DEC-000123, unique
signal_id: str | None
run_id: str | None          # RUN-000078
action_type: str            # ∈ ACTION_TYPES
status: str                 # ∈ DECISION_STATUS
actor: str                  # "agent:replenishment" | "user:3" | "system"
proposed_at: datetime
decided_at: datetime | None
executed_at: datetime | None
inputs: str                 # JSON. Every value that fed the decision
computation: str            # JSON. The arithmetic, step by step
policy_citation: str | None # the manual sentence, verbatim
escalation_reason: str | None   # ∈ ESCALATION_REASONS
system_objection: str | None    # populated when a human overrode
autonomy_mode: str          # ∈ AUTONOMY_MODES, as of decision time
execution_ref: str | None   # e.g. PO-2026-0042
reversal_of: str | None
provenance: str             # JSON: field → ∈ PROVENANCE
```

Three columns carry the product's differentiation and must never be left null when applicable:

- **`policy_citation`** — the verbatim manual sentence. M-12 should read 100%; anything less is a defect.
- **`system_objection`** — written when a human's counter-proposal is worse than the system's. A ledger in which the system never disagreed is a ledger of a system nobody was governing.
- **`provenance`** — per-field origin. This is what makes M-14 ("five fabricated numeric fields → zero") checkable rather than asserted.

### 3.3 `approvals`

```python
approval_id: str        # APR-000012
decision_id: str
requested_at: datetime
requested_from_role: str    # "manager"
decided_by_user_id: int | None
decided_at: datetime | None
outcome: str | None     # approved | rejected | countered | expired
counter_payload: str | None  # JSON: the human's alternative
rationale: str | None
expires_at: datetime
sla_breached: bool
```

---

## 4. Existing-schema facts every stream must know

These are verified properties of the current database that will break code written without them. They are in the contract file because each one has already cost time.

### 4.1 SQLAlchemy `Enum` on SQLite cannot gain members

The three existing enums render as `VARCHAR` plus a `CHECK` constraint:

| Enum | Members | Consequence |
|---|---|---|
| `Category` | `grocery`, `electronics`, `clothing`, `household`, `personal_care` | No sixth category, ever |
| `MovementType` | `receipt`, `sale`, `adjustment`, `transfer`, `returnm` | No sixth movement type |
| `POStatus` | `draft`, `submitted`, `acknowledged`, `received`, `cancelled` | **No sixth PO status.** No `partially_received` |

With no Alembic and `create_all` being additive at *table* granularity only, an existing table's CHECK constraint is immovable. Hence: **every status-like column on every new table is `String`.**

This is why partial receipt is a derived predicate rather than a status (WS-9):

```python
is_partially_received = (
    po.status in ("submitted", "acknowledged")
    and any(0 < (i.quantity_received or 0) < i.quantity_ordered for i in po.items)
)
```

The predicate is better than the status would have been — it carries the quantities, not just a label.

### 4.2 `MovementType.returnm` — the name/value trap

```python
MovementType.returnm.value == "return"     # the Python value
# but the database column contains "returnm"
```

SQLAlchemy's `Enum` persists the member **name**, not its value. The current database contains a movement row with `movement_type = "returnm"`. Any stream filtering movements by raw string must use the name. WS-1 will hit this first, computing demand.

### 4.3 Inventory is valued at `cost_price`

`products` carries both `unit_price` (selling) and `cost_price` (purchase), both non-null. Every capital and valuation figure uses `cost_price`.

Verified against the existing data, four ways — every PO total equals `Σ quantity × cost_price`:

| PO | Arithmetic | Total |
|---|---|---|
| `PO-2026-0001` | 50 × ₹600 | ₹30,000 |
| `PO-2026-0002` | 10 × ₹22,000 | ₹220,000 |
| `PO-2026-0003` | 15 × ₹41,000 | ₹615,000 |
| `PO-2026-0004` | 120 × ₹90 | ₹10,800 |

Using `unit_price` instead would inflate every capital figure by the full margin — invisible on a slide, fatal in review.

### 4.4 `users` has exactly one row

`admin@retail.com`, role `manager`. `users.role` is `String(50)` at `models.py:184`, so **new roles are a seed concern, not a schema concern.** WS-2 seeds a `staff` user; without it, M-34's RBAC 403 cannot be demonstrated and AD-12's least-privilege agent identity has no second subject.

### 4.5 Zero of five products have a computable daily demand

| Product | Sale events | Distinct days |
|---|---|---|
| Rice | 3 | **1** |
| Headphones | 0 | 0 |
| TV | 0 | 0 |
| Detergent | 0 | 0 |
| Colgate | 0 | 0 |

Every consumer of demand must handle `insufficient` as the **normal** case, not the edge case. WS-1's `compute_daily_demand` returns a verdict, never a bare float, and `0.0` is never returned for "no data" (§5.1).

---

## 5. Analytics — published by WS-1, consumed by WS-3, 7, 8, 15, 17

### 5.1 The return shape, which is the whole contract

```python
@dataclass(frozen=True)
class Computed:
    value: float | None
    sufficiency: str          # ∈ SUFFICIENCY
    inputs: dict              # every input that produced value
    formula: str              # "(demand × lead_time) + (demand × safety_days)"
    citation: str | None      # "manual §3 line 35"
    sample_size: int
    span_days: int
```

**`value is None` whenever `sufficiency == "insufficient"` or `"none"`.** Not `0.0`. This single rule is what makes D4's refusal possible and what prevents the system from ordering nothing for an out-of-stock product because "demand is zero".

### 5.2 The functions

```python
def compute_daily_demand(db, product_id: int, window_days: int = 30) -> Computed: ...
def derive_reorder_point(db, product_id: int, *, use_measured_lead_time: bool = False) -> Computed: ...
def compute_eoq(db, product_id: int, ordering_cost: float, holding_rate: float) -> Computed: ...
def score_sufficiency(db, product_id: int) -> Computed: ...
def measured_lead_time(db, supplier_id: int) -> Computed: ...
def inventory_value(db, *, scope: str = "global", scope_id: int | None = None) -> Computed: ...
def days_on_hand(db, product_id: int) -> Computed: ...
def stock_turn(db, window_days: int = 90) -> Computed: ...
```

### 5.3 The two assertions that define correctness

Taken verbatim from the customer's manual, and the cheapest high-value tests in the build:

```python
# manual §3 line 35 — reorder point worked example
assert (10 * 5) + (10 * 2) == 70

# manual §9 line 102 — order quantity worked example
assert (5 * 7) + (5 * 14) == 105
```

`derive_reorder_point` must reproduce the first given those inputs. If it does not, the arithmetic disagrees with the client's own document and every number in the product is wrong in the same direction.

### 5.4 Sufficiency thresholds — frozen, because two streams branch on them

| Verdict | Condition |
|---|---|
| `sufficient` | ≥ 14 sale events across ≥ 21 distinct days |
| `thin` | ≥ 5 sale events across ≥ 7 distinct days |
| `insufficient` | ≥ 1 sale event, below `thin` |
| `none` | 0 sale events |

`thin` produces a value **and** forces escalation (WS-5 rule 5). `insufficient` and `none` produce no value at all.

Rice today: 3 events, 1 distinct day → `insufficient`. Every other product → `none`. These thresholds are a judgment call, stated here so it is one judgment rather than four.

---

## 6. Signals — published by WS-3

```python
def run_detectors(db, *, product_ids: list[int] | None = None) -> list[Signal]: ...
def dedup_key_for(signal_type: str, product_id: int | None, supplier_id: int | None) -> str: ...
```

Each detector, same shape, one module each:

```python
def detect(db, product_id: int) -> Signal | None: ...
```

| Detector | Fires when | Verified baseline |
|---|---|---|
| `threshold_breach` | `on_hand <= reorder_point` | 3 alerts exist today |
| `projected_breach` | projected on-hand < 0 within lead time + safety | **Zero — impossible today** |
| `po_overdue` | `clock.now() > expected_delivery` and not received | **Zero.** A 2-day-late PO went unnoticed |
| `config_drift` | `abs(stored_rop − derived_rop)` beyond tolerance | **Zero — no re-derivation exists** |
| `supplier_drift` | measured lead time > contract lead time | **Zero** |
| `capital_drag` | `on_hand` far above requirement, or no movement ≥30 days | **Zero** |
| `data_insufficient` | sufficiency ∈ {`insufficient`, `none`} on a stocked SKU | **Zero** |

Six of seven have a verified baseline of zero. That is the impact claim in file 10 §2.1 (M-4) and it is structural, not aspirational — no code path exists today that could produce any of them.

---

## 7. Policy — published by WS-5, consumed by WS-8

```python
@dataclass(frozen=True)
class PolicyVerdict:
    allowed: bool
    requires_approval: bool
    matched_rule: str            # "R4: value_threshold"
    escalation_reason: str | None
    citation: str | None
    blast_radius: int
    explanation: str

def evaluate(db, context: DecisionContext) -> PolicyVerdict: ...
```

```python
@dataclass(frozen=True)
class DecisionContext:
    action_type: str
    product_id: int | None
    supplier_id: int | None
    quantity: int | None
    value_inr: float | None
    sufficiency: str
    is_cheapest_supplier: bool | None
    affected_product_count: int
    autonomy_mode: str
```

**Rules are evaluated in order; first match wins.** The order *is* the semantics — a policy you cannot predict by reading top to bottom is not a governance control. WS-5 may not reorder them.

The boundary to get exactly right: **₹50,001 requires approval, ₹49,999 does not.** The threshold is quoted from the manual (§10 line 113, *"above ₹50,000"*), so an off-by-one is a governance failure rather than a rounding issue.

---

## 8. Governance — published by WS-4

```python
def create_decision(db, *, signal_id, action_type, inputs: dict,
                    computation: dict, provenance: dict,
                    verdict: PolicyVerdict, run_id: str | None) -> Decision: ...

def request_approval(db, decision: Decision) -> Approval: ...
def approve(db, approval_id: str, user_id: int, rationale: str | None) -> Decision: ...
def reject(db, approval_id: str, user_id: int, rationale: str) -> Decision: ...
def counter(db, approval_id: str, user_id: int, payload: dict) -> CounterResult: ...
def record_refusal(db, *, signal_id, reason: str, needed: str, have: str) -> Decision: ...
```

```python
@dataclass(frozen=True)
class CounterResult:
    decision: Decision
    recomputed: dict
    system_objection: str | None   # non-null when the human's number is worse
    accepted: bool
```

`counter` **must** recompute against the human's numbers and populate `system_objection` when the outcome is worse. A `/counter` that silently accepts produces a ledger of a system nobody ever disagreed with — and the demo's strongest governance moment is the system losing the argument on the record.

**`reject` requires a rationale. `approve` does not.** Deliberate asymmetry: a rejection is the signal that the system's calibration is wrong, and it is the only free training data in the product.

---

## 9. Execution — published by WS-9

```python
@dataclass(frozen=True)
class ExecutionResult:
    ok: bool
    execution_ref: str | None    # PO-2026-0042
    failed_precondition: str | None
    detail: str

def execute_decision(db, decision: Decision) -> ExecutionResult: ...
def check_preconditions(db, decision: Decision) -> list[str]: ...  # [] means clear
```

The seven preconditions, **re-checked at execution time even if checked at proposal time.** A durable interrupt means an approval can arrive hours after the proposal, by which point any of them may have flipped:

| # | Precondition |
|---|---|
| 1 | Kill switch is off |
| 2 | Autonomy mode still permits this action |
| 3 | No open PO already covers this SKU |
| 4 | Supplier is still `active` |
| 5 | Stock position has not already resolved the need |
| 6 | The idempotency key has not been used |
| 7 | Value still within the authorised band |

Precondition 5 is the one that matters most in a demo: a manager approves at 09:14 a replenishment proposed at 08:00, and in between a delivery arrived. A system that orders anyway has a governance surface but no judgment.

**Invariant WS-9 must hold on every write:** `sum(stock_movements.quantity) == stock_levels.quantity_on_hand` per product (M-16). The existing seeder's `verify(db)` already checks this; the agent's writes must not be the first thing to break it.

---

## 10. Sourcing — published by WS-7

```python
@dataclass(frozen=True)
class SupplierChoice:
    supplier_id: int
    unit_price: float
    lead_time_days: int
    is_cheapest: bool
    rejected_alternatives: list[dict]
    rationale: str

def select_supplier(db, product_id: int, quantity: int) -> SupplierChoice: ...

@dataclass(frozen=True)
class Scorecard:
    supplier_id: int
    on_time_rate: float | None      # None when sample_size == 0
    sample_size: int                # ALWAYS rendered beside the rate
    avg_days_late: float | None
    contract_lead_time: int
    measured_lead_time: float | None
    drift_days: float | None

def scorecard(db, supplier_id: int) -> Scorecard: ...
```

**`sample_size` is not optional and not decorative.** The database contains exactly one completed PO. A scorecard showing "80% on-time" from one observation is fabrication with a progress bar. `on_time_rate` is `None` at `sample_size == 0`, and the UI renders the sample size at the same visual weight as the rate.

`rejected_alternatives` exists so the ledger can show what was *not* chosen. A recommendation without the discarded options is unauditable.

---

## 11. Pipeline — published by WS-8

```python
def build_inventory_graph(): ...                    # graded — see below
def run_pipeline(trigger: str, *, product_ids=None, run_id=None) -> RunResult: ...
def resume_pipeline(run_id: str, approval_outcome: dict) -> RunResult: ...
```

The `InventoryState` keys other streams read:

```python
class InventoryState(TypedDict):
    product_id: int
    messages: list                  # >= 4 on every path (graded)
    analysis_status: str            # ∈ 4 graded values only
    signal_id: str | None
    decision_id: str | None
    computed: dict                  # WS-1 Computed results, serialised
    verdict: dict | None            # WS-5 PolicyVerdict, serialised
    supplier_choice: dict | None    # WS-7 SupplierChoice, serialised
    execution: dict | None          # WS-9 ExecutionResult, serialised
    refusal: dict | None            # what was needed, what was available
```

**The five graded assertions WS-8 must not break:**

| Test | Assertion |
|---|---|
| `phase5/test_routing.py:37-42` | Four node names appear in `inspect.getsource(build_inventory_graph)` |
| `phase5/test_routing.py:45-48` | `"demand_forecaster"` present **and** an entry-point call |
| `phase5/test_e2e.py:78` | `len(result["messages"]) >= 4` |
| `phase5/test_e2e.py:102` | `analysis_status ∈ {complete, reorder_required, healthy, analyzing}` |
| `phase5/test_e2e.py:167` | `analysis_status ∈ {reorder_required, complete}` |

The entry-point assertion is source-inspection and technically gameable. It is not gamed: `demand_forecaster` is genuinely the entry point because deterministic computation genuinely runs first. On the refusal path the ≥4 messages are three real `demand_forecaster` steps plus the refusal — **no filler messages**, because a padded message list to satisfy a test is exactly the dishonesty the package claims to have removed.

---

## 12. HTTP conventions

Every stream's router follows these, so the UI's API client is written once.

### 12.1 The publication contract — the rule that keeps `main.py` safe

```python
# src/backend/routers/<name>.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/<name>", tags=["<name>"])
```

**Expose a module-level `router` and stop.** Do not import it anywhere. Do not touch `main.py`. Integration writes the import at `main.py:12` and the `include_router` call at `:177` in one pass.

Eight streams have a legitimate reason to add two lines to `main.py`. All eight are refused, because two of them adding those lines in parallel produces a file where one stream's router silently does not exist.

### 12.2 Response envelope

```json
{
  "data": {},
  "meta": {
    "computed_at": "2026-08-25T08:00:00",
    "clock_offset_days": 0,
    "provenance": { "recommended_qty": "computed", "narrative": "generated" },
    "data_disclosure": "synthetic"
  }
}
```

`meta.provenance` and `meta.data_disclosure` are **required on any response containing a business number.** They are what let the UI render provenance marks without guessing, and what stop a synthetic figure being exported stripped of its caveat.

### 12.3 Error envelope

```json
{
  "error": {
    "code": "insufficient_data",
    "message": "Cannot compute demand for SKU-PRC-0001",
    "needed": "14 sale events across 21 days",
    "have": "0 sale events",
    "citation": "manual §3 line 35"
  }
}
```

`needed` and `have` are required on `insufficient_data`. An error that says "cannot compute" is a failure; one that says "I needed 14 events across 21 days and have 0" is a finding.

### 12.4 Status codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 202 | Accepted — pipeline started, run_id returned |
| 400 | Malformed |
| 403 | **RBAC denial. Body names the required role** (M-34) |
| 409 | Precondition failed or idempotency replay |
| 422 | `insufficient_data` — a legitimate refusal, **not** a 500 |
| 429 | LLM quota exhausted. Body states the decision completed without narrative |

422 and 429 are the ones streams get wrong. A refusal is not a server error, and a quota exhaustion is not a failed decision — the numbers were computed before the LLM was ever asked (AD-2).

---

## 13. UI contracts — published by WS-6

### 13.1 Primitives — WS-6 owns these; WS-11/12/13/14 consume only

```jsx
<Card title elevation actions>
<Table columns rows emptyState loading />
<SeverityDot severity />          {/* shape + text label, never colour alone */}
<ProvenanceMark kind />           {/* "computed" | "retrieved" | "generated" */}
<EvidenceBlock inputs formula citation result />
<RefusalCard needed have suggestion />
<EmptyState reason formula missingInput />
<AuthorityBadge mode />
<ThreeDoorPanel onApprove onReject onCounter />   {/* equal visual weight */}
<MetricTile metric tier disclosure />
```

Two rules that would otherwise drift across four streams:

- **`<SeverityDot>` never encodes severity in colour alone.** Shape plus text label. A colour-only severity system is unreadable to roughly 8% of male viewers and unreadable in a projected slide deck.
- **`<ThreeDoorPanel>` gives approve, reject and counter identical visual weight.** Every UI convention in existence pushes toward one prominent primary button. A governance surface that nudges toward approval is not a governance surface.

A screen stream that needs a new primitive **requests it** and stubs locally. It does not add one — `components/` has one owner.

### 13.2 Query keys — frozen so caches invalidate correctly

```js
['signals', filters]
['signal', signalId]
['decisions', filters]
['decision', decisionId]
['approvals', 'pending']
['approval', approvalId]
['policies']
['impact']
['impact', 'gaps']
['supplier', supplierId, 'scorecard']
['tower']
```

Ad-hoc keys are the standard way three UI streams end up showing three different versions of the same approval queue. After an approval mutation, invalidate `['approvals','pending']`, `['decisions']`, and `['tower']`.

### 13.3 Required states on every screen

Four, all four, every screen: **loading**, **empty**, **error**, **refusal**. The fourth is unusual and it is the point — a refusal is a legitimate result with its own rendering (`<RefusalCard>`), not an error banner. WS-6 ships all four for every primitive so no screen stream has to invent one.

---

## 14. Metrics — published by WS-17

```python
@dataclass(frozen=True)
class MetricValue:
    key: str                  # "M-14"
    label: str
    value: float | None       # None for every T3 metric. Always.
    tier: str                 # ∈ METRIC_TIERS
    formula: str
    missing_input: str | None  # required and non-null when tier == "T3"
    data_disclosure: str      # ∈ DATA_DISCLOSURE
    window: str
    scope: str

def compute_all(db) -> list[MetricValue]: ...
def gaps(db) -> list[MetricValue]: ...   # T3 only, for "What we cannot measure yet"
```

**The single hardest-enforced rule in the contract: a T3 metric returns `value = None`, always, with `missing_input` populated.**

It will be tempting to return a number, because for M-23 the multiplication is arithmetically available — `products` carries both `unit_price` and `cost_price`, so unit margin is computable today. The blocker is not a missing field; it is that every sale in the database was generated by the seeder. A rupee figure derived from seeded sales is a statement about the seeder, not about a business.

**The fact that the multiplication is real does not make the answer true.** One invented figure compromises every honest number beside it, and the Impact screen's entire value is that a reviewer can check any figure on it.

---

## 15. Invariants CI enforces

Cheap greps and assertions, run on every stream's branch. Each one exists because a plausible, well-intentioned change would otherwise break something silently.

| # | Check | Guards |
|---|---|---|
| 1 | No `datetime.now()` / `date.today()` / `time.time()` in `src/` | The clock; the 90-day backfill |
| 2 | No `sqlalchemy.Enum` in `models_*.py` | The status cage (§4.1) |
| 3 | No `server_default=func.now()` on a new table | Timestamps the clock cannot see |
| 4 | All five graded phases green | The whole honesty claim |
| 5 | `git diff --name-only` ⊆ the stream's owned files | Silent cross-stream overwrites |
| 6 | No `main.py` diff outside integration | The eight-way collision |
| 7 | No new entry in `requirements.txt` / `package.json` outside WS-0 | Dependency drift |
| 8 | Every T3 metric returns `value is None` | The fabrication rule |
| 9 | Every `Computed` with `sufficiency ∈ {insufficient, none}` has `value is None` | Zero-demand false negatives |
| 10 | `sum(movements) == quantity_on_hand` after every execution test | M-16 |

Checks 5 and 6 are the parallel-execution guards, and they are mechanical for a reason. In a build with seven concurrent instances, **a helpful edit to a file you do not own is indistinguishable from a bug.** The check finds it in seconds; integration would find it in hours.

---

**Next:** [16-DEPENDENCY-GRAPH.md](16-DEPENDENCY-GRAPH.md) shows what blocks what, and where the critical path actually runs.
