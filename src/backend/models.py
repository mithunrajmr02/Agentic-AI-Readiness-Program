import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.backend.database import Base


class Category(str, enum.Enum):
    grocery = "grocery"
    electronics = "electronics"
    clothing = "clothing"
    household = "household"
    personal_care = "personal_care"


CATEGORY_PREFIXES = {
    "grocery": "GRO",
    "electronics": "ELC",
    "clothing": "CLO",
    "household": "HHD",
    "personal_care": "PRC"
}


class MovementType(str, enum.Enum):
    receipt = "receipt"
    sale = "sale"
    adjustment = "adjustment"
    transfer = "transfer"
    returnm = "return"
    return_movement = "return"


class POStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    acknowledged = "acknowledged"
    received = "received"
    cancelled = "cancelled"


CASCADE_DELETE_ORPHAN = "all, delete-orphan"
PRODUCTS_ID_FK = "products.id"
SUPPLIERS_ID_FK = "suppliers.id"
PURCHASE_ORDERS_ID_FK = "purchase_orders.id"


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    supplier_code = Column(String(20), unique=True, nullable=False, index=True)
    contact_email = Column(String(200))
    payment_terms_days = Column(Integer, default=30)
    lead_time_days = Column(Integer, default=7)
    is_active = Column(Boolean, default=True)

    products = relationship("Product", back_populates="supplier", cascade=CASCADE_DELETE_ORPHAN)
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier", cascade=CASCADE_DELETE_ORPHAN)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    category = Column(Enum(Category), nullable=False, index=True)
    unit_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    unit_of_measure = Column(String(20), default="pieces")
    reorder_point = Column(Integer, default=10)
    reorder_quantity = Column(Integer, default=50)
    supplier_id = Column(Integer, ForeignKey(SUPPLIERS_ID_FK), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now())

    supplier = relationship("Supplier", back_populates="products")
    stock_level = relationship("StockLevel", back_populates="product", uselist=False, cascade=CASCADE_DELETE_ORPHAN)
    movements = relationship("StockMovement", back_populates="product", cascade=CASCADE_DELETE_ORPHAN)
    alerts = relationship("StockAlert", back_populates="product", cascade=CASCADE_DELETE_ORPHAN)


class StockLevel(Base):
    __tablename__ = "stock_levels"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey(PRODUCTS_ID_FK), unique=True, nullable=False, index=True)
    quantity_on_hand = Column(Integer, default=0)
    quantity_reserved = Column(Integer, default=0)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    product = relationship("Product", back_populates="stock_level")

    @property
    def quantity_available(self) -> int:
        return max(0, (self.quantity_on_hand or 0) - (self.quantity_reserved or 0))


class StockMovement(Base):
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey(PRODUCTS_ID_FK), nullable=False, index=True)
    movement_type = Column(Enum(MovementType), nullable=False)
    quantity = Column(Integer, nullable=False)
    reference_number = Column(String(50), nullable=True)
    notes = Column(String(500), nullable=True)
    recorded_at = Column(DateTime, server_default=func.now())
    recorded_by = Column(String(100), default="system")
    
    product = relationship("Product", back_populates="movements")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(20), unique=True, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey(SUPPLIERS_ID_FK), nullable=False, index=True)
    status = Column(Enum(POStatus), default=POStatus.draft, index=True)
    total_amount = Column(Float, default=0.0)
    order_date = Column(Date, nullable=False)
    expected_delivery = Column(Date, nullable=True)
    received_date = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("POItem", back_populates="purchase_order", cascade=CASCADE_DELETE_ORPHAN)


class POItem(Base):
    __tablename__ = "po_items"
    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey(PURCHASE_ORDERS_ID_FK), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey(PRODUCTS_ID_FK), nullable=False, index=True)
    quantity_ordered = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    quantity_received = Column(Integer, nullable=True)
    
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")


class StockAlert(Base):
    __tablename__ = "stock_alerts"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey(PRODUCTS_ID_FK), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)
    message = Column(String(500))
    is_resolved = Column(Boolean, default=False, index=True)
    triggered_at = Column(DateTime, server_default=func.now())
    
    product = relationship("Product", back_populates="alerts")



class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100))
    role = Column(String(50), default="staff")
    is_active = Column(Boolean, default=True)

