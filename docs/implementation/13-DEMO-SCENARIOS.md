# 13 — Demo Scenarios

> **Status:** Proposal. Nothing here is approved.
> **Purpose:** Specify the four demo scenarios as reproducible engineering artifacts — seed state, clock position, expected signals, click path, and the claim each one proves.
> **Governing constraint (verbatim from the brief):** *"Do not limit the product because the final presentation is only 4–5 minutes. We can build a substantially larger system and showcase the strongest workflows."*

---

## 1. A demo scenario is a fixture, not a script

The distinction matters because it determines what gets built.

| A demo script | A demo fixture |
|---|---|
| A sequence of clicks the presenter memorises | A named database state, restorable in one action |
| Breaks when the data drifts | Reproducible on any machine, any number of times |
| Cannot be tested | **Is a test.** Seed → run → assert the expected signals appeared |
| Lives in a slide deck | Lives in `demo_scenarios`, exercised by CI |

Every scenario below is specified as a row in `demo_scenarios` (file 12 §2.8) with a `seed_spec`, a `clock_offset_days`, and an `expected_signals` list. That last field is what turns a demo into an integration test: **if seeding scenario D1 and running the pipeline does not produce exactly the signals named in `expected_signals`, the build is broken.** The presenter is never the person who discovers this.

This is also the answer to the most common demo failure mode in a room of near-identical POCs: the presenter clicks something, the state is wrong, and thirty seconds evaporate. A one-click reset to a known-good state removes that failure mode entirely.

---

## 2. The verified current seed state

> **VERIFIED 2026-08-25** against `inventory.db`. Every figure in this section is read from the database, not inferred.

Everything in this document is built on top of what is actually there, so it is worth setting down precisely.

### 2.1 Products

| id | SKU | Name | Category | `unit_price` | `cost_price` | ROP | ROQ | Supplier | On hand |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `SKU-GRO-0001` | Organic Basmati Rice 10kg | grocery | ₹850 | ₹600 | 15 | 60 | 4 | **167** |
| 2 | `SKU-ELC-0001` | Sony WH-1000XM5 Headphones | electronics | ₹29,990 | ₹22,000 | 10 | 25 | 2 | **4** |
| 3 | `SKU-ELC-0002` | Samsung 55" 4K QLED TV | electronics | ₹54,990 | ₹41,000 | 5 | 15 | 2 | **0** |
| 4 | `SKU-HHD-0001` | Ariel Matic Detergent 2L | household | ₹450 | ₹310 | 20 | 100 | 1 | **50** |
| 5 | `SKU-PRC-0001` | Colgate Total 150g | personal_care | ₹130 | ₹90 | 30 | 120 | 3 | **0** |

### 2.2 Suppliers

| id | Name | Code | Contract `lead_time_days` | Payment terms | Active |
|---|---|---|---|---|---|
| 1 | Reliable Wholesale Ltd | `SUP-0001` | 7 | 30 | ✓ |
| 2 | Apex Logistics & Supplies | `SUP-0002` | **3** | 15 | ✓ |
| 3 | Metro Goods Distribution | `SUP-0003` | **10** | 45 | ✓ |
| 4 | Global Logistics Corp | `SUP-0005` | 5 | 45 | ✓ |

### 2.3 Purchase orders — the most informative table in the database

| PO | Supplier | Status | Total | Ordered | Expected | Received | Item |
|---|---|---|---|---|---|---|---|
| `PO-2026-0001` | 4 | `received` | ₹30,000 | 08-14 | 08-21 | **08-23** | 50 × Rice @ ₹600 |
| `PO-2026-0002` | 2 | **`draft`** | ₹220,000 | 08-22 | 08-28 | — | 10 × Headphones @ ₹22,000 |
| `PO-2026-0003` | 2 | `submitted` | ₹615,000 | 08-22 | 08-29 | — | 15 × TV @ ₹41,000 |
| `PO-2026-0004` | 3 | **`draft`** | ₹10,800 | 08-23 | 09-02 | — | 120 × Colgate @ ₹90 |

Four findings fall straight out of this table, and **none of them is visible anywhere in the current product**:

1. **`PO-2026-0001` is late twice over.** Supplier 4's contract lead time is 5 days. The PO was raised 08-14 with an expected delivery of 08-21 — that promise is already **7 days**, two days beyond the contract. It actually arrived 08-23: **9 days**, four days beyond contract and two beyond the promise. Two distinct drifts, one PO, nobody looking.
2. **PO totals are computed at `cost_price`.** ₹615,000 = 15 × ₹41,000; ₹10,800 = 120 × ₹90; ₹220,000 = 10 × ₹22,000; ₹30,000 = 50 × ₹600. All four reconcile exactly. This confirms the valuation convention in [10-IMPACT-METRICS.md](10-IMPACT-METRICS.md) §2.4 — inventory and orders are valued at cost, not at retail.
3. **Two draft POs have been sitting unsubmitted since 08-22 and 08-23.** Nothing in the codebase transitions a PO out of `draft` (metric M-17: three of five PO statuses are unreachable). A draft PO reserves nothing, orders nothing, and tells nobody. It is a note to self that looks like an action.
4. **All three unresolved stock alerts correspond to products that appear to be "handled".** Headphones → draft PO. TV → submitted PO. Colgate → draft PO. There is no link between `stock_alerts` and `purchase_orders`, so an operator reading the alert list has no way to know that one of the three is genuinely in flight and two are stuck. **The alert list overstates the problem count and understates the problem.**

### 2.4 Alerts and users

| Alert | Product | Type | Resolved |
|---|---|---|---|
| 1 | 2 — Headphones | `low_stock` | ✗ |
| 2 | 3 — TV | `out_of_stock` | ✗ |
| 3 | 5 — Colgate | `out_of_stock` | ✗ |

**`users` contains exactly one row:** `admin@retail.com`, role `manager`. There is no staff user and no agent user. Both are required — the RBAC demonstration (M-34) needs a staff account to be refused, and AD-12's least-privilege agent identity needs `agent@retail.com`. This is a **seed requirement, not a schema change**: `users.role` is `String(50)` (`models.py:184`), so adding an `agent` role costs zero migrations.

### 2.5 Movement history — the constraint that shapes every scenario

Thirteen movements exist. All thirteen carry a `recorded_at` inside a single calendar day (2026-08-23, between 08:50:18 and 15:56:44).

| Product | Movements | Of which sales |
|---|---|---|
| 1 — Rice | 10 | **3** |
| 2 — Headphones | 1 (receipt) | 0 |
| 3 — TV | 0 | 0 |
| 4 — Detergent | 1 (receipt) | 0 |
| 5 — Colgate | 0 | 0 |

**Zero of five products have a computable average daily demand.** Four have no sales at all; the fifth has three sales that share a single timestamp, so dividing by an elapsed period yields either infinity or a one-day rate that means nothing.

This is more severe than the earlier note that "two products have no movements", and it is the single most important fact in this document. It means:

- Every demand-derived number — reorder point, forecast, order quantity, days-on-hand, stock turn — is **currently uncomputable for the entire catalogue.**
- The `data_insufficient` signal is not an edge case bolted on for credibility. On today's data it is the **correct verdict for every SKU.**
- A 90-day movement backfill is not a nice-to-have for the demo. It is the precondition for the product having anything to say.

**And it explains why the backfill must set `recorded_at` explicitly.** `StockMovement.recorded_at` is `server_default=func.now()` (`models.py:133`), which SQLite evaluates at insert time. `clock.now()` cannot influence a database-side default. A seeder that omits the column will produce ninety days of history all stamped with today's date — exactly the defect that produced the current state. File 12 §4 states this as a hard implementation rule; this is the evidence for it.

---

## 3. What the seeder must produce

The scenarios below assume a `seed_demo.py` that layers onto — never replaces — the verified state above.

| Requirement | Detail | Why |
|---|---|---|
| 90-day movement backfill | Explicit `recorded_at` from `clock.now() − N days` | §2.5. Without it nothing is computable |
| Per-SKU demand rate | A parameter of the scenario, not a discovery | Fixtures are designed. Disclosed as synthetic |
| Weekday/weekend shape | Grocery and personal care skew to weekends | §12 characterises categories; a flat rate is less realistic than a shaped one and costs nothing |
| Three users | `admin@retail.com` (manager), a staff account, `agent@retail.com` | §2.4 |
| Supplier–product pricing | `supplier_products` rows, ≥2 suppliers for ≥1 product | Needed for the non-cheapest-supplier policy rule and BW-3 |
| Preserved PO history | `PO-2026-0001`'s dates left exactly as they are | Its lateness is real evidence; regenerating it would destroy the strongest un-manufactured finding in the database |
| Idempotent reset | Truncate scenario-owned rows, restore baseline, re-seed | The demo must survive being run twice |

### 3.1 The demand rates, stated openly

| SKU | Units/day | Justification |
|---|---|---|
| Rice | 4.0 | §12: grocery is *"high sales velocity"* |
| Headphones | 1.5 | §12: electronics is *"lower sales velocity"* |
| TV | 0.2 | §12 + ₹41,000 unit cost. ~18 units/90 days |
| Detergent | 6.0 | §12: household is *"moderate sales velocity, highly predictable"* |
| **Colgate** | **0 — deliberately** | **Reserved for D4. Must have no history** |

These are chosen to exercise specific code paths. They are labelled synthetic everywhere they surface, and no rupee outcome figure is derived from them (see file 10 §3.1). **A fixture designed to hit a branch is normal engineering; a fixture presented as a measurement is not.** The distinction is maintained in the UI by the `data_disclosure` column, not by the presenter's memory.

### 3.2 The category manual contradicts the category data

Worth surfacing because the config audit (D3) will find it, and it is grounded in the customer's own document.

| §12 line | Manual says | Data says |
|---|---|---|
| Electronics | *"longer supplier lead times typical"* | Electronics supplier Apex has the **shortest** lead time in the catalogue (3 days) |
| Personal Care | *"High sales velocity"* | Colgate has **zero** recorded sales |
| Grocery | *"requires tight reorder management"* | Rice's reorder point is 15 against a supplier that takes 9 days |

An audit that only checks arithmetic finds none of this. An audit that checks the data against the customer's own written characterisation finds all three. That is a meaningfully different product, and it costs one RAG retrieval per category.

---

## 4. The scenario engine

```
demo_scenarios
  id, key, name, description
  seed_spec          JSON — products, demand rates, stock overrides, PO overrides, users
  clock_offset_days  Integer — where clock.now() sits relative to real now
  expected_signals   JSON — the assertion. [{signal_type, sku, severity}]
  is_active          Boolean — exactly one active at a time
```

| Operation | Endpoint | Effect |
|---|---|---|
| List | `GET /api/simulation/scenarios` | Manager only |
| Load | `POST /api/simulation/scenarios/:key/load` | Reset → seed → set clock offset. Idempotent |
| Advance clock | `POST /api/simulation/clock` | `{days: n}` — moves `clock.now()`, fires time-based detectors |
| Run pipeline | `POST /api/agent/run` | Manual trigger, same entry point the scheduler uses |
| Verify | `GET /api/simulation/scenarios/:key/verify` | Compares produced signals to `expected_signals`. **Returns pass/fail** |

The `verify` endpoint is the piece that most demo tooling omits. It is what lets the pre-flight checklist (§10) be executed as a single request rather than a visual inspection, and it is what CI calls.

**Guardrail.** Every simulation endpoint is manager-only, and every one is disabled unless `DEMO_MODE=true`. A time machine and a database reset are not features of a production inventory system. They are development infrastructure that happens to be visible in the demo, and they must be gated as such.

---

## 5. D1 — The Governed High-Value Order

> **Proves:** governance is real, the interrupt is durable, and the human is in command without the system being servile.
> **Business workflow:** BW-2 (escalated replenishment). **Capabilities:** C1, C3, C4, C5, C6.
> **Status: PRIMARY.** This is the scenario the demo is built around.

### 5.1 A correction to the label

The spine ([00-EXECUTIVE-SUMMARY.md](00-EXECUTIVE-SUMMARY.md) §7) calls D1 *"The Refusal"*. That shorthand is imprecise and the imprecision is worth removing, because the package makes two different claims that both get called refusal:

| | What it declines | Scenario |
|---|---|---|
| **Refusal of authority** | Declines to *act alone*. Produces a complete recommendation and routes it to a human | **D1** |
| **Refusal to answer** | Declines to *produce a number* because the evidence does not support one | **D4** |

D1 is the first. The agent knows exactly what to do and does not have the authority to do it. D4 is the second, and it is the rarer and more interesting claim. Conflating them costs the demo its sharpest distinction, so from here the two are named separately.

### 5.2 Seed

```json
{
  "key": "D1_governed_order",
  "clock_offset_days": 0,
  "seed_spec": {
    "backfill_days": 90,
    "demand": {"SKU-ELC-0001": 1.5, "SKU-GRO-0001": 4.0,
               "SKU-HHD-0001": 6.0, "SKU-ELC-0002": 0.2,
               "SKU-PRC-0001": 0.0},
    "stock": {"SKU-ELC-0001": 4},
    "preserve_pos": ["PO-2026-0001", "PO-2026-0002"],
    "autonomy": {"mode": "assisted", "max_order_value": 50000}
  },
  "expected_signals": [
    {"type": "threshold_breach", "sku": "SKU-ELC-0001", "severity": "warning"},
    {"type": "config_drift",     "sku": "SKU-GRO-0001", "severity": "critical"},
    {"type": "data_insufficient","sku": "SKU-PRC-0001", "severity": "info"}
  ]
}
```

### 5.3 The arithmetic, fully derived

Every number the agent shows is computed from a seeded input and a manual formula. Nothing is generated.

| Step | Computation | Value | Grounding |
|---|---|---|---|
| Available | `on_hand − reserved` | 4 − 0 = **4** | `StockLevel.quantity_available` |
| Demand | 90-day sales ÷ 90 | **1.5/day** | Backfill |
| Lead time | Supplier 2 contract | **3 days** | `suppliers.lead_time_days` |
| Safety days | Manual worked example | **2** | §3 line 35: `(10 × 5) + (10 × 2)` |
| Derived ROP | `(1.5 × 3) + (1.5 × 2)` | **8** | §3 line 33 |
| Stored ROP | | 10 | `products.reorder_point` |
| Breach | 4 < 8 **and** 4 < 10 | **Yes, under both** | — |
| Gap to ROP | 8 − 4 | 4 | — |
| Cycle cover | `1.5 × (3 + 2)` | 8 (7.5 → 8) | §9 line 102's shape |
| **Recommended qty** | 4 + 8 | **12 units** | — |
| **Order value** | `12 × ₹22,000` | **₹264,000** | `supplier_products.unit_price` |
| Threshold | | ₹50,000 | **§10 line 113 verbatim** |
| Verdict | ₹264,000 > ₹50,000 | **Escalate on value** | Policy rule 8 |

The breach holds under both the derived and the stored reorder point. That matters: if the two disagreed on whether to act at all, the demo would open on an argument about methodology instead of an action.

### 5.4 The draft-PO wrinkle

`PO-2026-0002` — 10 headphones, ₹220,000, `draft` since 08-22 — is deliberately left in the seed, because the correct reasoning about it is not obvious and demonstrates something a threshold check cannot.

The agent's finding, stated on the signal detail:

> A draft purchase order for 10 units exists, raised 22 Aug. I am treating inbound coverage as **zero**, because no code path in this system transitions a purchase order out of `draft` — three of five statuses are never reached. A draft order reserves no stock and notifies no supplier. **It is a note that looks like an action.** Flagging it separately.

This is the difference between a system that reads a status field and a system that knows what the status field is worth. It is also verifiable in ninety seconds by anyone who greps for `POStatus.submitted`.

### 5.5 The counter-proposal

The manager reduces 12 → 6. This is the beat that decides whether the governance surface is real.

| | |
|---|---|
| **Recompute** | 4 + 6 = 10 available; derived ROP 8; margin **2 units** |
| **Cover above ROP** | 2 ÷ 1.5 = **1.3 days** |
| **System objection** | *"6 units returns available stock to 10, two above the derived reorder point of 8. At 1.5 units/day this SKU re-breaches in 1.3 days and will require a second order — and a second ordering cost — inside the week. Recommended quantity remains 12."* |
| **Manager action** | Approves 6 anyway |
| **Recorded** | `approvals.system_objection` = the text above; `objection_overridden` = `true` |
| **Result** | PO for 6 units, ₹132,000, status `submitted` |

Three properties of this design deserve stating:

- **The system loses the argument and records that it lost.** A governance log that only contains agreements is a log of a system nobody disagreed with.
- **The objection is computed, not phrased by an LLM.** 1.3 days is arithmetic. Had the model written this sentence it could have said "about a week" and been wrong in the customer's favour.
- **Reducing the quantity does not evade the threshold.** ₹132,000 is still above ₹50,000. And in the case where a counter-proposal *does* drop the value below the threshold, approval is already granted by the act of countering — the manager who set the number is the manager who authorised it.

### 5.6 The interrupt

The point of the scenario, and the sole architectural justification for LangGraph (AD-6).

| Time | Event |
|---|---|
| 08:00 | Scheduler triggers. Graph runs `demand_forecaster` → … → `policy_gate` |
| 08:00 | `policy_gate` returns `escalate:value`. Graph halts at `interrupt_before=["executor"]`. State checkpointed |
| — | **The process may restart. The state survives.** |
| 09:14 | Manager opens `/approvals/APR-000012`, counters, approves |
| 09:14 | Graph **resumes from the checkpoint** into `executor` — not re-run from the top |
| 09:14 | `executor` re-checks all seven preconditions against *current* state, writes the PO |
| 09:14 | `inventory_auditor` verifies the write; `recorder` closes the run |

The re-check at resume is what makes the pause safe rather than merely convenient. Between 08:00 and 09:14 the stock could have moved, the supplier could have been deactivated, another PO could have been raised. An approval is authorisation to act on a decision, not a guarantee that the world stood still — so the executor validates before it writes, and refuses if a precondition has changed.

**If the interrupt were removed, LangGraph should be removed with it.** The fallback specified in AD-6 (serialise state onto the `decisions` row, re-enter at `executor`) exists precisely so that this scenario is deliverable even if the checkpointer proves troublesome.

### 5.7 Failure modes and their handling

| If | Then | Visible as |
|---|---|---|
| LLM quota exhausted | Decision completes without narrative. Numbers unaffected | A banner: *"Narrative unavailable — quota. Decision unaffected."* Becomes **M-36** |
| Checkpointer misbehaves | AD-6 fallback path | No visible difference |
| Supplier deactivated between 08:00 and approval | Executor refuses at precondition 4 | A refusal card naming the precondition |
| Duplicate PO raised meanwhile | Duplicate-order guard (AD-15) blocks | *"An open order for this SKU already exists."* |

Every one of these degrades to something that is still worth showing. That is a design property, not luck.

---

## 6. D2 — The Green Dashboard That Is Wrong

> **Proves:** the product finds problems that no threshold can see, and separates authority by the *kind* of change, not the size of it.
> **Business workflows:** BW-3 (late delivery → re-source), BW-4 (configuration correction). **Capabilities:** C2, C9, C10, C11.
> **Status: PRIMARY.** The strongest single insight in the package.

### 6.1 Why this is the best beat available

The current dashboard shows three alerts. Rice is not one of them, because rice has 167 units against a reorder point of 15. Rice looks fine.

Drive rice down to 20 units — still above its reorder point of 15 — and **the current system remains completely silent.** No alert, no amber dot, nothing. And rice is, at that moment, five days from a stockout with a supplier that takes nine days to deliver.

The demo line is therefore: *"Your dashboard is green. Here is why that is the problem."* Nothing else in the package inverts the audience's expectation that cleanly.

### 6.2 Seed

```json
{
  "key": "D2_root_cause",
  "clock_offset_days": 0,
  "seed_spec": {
    "backfill_days": 90,
    "demand": {"SKU-GRO-0001": 4.0},
    "stock": {"SKU-GRO-0001": 20},
    "preserve_pos": ["PO-2026-0001"],
    "supplier_products": [
      {"sku": "SKU-GRO-0001", "supplier": 4, "unit_price": 600, "lead_time_days": 5},
      {"sku": "SKU-GRO-0001", "supplier": 1, "unit_price": 625, "lead_time_days": 7}
    ],
    "autonomy": {"mode": "assisted", "max_order_value": 50000}
  },
  "expected_signals": [
    {"type": "projected_breach", "sku": "SKU-GRO-0001", "severity": "critical"},
    {"type": "supplier_drift",   "supplier": 4,         "severity": "warning"},
    {"type": "config_drift",     "sku": "SKU-GRO-0001", "severity": "critical"}
  ]
}
```

Note `clock_offset_days: 0`. **The supplier drift needs no clock manipulation at all** — `PO-2026-0001`'s lateness is already in the database, four days past contract, and nothing has ever looked at it. That is the least manufactured finding in the entire demo.

### 6.3 The three findings

**Finding 1 — supplier drift.** From `PO-2026-0001`, verified:

| Measure | Value |
|---|---|
| Contract lead time (supplier 4) | 5 days |
| Promised at PO time (08-14 → 08-21) | **7 days** — the promise already broke the contract |
| Actual (08-14 → 08-23) | **9 days** |
| Variance vs contract | **+4 days (80%)** |

Single observation, so the honest statement is *"one observation, 4 days over contract"* — not *"average lateness"*. A supplier scorecard built on `n = 1` must say `n = 1`. The alternative — a confident-looking reliability percentage from one data point — is the fabrication this package exists to avoid.

**Finding 2 — configuration drift, the consequence.** The reorder point encodes an assumption about lead time. Rice's encodes the wrong one.

| Reorder point derived using | Formula | Value |
|---|---|---|
| Contract lead time (5) | `(4 × 5) + (4 × 2)` | 28 |
| **Measured lead time (9)** | `(4 × 9) + (4 × 2)` | **44** |
| **Stored** | — | **15** |

Stored 15 is 13 below the contract-derived figure and **29 below the measured one.** At 4 units/day, a reorder point of 15 buys **3.75 days of cover** against a supplier that takes **9 days**. Rice does not stock out because of a demand spike. It stocks out **every cycle, structurally, by configuration.**

**Finding 3 — the projected breach, and the sting.** At 20 units and 4/day, rice stocks out in **5 days.** The supplier takes 9. **Ordering today is already four days too late — and the reorder point is the reason nobody ordered a week ago.** The system does not merely report a coming stockout; it reports that the stockout is already unavoidable and names the specific stored value responsible.

### 6.4 One signal, two actions, two authority outcomes

This is the mechanically interesting part, and it is the clearest possible illustration of why `policy_gate` is a separate node.

| Action | Value | Policy rule | Outcome |
|---|---|---|---|
| Order 68 units of rice from supplier 4 | 68 × ₹600 = **₹40,800** | Rule 8: below ₹50,000 | **Executes autonomously** |
| Change reorder point 15 → 44 | Not a monetary transaction | **Rule 7: reorder-point changes always escalate** | **Escalates to manager** |

*(68 = gap to derived ROP (44 − 20 = 24) + one cycle of cover (4 × (9 + 2) = 44).)*

The order value is deliberately below the threshold so the two outcomes differ for a reason that is about the *nature* of the change rather than its size. From BW-4, restated because it is the crux:

> **A reorder point is not a transaction, it is a standing instruction.** A wrong order costs one order. A wrong reorder point costs every order after it, silently, until somebody notices. The blast radius of a configuration change is unbounded in time, so it escalates regardless of value.

A system that escalated on rupees alone would have quietly rewritten a standing policy and correctly ordered the rice. That is the wrong pair of decisions, and getting the pair right is a governance design claim, not an LLM claim.

### 6.5 Why the re-source is proposed but not taken

Supplier 1 also stocks rice, at ₹625 vs ₹600 — 4% more, with a 7-day contract lead time against supplier 4's 5 (measured 9).

The agent does **not** switch. It records:

> Supplier 4 delivered 4 days over contract on the single order in the record. Supplier 1 quotes ₹625 (+4.2%) with a 7-day contract lead time. **One observation is not a supplier evaluation.** §6 requires assessment on price competitiveness, lead time reliability, quality compliance, and payment terms; I can measure the first and part of the second. Recommending you request an explanation from supplier 4 before re-sourcing. Flagging supplier 1 as a qualified alternate.

**Recommending an action it declines to take, with a stated reason, on one screen** is the behaviour that separates judgment from enthusiasm. It also passes the reject test in file 04 §9: a system that re-sourced on one late delivery would be worse than the human it replaced.

---

## 7. D3 — The Audit Nobody Ran

> **Proves:** the system finds a class of problem that is invisible by construction, and quantifies it in both directions.
> **Business workflow:** BW-4 at catalogue scale. **Capabilities:** C2, C6, C10.
> **Status: HIGH VALUE — the closer, if time allows.**

### 7.1 The finding

Re-derive all five stored reorder points from the manual's §3 formula using the seeded demand and each supplier's lead time:

| SKU | Stored | Derived | Δ | Direction | Consequence |
|---|---|---|---|---|---|
| Rice | 15 | **44** | −29 | **Dangerously low** | Stocks out every cycle (§6.3) |
| Detergent | 20 | **54** | −34 | **Dangerously low** | `(6 × 7) + (6 × 2)`. Worst absolute gap |
| Headphones | 10 | **8** | +2 | Over-cautious | 2 × ₹22,000 = ₹44,000 idle |
| TV | 5 | **1** | +4 | Over-cautious | 4 × ₹41,000 = **₹164,000 idle** |
| **Colgate** | 30 | **cannot derive** | — | **Unknown** | Zero sales history |

**Zero of five stored reorder points are correct.** Two are dangerously low, two trap capital, and one cannot be assessed at all.

Three observations that make this more than a table:

1. **Neither dangerous SKU is alerting.** Rice (20 on hand) and detergent (50 on hand) are both above their stored reorder points. The current system is silent on both. Its silence is a function of the very values that are wrong — **the alerting mechanism is calibrated by the thing being audited.** That circularity is why no amount of dashboard polish surfaces this.
2. **Drift runs in both directions, and only one direction has a rupee figure.** ₹208,000 of over-cautious capital (₹164,000 + ₹44,000) is T1-computable and must be labelled synthetic. The under-cautious side has no defensible rupee figure at all, because that requires real demand and real margin — file 10 §3.1. The audit therefore reports *"two SKUs at structural stockout risk"* as a count, and the capital figure as a labelled synthetic amount. **Two findings, two different epistemic statuses, disclosed differently on the same screen.**
3. **The fifth row is the important one.** A tool that quietly derived a number for Colgate would look more capable and be less trustworthy. `cannot derive` on one row of five is the audit's credibility.

### 7.2 The second unaudited value

`products.reorder_quantity` (default 50, seeded 15–120) is a **second** stored configuration value that nothing re-derives. It is the same defect class and the same mechanism, so C10 covers both at no additional cost — roughly doubling the audit surface for free. Stated in file 12 §9; it belongs in D3's output table as a second column once the first is working.

### 7.3 The category cross-check

§3.2's three manual-vs-data contradictions surface here, each with a quoted §12 line. This is the part of D3 that RAG genuinely earns rather than decorates: the audit is comparing computed reality against a sentence in the customer's own document, and citing it.

### 7.4 Batch approval

Five findings, one review screen, individually checkable. Each approved change writes its own `decisions` row with its own `policy_citation` and its own before/after values. Batch is a UI affordance over individual decisions — **not** a single coarse decision covering five products. A batch approval that produces one audit record has destroyed exactly the auditability it was built to provide.

---

## 8. D4 — The Refusal

> **Proves:** the system knows the boundary of its own evidence and will not cross it to look useful.
> **Business workflow:** BW-5. **Capabilities:** C1, C2, C6.
> **Status: PRIMARY, embedded.** Pre-computed and visible at step 2 of the click path rather than run live.

### 8.1 Why Colgate, and not the TV

Both have zero movement history. The choice is not arbitrary and the reasoning is the scenario's whole point.

| | Colgate (P5) | TV (P3) |
|---|---|---|
| History | Zero sales | Zero sales |
| Order value at stored ROQ | 120 × ₹90 = **₹10,800** | 15 × ₹41,000 = ₹615,000 |
| vs ₹50,000 threshold | **Below — autonomous-eligible** | Far above — escalates anyway |
| If refused, the reason is | **Evidence, unambiguously** | Confounded with value |

**Colgate isolates the variable.** It is the case where the agent *had* the authority to act, the value was small, nothing would have stopped it — and it declined anyway, purely because the evidence was insufficient. The TV's refusal would be indistinguishable from a threshold check.

A refusal that costs the system nothing is not a demonstration of judgment. This one costs it its only autonomous action of the run.

### 8.2 The refusal, in full

> **`SKU-PRC-0001` — Colgate Total 150g — OUT OF STOCK.**
> **I am not going to size this order.**
>
> The method in §3 requires average daily demand. This SKU has **zero recorded sales in the 90-day window.** I will not substitute a guess for a measurement, and the stored reorder point of 30 was not derived from anything I can see.
>
> **Three things you should know:**
>
> 1. A **draft** purchase order for 120 units (₹10,800) has existed since 23 Aug and has never been submitted. Draft orders reserve nothing and notify nobody. Nothing in this system submits them.
> 2. This supplier's lead time is **10 days — the longest in your catalogue.** A wrong quantity here is wrong for ten days.
> 3. Your category manual describes Personal Care as *"high sales velocity"* (§12). The data shows zero. **Either sales are not being recorded against this SKU, or the SKU is not selling.** Those have opposite remedies and I cannot distinguish them from here.
>
> **If you want to act now:** submit the existing draft for 120 units. At an unknown demand rate that is somewhere between four days and four months of cover. **I cannot narrow that range** — and neither can the reorder point of 30.
>
> **What would let me answer:** 30 days of recorded sales for this SKU, or your estimate of daily demand. Either one and I will size it.

### 8.3 What each paragraph is doing

| Paragraph | Function | Why it is not padding |
|---|---|---|
| Refusal + reason | The core claim | Names the missing input, not a vague "low confidence" |
| Draft PO | An adjacent finding | The SKU is out of stock *and* someone thought they had ordered it |
| Lead time | Stakes | Explains why *this* refusal matters more than another |
| Manual vs data | Two hypotheses | **The strongest sentence.** Two explanations with opposite remedies, honestly undecided |
| Conservative option | Not a dead end | Offers an action and quantifies its uncertainty as a range |
| The ask | A specification | Converts a refusal into a two-line request |

Paragraph 4 is the one to say out loud. *"Either sales are not being recorded, or the SKU is not selling — those have opposite remedies and I cannot distinguish them"* is a sentence no baseline POC will produce, because producing it requires holding two hypotheses and declining to pick. Confidence is cheap; calibrated uncertainty is not.

### 8.4 The honest limit

From BW-5, restated because it constrains the running order: **a refusal is only impressive if the system also acts confidently elsewhere in the same demo.** Shown alone it reads as a system that cannot do anything. That is why D4 is not a separate live run — it is the second thing the audience sees, immediately after evidence that the system executed two other decisions autonomously overnight. The sequence supplies the contrast that makes the refusal legible as judgment rather than incapacity.

---

## 9. The click path

One continuous path, one browser tab, one application. It visits the outputs of D4, D2, and D1 in that order, because the refusal needs the autonomy context and the autonomy needs somewhere to land.

### 9.1 The eight steps

| # | Screen | Action | Said | Proves |
|---|---|---|---|---|
| 1 | `/tower` | Land. Point at **HANDLED WHILE YOU WERE AWAY** — 2 executed, 1 declined, 3 awaiting you | *"Nobody asked it to do this. It ran at 08:00."* | **Autonomy** |
| 2 | `/decisions/DEC-000124` | Open the **declined** Colgate row | *"It refused. It had the authority and the value was ₹10,800 — it refused on evidence."* | **Judgment** |
| 3 | `/signals/SIG-000045` | The rice signal. Evidence block: 15 vs 44, measured lead 9 vs contract 5, §3 citation. **Two decisions from one signal — one executed, one pending** | *"Your dashboard is green. This says you stock out in five days and your own reorder point is why."* | **Insight + authority split** |
| 4 | `/approvals/APR-000012` | The headphones escalation. Read the quoted §10 sentence aloud | *"It read your manual. That is your sentence, not ours."* | **Governance** |
| 5 | *same* | Counter-propose **12 → 6**. Show the recompute and the objection | *"I'm overruling it. It disagrees, in writing, with arithmetic."* | **Partnership** |
| 6 | *same* | Approve. The suspended graph resumes; PO reaches `submitted`; ledger entry appears | *"That decision was paused in a checkpoint. It just resumed and re-checked before writing."* | **It closes the loop** |
| 7 | Staff login → `/inventory` | Attempt a PO. Take the 403 | *"Fifteen seconds. Volunteered, not asked."* | **RBAC** |
| 8 | `/impact` | Scroll to **WHAT WE CANNOT MEASURE YET** | *"We will not put a rupee figure on your slide. Here's the formula and the one input we need."* | **Credibility** |

### 9.2 Corrections to the path as drafted in file 07

> **Two changes** to [07-UX-ARCHITECTURE.md](07-UX-ARCHITECTURE.md) §10, made after grounding the scenarios in real seed data.

| # | Was | Now | Why |
|---|---|---|---|
| 3 | The signal behind step 4's approval | **The rice signal** — a different case | Step 3 was redundant with step 4's evidence block. Spending it on D2's green-dashboard inversion buys the demo its best insight at no time cost |
| 5 | Counter-propose **240 → 120** | Counter-propose **12 → 6** | 240 units of ₹22,000 headphones is ₹5.3M and not a plausible order. 12 → 6 derives from the verified `cost_price` and the seeded demand rate |

File 07 will be amended to match.

### 9.3 Why this order

- **Autonomy before refusal.** Step 2's refusal reads as judgment only because step 1 has already shown two autonomous executions. Reversed, it reads as a system that cannot act (§8.4).
- **Insight before interaction.** Step 3 asks nothing of the audience. It is the only step whose value is entirely in what is on the screen, and it lands better before attention shifts to the presenter's clicking.
- **The interrupt in the middle, not at the end.** Step 6 is the strongest technical claim and needs the two steps after it to be *cheap* — 7 and 8 are fifteen seconds and one scroll. Ending on the technical peak leaves no room to recover if the resume is slow.
- **Credibility last.** Step 8 is what the audience carries out of the room, and it is the one step that no other POC will have.

### 9.4 Timing

| Steps | Minutes | Cut priority |
|---|---|---|
| 1–2 | 0:45 | **Never cut** |
| 3 | 0:45 | **Never cut** — best insight per second in the package |
| 4–6 | 2:00 | **Never cut** — the interrupt is the architecture claim |
| 7 | 0:15 | Cut second |
| 8 | 0:30 | **Never cut** |
| | **4:15** | |

Fifteen seconds of slack in a five-minute slot. If the slot is eight minutes: add D3 (§7) as a closer after step 8 — the audit table is a single screen and the finding *"zero of five reorder points are correct"* is a strong last line.

Cut order under pressure: **step 7 first** (RBAC can be asserted and offered for Q&A), **step 5 second** (approve without countering; loses the partnership beat but keeps the interrupt). Steps 1–3, 6, and 8 are the demo. Below that there is no demo, only a tour.

---

## 10. Pre-flight

Executed as requests, not as a visual inspection.

| # | Check | How |
|---|---|---|
| 1 | Scenario loaded, clock at offset | `POST /api/simulation/scenarios/D1_governed_order/load` |
| 2 | **Expected signals present** | `GET /api/simulation/scenarios/D1_governed_order/verify` → `pass` |
| 3 | One approval pending, one decision declined, two executed | `GET /api/decisions?status=...` |
| 4 | The graph is genuinely suspended | `GET /api/agent/runs/RUN-000078` → `interrupted_at` non-null |
| 5 | Three users exist and log in | Manager, staff, agent |
| 6 | Ledger invariant holds | `GET /api/impact` → M-16 green |
| 7 | LLM reachable **and** the no-LLM path works | Run once with the key unset. Numbers must be identical |
| 8 | Reset is idempotent | Load twice. Verify twice. Both pass |

Check 7 is the one most likely to be skipped and most likely to matter. If the numbers differ between the LLM and no-LLM runs, an LLM is producing a business figure and AD-2 is violated — which would invalidate M-14, the strongest metric in the package. **It is a correctness check disguised as a demo check.**

Check 8 exists because the demo will be run more than once, and a fixture that only works on a clean database is not a fixture.

---

## 11. Contingencies

| If | Then | Cost |
|---|---|---|
| LLM quota exhausted | Proceed. Narratives absent, all numbers intact. **Say so** — it becomes M-36 | None. It is evidence for AD-2 |
| Checkpointer fails | AD-6 fallback: state on the `decisions` row, re-enter at `executor` | Invisible |
| Scenario verify fails | Load the previous scenario. Never present unverified state | ~20 seconds |
| Network to Gemini down | Same as quota exhausted | None |
| A screen errors | Every screen has a designed error state (file 07 §8) with the ID visible | The ID is still quotable |

**The demo has no single point of failure that produces a blank screen.** Every degradation path ends somewhere the presenter can keep talking, and two of them are things worth pointing at.

---

## 12. What is deliberately not simulated

| Not faked | Why |
|---|---|
| A stockout actually costing money | Requires real margin and real demand. File 10 §3.1 |
| Supplier email or acknowledgement | The PO reaches `submitted`. Pretending a supplier replied is theatre |
| Multi-store transfers | `transfer` exists as a movement type; no store entity does. Inventing one is scope, not value |
| A forecast accuracy figure | Measured against seeder output. Circular |
| More than one late delivery | One is what the data supports. Two would be manufactured, and **the honesty of `n = 1` is the point** |
| A live customer order stream | No order entity. M-25's gap is disclosed, not filled with fiction |

The last row is the discipline the whole package rests on: **the demo's credibility comes from the fact that the things it does not show are named rather than fabricated.**

---

## 13. Scenario coverage

| | D1 | D2 | D3 | D4 |
|---|---|---|---|---|
| **Signals** | `threshold_breach` | `projected_breach`, `supplier_drift`, `config_drift` | `config_drift`, `capital_drag` | `data_insufficient` |
| **Workflows** | BW-2 | BW-3, BW-4 | BW-4 at scale | BW-5 |
| **Autonomous action** | — | ✓ (₹40,800) | — | Declined |
| **Escalation** | ✓ value | ✓ config | ✓ batch | — |
| **Refusal** | — | — | ✓ 1 of 5 rows | ✓ |
| **Metrics** | M-1, M-7, M-9, M-10, M-14 | M-4, M-5, M-6 | M-6, M-20 | M-11, M-14 |
| **Clock offset** | 0 | **0** | 0 | 0 |
| **Status** | PRIMARY | PRIMARY | Closer | PRIMARY, embedded |

All four run at `clock_offset_days: 0`. **The demo needs no time travel** — every finding is derivable from the 90-day backfill plus evidence already sitting in the database. The clock (C8) is still required, for the 90-day backfill itself and for `po_overdue` detection, which needs the clock at +5 days to make `PO-2026-0003` (expected 08-29) overdue. That is a fifth scenario worth building for the Q&A answer to *"what about things that are late?"*, and it is not on the critical path.

Between them the four scenarios exercise all seven signal types, five of six business workflows, all three authority outcomes, and both refusal kinds. **BW-6 (goods receipt) is the only workflow with no scenario** — it is demonstrated by the receiving screen directly, and its metrics (M-13, M-16) surface as invariants on the Impact page rather than as a narrative beat.

---

**Next:** [14-PARALLEL-WORKSTREAMS.md](14-PARALLEL-WORKSTREAMS.md) divides all of this into workstreams that multiple Claude Code instances can build simultaneously without colliding.
