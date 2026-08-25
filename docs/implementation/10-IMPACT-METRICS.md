# 10 — Impact Metrics

> **Status:** Proposal. Nothing here is approved.
> **Purpose:** Define exactly what this system can measure, exactly what it cannot, and the formula plus missing input for everything in the second category.
> **Governing constraint (verbatim from the brief):** *"Do not invent unsupported ROI numbers. Determine how impact could actually be measured or demonstrated."*

---

## 1. The rule

Every metric in this document is placed in exactly one of three tiers, and the tier is stated wherever the metric appears in the product.

| Tier | Definition | Shown as |
|---|---|---|
| **T1 — Computable now** | Derived entirely from data the system generates about itself, on synthetic seed data | A number, with its formula available |
| **T2 — Demonstrable live** | Observed in the room during a demo, not stored | A measured observation, disclosed as such |
| **T3 — Requires client data** | The formula is known; a specific input is not available | **An empty box naming the formula and the missing input** |

The third tier is the unusual one and it is the point. Most POCs in this position present a slide reading "40% reduction in stockouts" with no derivation. Steward's Impact screen has a section titled **"WHAT WE CANNOT MEASURE YET"** that lists those metrics with their formulas and their missing inputs.

**Why show the empty boxes rather than omit them.** Three reasons, in increasing order of importance:

1. Omitting them invites the question anyway, in a worse setting — during Q&A, without a prepared answer.
2. Naming the missing input is a *specification for the client engagement*: "give us 90 days of real sales and unit margin, and this box fills in."
3. A system that distinguishes what it knows from what it does not is demonstrating exactly the epistemic discipline the whole product claims. **The empty box is a working demonstration of the product's central thesis, not an apology for it.**

A reviewer who sees a fabricated ROI figure discounts everything else on the slide. A reviewer who sees a labelled gap trusts the numbers that are filled in.

---

## 2. T1 — Computable now

All of these are computable on synthetic seed data because they measure **the system's own behaviour**, not business outcomes. That distinction is what makes them defensible.

### 2.1 Decision and detection

| ID | Metric | Formula | Source | Baseline |
|---|---|---|---|---|
| **M-1** | Signal→action latency | `decisions.executed_at − signals.raised_at`, median and p95 | `signals`, `decisions` | **≤24h per §10 item 3** — the only manual-documented baseline |
| **M-2** | Detection latency | `signals.raised_at − underlying_event_at` | `signals`, `stock_movements` | Up to one human check interval |
| **M-3** | Signals by detector class | `count(signals) group by signal_type` | `signals` | 2 of 7 classes detectable today |
| **M-4** | Signals of a class impossible before | `count` where `signal_type ∈ {projected_breach, po_overdue, config_drift, supplier_drift, capital_drag, data_insufficient}` | `signals` | **Zero — structurally** |
| **M-5** | Overdue POs surfaced | `count(signals where type = po_overdue)` | `signals` | **Zero.** Verified: a 2-day-late PO went unnoticed |
| **M-6** | Config drift found and corrected | `count(decisions where action = reorder_point_change and status = executed)` | `decisions` | Zero — no re-derivation exists |

M-4 is the strongest family. It does not claim an improvement percentage; it claims **a category of detection that was previously impossible now occurs N times.** That claim needs no client data to be true, and it cannot be made by a POC that only checks thresholds.

### 2.2 Autonomy and governance

| ID | Metric | Formula | Source |
|---|---|---|---|
| **M-7** | Autonomy rate | `count(status=executed AND actor=agent) / count(all executed)` | `decisions` |
| **M-8** | Escalation rate by reason | `count group by escalation_reason` — value / sufficiency / non-cheapest / config / blast-radius | `decisions` |
| **M-9** | Approval outcome mix | approved / rejected / modified / expired as proportions | `approvals` |
| **M-10** | Approval latency | `approvals.decided_at − decisions.pending_at`, median and p95 | `approvals`, `decisions` |
| **M-11** | Refusal rate | `count(status=insufficient_data) / count(all runs)` | `decisions` |
| **M-12** | Policy citation coverage | `count(decisions with non-null policy_citation) / count(decisions requiring a policy check)` | `decisions` |
| **M-13** | Attribution completeness | `count(writes with a resolved actor) / count(all writes)` | `decisions`, `stock_movements` |

M-8's breakdown is more informative than M-7's headline. An autonomy rate of 70% is a number; *"of the 30% escalated, 11% were on value, 14% on evidence quality, 5% on supplier choice"* is a description of how the system's judgment is calibrated. **A single autonomy percentage can be gamed by loosening a threshold; the breakdown cannot.**

M-12 should read 100%. Anything less is a defect, which makes it a useful invariant rather than a KPI.

### 2.3 Method quality — the strongest available claim

| ID | Metric | Formula | Baseline | Target |
|---|---|---|---|---|
| **M-14** | **Fabricated numeric fields** | Count of business-consequential numeric fields whose value originates from an LLM | **5** | **0** |
| **M-15** | LLM numeric violations | `count(agent_runs where llm_numeric_violation)` | Unmeasured | Tracked, non-zero expected |
| **M-16** | Ledger invariant integrity | `sum(stock_movements.quantity) == stock_levels.quantity_on_hand` per product | Held by the seeder's `verify(db)` | Held after every agent write |
| **M-17** | Unreachable state count | PO statuses never reached by any code path | **3** (`submitted`, `acknowledged`, `cancelled`) | 1 (`cancelled`, deliberately) |

**M-14 is the single most defensible metric in the package**, and it is worth stating why in full.

The five fields, each verifiable by reading the current code:

| Field | Current origin | Proposed origin |
|---|---|---|
| `forecast_units` | LLM output | `average_daily_demand × horizon`, §3 |
| `confidence` | LLM self-report | Sufficiency score from sale-event count and span |
| `recommended_qty` | LLM output | `demand × (lead_time + safety_days)`, §9 line 102 |
| `unit_price` | LLM output — **recorded as ₹580.0 against a real ₹600.0** | `supplier_products.unit_price` |
| `estimated_lead_time_days` | LLM output | `suppliers.lead_time_days`, measured actuals |

Properties that make M-14 unusually strong:

- **Verifiable by inspection.** A reviewer reads the code and confirms it. No trust required.
- **Needs no client data.** It is a claim about method, not outcome.
- **Already evidenced in the repository.** `agents.py:389-406` records that in **3 of 3 runs** the model invented `supplier_id: 101`, the ₹580.0 price, and a fabricated *"Bulk discount… Price valid for 30 days"*. The code then overwrites the model's output at `agents.py:318` — the codebase already knows the output is untrustworthy.
- **It is the metric a technical evaluator cares about most**, because every other number in the system depends on it.

"5 → 0" beats "40% fewer stockouts" for this audience, because one is checkable in ninety seconds and the other is not checkable at all.

### 2.4 Capital and inventory position

Computable on seeded data, but **the seed data is synthetic and every display of these must say so.**

| ID | Metric | Formula | Grounding |
|---|---|---|---|
| **M-18** | Days on hand | `quantity_on_hand / average_daily_sales` | **§13 line 139 verbatim** |
| **M-19** | Slow-moving count | Products with no movement in ≥30 days | **§13 line 136 verbatim** |
| **M-20** | Stock above requirement | `Σ max(0, on_hand − reorder_point) × cost_price` | Derived from §3 |
| **M-21** | Stock turn ratio | `COGS / average inventory value`, where `COGS = Σ (sale_qty × cost_price)` | **§13 line 137 verbatim.** Both inputs derivable — see §3.1 |
| **M-22** | Order-cost saving from consolidation | `orders_avoided × ordering_cost` | §9 line 98's `ordering_cost` term |

M-20 and M-21 use `products.cost_price`, not `unit_price` — inventory is valued at what it cost, not at what it might sell for. Getting that backwards would inflate every capital figure by the full margin, which is the sort of error that is invisible on a slide and fatal in a review.

M-22 is grounded but assumption-dependent: `ordering_cost` is not given a value in the manual. Displayed as *"N orders consolidated into M — at an assumed ordering cost of ₹X, that is ₹Y"*, with the assumption visibly labelled. **The order count is a fact; the rupee figure is a parameterised illustration**, and the UI must not let the second look like the first.

---

## 3. T3 — Requires client data

Named, with the formula and the specific missing input. **These appear in the product as empty, labelled boxes.**

| ID | Metric | Formula | Missing input | Why unavailable |
|---|---|---|---|---|
| **M-23** | Revenue protected | `stockout_days_avoided × daily_units × (unit_price − cost_price)` | **Real demand history only** — margin *is* available | See §3.1 |
| **M-24** | FTE hours saved | `decisions_automated × minutes_per_manual_decision` | **Time-and-motion baseline** for Anita's actual workflow | Never measured |
| **M-25** | Fill rate | `orders_fulfilled_immediately / total_orders` | **A customer-order entity** | §13 line 138 defines it; no order table exists |
| **M-26** | Stockout cost avoided | `stockout_days × lost_units × (unit_price − cost_price)` | **Real demand history only** | See §3.1 |
| **M-27** | True stock turn | `COGS / average_inventory_value` | **Real sales volume.** COGS *is* derivable — see §3.1 | §13 line 137 gives the formula |
| **M-28** | Working capital released | `Δ inventory_value` against a real position | **Real opening inventory** | Synthetic |
| **M-29** | Expediting cost avoided | `rush_orders_avoided × premium_rate` | **Rush-order premium** | Not modelled |
| **M-30** | Supplier price improvement | `Σ (previous_price − selected_price) × qty` | **Historical purchase prices** | Only current prices seeded |

### 3.1 Correction — unit margin and COGS *are* available

> **VERIFIED 2026-08-25.** An earlier draft of this table asserted *"no margin field"*. That was wrong, and the correction narrows the gap in a way worth stating precisely.

`products` (`models.py:77-96`) carries **both** prices:

| Column | Meaning |
|---|---|
| `unit_price` (Float, non-null) | Selling price |
| `cost_price` (Float, non-null) | Purchase cost |

So:

```
unit_margin = unit_price − cost_price                        ← computable today
COGS        = Σ (sale_movement.quantity × cost_price)        ← computable today
```

**What this changes.** M-23, M-26, and M-27 are not blocked on a missing *field*. They are blocked on a single missing input — **real demand history.** Every sale in the database is generated by the seeder, so any rupee figure derived from sales volume is a statement about the seeder, not about a business.

**What this does not change.** These metrics stay in T3, and the reasoning is the more important half of the correction: a number that is *arithmetically computable* from synthetic inputs is not *meaningful*. Publishing "₹4.2L revenue protected" because the code can multiply three seeded columns together would be exactly the fabrication this document exists to prevent — the fact that the multiplication is real does not make the answer true.

The honest framing on the Impact screen is therefore sharper than "we lack the data":

> **Revenue protected** — formula available, margin available, **awaiting real sales history.**
> `stockout_days_avoided × daily_units × (unit_price − cost_price)`
> Everything in this formula exists except the demand series. Ninety days of real sales fills this box.

That is a better disclosure than an empty box with a vague caveat, and it is a more concrete ask of the client: **one input, named, with the formula it feeds.**

Two observations worth making about this table.

**M-25 is the sharpest example of honest reporting.** §13 line 138 defines fill rate as *"the percentage of customer orders fulfilled immediately without stockouts"* — the client's own manual specifies a metric the client's own system cannot produce, because there is no customer-order entity. Stating that plainly is more valuable than producing a plausible number, and it is precisely the kind of finding a real engagement would want surfaced.

**M-24 is the metric a client will ask for first, and it is the one most often faked.** "We saved 12 FTE hours a week" requires knowing how long Anita currently spends, which nobody has measured. The formula is trivial; the baseline is the whole problem. Naming the missing baseline converts an unanswerable question into a two-week measurement task.

---

## 4. T2 — Demonstrable live

Measured in the room, not stored. These are the most persuasive because the audience watches the measurement happen.

| ID | Demonstration | What is measured | Why it lands |
|---|---|---|---|
| **M-31** | **The timing race** | Wall-clock: a signal fires; a volunteer navigates the current UI to raise the equivalent PO while the agent completes end to end | The audience times it. No slide can be disputed |
| **M-32** | Detection of the invisible | The clock advances; the overdue signal fires | Nobody in the room was watching for it |
| **M-33** | The refusal | An insufficient-data SKU is presented; the agent declines and names the shortfall | The system saying "I don't know" is more memorable than any success |
| **M-34** | The RBAC 403 | Staff attempts an approval and is refused | Governance verified in ~15 seconds |
| **M-35** | The rejection path | A manager rejects; the signal stays open and re-raises | Authority is real, not decorative |
| **M-36** | Graceful LLM failure | Quota exhausted mid-run; the decision completes without a narrative | Proves the LLM is not load-bearing |

M-31 needs care to stay honest: the volunteer is unfamiliar with the UI, so the comparison flatters the agent. The correct framing is *"this is the latency of a cold-start human, not of Anita at her best"* — and the honest baseline is not the race but **M-1's ≤24h from §10 item 3**, because Anita's real constraint is her check cadence, not her clicking speed.

M-36 turns the free-tier rate limit — a genuine constraint — into evidence for AD-2. That is not spin; the degradation behaviour is designed, and demonstrating it proves the architecture claim better than asserting it.

---

## 5. Where metrics surface

| Surface | Metrics | Audience |
|---|---|---|
| Control Tower — one line of text | M-7, M-1, M-4 | Anita, at a glance |
| Impact › Detection | M-3, M-4, M-5, M-6, M-2 | Manager |
| Impact › Decision | M-7, M-8, M-9, M-10, M-11 | Manager |
| Impact › Method | **M-14**, M-15, M-16, M-17, M-12 | **Technical reviewer** |
| Impact › Position | M-18–M-22, disclosed synthetic | Executive |
| Impact › **"What we cannot measure yet"** | M-23–M-30 with formulas | **Executive — the credibility section** |
| Supplier scorecard | Reliability, lateness variance | Anita |
| Autonomy settings | M-7, M-9 as calibration input | Manager |

The Method block exists because the most sceptical person in the room is technical, and M-14 is aimed squarely at them.

---

## 6. Snapshotting

`metric_snapshots` stores computed values at each tick so trends exist without recomputing history.

| Field | Purpose |
|---|---|
| `metric_key` | `M-7`, `M-14`, … |
| `value` | Numeric |
| `computed_at` | Clock-aware — respects C8's controllable clock |
| `window` | The period the value covers |
| `scope` | Global, category, or product |
| `tier` | T1 / T2 / T3 — travels with the value |
| `data_disclosure` | `synthetic` / `mixed` / `real` |

`data_disclosure` is a column, not a UI convention. Storing it means a synthetic-data figure cannot be exported into a deck stripped of its caveat — the caveat is part of the record. If C18's export is built, it carries the disclosure by construction.

---

## 7. The refusal, stated as policy

Metrics deliberately **not** produced, and the answer if asked:

| Requested | Answer |
|---|---|
| "X% stockout reduction" | Requires real demand history. The formula is M-26; the missing input is contribution margin |
| "₹N saved annually" | Requires margin and real volume. See M-23 |
| "N% forecast accuracy" | Would be measured against synthetic data the seeder generated. Circular and meaningless |
| "N FTE reduction" | Requires the time-and-motion baseline named in M-24 |
| "N× ROI" | Requires all of the above |

**A single invented figure would compromise every honest number beside it.** The Impact screen's value is that a reviewer can check any figure on it; one unfalsifiable claim destroys that property for the whole screen.

The strongest thing to say when asked for an ROI number: *"Here is the formula, here is the one input we don't have, and here is what we'd need from you to fill it in."* That is a consulting answer, not an evasion — and it is the answer this product's architecture is built to give.

---

## 8. Metric coverage against workflows

| Workflow | Primary metrics | Baseline quality |
|---|---|---|
| BW-1 autonomous | M-1, M-7, M-14 | **Strong** — §10 item 3 is client-documented |
| BW-2 escalated | M-8, M-9, M-10 | Moderate — no prior mechanism to compare |
| BW-3 late delivery | **M-5**, M-4 | **Strongest** — verified baseline of zero |
| BW-4 config fix | **M-6**, M-4 | **Strongest** — baseline of zero |
| BW-5 refusal | M-11, **M-14** | Strong — method claim, inspectable |
| BW-6 receipt | M-13, M-16 | Strong — defect fix, verifiable |

Four of six workflows have a baseline that is either **client-documented or verifiably zero.** Those are the four to lead with, because "this was previously impossible, here it is happening" survives scrutiny in a way "this is 40% better" does not.

---

## 9. The three numbers to say out loud

If the presentation has room for three metrics:

1. **M-14: five fabricated numeric fields → zero.** A method claim, checkable by reading the code, requiring no client data. The one a technical reviewer will remember.
2. **M-5 / M-6: detections of classes that were previously structurally impossible.** Not "better" — *newly possible*. Verified baselines of zero.
3. **M-1 against §10 item 3's 24 hours.** The only impact claim in the package measured against the client's own written standard.

And the fourth thing to say, which is not a number: **the Impact screen has a section listing what it cannot measure yet, with the formula and the missing input for each.** In a room of near-identical POCs, that section is likely the most differentiating single screen in the product.

---

**Next:** [11-TARGET-ARCHITECTURE.md](11-TARGET-ARCHITECTURE.md) specifies the system that produces all of this.
