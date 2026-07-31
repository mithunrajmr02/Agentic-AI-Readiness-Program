from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models import Category, MovementType, POStatus

# Auth Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "staff"

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str

# StockLevel Schemas
class StockLevelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    last_updated: Optional[datetime]

# StockMovement Schemas
class StockMovementCreate(BaseModel):
    movement_type: MovementType
    quantity: int
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    movement_type: MovementType
    quantity: int
    reference_number: Optional[str]
    notes: Optional[str]
    recorded_at: Optional[datetime]
    recorded_by: str

# Supplier Schemas
class SupplierCreate(BaseModel):
    name: str
    supplier_code: str
    contact_email: Optional[str] = None
    payment_terms_days: Optional[int] = 30
    lead_time_days: Optional[int] = 7

class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    supplier_code: str
    contact_email: Optional[str]
    payment_terms_days: int
    lead_time_days: int
    is_active: bool

# Product Schemas
class ProductCreate(BaseModel):
    name: str
    category: Category
    unit_price: float
    cost_price: float
    unit_of_measure: Optional[str] = "pieces"
    reorder_point: Optional[int] = 10
    reorder_quantity: Optional[int] = 50
    supplier_id: Optional[int] = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    name: str
    category: Category
    unit_price: float
    cost_price: float
    unit_of_measure: str
    reorder_point: int
    reorder_quantity: int
    supplier_id: Optional[int]
    created_at: Optional[datetime]
    stock_level: Optional[StockLevelResponse] = None
    movements: Optional[List[StockMovementResponse]] = []

# PO Item Schemas
class POItemCreate(BaseModel):
    product_id: int
    quantity_ordered: int
    unit_cost: float

class POItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    po_id: int
    product_id: int
    quantity_ordered: int
    unit_cost: float
    quantity_received: Optional[int]

# Purchase Order Schemas
class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    order_date: date
    expected_delivery: Optional[date] = None
    items: List[POItemCreate]

class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    po_number: str
    supplier_id: int
    status: POStatus
    total_amount: float
    order_date: date
    expected_delivery: Optional[date]
    received_date: Optional[date]
    created_at: Optional[datetime]
    items: List[POItemResponse] = []

# Stock Alert Schemas
class StockAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    alert_type: str
    message: str
    is_resolved: bool
    triggered_at: Optional[datetime]
    product: Optional[ProductResponse] = None

# Dashboard Schemas
class DashboardResponse(BaseModel):
    total_products: int
    low_stock_count: int
    out_of_stock_count: int
    open_po_count: int
    total_stock_value: float
