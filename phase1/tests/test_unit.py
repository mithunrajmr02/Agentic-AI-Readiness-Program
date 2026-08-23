import pytest
from unittest.mock import MagicMock
from datetime import date
from src.backend.services.inventory_service import generate_sku, generate_po_number, check_stock_alerts
from src.backend.models import StockLevel


def _db_holding(*identifiers):
    """Fake a DB whose matching identifier column already holds `identifiers`.

    The generators read the identifiers that exist and continue the sequence past
    the highest one, so the fake supplies rows rather than a row count. The
    previous fake stubbed `.count()` -- that pinned the tests to *how* the number
    was derived, so both passed just as happily when the derivation was wrong:
    counting rows meant one deletion made `POST /api/v1/orders` return HTTP 500
    on the UNIQUE constraint, forever, and neither test noticed.
    """
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [(i,) for i in identifiers]
    return mock_db


def test_sku_format():
    """TC-07-P1-UNIT-01: SKU Format Generation"""
    mock_db = _db_holding(*(f"SKU-GRO-{n:04d}" for n in range(1, 42)))
    sku = generate_sku("grocery", mock_db)
    assert sku == "SKU-GRO-0042"
    assert sku.startswith("SKU-GRO-")

def test_sku_categories():
    """TC-07-P1-UNIT-02: SKU Different Categories"""
    mock_db = _db_holding()
    assert generate_sku("electronics", mock_db).startswith("SKU-ELC-")
    assert generate_sku("clothing", mock_db).startswith("SKU-CLO-")
    assert generate_sku("household", mock_db).startswith("SKU-HHD-")

def test_po_number():
    """TC-07-P1-UNIT-03: PO Number Format"""
    year = date.today().year
    mock_db = _db_holding(*(f"PO-{year}-{n:04d}" for n in range(1, 42)))
    po_num = generate_po_number(mock_db)
    assert po_num == f"PO-{year}-0042"


def test_identifier_survives_deletion():
    """A deleted identifier must not drag the sequence back onto a live one.

    Reproduced against the running app before this was fixed: with
    PO-2026-0001..0009 on file, deleting one row left nine numbers issued but
    eight rows, so the generator proposed PO-2026-0009 -- already taken -- and
    the endpoint answered HTTP 500. Every later order creation failed the same
    way, because a row count can never catch back up to the numbers issued.
    """
    year = date.today().year
    # 0008 has been retired; 0009 is still live.
    survivors = [f"PO-{year}-{n:04d}" for n in (1, 2, 3, 4, 5, 6, 7, 9)]
    assert generate_po_number(_db_holding(*survivors)) == f"PO-{year}-0010"

    # Same shape for SKUs, and skip over a number that is taken but not highest.
    assert generate_sku("electronics", _db_holding("SKU-ELC-0001", "SKU-ELC-0004")) == "SKU-ELC-0005"

    # A malformed identifier must not crash the generator or claim a slot.
    assert generate_sku("grocery", _db_holding("SKU-GRO-legacy", "SKU-GRO-0002")) == "SKU-GRO-0003"

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

def _product(db, sku, cost_price, on_hand, reorder_point=10, with_stock_row=True,
             supplier_id=None):
    """Insert a product, optionally with a stock level, and return it."""
    from src.backend.models import Category, Product, StockLevel

    product = Product(
        sku=sku, name=f"Fixture {sku}", category=Category.grocery,
        unit_price=cost_price * 2, cost_price=cost_price,
        unit_of_measure="units", reorder_point=reorder_point, reorder_quantity=50,
        supplier_id=supplier_id,
    )
    db.add(product)
    db.flush()
    if with_stock_row:
        db.add(StockLevel(product_id=product.id, quantity_on_hand=on_hand,
                          quantity_reserved=0))
        db.flush()
    return product


def test_stock_value(db_session):
    """TC-07-P1-UNIT-07: Stock Value Calculation

    This test used to be:

        products_data = [{"quantity_on_hand": 100, "cost_price": 50.0}, ...]
        total = sum(p["quantity_on_hand"] * p["cost_price"] for p in products_data)
        assert total == 15000.0

    which computed the sum in the test and then asserted the test's own arithmetic
    -- no application code was involved. It passed unconditionally, and a mutation
    that blanked the `total_stock_value` accumulation in `get_dashboard_data`
    (src/backend/services/inventory_service.py:190) left the whole Phase-1 suite
    green. Stock value is now read back out of the function that computes it.
    """
    from src.backend.services.inventory_service import get_dashboard_data

    _product(db_session, "SKU-GRO-9001", cost_price=50.0, on_hand=100)   # 5,000
    _product(db_session, "SKU-GRO-9002", cost_price=200.0, on_hand=50)   # 10,000
    db_session.commit()

    assert get_dashboard_data(db_session)["total_stock_value"] == 15000.0


def test_dashboard_counts_classify_each_product_once(db_session):
    """Availability drives exactly one of the out-of-stock / low-stock buckets."""
    from src.backend.services.inventory_service import get_dashboard_data

    _product(db_session, "SKU-GRO-9010", cost_price=10.0, on_hand=0, reorder_point=5)
    _product(db_session, "SKU-GRO-9011", cost_price=10.0, on_hand=3, reorder_point=5)
    _product(db_session, "SKU-GRO-9012", cost_price=10.0, on_hand=5, reorder_point=5)
    _product(db_session, "SKU-GRO-9013", cost_price=10.0, on_hand=500, reorder_point=5)
    db_session.commit()

    data = get_dashboard_data(db_session)
    assert data["total_products"] == 4
    assert data["out_of_stock_count"] == 1
    # available == reorder_point is low, not healthy: the comparison is `<=`.
    assert data["low_stock_count"] == 2
    assert data["total_stock_value"] == (0 + 3 + 5 + 500) * 10.0


def test_dashboard_treats_oversold_stock_as_out_of_stock(db_session):
    """Negative availability is out of stock, not low stock.

    `quantity_available` is an unclamped subtraction, so an oversold line can go
    below zero. Classifying that as "low" would leave it out of the out-of-stock
    count an operator uses to decide what to reorder first.
    """
    from src.backend.models import StockLevel
    from src.backend.services.inventory_service import get_dashboard_data

    product = _product(db_session, "SKU-GRO-9020", cost_price=10.0, on_hand=2,
                       reorder_point=5)
    stock = db_session.query(StockLevel).filter(
        StockLevel.product_id == product.id
    ).first()
    stock.quantity_reserved = 9          # available == -7
    db_session.commit()

    data = get_dashboard_data(db_session)
    assert data["out_of_stock_count"] == 1
    assert data["low_stock_count"] == 0
    # Value follows quantity_on_hand, which is still 2 -- reserved stock is held,
    # not gone.
    assert data["total_stock_value"] == 20.0


def test_dashboard_skips_products_with_no_stock_row(db_session):
    """A product with no stock_level row is counted but contributes no value.

    `get_dashboard_data` guards on `if stock:`, so such a product falls through
    every bucket. That is why the seed fixture writes an explicit zero row for
    out-of-stock products instead of leaving the relationship empty.
    """
    from src.backend.services.inventory_service import get_dashboard_data

    _product(db_session, "SKU-GRO-9030", cost_price=99.0, on_hand=0,
             with_stock_row=False)
    db_session.commit()

    data = get_dashboard_data(db_session)
    assert data["total_products"] == 1
    assert data["out_of_stock_count"] == 0
    assert data["low_stock_count"] == 0
    assert data["total_stock_value"] == 0.0


def test_dashboard_open_po_count_excludes_closed_orders(db_session):
    """draft/submitted/acknowledged are open; received and cancelled are not."""
    from src.backend.models import POStatus, PurchaseOrder, Supplier
    from src.backend.services.inventory_service import get_dashboard_data

    supplier = Supplier(supplier_code="SUP-9001", name="Fixture Vendor",
                        contact_email="v@example.com", payment_terms_days=30,
                        lead_time_days=5, is_active=True)
    db_session.add(supplier)
    db_session.flush()

    for n, status in enumerate([POStatus.draft, POStatus.submitted,
                               POStatus.acknowledged, POStatus.received,
                               POStatus.cancelled], start=1):
        db_session.add(PurchaseOrder(
            po_number=f"PO-9000-{n:04d}", supplier_id=supplier.id, status=status,
            order_date=date.today(), total_amount=100.0,
        ))
    db_session.commit()

    assert get_dashboard_data(db_session)["open_po_count"] == 3

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


