"""``/api/simulation`` — the HTTP surface, including both refusals.

The router is tested against a minimal app that mounts only ``router``, with
``get_db`` and ``get_current_user`` overridden. That is deliberate: the module
publishes a router and stops, because wiring it into ``main.py`` is an integration
step owned by another stream. A test that asserted the wiring exists would fail
today and, worse, would fail again the day the wiring lands correctly.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.database import get_db
from src.backend.routers.auth import get_current_user
from src.backend.routers.simulation import router


class _User:
    """Just enough user for the RBAC gate: it reads ``role`` and nothing else."""

    def __init__(self, role):
        self.id = 1
        self.email = f"{role}@retail.com"
        self.role = role


def _client(db, role="manager"):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: _User(role)
    return TestClient(app)


@pytest.fixture
def manager(db, demo_mode):
    return _client(db)


# --- the two gates ------------------------------------------------------------


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/simulation/scenarios"),
        ("post", "/api/simulation/scenarios/D1_governed_order/load"),
        ("get", "/api/simulation/scenarios/D1_governed_order/verify"),
        ("post", "/api/simulation/clock"),
        ("post", "/api/simulation/reset"),
    ],
)
def test_every_endpoint_refuses_without_demo_mode(db, no_demo_mode, method, path):
    """Doc 13 §4: *"A time machine and a database reset are not features of a
    production inventory system."* Every endpoint, not most of them."""
    client = _client(db)
    # Only the POST bodies carry a payload; this client's `get` takes no `json`.
    kwargs = {"json": {"days": 0}} if method == "post" else {}
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 403
    body = response.json()
    assert body["error"]["code"] == "demo_mode_required"
    assert body["error"]["needed"] == "DEMO_MODE=true"


@pytest.mark.parametrize("role", ["staff", "agent"])
def test_a_non_manager_is_refused_and_told_which_role_it_needs(db, demo_mode, role):
    """M-34 and §12.4: a 403 body names the required role. "Forbidden" with no
    explanation is what makes RBAC feel like a malfunction."""
    client = _client(db, role=role)
    response = client.get("/api/simulation/scenarios")
    assert response.status_code == 403
    body = response.json()
    assert body["error"]["code"] == "rbac_denied"
    assert "manager" in body["error"]["needed"]
    assert role in body["error"]["have"]


def test_the_demo_mode_gate_is_checked_before_the_role_gate(db, no_demo_mode):
    """Whether this surface exists at all should not depend on who is asking, so a
    staff user in production learns the harness is off — not that they are the
    wrong role for an endpoint that should never be reachable."""
    client = _client(db, role="staff")
    response = client.get("/api/simulation/scenarios")
    assert response.json()["error"]["code"] == "demo_mode_required"


def test_the_error_body_is_not_nested_under_detail(db, no_demo_mode):
    """``HTTPException`` would render ``{"detail": {"error": ...}}`` and break the
    frozen §12.3 envelope. This is why the guards return a response."""
    response = _client(db).get("/api/simulation/scenarios")
    assert "detail" not in response.json()
    assert set(response.json()) == {"error"}


# --- envelopes ----------------------------------------------------------------


def test_the_success_envelope_carries_the_frozen_meta_block(manager):
    response = manager.get("/api/simulation/scenarios")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"data", "meta"}
    meta = body["meta"]
    assert set(meta) == {"computed_at", "clock_offset_days", "provenance", "data_disclosure"}
    assert meta["clock_offset_days"] == 0
    assert all(isinstance(value, str) for value in meta["provenance"].values())


def test_every_response_declares_the_data_as_synthetic(manager):
    """Doc 13's whole dataset is designed. A response that let a reader assume
    otherwise would be the most consequential lie the system could tell."""
    for method, path in (
        ("get", "/api/simulation/scenarios"),
        ("get", "/api/simulation/scenarios/D1_governed_order/verify"),
        ("post", "/api/simulation/reset"),
    ):
        response = getattr(manager, method)(path)
        assert response.status_code == 200, path
        assert response.json()["meta"]["data_disclosure"] == "synthetic", path


# --- scenarios ---------------------------------------------------------------


def test_listing_returns_the_four_scenarios_in_demo_order(manager):
    from src.simulation.scenarios import SCENARIO_KEYS

    data = manager.get("/api/simulation/scenarios").json()["data"]
    assert [row["key"] for row in data] == list(SCENARIO_KEYS)
    assert all(row["expected_signals"] for row in data)


def test_loading_a_scenario_seeds_the_history(manager):
    response = manager.post("/api/simulation/scenarios/D1_governed_order/load")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["key"] == "D1_governed_order"
    assert data["clock_offset_days"] == 0
    assert data["seeded"]["history"]["distinct_recorded_dates"] >= 90


def test_an_unknown_scenario_key_is_a_404_not_a_500(manager):
    for method, path in (
        ("post", "/api/simulation/scenarios/D9_nope/load"),
        ("get", "/api/simulation/scenarios/D9_nope/verify"),
    ):
        response = getattr(manager, method)(path)
        assert response.status_code == 404, path
        assert response.json()["error"]["code"] == "scenario_not_found", path
        assert "D9_nope" in response.json()["error"]["message"], path


def test_verify_reports_failure_as_a_200_with_passed_false(manager):
    """A scenario whose signals have not been raised is a *result*, not a
    transport error. CI reads ``passed``; an HTTP failure code here would conflate
    "the pipeline is wrong" with "the request went wrong"."""
    manager.post("/api/simulation/scenarios/D4_refusal/load")
    response = manager.get("/api/simulation/scenarios/D4_refusal/verify")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["passed"] is False
    assert len(data["missing"]) == data["expected_count"]


def test_verify_reports_pass_once_the_signals_exist(manager, db, raise_signals):
    from src.simulation.scenarios import _decode, get_scenario

    manager.post("/api/simulation/scenarios/D4_refusal/load")
    raise_signals(_decode(get_scenario(db, "D4_refusal").expected_signals, []))

    data = manager.get("/api/simulation/scenarios/D4_refusal/verify").json()["data"]
    assert data["passed"] is True
    assert data["missing"] == []


# --- the clock ---------------------------------------------------------------


def test_moving_the_clock_returns_both_offsets_and_the_new_date(manager):
    from src.core import clock

    response = manager.post("/api/simulation/clock", json={"days": 14})
    assert response.status_code == 200
    data = response.json()["data"]
    assert (data["from_offset"], data["to_offset"]) == (0, 14)
    assert data["today"] == clock.today().isoformat()
    assert clock.offset_days() == 14


def test_days_is_absolute_so_the_same_request_twice_lands_on_the_same_date(manager):
    """Pressing the same button twice must not drift. A presenter who clicks
    "+14 days" twice because the first click looked slow should not end up a
    month out with no way to tell."""
    first = manager.post("/api/simulation/clock", json={"days": 14}).json()["data"]
    second = manager.post("/api/simulation/clock", json={"days": 14}).json()["data"]
    assert second["to_offset"] == first["to_offset"] == 14
    assert second["today"] == first["today"]


def test_relative_moves_from_wherever_the_clock_currently_sits(manager):
    manager.post("/api/simulation/clock", json={"days": 10})
    data = manager.post("/api/simulation/clock", json={"days": 5, "relative": True}).json()["data"]
    assert (data["from_offset"], data["to_offset"]) == (10, 15)


def test_the_clock_can_be_moved_backwards(manager):
    """Projections are the interesting direction, but a presenter who overshoots
    needs a way back that is not a database reset."""
    manager.post("/api/simulation/clock", json={"days": 30})
    data = manager.post("/api/simulation/clock", json={"days": -30, "relative": True}).json()["data"]
    assert data["to_offset"] == 0


def test_moving_the_clock_emits_clock_advanced_with_both_offsets(manager):
    """``clock`` deliberately knows nothing about the event bus — its docstring
    says this event is the router's job. A detector needs the interval it skipped,
    not only where it landed, so both offsets are in the payload."""
    from src.core import events

    seen = []
    events.subscribe("clock.advanced", seen.append)
    try:
        manager.post("/api/simulation/clock", json={"days": 7})
        manager.post("/api/simulation/clock", json={"days": 3, "relative": True})
    finally:
        events._subscribers.pop("clock.advanced", None)

    assert seen == [
        {"from_offset": 0, "to_offset": 7},
        {"from_offset": 7, "to_offset": 10},
    ]


def test_the_clock_endpoint_refuses_without_demo_mode_before_touching_the_clock(db, no_demo_mode):
    """The gate is the router's, and ``clock.set_offset`` has its own. Belt and
    braces on the one operation that can invalidate every timestamp in the
    database."""
    from src.core import clock

    response = _client(db).post("/api/simulation/clock", json={"days": 30})
    assert response.status_code == 403
    assert clock.offset_days() == 0


def test_a_clock_refusal_from_the_core_becomes_a_409(db, monkeypatch, demo_mode):
    """If the two DEMO_MODE checks ever disagree, the core's ``RuntimeError`` must
    surface as a precondition failure in the frozen envelope — never as a 500."""
    from src.core import clock

    def refuse(_offset):
        raise RuntimeError("clock.set_offset is simulation-only and requires DEMO_MODE")

    monkeypatch.setattr(clock, "set_offset", refuse)
    response = _client(db).post("/api/simulation/clock", json={"days": 5})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "precondition_failed"


def test_a_non_integer_offset_is_rejected_by_validation(manager):
    response = manager.post("/api/simulation/clock", json={"days": "next tuesday"})
    assert response.status_code == 422


# --- reset -------------------------------------------------------------------


def test_reset_restores_the_baseline_positions_over_http(manager, db):
    from src.simulation.backfill import distinct_recorded_dates

    manager.post("/api/simulation/scenarios/D1_governed_order/load")
    assert distinct_recorded_dates(db) >= 90

    data = manager.post("/api/simulation/reset").json()["data"]
    assert data["positions"] == {
        "SKU-GRO-0001": 167,
        "SKU-ELC-0001": 4,
        "SKU-ELC-0002": 0,
        "SKU-HHD-0001": 50,
        "SKU-PRC-0001": 0,
    }
    assert distinct_recorded_dates(db) == 1


def test_reset_returns_the_clock_to_real_time_over_http(manager):
    from src.core import clock

    manager.post("/api/simulation/clock", json={"days": 45})
    manager.post("/api/simulation/reset")
    assert clock.offset_days() == 0


# --- shape -------------------------------------------------------------------


def test_the_router_is_mounted_under_the_documented_prefix():
    """Doc 13 §4's paths, asserted on the router itself rather than on ``main.py``,
    which this stream does not own and must not wire."""
    assert router.prefix == "/api/simulation"
    paths = {route.path for route in router.routes}
    assert paths == {
        "/api/simulation/scenarios",
        "/api/simulation/scenarios/{key}/load",
        "/api/simulation/scenarios/{key}/verify",
        "/api/simulation/clock",
        "/api/simulation/reset",
    }
