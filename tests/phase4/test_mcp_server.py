import pytest
from unittest.mock import patch, MagicMock
import requests as req


def test_server_starts():
    """TC-07-P4-MCP-01: Server Starts"""
    from src.mcp_server.mcp_app import mcp
    assert mcp is not None
    assert "Inventory" in mcp.name or "Management" in mcp.name


def test_6_tools():
    """TC-07-P4-MCP-02: 6 Tools Discoverable"""
    import src.mcp_server.mcp_app as app
    for name in [
        "update_stock",
        "create_purchase_order",
        "get_low_stock_products",
        "get_supplier_catalog",
        "get_purchase_orders",
        "get_inventory_dashboard",
    ]:
        assert hasattr(app, name), f"'{name}' not found"


def test_update_stock():
    """TC-07-P4-MCP-03: update_stock Works"""
    mock_r = {"id": 1, "product_id": 1, "movement_type": "receipt", "quantity": 100}
    with patch("src.mcp_server.mcp_app.requests.patch") as mp_patch, patch("src.mcp_server.mcp_app.requests.post") as mp_post:
        mp_patch.return_value.status_code = 200
        mp_patch.return_value.json.return_value = mock_r
        mp_patch.return_value.raise_for_status = MagicMock()
        mp_post.return_value.status_code = 200
        mp_post.return_value.json.return_value = mock_r
        mp_post.return_value.raise_for_status = MagicMock()
        
        from src.mcp_server.mcp_app import update_stock
        result = update_stock(product_id=1, movement_type="receipt", quantity=100)
        assert isinstance(result, dict)
        assert mp_patch.called or mp_post.called


def test_create_po():
    """TC-07-P4-MCP-04: create_purchase_order Works"""
    mock_r = {"id": 1, "po_number": "PO-2026-0001", "status": "draft", "total_amount": 28000.0}
    with patch("src.mcp_server.mcp_app.requests.post") as mp:
        mp.return_value.status_code = 201
        mp.return_value.json.return_value = mock_r
        mp.return_value.raise_for_status = MagicMock()
        from src.mcp_server.mcp_app import create_purchase_order
        result = create_purchase_order(
            supplier_id=1,
            order_date="2026-06-18",
            items=[{"product_id": 1, "quantity_ordered": 100, "unit_cost": 280.0}]
        )
        assert isinstance(result, dict)
        assert result.get("po_number") is not None


def test_get_low_stock():
    """TC-07-P4-MCP-05: get_low_stock_products Works"""
    mock_r = [{"id": 1, "sku": "SKU-GRO-0001", "quantity_available": 5, "reorder_point": 20}]
    with patch("src.mcp_server.mcp_app.requests.get") as mg:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = mock_r
        mg.return_value.raise_for_status = MagicMock()
        from src.mcp_server.mcp_app import get_low_stock_products
        result = get_low_stock_products()
        assert isinstance(result, (list, dict))


def test_supplier_catalog():
    """TC-07-P4-MCP-06: get_supplier_catalog Works"""
    mock_r = [{"sku": "SKU-GRO-0001", "name": "Basmati Rice", "cost_price": 280.0}]
    with patch("src.mcp_server.mcp_app.requests.get") as mg:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = mock_r
        mg.return_value.raise_for_status = MagicMock()
        from src.mcp_server.mcp_app import get_supplier_catalog
        result = get_supplier_catalog(supplier_id=1)
        assert isinstance(result, (list, dict))


def test_inventory_dashboard():
    """TC-07-P4-MCP-07: get_inventory_dashboard Works"""
    mock_r = {"total_products": 500, "low_stock_count": 25, "open_po_count": 8}
    with patch("src.mcp_server.mcp_app.requests.get") as mg:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = mock_r
        mg.return_value.raise_for_status = MagicMock()
        from src.mcp_server.mcp_app import get_inventory_dashboard
        result = get_inventory_dashboard()
        assert isinstance(result, dict)
        assert result.get("total_products") == 500


def test_api_unavailable_error():
    """TC-07-P4-MCP-08: API Unavailable Returns Error"""
    with patch("src.mcp_server.mcp_app.requests.get", side_effect=req.exceptions.ConnectionError("refused")):
        from src.mcp_server.mcp_app import get_inventory_dashboard
        result = get_inventory_dashboard()
        assert isinstance(result, dict) and "error" in result
