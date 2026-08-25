"""Sourcing tables — WS-0 owns the schema; WS-2 seeds, WS-7 writes rows.

15-SHARED-CONTRACTS.md §3 maps ``supplier_products`` to this module. It resolves
the per-supplier commercial terms for a product (price, lead time, MOQ). Unique on
(supplier_id, product_id) so a supplier lists each product exactly once. Same WS-0
conventions: String not Enum, explicit ``clock.now()`` timestamps.
"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
)

from src.backend.database import Base

PRODUCTS_ID_FK = "products.id"
SUPPLIERS_ID_FK = "suppliers.id"


class SupplierProduct(Base):
    """A supplier's commercial terms for one product (§ doc 12)."""

    __tablename__ = "supplier_products"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey(SUPPLIERS_ID_FK), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey(PRODUCTS_ID_FK), nullable=False, index=True)
    unit_price = Column(Float, nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    min_order_quantity = Column(Integer, default=1)
    pack_size = Column(Integer, default=1)
    is_preferred = Column(Boolean, default=False, nullable=False)
    last_price_update = Column(DateTime, nullable=True)  # clock.now()

    __table_args__ = (
        UniqueConstraint("supplier_id", "product_id", name="uq_supplier_product"),
    )
