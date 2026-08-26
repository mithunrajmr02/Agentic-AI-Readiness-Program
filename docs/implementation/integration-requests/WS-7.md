# WS-7 — Integration Requests & Published Contracts

**Wave 1 · Supplier Intelligence · status: COMPLETE, all tests green.**

## 1. What WS-7 Published

### 1.1 Sourcing Core (`src/sourcing/`)
- `src/sourcing/__init__.py`: Public exports for `Scorecard`, `scorecard`, `SupplierChoice`, `select_supplier`, `compute_supplier_drift`, `detect_supplier_drift`, `list_supplier_drifts`.
- `src/sourcing/scorecard.py`:
  - `Scorecard` dataclass: `supplier_id: int`, `on_time_rate: float | None`, `sample_size: int`, `avg_days_late: float | None`, `contract_lead_time: int`, `measured_lead_time: float | None`, `drift_days: float | None`.
  - `scorecard(db, supplier_id: int) -> Scorecard`: Evaluates completed POs (`received_date.isnot(None)`).
  - **`n = 1` honesty rule (doc 14 §WS-7, doc 18 §4.7)**: When `sample_size < 5`, `on_time_rate` is strictly `None` to eliminate fabricated percentages from insufficient observations.
- `src/sourcing/selection.py`:
  - `SupplierChoice` dataclass: `supplier_id: int`, `unit_price: float`, `lead_time_days: int`, `is_cheapest: bool`, `rejected_alternatives: list[dict]`, `rationale: str`.
  - `select_supplier(db, product_id: int, quantity: int = 1, prefer_supplier_id: int | None = None) -> SupplierChoice`:
    - Queries active suppliers in `supplier_products`.
    - Fallback to `Product.supplier_id` default supplier.
    - **Active supplier precondition (manual §6 line 74)**: Inactive suppliers are excluded by construction.
    - Resolves cheapest active supplier and populates `rejected_alternatives` with price/lead-time delta explanations.
    - Raises `InsufficientData` when 0 active suppliers exist.
- `src/sourcing/drift.py`:
  - `compute_supplier_drift(db, supplier_id: int) -> dict`: Evaluates variance between contractual lead time and actual delivery fulfillment time, collecting PO evidence (e.g. `PO-2026-0001` +4 days drift vs contract).
  - `detect_supplier_drift(db, supplier_id: int, tolerance_days: float = 0.0) -> dict | None`.
  - `list_supplier_drifts(db, tolerance_days: float = 0.0) -> list[dict]`.

### 1.2 Suppliers REST API Router (`src/backend/routers/suppliers.py`)
- Exposes module-level `router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])`
- Endpoints:
  - `GET /api/suppliers`: List registered suppliers (supports `active_only` filter).
  - `GET /api/suppliers/{supplier_id}`: Supplier details with embedded scorecard.
  - `GET /api/suppliers/{supplier_id}/scorecard`: Standalone supplier reliability & lead-time scorecard.
  - `GET /api/suppliers/compare/{product_id}`: Catalog comparison from `supplier_products` with recommended `SupplierChoice`.
  - `GET /api/suppliers/{supplier_id}/products`: Catalog of products provided by this supplier.
  - `GET /api/suppliers/{supplier_id}/drift`: Drift analysis with PO delivery evidence.
  - `GET /api/suppliers/drifts/all`: All suppliers exhibiting lead-time drift above tolerance.
- All responses wrapped in standard `success_envelope` / `error_envelope`.

### 1.3 Test Suite (`tests/sourcing/`)
- `tests/sourcing/conftest.py`: Fixtures with in-memory SQLite DB, seed suppliers, products, PO-2026-0001, supplier_products, and TestClient.
- `tests/sourcing/test_scorecard.py`:
  - `test_scorecard_empty_history`: `sample_size=0`, `on_time_rate=None`.
  - `test_scorecard_single_observation_honesty`: `sample_size=1`, `on_time_rate=None` (n = 1 honesty test).
  - `test_scorecard_multiple_observations_produces_rate`: `sample_size=5` produces `on_time_rate=0.8`.
  - `test_scorecard_invalid_supplier_raises_value_error`.
  - `test_scorecard_on_seeded_database`: Verifies live seeded DB (`PO-2026-0001` with supplier 4 -> `sample_size=1`, `measured_lead_time=9.0`, `drift_days=4.0`).
- `tests/sourcing/test_selection.py`:
  - `test_select_supplier_chooses_cheapest_active`: Resolves cheapest active supplier and captures rejected alternatives.
  - `test_select_supplier_inactive_excluded`: Inactive suppliers excluded even when cheaper (§6 line 74).
  - `test_select_supplier_fallback_to_product_default`: Graceful fallback to `Product.supplier_id`.
  - `test_select_supplier_no_active_supplier_raises_insufficient_data`: `InsufficientData` error when 0 active suppliers.
  - `test_select_supplier_with_preference`: Evaluates non-cheapest supplier preference with `is_cheapest=False`.
  - `test_select_supplier_on_seeded_database`.
- `tests/sourcing/test_drift.py`:
  - `test_supplier_drift_computation`: `PO-2026-0001` produces +4 days drift vs contract.
  - `test_detect_supplier_drift_with_tolerance`: Tolerance filtering.
  - `test_supplier_drift_on_seeded_database`.
- `tests/sourcing/test_router.py`:
  - `test_list_suppliers`, `test_get_supplier_detail`, `test_get_supplier_scorecard`, `test_compare_suppliers_for_product`, `test_get_supplier_products`, `test_get_supplier_drift`, `test_get_all_drifts`, `test_nonexistent_supplier_returns_404`.

Total sourcing tests: **21 passed**.

---

## 2. Integration Notes for Integration Wave (Wave 4)

- **Router Wiring in `src/backend/main.py`**:
  ```python
  from src.backend.routers.suppliers import router as suppliers_router
  ...
  app.include_router(suppliers_router)
  ```
- **Frozen File Compliance**:
  - `src/backend/main.py`: Unmodified. Module-level `router` published.
  - `src/backend/models.py`: Unmodified. Consumes `models.py` and `models_sourcing.py`.
  - `requirements.txt`: Unmodified.
  - `tests/phase1..5/`: Unmodified.
- **Clock Discipline**: 100% compliant with `clock.now()` / `clock.today()`. No forbidden wall-clock functions.
- **Graded Invariants**: Zero writes outside owned directories; no SQLAlchemy Enums on new structures.
