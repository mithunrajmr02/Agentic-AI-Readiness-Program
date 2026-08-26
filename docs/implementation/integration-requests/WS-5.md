# WS-5 — Integration Requests & Published Contracts

**Wave 1 · Policy Engine · status: COMPLETE, all tests green.**

## 1. What WS-5 Published

### 1.1 Policy Engine Core (`src/policy/`)
- `src/policy/__init__.py`: Public exports for `PolicyVerdict`, `DecisionContext`, `evaluate`, `evaluate_rules`, `DEFAULT_POLICY_LIMIT`, `CITATIONS`, `is_kill_switch_engaged`, `engage_kill_switch`, `release_kill_switch`, `check_blast_radius`, `get_effective_policy`, `get_policy_threshold`.
- `src/policy/rules.py`:
  - `@dataclass(frozen=True) PolicyVerdict`: `allowed`, `requires_approval`, `matched_rule`, `escalation_reason`, `citation`, `blast_radius`, `explanation`.
  - `@dataclass(frozen=True) DecisionContext`: `action_type`, `product_id`, `supplier_id`, `quantity`, `value_inr`, `sufficiency`, `is_cheapest_supplier`, `affected_product_count`, `autonomy_mode`.
  - `evaluate_rules(...)`: Pure evaluation of the ten authority rules in strict order (first match wins):
    1. R1: Kill switch engaged (`forbidden`)
    2. R2: Mode off (`forbidden`)
    3. R3: Mode shadow (`forbidden`)
    4. R4: Data sufficiency insufficient/none/thin (`requires_approval`, citing §4 line 45)
    5. R5: Blast-radius exceeded (`requires_approval`)
    6. R6: Non-cheapest supplier (`requires_approval`, citing §6 line 74)
    7. R7: Config change (`requires_approval`, citing §3 line 33)
    8. R8: Order value > policy limit (`requires_approval`, citing §10 line 113)
    9. R9: Mode assisted (`requires_approval`)
    10. R10: Within authority (`autonomous`)
- `src/policy/killswitch.py`: `is_kill_switch_engaged`, `engage_kill_switch` (mandatory reason), `release_kill_switch` (with `clock.now()` audit timestamps).
- `src/policy/blast_radius.py`: `check_blast_radius` evaluating hourly decision count and daily spend cap.
- `src/policy/evaluator.py`: `evaluate(db, context)` and `get_policy_threshold(db)`.

### 1.2 Policies REST API Router (`src/backend/routers/policies.py`)
- Exposes module-level `router = APIRouter(prefix="/api/policies", tags=["policies"])`
- Endpoints:
  - `GET /api/policies/autonomy` (Role: any)
  - `PATCH /api/policies/autonomy` (Role: manager)
  - `POST /api/policies/kill-switch` (Role: manager)
  - `GET /api/policies/threshold` (Role: any)
  - `GET /api/policies/reload` (Role: manager)

### 1.3 Test Suite (`tests/policy/`)
- `tests/policy/test_rules.py`: 30 unit tests covering all 10 rules, threshold boundaries (₹50,001 vs ₹50,000 vs ₹49,999), config changes at any value, precedence order.
- `tests/policy/test_killswitch.py`: 5 tests covering engagement, release, mandatory reasons, audit logs, and scoped overrides.
- `tests/policy/test_blast_radius.py`: 4 tests for hourly and daily cap enforcement.
- `tests/policy/test_evaluator.py`: 6 tests for DB-backed evaluation, threshold retrieval, and overrides.
- `tests/policy/test_router.py`: 10 tests verifying endpoints, envelopes, and manager RBAC 403 enforcement.

Total policy tests: **55 passed**.

---

## 2. Integration Notes for Integration Wave (Wave 4)

- **Router Wiring in `src/backend/main.py`**:
  ```python
  from src.backend.routers.policies import router as policies_router
  ...
  app.include_router(policies_router)
  ```
- **No dependencies added**: Standard library, SQLAlchemy, and FastAPI/Pydantic were used exclusively.
- **Clock Discipline**: 100% compliant with `clock.now()` / `clock.today()`. Zero usage of forbidden wall-clock functions.
