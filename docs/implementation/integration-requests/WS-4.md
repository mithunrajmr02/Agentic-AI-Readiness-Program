# WS-4 — Integration Requests & Published Contracts

**Wave 1 · Governance Backend · status: COMPLETE, all tests green.**

## 1. What WS-4 Published

### 1.1 Governance Core (`src/governance/`)
- `src/governance/__init__.py`: Public exports for `create_decision`, `record_refusal`, `get_decision`, `request_approval`, `approve`, `reject`, `get_approval`, `get_approval_for_decision`, `counter`, `CounterResult`, `list_decisions`, `format_decision_record`, `list_approvals`, `format_approval_record`.
- `src/governance/decisions.py`:
  - `create_decision(db, *, signal_id, action_type, inputs, computation, provenance, verdict, run_id, ...)`:
    - Sequential business identifier generation via `next_id("DEC")` (`DEC-000001`, `DEC-000002`, ...).
    - Stores explicit `clock.now()` timestamps (no database defaults).
    - Snapshots inputs, computation, provenance, and verbatim policy citations.
    - Emits synchronous in-process event `decision.created` with payload `{"decision_id", "signal_id", "action_type"}`.
  - `record_refusal(db, *, signal_id, reason, needed, have, ...)`:
    - Creates honest refusal decisions with `status="insufficient_data"`, `action_type="no_action"`, and `escalation_reason="insufficient_evidence"` (BW-5, D4).
    - Emits synchronous event `decision.refused` with payload `{"decision_id", "reason"}`.
  - `get_decision(db, decision_id)`: Fetches a single decision by its business ID.
- `src/governance/approvals.py`:
  - `request_approval(db, decision, *, requested_from_role="manager", sla_hours=24)`:
    - Sequential business identifier generation via `next_id("APR")` (`APR-000001`, `APR-000002`, ...).
    - Computes `expires_at = clock.now() + timedelta(hours=sla_hours)`.
    - Updates decision status to `"pending_approval"`.
    - Emits synchronous event `decision.pending_approval` with payload `{"decision_id", "approval_id", "escalation_reason"}`.
  - `approve(db, approval_id, user_id, rationale=None)`:
    - Validates approval is pending and not expired.
    - Updates approval to `outcome="approved"`, stamps `decided_at` and `decided_by_user_id`.
    - Transitions decision to `status="approved"`, `actor=f"user:{user_id}"`.
    - Does not require a rationale.
  - `reject(db, approval_id, user_id, rationale)`:
    - Enforces mandatory, non-empty rationale string.
    - Updates approval to `outcome="rejected"`, transitions decision to `status="rejected"`.
  - `get_approval(db, approval_id)` & `get_approval_for_decision(db, decision_id)`.
- `src/governance/counter.py`:
  - `@dataclass(frozen=True) CounterResult`: `decision: Decision`, `recomputed: dict`, `system_objection: str | None`, `accepted: bool`.
  - `counter(db, approval_id, user_id, payload)`:
    - Recomputes stock coverage, post-receipt stock level, and days to re-breach against human-provided quantity.
    - Generates deterministic `system_objection` when the human's quantity leads to premature re-breach below safety stock.
    - Stores `system_objection` and `objection_overridden=True` on the approval and decision records.
    - Transitions approval to `outcome="countered"` and decision to `status="countered"`.
- `src/governance/ledger.py`:
  - `list_decisions` & `list_approvals`: Query and filter ledger entries by status, action_type, actor, signals, runs, and outcomes.
  - `format_decision_record`: Deserializes JSON columns (`inputs`, `computation`, `provenance`) and attaches the projected 4-value graded `analysis_status` (`analyzing`, `reorder_required`, `healthy`, `complete`) per doc 15 §2.5.
  - `format_approval_record`: Formats approval details, parses `counter_payload`, and derives SLA expiration status.

### 1.2 REST API Routers (`src/backend/routers/`)
- `src/backend/routers/decisions.py`:
  - Module-level router: `router = APIRouter(prefix="/api/decisions", tags=["decisions"])`.
  - `GET /api/decisions`: Filterable list wrapped in `ResponseEnvelope`.
  - `GET /api/decisions/{decision_id}`: Full decision audit details.
  - `GET /api/decisions/{decision_id}/run`: Linked agent run telemetry trace from `agent_runs`.
  - **No POST endpoint** (decisions are created by internal graph/governance only).
- `src/backend/routers/approvals.py`:
  - Module-level router: `router = APIRouter(prefix="/api/approvals", tags=["approvals"])`.
  - RBAC: Enforces manager role authorization (returns HTTP 403 naming required role per M-34); blocks agent self-approval (HTTP 403).
  - `GET /api/approvals`: Approval queue list.
  - `GET /api/approvals/{approval_id}`: Approval detail with linked decision.
  - `POST /api/approvals/{approval_id}/approve`: Door 1 (Manager approval).
  - `POST /api/approvals/{approval_id}/reject`: Door 2 (Manager rejection with mandatory rationale).
  - `POST /api/approvals/{approval_id}/counter`: Door 3 (Manager counter-proposal with recomputation and objection).

### 1.3 Test Suite (`tests/governance/`)
- `tests/governance/test_decisions.py`: Decision creation, auto-approval, pending approval, refusal recording, and 12-to-4 status projections.
- `tests/governance/test_approvals.py`: Approval lifecycle, approve without rationale, reject requiring rationale, SLA expiration handling, and double-resolution protection.
- `tests/governance/test_counter.py`: Counter-proposal recomputation, system objection derivation, and persistence.
- `tests/governance/test_ledger.py`: Filtering decisions and approvals by status/action/signals.
- `tests/governance/test_api.py`: REST response envelopes, parameter filtering, and RBAC enforcement (401 unauthenticated, 403 staff, 403 agent).

Total governance tests: **28 passed**.

---

## 2. Integration Notes for Integration Wave (Wave 4)

- **Router Wiring in `src/backend/main.py`**:
  ```python
  from src.backend.routers.decisions import router as decisions_router
  from src.backend.routers.approvals import router as approvals_router
  ...
  app.include_router(decisions_router)
  app.include_router(approvals_router)
  ```
- **Dependencies**: No external runtime dependencies added. Uses standard library, SQLAlchemy, and FastAPI.
- **Clock Discipline**: 100% compliant with `clock.now()` / `clock.today()`. Zero usage of forbidden wall-clock functions.
- **Schema Separation**: Zero modifications to `src/backend/models.py`. All writes target `models_governance.py` (`decisions`, `approvals`).
