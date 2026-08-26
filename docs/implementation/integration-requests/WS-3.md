# WS-3 — Integration Requests & Published Contracts

**Wave 1 · Signal Engine · status: COMPLETE, all tests green.**

## 1. What WS-3 Published

### 1.1 Signal Engine Core (`src/signals/`)
- `src/signals/__init__.py`: Public exports for `SignalCandidate`, `raise_signal`, `resolve_signal`, `get_signal`, `list_signals`, `run_detectors`, `dedup_key_for`, `setup_event_handlers`.
- `src/signals/dedup.py`: Canonical deduplication keys formatted as `{signal_type}:prod:{product_id}`, `{signal_type}:po:{po_id}`, `{signal_type}:supp:{supplier_id}`, and `{signal_type}:global`.
- `src/signals/analytics_adapter.py`: Pure metrics derivation adapter conforming to the frozen `Computed` contract. Strictly returns `value=None` whenever sufficiency is `insufficient` or `none`.
- `src/signals/detectors/`:
  - `threshold_breach.py`: Evaluates `quantity_on_hand <= reorder_point` (critical when stock = 0; citations: §4 line 41, §4 line 43).
  - `projected_breach.py`: Forecasts stock depletion within lead time + safety stock (citation: §3 line 33).
  - `po_overdue.py`: Detects `expected_delivery < clock.today()` on unreceived purchase orders (citation: §10 item 4).
  - `config_drift.py`: Identifies `abs(configured_rop - computed_rop) / computed_rop > 20%` (citation: §3 line 33).
  - `supplier_drift.py`: Detects measured lead time > contract lead time or on-time rate < 80% (citation: §6 line 74).
  - `capital_drag.py`: Flags inventory with days on hand > 60 or inactive for 30+ days (citation: §13 line 136).
  - `data_insufficient.py`: Detects cold-start products with insufficient sales history (specifically flags Colgate; citation: §4 line 45).
- `src/signals/engine.py`:
  - Sequential ID generation via `next_id("SIG")` (`SIG-000001`, `SIG-000002`, ...).
  - Synchronous scanning (`run_detectors`) across catalog or scoped product IDs.
  - Lifecycle state management (`open`, `resolved`).
  - Event subscriptions: `stock.movement_recorded`, `stock.level_changed`, `po.received`, `decision.executed`.
  - Event publications: `signal.raised`, `signal.resolved`.

### 1.2 Signals REST API Router (`src/backend/routers/signals.py`)
- Exposes module-level `router = APIRouter(prefix="/api/signals", tags=["signals"])`
- Endpoints:
  - `GET /api/signals`: Filter by `status`, `signal_type`, `severity`, `product_id`, `supplier_id`, `po_id`.
  - `GET /api/signals/{signal_id}`: Detail view with parsed structured evidence.
  - `POST /api/signals/scan`: Run synchronous detection scan.
  - `POST /api/signals/{signal_id}/dismiss`: Dismiss/resolve open signal.
- All responses are wrapped in `success_envelope` / `error_envelope`.

### 1.3 Test Suite (`tests/signals/`)
- `tests/signals/test_threshold_breach.py`: Out-of-stock and low-stock assertions.
- `tests/signals/test_projected_breach.py`: Stock velocity and lead-time depletion assertions.
- `tests/signals/test_po_overdue.py`: Overdue delivery and simulation clock advance assertions.
- `tests/signals/test_config_drift.py`: ROP config drift and tolerance assertions.
- `tests/signals/test_supplier_drift.py`: Measured lead time and supplier reliability drift assertions.
- `tests/signals/test_capital_drag.py`: Dormant/excess inventory capital drag assertions.
- `tests/signals/test_data_insufficient.py`: **Colgate data insufficiency assertion** and healthy history assertion.
- `tests/signals/test_dedup.py`: Idempotent open signal updates and post-resolution regeneration.
- `tests/signals/test_engine.py`: Engine scan, query filters, and event bus handlers.
- `tests/signals/test_router.py`: REST endpoints, envelopes, and status codes.

Total signals tests: **39 passed**.

---

## 2. Integration Notes for Integration Wave (Wave 4)

- **Router Wiring in `src/backend/main.py`**:
  ```python
  from src.backend.routers.signals import router as signals_router
  ...
  app.include_router(signals_router)
  ```
- **Event Bus Wiring**:
  ```python
  from src.signals.engine import setup_event_handlers
  ...
  setup_event_handlers()
  ```
- **Dependencies**: No external runtime dependencies added. Uses standard library, SQLAlchemy, and FastAPI.
- **Clock Discipline**: 100% compliant with `clock.now()` / `clock.today()`. Zero usage of forbidden wall-clock functions.
- **Decisions Separation**: WS-3 creates zero rows in `decisions` table (strict separation between WS-3 detection and WS-4 decisioning).
