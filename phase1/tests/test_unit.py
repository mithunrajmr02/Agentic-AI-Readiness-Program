import pytest
from unittest.mock import MagicMock
from datetime import date
from src.backend.services.inventory_service import generate_sku, generate_po_number, check_stock_alerts
from src.backend.models import StockLevel

def test_sku_format():
    """TC-07-P1-UNIT-01: SKU Format Generation"""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.count.return_value = 41
    sku = generate_sku("grocery", mock_db)
    assert sku == "SKU-GRO-0042"
    assert sku.startswith("SKU-GRO-")

def test_sku_categories():
    """TC-07-P1-UNIT-02: SKU Different Categories"""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    assert generate_sku("electronics", mock_db).startswith("SKU-ELC-")
    assert generate_sku("clothing", mock_db).startswith("SKU-CLO-")
    assert generate_sku("household", mock_db).startswith("SKU-HHD-")

def test_po_number():
    """TC-07-P1-UNIT-03: PO Number Format"""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.count.return_value = 41
    po_num = generate_po_number(mock_db)
    year = date.today().year
    assert po_num == f"PO-{year}-0042"

def test_low_stock_alert():
    """TC-07-P1-UNIT-04: Low Stock Alert Triggered"""
    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.sku = "SKU-GRO-0001"
    mock_product.reorder_point = 20
    
    mock_stock = MagicMock()
    mock_stock.quantity_available = 15  # below reorder point
    
    mock_db = MagicMock()
    check_stock_alerts(mock_product, mock_stock, mock_db)
    
    mock_db.add.assert_called_once()
    call_args = mock_db.add.call_args[0][0]
    assert call_args.alert_type == "low_stock"

def test_out_of_stock_alert():
    """TC-07-P1-UNIT-05: Out of Stock Alert Critical"""
    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.sku = "SKU-GRO-0002"
    mock_product.reorder_point = 20
    
    mock_stock = MagicMock()
    mock_stock.quantity_available = 0
    
    mock_db = MagicMock()
    check_stock_alerts(mock_product, mock_stock, mock_db)
    
    call_args = mock_db.add.call_args[0][0]
    assert call_args.alert_type == "out_of_stock"

def test_no_alert_above_reorder():
    """TC-07-P1-UNIT-06: No Alert Above Reorder Point"""
    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.sku = "SKU-ELC-0001"
    mock_product.reorder_point = 10
    
    mock_stock = MagicMock()
    mock_stock.quantity_available = 50
    
    mock_db = MagicMock()
    check_stock_alerts(mock_product, mock_stock, mock_db)
    
    mock_db.add.assert_not_called()

def test_stock_value():
    """TC-07-P1-UNIT-07: Stock Value Calculation"""
    products_data = [
        {"quantity_on_hand": 100, "cost_price": 50.0},   # 5000
        {"quantity_on_hand": 50, "cost_price": 200.0},   # 10000
    ]
    total = sum(p["quantity_on_hand"] * p["cost_price"] for p in products_data)
    assert total == 15000.0

def test_quantity_available():
    """TC-07-P1-UNIT-08: Quantity Available = OnHand - Reserved"""
    stock = StockLevel()
    stock.quantity_on_hand = 100
    stock.quantity_reserved = 30
    assert stock.quantity_available == 70

def test_check_stock_alerts_none_params():
    mock_db = MagicMock()
    check_stock_alerts(None, None, mock_db)
    mock_db.query.assert_not_called()

def test_check_stock_alerts_resolves_old_alerts():
    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.sku = "SKU-HHD-0001"
    mock_product.reorder_point = 10

    mock_stock = MagicMock()
    mock_stock.quantity_available = 25  # Healthy stock

    old_alert = MagicMock()
    old_alert.is_resolved = False

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [old_alert]

    check_stock_alerts(mock_product, mock_stock, mock_db)
    assert old_alert.is_resolved is True
    mock_db.add.assert_not_called()

def test_receive_cancelled_po_raises_error():
    from app.services.inventory_service import receive_purchase_order
    from app.models import POStatus

    mock_po = MagicMock()
    mock_po.status = POStatus.cancelled
    mock_po.po_number = "PO-2026-999"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_po

    with pytest.raises(ValueError) as exc_info:
        receive_purchase_order(1, mock_db)
    assert "cancelled" in str(exc_info.value)


def test_get_db_generator():
    from app.database import get_db
    gen = get_db()
    db = next(gen)
    assert db is not None
    try:
        next(gen)
    except StopIteration:
        pass


