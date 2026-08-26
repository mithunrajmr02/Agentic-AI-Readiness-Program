"""Tests for supplier selection logic (WS-7).

15-SHARED-CONTRACTS.md §10 / 14-PARALLEL-WORKSTREAMS.md §WS-7.
Verifies supplier selection criteria, active supplier precondition enforcement,
cheapest active supplier resolution, and rejected alternatives reporting.
"""
from unittest.mock import MagicMock

import pytest

from src.backend.models import Category, Product, Supplier
from src.backend.models_sourcing import SupplierProduct
from src.core.errors import InsufficientData
from src.sourcing.selection import SupplierChoice, select_supplier


def test_select_supplier_chooses_cheapest_active():
    """Selects the cheapest active supplier and records rejected alternatives."""
    supp1 = MagicMock()
    supp1.id = 1
    supp1.name = "Supplier Alpha"
    supp1.is_active = True

    supp2 = MagicMock()
    supp2.id = 2
    supp2.name = "Supplier Beta"
    supp2.is_active = True

    sp1 = MagicMock()
    sp1.supplier_id = 1
    sp1.product_id = 10
    sp1.unit_price = 500.0
    sp1.lead_time_days = 7
    sp1.min_order_quantity = 10
    sp1.is_preferred = False

    sp2 = MagicMock()
    sp2.supplier_id = 2
    sp2.product_id = 10
    sp2.unit_price = 450.0  # cheaper
    sp2.lead_time_days = 5
    sp2.min_order_quantity = 5
    sp2.is_preferred = False

    class MockQuery:
        def join(self, *args, **kwargs):
            return self

        def filter(self, *args, **kwargs):
            return self

        def all(self):
            return [(sp1, supp1), (sp2, supp2)]

    class MockDB:
        def query(self, *entities):
            return MockQuery()

    choice = select_supplier(MockDB(), product_id=10, quantity=20)
    assert isinstance(choice, SupplierChoice)
    assert choice.supplier_id == 2
    assert choice.unit_price == 450.0
    assert choice.lead_time_days == 5
    assert choice.is_cheapest is True
    assert len(choice.rejected_alternatives) == 1
    assert choice.rejected_alternatives[0]["supplier_id"] == 1
    assert "Higher unit price" in choice.rejected_alternatives[0]["reason"]
    assert "Supplier Beta" in choice.rationale


def test_select_supplier_inactive_excluded(db):
    """Doc 14 §WS-7: Inactive suppliers are excluded (§6 line 74)."""
    # Create an inactive supplier offering a lower price
    p = db.query(Product).filter(Product.id == 1).first()
    inactive_supp = db.query(Supplier).filter(Supplier.id == 5).first()
    assert inactive_supp.is_active is False

    sp_inactive = SupplierProduct(
        id=99,
        supplier_id=5,
        product_id=1,
        unit_price=400.0,  # Cheaper than 600.0
        lead_time_days=2,
        min_order_quantity=1,
        is_preferred=False,
    )
    db.add(sp_inactive)
    db.commit()

    choice = select_supplier(db, product_id=1)
    # Must NOT select inactive supplier 5 despite cheaper price
    assert choice.supplier_id == 4
    assert choice.unit_price == 600.0
    assert choice.is_cheapest is True


def test_select_supplier_fallback_to_product_default(db):
    """When supplier_products has no records, falls back to Product.supplier_id."""
    # Product 2 (Sony Headphones) has supplier_id=2 and no SupplierProduct entries
    choice = select_supplier(db, product_id=2)
    assert choice.supplier_id == 2
    assert choice.unit_price == 22000.0
    assert choice.lead_time_days == 3
    assert choice.is_cheapest is True
    assert len(choice.rejected_alternatives) == 0


def test_select_supplier_no_active_supplier_raises_insufficient_data(db):
    """When no active supplier exists, raises InsufficientData (§12.3 / §12.4)."""
    # Product with inactive supplier and no supplier_products
    p_orphan = Product(
        id=999,
        sku="SKU-ORPHAN",
        name="Orphan Product",
        category=Category.grocery,
        unit_price=100.0,
        cost_price=50.0,
        supplier_id=5,  # Inactive supplier
    )
    db.add(p_orphan)
    db.commit()

    with pytest.raises(InsufficientData) as exc_info:
        select_supplier(db, product_id=999)

    assert "supplier selection for product 999" in exc_info.value.what
    assert "at least 1 active supplier" in exc_info.value.needed


def test_select_supplier_with_preference(db):
    """select_supplier honors prefer_supplier_id when provided and active."""
    # Product 1 is offered by supplier 4 (600.0) and supplier 1 (620.0)
    choice = select_supplier(db, product_id=1, prefer_supplier_id=1)
    assert choice.supplier_id == 1
    assert choice.unit_price == 620.0
    assert choice.is_cheapest is False  # 620.0 > 600.0
    assert len(choice.rejected_alternatives) == 1
    assert choice.rejected_alternatives[0]["supplier_id"] == 4
