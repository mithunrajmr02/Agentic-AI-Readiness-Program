"""Tests for the Policies REST API router — WS-5.

15-SHARED-CONTRACTS.md §12 / 12-DATA-AND-API-CHANGES.md §5.4.
Tests:
- GET /api/policies/autonomy (envelope, metadata)
- PATCH /api/policies/autonomy (manager success, staff 403)
- POST /api/policies/kill-switch (manager engage/release, mandatory reason, staff 403)
- GET /api/policies/threshold (verbatim citation and section)
- GET /api/policies/reload (manager reload, staff 403)
"""
import pytest
from fastapi import status


# --- GET /api/policies/autonomy ----------------------------------------------

def test_get_autonomy_policy(client):
    resp = client.get("/api/policies/autonomy")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert "data" in body
    assert "meta" in body
    assert body["meta"]["provenance"] == {"policy": "retrieved"}
    assert body["meta"]["data_disclosure"] == "real"
    data = body["data"]
    assert data["scope_type"] == "global"
    assert data["mode"] == "autonomous"
    assert data["kill_switch_engaged"] is False


# --- PATCH /api/policies/autonomy --------------------------------------------

def test_patch_autonomy_policy_as_manager(client, manager_token):
    payload = {
        "mode": "assisted",
        "max_order_value": 30000.0,
        "max_orders_per_hour": 5,
        "max_value_per_day": 200000.0,
        "min_sale_events": 12,
        "min_history_days": 45,
        "safety_stock_days": 3,
        "drift_tolerance_pct": 15.0,
    }
    resp = client.patch(
        "/api/policies/autonomy",
        json=payload,
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    assert data["mode"] == "assisted"
    assert data["max_order_value"] == 30000.0
    assert data["max_orders_per_hour"] == 5
    assert data["max_value_per_day"] == 200000.0
    assert data["min_sale_events"] == 12
    assert data["min_history_days"] == 45
    assert data["safety_stock_days"] == 3
    assert data["drift_tolerance_pct"] == 15.0
    assert data["updated_at"] is not None


def test_patch_autonomy_policy_as_staff_forbidden(client, staff_token):
    payload = {"mode": "off"}
    resp = client.patch(
        "/api/policies/autonomy",
        json=payload,
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert "Manager role required" in resp.json()["detail"]


def test_patch_autonomy_policy_invalid_mode(client, manager_token):
    payload = {"mode": "unrecognized_mode"}
    resp = client.patch(
        "/api/policies/autonomy",
        json=payload,
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid autonomy mode" in resp.json()["detail"]


# --- POST /api/policies/kill-switch ------------------------------------------

def test_kill_switch_lifecycle_as_manager(client, manager_token):
    # Engage kill switch
    engage_payload = {
        "engaged": True,
        "reason": "Suspicious inventory drift detected across suppliers",
        "scope_type": "global",
    }
    resp = client.post(
        "/api/policies/kill-switch",
        json=engage_payload,
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    assert data["kill_switch_engaged"] is True
    assert data["kill_switch_reason"] == "Suspicious inventory drift detected across suppliers"

    # Verify via GET
    get_resp = client.get("/api/policies/autonomy")
    assert get_resp.json()["data"]["kill_switch_engaged"] is True

    # Release kill switch
    release_payload = {
        "engaged": False,
        "reason": "Investigation completed, operations safe to resume",
        "scope_type": "global",
    }
    release_resp = client.post(
        "/api/policies/kill-switch",
        json=release_payload,
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert release_resp.status_code == status.HTTP_200_OK
    assert release_resp.json()["data"]["kill_switch_engaged"] is False


def test_kill_switch_engage_requires_reason(client, manager_token):
    payload = {
        "engaged": True,
        "reason": "",
        "scope_type": "global",
    }
    resp = client.post(
        "/api/policies/kill-switch",
        json=payload,
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "reason is required" in resp.json()["detail"].lower()


def test_kill_switch_as_staff_forbidden(client, staff_token):
    payload = {
        "engaged": True,
        "reason": "Staff attempt",
    }
    resp = client.post(
        "/api/policies/kill-switch",
        json=payload,
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert "Manager role required" in resp.json()["detail"]


# --- GET /api/policies/threshold ---------------------------------------------

def test_get_policy_threshold_endpoint(client):
    resp = client.get("/api/policies/threshold")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["meta"]["provenance"] == {"threshold": "retrieved"}
    assert body["meta"]["data_disclosure"] == "real"
    data = body["data"]
    assert data["threshold_inr"] == 50000.0
    assert data["default_threshold_inr"] == 50000.0
    assert data["source"] == "retrieved"
    assert "Section 10" in data["section"]
    assert "₹50,000" in data["citation"]


# --- GET /api/policies/reload ------------------------------------------------

def test_reload_policies_as_manager(client, manager_token):
    resp = client.get(
        "/api/policies/reload",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert "policy" in body["data"]
    assert "threshold" in body["data"]
    assert "reloaded_at" in body["data"]


def test_reload_policies_as_staff_forbidden(client, staff_token):
    resp = client.get(
        "/api/policies/reload",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert "Manager role required" in resp.json()["detail"]
