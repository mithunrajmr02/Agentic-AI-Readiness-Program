# 18 — Integration & Testing

> **Status:** Proposal. Nothing here is approved.
> **Purpose:** What "verified" means at each layer, which tests are worth writing, and which claims are deliberately left unverified.

---

## 1. Three questions a test suite here has to answer

This build makes three claims that a reviewer can and will check. Everything below exists to make each one falsifiable.

| Claim | Test that could falsify it |
|---|---|
| **"No business number originates from an LLM"** (M-14) | Run the pipeline with the LLM disabled. Every number must be identical |
| **"The arithmetic matches the client's own manual"** | The two worked examples from §3 line 35 and §9 line 102, as literal assertions |
| **"The human-in-the-loop interrupt is durable"** (AD-6) | Kill the process between proposal and approval. Resume. The decision must still execute |

A test suite that does not include those three has not tested the product — it has tested some code that happens to be in the product. They are also, notably, three of the cheapest tests in the plan.

---

## 2. The regression floor — 210 existing tests

> **VERIFIED 2026-08-25.**

| Suite | Tests | Guards |
|---|---|---|
| `tests/phase1` | **65** | Schema, CRUD, auth, service layer |
| `tests/phase2` | **34** | RAG: ≥20 chunks, ≤600 chars, retrieval |
| `tests/phase3` | **38** | Agent: `len(agent.tools) == 7`, `build_agent_executor` |
| `tests/phase4` | **33** | MCP: ≥6 tools, chat interface, observability |
| `tests/phase5` | **40** | Multi-agent: routing by source inspection, E2E status values |
| **Total** | **210** | |

**All 210 are read-only for every stream, including integration.** They run at every wave gate, and they run in each stream's own definition-of-done.

`tests/conftest.py` is fourteen lines and does one thing: put the repo root on `sys.path` so `src.*` resolves under `--import-mode=importlib`. It is shared by all five suites. **Nobody touches it** — a change there breaks all 210 at once, which is the largest available blast radius in the repository.

### 2.1 The graded tests are not a nuisance

It is tempting to treat 210 inherited tests as an obstacle to a redesign. They are the opposite: they are the only *independent* evidence that a substantial rewrite did not break the working system. A rewrite that keeps all 210 green has a property no amount of narration can supply.

Which is why the prohibition is absolute. **A stream that cannot make its change without editing a graded test has found a design error, not a test error.** The correct response is an integration request, not an edit.

---

## 3. Test layers

| Layer | Owner | Runs | Purpose |
|---|---|---|---|
| **Graded regression** | Every stream | Every stream's DoD + every gate | Nothing broke |
| **Unit** | The stream | The stream's worktree | Its own logic, against stubs |
| **Contract** | The stream | The stream's worktree | Its published signatures match file 15 |
| **Integration** | Integration | Wave gates | Real implementations replace stubs |
| **Scenario** | Integration | Gate 3, Gate Final | `expected_signals` verification |
| **Click-path E2E** | Integration | Gate Final | The 8 demo steps, browser |
| **Invariant (CI)** | Automatic | Every commit | Greps and assertions from file 15 §15 |

### 3.1 The stub discipline

Wave 1 streams test against stubs of each other. Two rules keep that honest:

1. **A stub lives in the consuming stream's `tests/` directory, never in `src/`.** A stub that ships is a fake in production.
2. **A stub must return the contract's failure cases, not just its happy path.** A stub for `compute_daily_demand` that always returns a float lets WS-3 forget the `insufficient` branch — and that branch is the entire D4 refusal.

The second rule is the one that gets skipped. It is also the one that produces the failure where two streams pass all their own tests and the composition is broken.

---

## 4. The tests worth writing, ranked

Ordered by (evidence value) ÷ (cost to write). The top five are all cheap.

### 4.1 The two manual assertions — WS-1

```python
def test_reorder_point_matches_manual_worked_example():
    # manual §3 line 35: "(10 × 5) + (10 × 2) = 70 units"
    assert derive_reorder_point_from(demand=10, lead_time=5, safety_days=2).value == 70

def test_order_quantity_matches_manual_worked_example():
    # manual §9 line 102: "(5 × 7) + (5 × 14) = 105 units"
    assert order_quantity_from(demand=5, lead_time=7, safety_days=14).value == 105
```

Two lines each. They are the executable proof that the system's arithmetic agrees with the customer's own document. If either fails, every number in the product is wrong in the same direction, and no amount of downstream testing would find it — the whole system would be consistently wrong.

### 4.2 The LLM-off equivalence test — integration

```python
def test_every_number_identical_without_llm(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    with_llm = run_pipeline("manual", product_ids=[1])
    without   = run_pipeline("manual", product_ids=[1])
    assert with_llm["computed"] == without["computed"]
    assert without["narrative"] is None
```

**This is the single most important new test in the build.** It is the mechanical proof of AD-2 and the thing that earns M-14. Everything else about the architecture is an argument; this is a measurement.

It is also a demo pre-flight check (file 13 §10, check 7), which is unusual and worth noting: a correctness test that doubles as a rehearsal step.

### 4.3 The durable interrupt across a real restart — WS-8

```python
def test_interrupt_survives_process_restart(tmp_path):
    run_id = start_pipeline(product_ids=[3])       # TV: ₹264,000 → escalates
    assert pending_approval_exists(run_id)
    restart_process()                              # actually restart. Not mocked
    resume_pipeline(run_id, {"outcome": "approved", "user_id": 1})
    assert po_exists_for(product_id=3)
```

AD-6 states that the durable interrupt is **the entire justification for using LangGraph**. If it is not tested across a genuine restart, LangGraph is unearned complexity and the honest move would be to remove it. A mocked restart tests the mock.

### 4.4 The `value is None` invariant — WS-1, WS-17

```python
@pytest.mark.parametrize("product_id", [1, 2, 3, 4, 5])
def test_insufficient_never_returns_zero(product_id):
    c = compute_daily_demand(db, product_id)
    if c.sufficiency in ("insufficient", "none"):
        assert c.value is None      # never 0.0

def test_every_t3_metric_returns_none():
    for m in compute_all(db):
        if m.tier == "T3":
            assert m.value is None
            assert m.missing_input
```

Cheap, parametrised, and it guards the two most likely fabrications in the system: treating "no data" as "zero demand", and filling a T3 box with an arithmetically-available but meaningless number.

The second one is worth dwelling on. For M-23 the multiplication *is* available — `products` carries both `unit_price` and `cost_price`, so unit margin is computable today. The blocker is that every sale was generated by the seeder. **The fact that the multiplication is real does not make the answer true**, and this test is what enforces that distinction against a future well-meaning change.

### 4.5 The ledger invariant after every write — WS-9

```python
def test_movements_sum_to_stock_level_after_agent_write():
    for pid in all_product_ids(db):
        total = sum(m.quantity for m in movements_for(db, pid))
        assert total == stock_level(db, pid).quantity_on_hand
```

The existing seeder's `verify(db)` already asserts this. The agent's writes must not be the first thing to break it. Runs after every execution test, and it is the cheapest way to detect a whole class of write bugs.

### 4.6 The precondition re-check — WS-9

```python
def test_delivery_during_approval_window_cancels_execution():
    d = propose_replenishment(product_id=2)     # 4 on hand, ROP 10
    receive_po(po_id=2)                          # 10 units arrive: 4 → 14
    result = execute_decision(db, d)
    assert not result.ok
    assert result.failed_precondition == "need_already_resolved"
```

This is the test that separates a governance surface from actual judgment. A durable interrupt means approval can arrive hours after proposal; a system that executes anyway has an approval workflow and no sense.

### 4.7 The `n = 1` honesty test — WS-7

```python
def test_scorecard_reports_sample_size_not_a_percentage():
    s = scorecard(db, supplier_id=4)     # exactly one completed PO exists
    assert s.sample_size == 1
    assert s.on_time_rate is None or s.sample_size >= 5
```

The database contains exactly one completed PO. A scorecard rendering "80% on-time" from one observation is fabrication with a progress bar.

### 4.8 The RBAC 403 — WS-4

```python
def test_staff_cannot_approve():
    r = client.post(f"/api/approvals/{aid}/approve", headers=staff_auth())
    assert r.status_code == 403
    assert "manager" in r.json()["error"]["message"]

def test_agent_cannot_approve_its_own_decision():
    r = client.post(f"/api/approvals/{aid}/approve", headers=agent_auth())
    assert r.status_code == 403
```

The second is the more interesting one and it is AD-12's actual content. An agent that can approve its own escalation has no governance at all, only paperwork.

`users` currently has exactly one row (`admin@retail.com`, role `manager`), and `users.role` is `String(50)` at `models.py:184` — so the staff and agent identities are a **seed** requirement for WS-2, not a schema change.

---

## 5. Scenario verification — the test that makes the demo safe

```
GET /api/simulation/scenarios/:key/verify
```

Each of the four `demo_scenarios` rows carries an `expected_signals` list. Verification loads the scenario, runs the pipeline, and compares.

```python
@pytest.mark.parametrize("key", ["d1_governed_order", "d2_green_dashboard",
                                 "d3_audit", "d4_refusal"])
def test_scenario_produces_expected_signals(key):
    load_scenario(key)
    actual = {s.signal_type for s in run_detectors(db)}
    assert scenario(key).expected_signals <= actual
```

**This is the difference between a demo and a rehearsal.** If seeding D1 and running the pipeline does not produce exactly the signals D1 promises, the build is broken — and the presenter should never be the person who discovers that.

All four scenarios run at `clock_offset_days: 0`, which is a deliberate property: no scenario depends on time manipulation to produce its finding. D2's late-delivery evidence is already in the database — `PO-2026-0001` has a 5-day contract lead time, a 7-day promised delivery, and a 9-day actual receipt. Nothing has ever looked at it.

---

## 6. The LLM problem in tests

The free tier is **15 requests/minute, 1,500/day**. There are already 210 tests. A test suite that calls Gemini is slow, rate-limited, non-deterministic, and unrunnable offline.

**Rule: no new test calls an LLM, with exactly three exceptions.**

| Exception | Test |
|---|---|
| Narrative generation produces prose | One test, one call, asserts non-empty and contains no digits outside quoted evidence |
| Quota exhaustion degrades gracefully | Mock a 429. Assert the decision still completes and numbers are unchanged |
| The RAG citation is retrieved, not generated | Assert the returned sentence appears verbatim in `inventory_manual.md` |

This is affordable **because of** the architecture. WS-1, WS-2, WS-3, WS-4, WS-5, WS-9 and WS-17 need no LLM at all — every business number is deterministic by construction. If a large fraction of the new suite needed an LLM, that would itself be evidence that AD-2 is false.

The third exception is worth its cost: it is how you distinguish a real citation from a plausible-sounding invented one, and a fabricated policy citation would be worse than none.

---

## 7. What is deliberately not tested

Stated because an untested claim silently presented as verified is the failure mode this package is built to avoid.

| Not tested | Why | Honest framing |
|---|---|---|
| Forecast **accuracy** | Would be measured against data the seeder generated. Circular | "Accuracy against synthetic data is meaningless. The formula is testable; the accuracy is not" |
| Business outcome metrics (M-23 … M-30) | No real demand history | T3, with the formula and the missing input shown |
| Load and concurrency beyond `next_id` | SQLite, single store, no scale claim | "This is a single-store system. Multi-store is a rearchitecture" |
| LLM output quality | Non-deterministic, and not load-bearing | The LLM writes prose. Prose quality is judged by reading it |
| Browser matrix | One demo, one machine | Chrome only |
| Real MCP protocol transport | C19 is OPTIONAL; the current server is bypassed by in-process import | Stated plainly in file 04, not hidden |

The MCP row is the uncomfortable one and it belongs here. The MCP server exists, exposes six tools, and passes 33 graded tests — **and the protocol is never actually spoken**, because the chat interface imports the tool functions in-process. Testing "MCP works" would be testing an import. If C19 is built, that changes; until then, saying so is better than implying otherwise.

---

## 8. CI invariant checks

Fast, mechanical, and each one exists because a plausible well-intentioned change would otherwise break something silently.

```bash
# 1 — the clock
grep -rn "datetime.now()\|datetime.utcnow()\|date.today()\|time.time()" src/ --include=*.py
# expect: nothing (after WS-9 fixes inventory_service.py:137)

# 2 — the status cage
grep -rn "Enum(" src/backend/models_*.py
# expect: nothing

# 3 — invisible timestamps on new tables
grep -rn "server_default=func.now()" src/backend/models_*.py
# expect: nothing

# 4 — the graded floor
pytest tests/phase1 tests/phase2 tests/phase3 tests/phase4 tests/phase5 -q
# expect: 210 passed

# 5 — scope discipline (per stream)
git diff --name-only | grep -vFf .owned-files
# expect: nothing

# 6 — main.py touched only by integration
git diff --name-only main | grep "src/backend/main.py"
# expect: nothing, outside integration branches
```

Checks 5 and 6 are the parallel-execution guards. They are mechanical because in a seven-wide build **a helpful edit to a file you do not own is indistinguishable from a bug** — the grep finds it in seconds; integration would find it hours later, after the owner has built on top of it.

---

## 9. Verification ledger — claim → test

Every substantive claim in the package, and the specific thing that could falsify it.

| Claim | Verified by | Status |
|---|---|---|
| Arithmetic matches the manual | §4.1, two assertions | Testable |
| No business number comes from an LLM (M-14) | §4.2, LLM-off equivalence | Testable |
| The interrupt is durable (AD-6) | §4.3, real process restart | Testable |
| "No data" is never treated as zero | §4.4, parametrised | Testable |
| Ledger integrity holds after agent writes (M-16) | §4.5 | Testable |
| Approval-window changes are respected | §4.6, precondition re-check | Testable |
| Supplier reliability is not fabricated | §4.7, `n = 1` | Testable |
| An agent cannot approve itself (AD-12) | §4.8 | Testable |
| Six of seven signal classes were previously impossible (M-4) | Baseline is code inspection, **not a test** | Argued, inspectable |
| Detection latency beats §10's 24 hours (M-1) | Measured from `signals` and `decisions` | Computable |
| T3 metrics are never fabricated | §4.4, second test | Testable |
| Demo scenarios reproduce | §5, four parametrised | Testable |
| Nothing existing broke | 210 graded tests | Testable |
| Business outcomes improve | **Nothing. Requires client data** | **Not claimed** |

The last two rows are the ones to read together. Thirteen claims are mechanically checkable; the fourteenth is not, and is therefore not made. **A package that verified thirteen claims and quietly asserted a fourteenth would have wasted the credibility earned by the other thirteen.**

---

## 10. The four numbers that define done

| Measure | Target |
|---|---|
| Graded tests still passing | **210 / 210** |
| Demo scenarios verifying | **4 / 4** |
| Numbers that change when the LLM is disabled | **0** |
| T3 metrics displaying a value | **0** |

Four numbers, all checkable in under five minutes, and each one falsifiable by anyone in the room.

---

**Next:** [19-ROADMAP.md](19-ROADMAP.md) prioritises the whole opportunity space into MUST BUILD / HIGH VALUE / OPTIONAL / REJECT.
