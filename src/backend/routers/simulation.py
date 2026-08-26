"""``/api/simulation`` — the demo harness control surface.

Doc 13 §4. Four operations: list the scenarios, load one, move the clock, and
verify that what the pipeline raised matches what the scenario said it would.

    GET  /api/simulation/scenarios
    POST /api/simulation/scenarios/{key}/load
    GET  /api/simulation/scenarios/{key}/verify
    POST /api/simulation/clock
    POST /api/simulation/reset

``verify`` is the endpoint most demo tooling omits, and it is the reason the
pre-flight checklist is a request rather than a visual inspection.

Two gates, both mandatory
-------------------------
Doc 13 §4: *"Every simulation endpoint is manager-only, and every one is disabled
unless ``DEMO_MODE=true``. A time machine and a database reset are not features of
a production inventory system."* Both checks run before any work, in that order —
DEMO_MODE first, because whether this surface exists at all should not depend on
who is asking.

Integration status
------------------
Wired into ``src/backend/main.py`` by the Wave-1 integration commit; the router is
registered and all five operations are reachable. The remaining request filed in
``docs/implementation/integration-requests/WS-2.md`` -- an app-level
``StewardError`` handler so error bodies keep the frozen ``{"error": {...}}``
shape -- is still open, which is why the guards below still hand-build their
responses.

Why the error bodies are hand-built
-----------------------------------
``HTTPException`` renders its payload under ``detail``, which would produce
``{"detail": {"error": {...}}}`` and break the frozen §12.3 envelope. Until a
``StewardError`` handler is registered at app level, these endpoints return an
explicit ``JSONResponse`` carrying the envelope verbatim. That is why the guards
return a response instead of raising.
"""
import os

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.contracts.envelopes import ErrorDetail, ErrorEnvelope, success_envelope
from src.backend.database import get_db
from src.backend.models import User
from src.backend.routers.auth import MANAGER_ROLE, get_current_user
from src.core import clock, events
from src.simulation.reset import reset_simulation
from src.simulation.scenarios import list_scenarios, load_scenario, verify_scenario

router = APIRouter(prefix="/api/simulation", tags=["simulation"])

#: Mirrors the truthy set ``clock`` uses for its own DEMO_MODE gate. Duplicated
#: rather than imported because ``clock`` exposes it privately, and this router
#: must be able to refuse before it touches the clock at all. WS-2.md asks WS-0 to
#: publish a public ``clock.demo_mode_enabled()`` so the two cannot drift.
_DEMO_TRUTHY = frozenset({"1", "true", "yes", "on"})

#: Everything this router returns describes a designed fixture. Never "real".
DISCLOSURE = "synthetic"


def demo_mode_enabled() -> bool:
    """Read DEMO_MODE at call time, not import time, so it stays configurable."""
    return os.getenv("DEMO_MODE", "").strip().lower() in _DEMO_TRUTHY


def _error(status_code: int, code: str, message: str, **extra) -> JSONResponse:
    """Build a frozen §12.3 error body from the WS-0 models, not by hand."""
    envelope = ErrorEnvelope(error=ErrorDetail(code=code, message=message, **extra))
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


def _guard(current_user: User) -> JSONResponse | None:
    """The two gates. Returns a response to send, or ``None`` to proceed."""
    if not demo_mode_enabled():
        return _error(
            403,
            "demo_mode_required",
            "The simulation harness is disabled. It is development infrastructure, "
            "not a feature of a production inventory system.",
            needed="DEMO_MODE=true",
            have="DEMO_MODE unset or false",
        )
    if getattr(current_user, "role", None) != MANAGER_ROLE:
        # §12.4 / M-34: a 403 body names the role the caller would need.
        return _error(
            403,
            "rbac_denied",
            f"The simulation harness requires the '{MANAGER_ROLE}' role.",
            needed=f"role '{MANAGER_ROLE}'",
            have=f"role '{getattr(current_user, 'role', None)}'",
        )
    return None


class ClockRequest(BaseModel):
    """``{"days": n}`` — doc 13 §4.

    ``days`` is the **absolute** simulation offset by default, so pressing the
    same button twice lands on the same date instead of drifting. Pass
    ``relative: true`` to move by ``days`` from wherever the clock currently sits.
    """

    days: int = Field(description="Simulation offset in days (absolute unless relative=true)")
    relative: bool = Field(default=False, description="Treat `days` as a delta from the current offset")


@router.get("/scenarios")
def get_scenarios(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Every scenario, its seed spec, and the signals it asserts."""
    denied = _guard(current_user)
    if denied is not None:
        return denied
    return success_envelope(
        list_scenarios(db),
        provenance={"scenarios": "retrieved"},
        data_disclosure=DISCLOSURE,
    )


@router.post("/scenarios/{key}/load")
def post_load_scenario(
    key: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Reset, seed, and set the clock offset. Idempotent — doc 13 §4."""
    denied = _guard(current_user)
    if denied is not None:
        return denied
    try:
        result = load_scenario(db, key)
    except KeyError:
        return _error(404, "scenario_not_found", f"No demo scenario with key '{key}'.")
    except RuntimeError as exc:
        # clock.set_offset refusing a nonzero offset without DEMO_MODE. The world
        # is not in the state this action requires — §12.4 → 409.
        return _error(409, "precondition_failed", str(exc))
    return success_envelope(
        result, provenance={"dataset": "computed"}, data_disclosure=DISCLOSURE
    )


@router.get("/scenarios/{key}/verify")
def get_verify_scenario(
    key: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Compare the signals raised against ``expected_signals``. Returns pass/fail."""
    denied = _guard(current_user)
    if denied is not None:
        return denied
    try:
        result = verify_scenario(db, key)
    except KeyError:
        return _error(404, "scenario_not_found", f"No demo scenario with key '{key}'.")
    return success_envelope(
        result, provenance={"verification": "computed"}, data_disclosure=DISCLOSURE
    )


@router.post("/clock")
def post_clock(
    payload: ClockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Move the simulation calendar and announce it.

    ``clock`` deliberately knows nothing about the event bus, so this endpoint is
    where ``clock.advanced`` is emitted — carrying both the old and the new offset,
    because a time-based detector needs to know the interval it just skipped, not
    only where it landed.
    """
    denied = _guard(current_user)
    if denied is not None:
        return denied

    from_offset = clock.offset_days()
    to_offset = from_offset + payload.days if payload.relative else payload.days
    try:
        clock.set_offset(to_offset)
    except RuntimeError as exc:
        return _error(409, "precondition_failed", str(exc))

    events.emit("clock.advanced", {"from_offset": from_offset, "to_offset": to_offset})
    return success_envelope(
        {
            "from_offset": from_offset,
            "to_offset": clock.offset_days(),
            "now": clock.now().isoformat(),
            "today": clock.today().isoformat(),
        },
        provenance={"clock": "computed"},
        data_disclosure=DISCLOSURE,
    )


@router.post("/reset")
def post_reset(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Remove everything the harness wrote and restore the baseline positions."""
    denied = _guard(current_user)
    if denied is not None:
        return denied
    return success_envelope(
        reset_simulation(db), provenance={"reset": "computed"}, data_disclosure=DISCLOSURE
    )
