"""Tests for Impact REST API router endpoints (WS-17)."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.database import get_db
from src.backend.routers.impact import router


@pytest.fixture
def client(test_db):
    """TestClient with impact router mounted and DB dependency overridden."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: test_db
    with TestClient(app) as c:
        yield c


def test_get_impact_summary(client):
    """Test GET /api/impact/summary and GET /api/impact."""
    response = client.get("/api/impact/summary")
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert "meta" in body
    assert "metrics" in body["data"]
    assert "categories" in body["data"]
    assert body["meta"]["data_disclosure"] == "synthetic"


def test_get_detection_metrics(client):
    """Test GET /api/impact/detection."""
    response = client.get("/api/impact/detection")
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert len(data) == 6
    keys = [m["key"] for m in data]
    assert keys == ["M-1", "M-2", "M-3", "M-4", "M-5", "M-6"]


def test_get_decision_metrics(client):
    """Test GET /api/impact/decision."""
    response = client.get("/api/impact/decision")
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert len(data) == 7
    keys = [m["key"] for m in data]
    assert keys == ["M-7", "M-8", "M-9", "M-10", "M-11", "M-12", "M-13"]


def test_get_method_metrics(client):
    """Test GET /api/impact/method (reviewer's block)."""
    response = client.get("/api/impact/method")
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert len(data) == 4
    keys = [m["key"] for m in data]
    assert keys == ["M-14", "M-15", "M-16", "M-17"]

    # M-14 value is 0.0
    m14 = next(m for m in data if m["key"] == "M-14")
    assert m14["value"] == 0.0


def test_get_position_metrics(client):
    """Test GET /api/impact/position."""
    response = client.get("/api/impact/position")
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert len(data) == 5
    keys = [m["key"] for m in data]
    assert keys == ["M-18", "M-19", "M-20", "M-21", "M-22"]


def test_get_impact_gaps(client):
    """Test GET /api/impact/gaps ('WHAT WE CANNOT MEASURE YET')."""
    response = client.get("/api/impact/gaps")
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert len(data) == 8

    for m in data:
        assert m["tier"] == "T3"
        assert m["value"] is None
        assert m["missing_input"] is not None
        assert len(m["missing_input"]) > 0


def test_get_all_metrics(client):
    """Test GET /api/impact/all."""
    response = client.get("/api/impact/all")
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert len(data) == 36


def test_get_single_metric_found_and_not_found(client):
    """Test GET /api/impact/metric/{key}."""
    res_ok = client.get("/api/impact/metric/M-14")
    assert res_ok.status_code == 200
    assert res_ok.json()["data"]["key"] == "M-14"

    res_not_found = client.get("/api/impact/metric/M-999")
    assert res_not_found.status_code == 404


def test_create_and_query_snapshots(client):
    """Test POST /api/impact/snapshots and GET /api/impact/snapshots/{metric_key}."""
    post_res = client.post("/api/impact/snapshots")
    assert post_res.status_code == 200
    assert len(post_res.json()["data"]) == 36

    get_res = client.get("/api/impact/snapshots/M-14")
    assert get_res.status_code == 200
    history = get_res.json()["data"]
    assert len(history) >= 1
    assert history[0]["metric_key"] == "M-14"
    assert history[0]["value"] == 0.0
