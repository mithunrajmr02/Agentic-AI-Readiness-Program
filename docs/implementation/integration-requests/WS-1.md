# WS-1 — Integration Requests & Published Contracts

**Wave 1 · Analytics Core · status: COMPLETE, all tests green.**

## 1. What WS-1 Published

### 1.1 Analytics Core (`src/analytics/`)
- `src/analytics/__init__.py`: Public exports for `Computed`, `compute_daily_demand`, `derive_reorder_point`, `derive_reorder_point_from`, `derive_reorder_quantity`, `order_quantity_from`, `compute_eoq`, `score_sufficiency`, `measured_lead_time`, `inventory_value`, `days_on_hand`, `stock_turn`.
- `src/analytics/sufficiency.py`:
  - Immutable frozen dataclass `Computed(value, sufficiency, inputs, formula, citation, sample_size, span_days)`.
  - Invariant: strictly enforces `value is None` whenever `sufficiency in ('insufficient', 'none')` (never `0.0`).
  - `score_sufficiency(db, product_id)`: Evaluates sample size and distinct day count against frozen thresholds (citation: §4 line 45).
- `src/analytics/demand.py`:
  - `compute_daily_demand(db, product_id, window_days=30)`: Pure function calculating sales demand velocity and sample size over rolling window (citation: §3 line 33).
  - `_is_sale_movement(m)`: Robustly matches sale movements across enum member name (`returnm` trap proof).
- `src/analytics/reorder.py`:
  - `derive_reorder_point(db, product_id, *, use_measured_lead_time=False, safety_stock_days=2)`: Implements `(demand × lead_time) + (demand × safety_days)` reproducing manual §3 line 35 worked example: `(10 * 5) + (10 * 2) = 70`.
  - `derive_reorder_quantity(db, product_id, *, lead_time_days=None, safety_days=14)`: Implements standard replenishment batch reproducing manual §9 line 102 worked example: `(5 * 7) + (5 * 14) = 105`.
  - `derive_reorder_point_from(demand, lead_time, safety_days=2)`: Direct calculation helper without database query.
  - `order_quantity_from(demand, lead_time, safety_days=14)`: Direct calculation helper without database query.
- `src/analytics/eoq.py`:
  - `compute_eoq(db, product_id, ordering_cost, holding_rate)`: Optimal batch size formula $\sqrt{\frac{2 \cdot \text{annual\_demand} \cdot S}{H}}$ (manual §9 line 98).
- `src/analytics/valuation.py`:
  - `inventory_value(db, *, scope="global", scope_id=None)`: Inventory stock value computed at `cost_price` (never `unit_price`, manual §8 line 91).
  - `days_on_hand(db, product_id)`: Inventory supply remaining: `quantity_on_hand / daily_demand` (manual §13 line 139). Clamps negative stock to `0.0`.
  - `stock_turn(db, window_days=90)`: Inventory turnover ratio: `COGS / average_inventory_value` (manual §13 line 137).
- `src/analytics/leadtime.py`:
  - `measured_lead_time(db, supplier_id)`: Supplier lead time from completed POs (`received_date - order_date`) and on-time delivery rate (manual §6 line 70, 74).

---

### 1.2 Test Suite (`tests/analytics/`)
- `tests/analytics/test_manual_assertions.py`: Verifies literal manual worked examples `assert (10*5)+(10*2) == 70` (§3 line 35) and `assert (5*7)+(5*14) == 105` (§9 line 102).
- `tests/analytics/test_contracts.py`: Verifies `Computed` dataclass structure, invariants, and frozen published signatures matching `15-SHARED-CONTRACTS.md` §5.
- `tests/analytics/test_demand.py`: Verifies sales velocity, rolling windows, distinct day counts, and `MovementType` casing/name handling.
- `tests/analytics/test_reorder.py`: Verifies ROP and ROQ derivations under measured and configured lead times.
- `tests/analytics/test_edge_cases.py`: Verifies zero-history, single-observation (1 day), and negative-stock on-hand cases.
- `tests/analytics/test_sufficiency.py`: Verifies sufficiency scoring across thresholds.
- `tests/analytics/test_leadtime.py`: Verifies actual supplier lead time measurements, sample sizes, and on-time delivery rates.
- `tests/analytics/test_eoq.py`: Verifies economic order quantity batch sizing and invalid parameter handling.
- `tests/analytics/test_valuation.py`: Verifies inventory valuation at `cost_price`, days on hand, and stock turn ratio.

Total analytics tests: **36 passed**.

---

## 2. Integration Notes for Downstream Consumers (WS-3, WS-5, WS-7, WS-8, WS-15, WS-17)

- **Import path**:
  ```python
  from src.analytics import (
      Computed,
      compute_daily_demand,
      derive_reorder_point,
      derive_reorder_quantity,
      compute_eoq,
      score_sufficiency,
      measured_lead_time,
      inventory_value,
      days_on_hand,
      stock_turn,
  )
  ```
- **Zero Database Writes**: WS-1 is 100% pure query functions. No transactions are initiated or committed.
- **Clock Discipline**: 100% compliant with `src.core.clock.now()`. Zero calls to `datetime.now()`, `date.today()`, `time.time()`.
- **Sufficiency Handling**: Downstream consumers (e.g. WS-3 signals, WS-8 autonomy loop) should check `computed.sufficiency in ('insufficient', 'none')` or `computed.value is None` to trigger escalation / refusal paths.
