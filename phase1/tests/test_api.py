import pytest

def test_create_product(client, auth_headers, seeded_supplier):
    """TC-07-P1-API-01: Create Product Returns 201 with SKU"""
    payload = {
        "name": "Basmati Rice 5kg",
        "category": "grocery",
        "unit_price": 350.0,
        "cost_price": 280.0,
        "unit_of_measure": "box",
        "reorder_point": 20,
        "reorder_quantity": 100,
        "supplier_id": seeded_supplier["id"]
    }
    response = client.post("/api/v1/products", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["sku"].startswith("SKU-GRO-")

def test_stock_update_alert(client, auth_headers, seeded_product):
    """TC-07-P1-API-02: Stock Update Creates Movement and Alert"""
    payload = {
        "movement_type": "sale",
        "quantity": -1000,
        "reference_number": "SALE-001",
        "notes": "Bulk sale"
    }
    response = client.patch(f"/api/v1/products/{seeded_product['id']}/stock",
                            json=payload, headers=auth_headers)
    assert response.status_code == 200
    
    # Check low stock alert
    alerts = client.get("/api/v1/stock/low-alerts", headers=auth_headers).json()
    assert any(p["id"] == seeded_product["id"] for p in alerts)

def test_create_po(client, auth_headers, seeded_supplier, seeded_product):
    """TC-07-P1-API-03: Create Purchase Order with PO Number"""
    payload = {
        "supplier_id": seeded_supplier["id"],
        "order_date": "2026-06-18",
        "expected_delivery": "2026-06-25",
        "items": [{"product_id": seeded_product["id"], "quantity_ordered": 100, "unit_cost": 280.0}]
    }
    response = client.post("/api/v1/orders", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert "po_number" in data
    assert data["po_number"].startswith("PO-")
    assert data["status"] == "draft"

def test_receive_po_updates_stock(client, auth_headers, submitted_po, seeded_product):
    """TC-07-P1-API-04: Receive PO Updates Stock"""
    initial_stock = client.get(f"/api/v1/products/{seeded_product['id']}",
                               headers=auth_headers).json().get("stock_level", {})
    response = client.patch(f"/api/v1/orders/{submitted_po}/receive", headers=auth_headers)
    assert response.status_code == 200
    
    updated = client.get(f"/api/v1/products/{seeded_product['id']}",
                         headers=auth_headers).json()
    new_stock = updated.get("stock_level", {})
    assert new_stock.get("quantity_on_hand", 0) > initial_stock.get("quantity_on_hand", 0)

def test_low_alerts(client, auth_headers):
    """TC-07-P1-API-05: Low Alerts Returns Correct Products"""
    response = client.get("/api/v1/stock/low-alerts", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_supplier_catalog(client, auth_headers, seeded_supplier):
    """TC-07-P1-API-06: Supplier Catalog Returns Products"""
    response = client.get(f"/api/v1/suppliers/{seeded_supplier['id']}/catalog",
                          headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_filter_by_category(client, auth_headers, seeded_product):
    """TC-07-P1-API-07: Filter Products by Category"""
    response = client.get("/api/v1/products?category=grocery", headers=auth_headers)
    assert response.status_code == 200
    for p in response.json():
        assert p["category"] == "grocery"

def test_dashboard(client, auth_headers):
    """TC-07-P1-API-08: Dashboard Returns Metrics"""
    response = client.get("/api/v1/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    for field in ["total_products", "low_stock_count", "out_of_stock_count",
                  "open_po_count", "total_stock_value"]:
        assert field in data

def test_get_product_not_found(client, auth_headers):
    response = client.get("/api/v1/products/99999", headers=auth_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_update_stock_not_found(client, auth_headers):
    payload = {"movement_type": "receipt", "quantity": 10}
    response = client.patch("/api/v1/products/99999/stock", json=payload, headers=auth_headers)
    assert response.status_code == 404

def test_supplier_catalog_not_found(client, auth_headers):
    response = client.get("/api/v1/suppliers/99999/catalog", headers=auth_headers)
    assert response.status_code == 404

def test_create_po_invalid_supplier(client, auth_headers, seeded_product):
    payload = {
        "supplier_id": 99999,
        "order_date": "2026-06-18",
        "items": [{"product_id": seeded_product["id"], "quantity_ordered": 10, "unit_cost": 100.0}]
    }
    response = client.post("/api/v1/orders", json=payload, headers=auth_headers)
    assert response.status_code == 400

def test_get_order_by_id_and_not_found(client, auth_headers, submitted_po):
    res1 = client.get(f"/api/v1/orders/{submitted_po}", headers=auth_headers)
    assert res1.status_code == 200
    assert res1.json()["id"] == submitted_po

    res2 = client.get("/api/v1/orders/99999", headers=auth_headers)
    assert res2.status_code == 404

def test_receive_po_duplicate_error(client, auth_headers, submitted_po):
    # First receive succeeds
    res1 = client.patch(f"/api/v1/orders/{submitted_po}/receive", headers=auth_headers)
    assert res1.status_code == 200

    # Second receive fails with 400
    res2 = client.patch(f"/api/v1/orders/{submitted_po}/receive", headers=auth_headers)
    assert res2.status_code == 400
    assert "already been received" in res2.json()["detail"]

def test_receive_po_not_found(client, auth_headers):
    response = client.patch("/api/v1/orders/99999/receive", headers=auth_headers)
    assert response.status_code == 404

def test_create_supplier_duplicate_code(client, auth_headers, seeded_supplier):
    payload = {
        "name": "Duplicate Wholesale Ltd",
        "supplier_code": seeded_supplier["supplier_code"],
        "contact_email": "dup@supplier.com"
    }
    response = client.post("/api/v1/suppliers", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_health_and_root_endpoints(client):
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "Welcome" in res_root.json()["message"]

def test_filter_products_by_low_stock(client, auth_headers, seeded_product):
    # Make stock low
    client.patch(
        f"/api/v1/products/{seeded_product['id']}/stock",
        json={"movement_type": "sale", "quantity": -100},
        headers=auth_headers
    )
    res = client.get("/api/v1/products?low_stock=true", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

def test_list_orders_filter_status_and_supplier(client, auth_headers, submitted_po, seeded_supplier):
    res = client.get(
        f"/api/v1/orders?status=draft&supplier_id={seeded_supplier['id']}",
        headers=auth_headers
    )
    assert res.status_code == 200
    assert len(res.json()) >= 1

