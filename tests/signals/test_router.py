"""Tests for signals REST router (WS-3)."""
from fastapi import status

from src.signals.engine import raise_signal


def test_get_signals_endpoint(client, sample_data, db):
    """GET /api/signals returns wrapped response envelope with signal items."""
    p_rice = sample_data["products"]["rice"]
    raise_signal(
        db,
        signal_type="threshold_breach",
        severity="medium",
        product_id=p_rice.id,
        detected_from="Test breach",
        evidence={"on_hand": 10},
    )

    response = client.get("/api/signals")
    assert response.status_code == status.HTTP_200_OK

    payload = response.json()
    assert "data" in payload
    assert "meta" in payload
    assert payload["meta"]["data_disclosure"] == "synthetic"
    assert len(payload["data"]) >= 1

    item = payload["data"][0]
    assert "signal_id" in item
    assert "signal_type" in item
    assert "evidence" in item


def test_get_signal_by_id_success_and_404(client, sample_data, db):
    """GET /api/signals/{signal_id} returns detail or 404."""
    p_rice = sample_data["products"]["rice"]
    sig = raise_signal(
        db,
        signal_type="threshold_breach",
        severity="critical",
        product_id=p_rice.id,
        detected_from="Test critical breach",
        evidence={"on_hand": 0},
    )

    # 200 OK
    res = client.get(f"/api/signals/{sig.signal_id}")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()["data"]
    assert data["signal_id"] == sig.signal_id
    assert data["severity"] == "critical"
    assert data["evidence"]["on_hand"] == 0

    # 404 Not Found
    res404 = client.get("/api/signals/SIG-999999")
    assert res404.status_code == status.HTTP_404_NOT_FOUND


def test_scan_signals_endpoint(client, sample_data):
    """POST /api/signals/scan executes detectors and returns newly generated signals."""
    response = client.post("/api/signals/scan", json={})
    assert response.status_code == status.HTTP_200_OK

    payload = response.json()
    assert "data" in payload
    assert len(payload["data"]) > 0


def test_scan_signals_endpoint_scoped(client, sample_data):
    """POST /api/signals/scan with specific product_ids restricts evaluation."""
    p_colgate = sample_data["products"]["colgate"]
    response = client.post("/api/signals/scan", json={"product_ids": [p_colgate.id]})
    assert response.status_code == status.HTTP_200_OK

    data = response.json()["data"]
    for item in data:
        assert item["product_id"] == p_colgate.id


def test_dismiss_signal_endpoint(client, sample_data, db):
    """POST /api/signals/{signal_id}/dismiss marks signal as resolved."""
    p_rice = sample_data["products"]["rice"]
    sig = raise_signal(
        db,
        signal_type="threshold_breach",
        severity="low",
        product_id=p_rice.id,
        detected_from="Minor breach",
        evidence={"on_hand": 39},
    )

    response = client.post(
        f"/api/signals/{sig.signal_id}/dismiss",
        json={"reason": "Acknowledged and ordered manually"},
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()["data"]
    assert data["status"] == "resolved"
    assert data["resolution"] == "Acknowledged and ordered manually"

    # 404 on invalid signal
    res404 = client.post(
        "/api/signals/SIG-000000/dismiss",
        json={"reason": "Test"},
    )
    assert res404.status_code == status.HTTP_404_NOT_FOUND
