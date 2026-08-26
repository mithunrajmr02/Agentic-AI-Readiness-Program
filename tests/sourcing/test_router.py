"""Tests for the suppliers REST API router (WS-7).

15-SHARED-CONTRACTS.md §10, §12 / 12-DATA-AND-API-CHANGES.md §5.7.
Verifies all /api/suppliers endpoints, envelopes, status codes, and error formats.
"""


def test_list_suppliers(client):
    """GET /api/suppliers returns list of suppliers in success_envelope."""
    response = client.get("/api/suppliers")
    assert response.status_code == 200
    json_data = response.json()
    assert "data" in json_data
    assert "meta" in json_data
    assert isinstance(json_data["data"], list)
    assert len(json_data["data"]) >= 4
    assert json_data["meta"]["provenance"]["suppliers"] == "retrieved"


def test_get_supplier_detail(client):
    """GET /api/suppliers/4 returns supplier details with embedded scorecard."""
    response = client.get("/api/suppliers/4")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["data"]["id"] == 4
    assert json_data["data"]["name"] == "Global Logistics Corp"
    assert "scorecard" in json_data["data"]
    assert json_data["data"]["scorecard"]["sample_size"] == 1


def test_get_supplier_scorecard(client):
    """GET /api/suppliers/4/scorecard returns standalone Scorecard."""
    response = client.get("/api/suppliers/4/scorecard")
    assert response.status_code == 200
    json_data = response.json()
    sc = json_data["data"]
    assert sc["supplier_id"] == 4
    assert sc["contract_lead_time"] == 5
    assert sc["measured_lead_time"] == 9.0
    assert sc["drift_days"] == 4.0
    assert sc["sample_size"] == 1
    assert sc["on_time_rate"] is None  # n=1 honesty
    assert json_data["meta"]["provenance"]["scorecard"] == "computed"


def test_compare_suppliers_for_product(client):
    """GET /api/suppliers/compare/1 returns catalog comparison and recommendation."""
    response = client.get("/api/suppliers/compare/1?quantity=50")
    assert response.status_code == 200
    json_data = response.json()
    data = json_data["data"]
    assert data["product_id"] == 1
    assert "comparison" in data
    assert "recommendation" in data
    assert data["recommendation"]["supplier_id"] == 4
    assert data["recommendation"]["is_cheapest"] is True


def test_get_supplier_products(client):
    """GET /api/suppliers/4/products returns product catalog."""
    response = client.get("/api/suppliers/4/products")
    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data["data"], list)
    assert any(p["product_id"] == 1 for p in json_data["data"])


def test_get_supplier_drift(client):
    """GET /api/suppliers/4/drift returns drift report with PO evidence."""
    response = client.get("/api/suppliers/4/drift")
    assert response.status_code == 200
    json_data = response.json()
    data = json_data["data"]
    assert data["supplier_id"] == 4
    assert data["drift_days"] == 4.0
    assert data["is_drifting"] is True
    assert len(data["po_evidence"]) >= 1
    assert data["po_evidence"][0]["po_number"] == "PO-2026-0001"


def test_get_all_drifts(client):
    """GET /api/suppliers/drifts/all returns list of drifting suppliers."""
    response = client.get("/api/suppliers/drifts/all")
    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data["data"], list)
    assert any(d["supplier_id"] == 4 for d in json_data["data"])


def test_nonexistent_supplier_returns_404(client):
    """Non-existent supplier returns HTTP 404."""
    response = client.get("/api/suppliers/99999/scorecard")
    assert response.status_code == 404
