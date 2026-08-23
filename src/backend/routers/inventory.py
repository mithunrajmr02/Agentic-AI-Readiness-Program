from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.models import (
    Product, StockLevel, StockMovement, PurchaseOrder, POItem,
    Supplier, StockAlert, Category, POStatus, MovementType, User
)
from src.backend.routers.auth import get_current_user
from src.backend.schemas import (
    ProductCreate, ProductResponse, ProductListResponse,
    StockMovementCreate, StockMovementResponse,
    PurchaseOrderCreate, PurchaseOrderResponse, SupplierCreate, SupplierResponse,
    DashboardResponse
)
from src.backend.services.inventory_service import (
    generate_sku, generate_po_number, check_stock_alerts,
    receive_purchase_order, get_dashboard_data
)
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1", tags=["inventory"])

# --- Products ---

@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # A supplier_id is optional, but if one is given it has to exist. Without this
    # check the insert reached SQLite and tripped `FOREIGN KEY constraint failed`,
    # which the catch-all handler in main.py turned into an opaque HTTP 500 --
    # measured against the running app: `supplier_id: 777777` returned
    # `{"detail": "Internal server error"}`. The product was never created (the
    # constraint held), so nothing was corrupted; the caller was simply told the
    # server had broken rather than which field was wrong.
    if product_in.supplier_id is not None:
        supplier = db.query(Supplier).filter(Supplier.id == product_in.supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=400, detail=f"Supplier {product_in.supplier_id} not found")

    sku = generate_sku(product_in.category.value if isinstance(product_in.category, Category) else str(product_in.category), db)

    product = Product(
        sku=sku,
        name=product_in.name,
        category=product_in.category,
        unit_price=product_in.unit_price,
        cost_price=product_in.cost_price,
        unit_of_measure=product_in.unit_of_measure or "pieces",
        reorder_point=product_in.reorder_point if product_in.reorder_point is not None else 10,
        reorder_quantity=product_in.reorder_quantity if product_in.reorder_quantity is not None else 50,
        supplier_id=product_in.supplier_id
    )
    db.add(product)
    db.flush()

    stock = StockLevel(product_id=product.id, quantity_on_hand=0, quantity_reserved=0)
    db.add(stock)

    db.commit()
    db.refresh(product)

    logger.info("product_created", poc_id="POC-07", phase="P1", sku=product.sku, name=product.name)
    return product


@router.get("/products", response_model=List[ProductListResponse])
def list_products(
    category: Optional[str] = None,
    low_stock: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)

    products = query.all()

    if low_stock:
        return [p for p in products if p.stock_level and p.stock_level.quantity_available <= (p.reorder_point or 0)]

    return products


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    movement_limit: int = Query(
        50, ge=1, le=500,
        description="How many of the most recent stock movements to include."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """US-07-P1-07: product details plus its *recent* movement history.

    Movements are queried explicitly instead of via lazy relationship loading.
    Relying on the relationship returned the ledger oldest-first and unbounded --
    the opposite of "recent", and it grows forever. The `id` tie-break matters:
    `recorded_at` uses SQLite's `func.now()`, which has one-second granularity, so
    movements recorded in the same second are otherwise ordered arbitrarily.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    recent_movements = (
        db.query(StockMovement)
        .filter(StockMovement.product_id == product_id)
        .order_by(StockMovement.recorded_at.desc(), StockMovement.id.desc())
        .limit(movement_limit)
        .all()
    )

    response = ProductResponse.model_validate(product)
    response.movements = [StockMovementResponse.model_validate(m) for m in recent_movements]

    logger.info(
        "movement_history_viewed",
        poc_id="POC-07",
        phase="P1",
        product_sku=product.sku,
        movements_returned=len(recent_movements),
    )
    return response


@router.patch("/products/{product_id}/stock", response_model=StockMovementResponse)
def update_stock(
    product_id: int,
    movement_in: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    stock = db.query(StockLevel).filter(StockLevel.product_id == product_id).first()
    if not stock:
        stock = StockLevel(product_id=product_id, quantity_on_hand=0, quantity_reserved=0)
        db.add(stock)
        db.flush()

    stock.quantity_on_hand += movement_in.quantity

    movement = StockMovement(
        product_id=product_id,
        movement_type=movement_in.movement_type,
        quantity=movement_in.quantity,
        reference_number=movement_in.reference_number,
        notes=movement_in.notes,
        recorded_by=current_user.full_name or current_user.email
    )
    db.add(movement)

    check_stock_alerts(product, stock, db)

    db.commit()
    db.refresh(movement)

    logger.info(
        "stock_updated",
        poc_id="POC-07",
        phase="P1",
        product_sku=product.sku,
        movement_type=movement_in.movement_type,
        quantity=movement_in.quantity,
        new_quantity_on_hand=stock.quantity_on_hand,
    )
    return movement

# --- Stock Alerts ---

@router.get("/stock/low-alerts", response_model=List[ProductListResponse])
def get_low_stock_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    products = db.query(Product).all()
    alert_products = []
    for p in products:
        if p.stock_level and p.stock_level.quantity_available <= (p.reorder_point or 0):
            alert_products.append(p)

    alert_products.sort(key=lambda x: x.stock_level.quantity_available if x.stock_level else 0)
    return alert_products

# --- Suppliers ---

@router.post("/suppliers", response_model=SupplierResponse, status_code=201)
def create_supplier(
    supplier_in: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Supplier).filter(Supplier.supplier_code == supplier_in.supplier_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Supplier code {supplier_in.supplier_code} already exists")

    supplier = Supplier(
        name=supplier_in.name,
        supplier_code=supplier_in.supplier_code,
        contact_email=str(supplier_in.contact_email) if supplier_in.contact_email else None,
        payment_terms_days=supplier_in.payment_terms_days or 30,
        lead_time_days=supplier_in.lead_time_days or 7,
        is_active=True
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/suppliers", response_model=List[SupplierResponse])
def list_suppliers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Supplier).all()


@router.get("/suppliers/{supplier_id}/catalog", response_model=List[ProductListResponse])
def get_supplier_catalog(supplier_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail=f"Supplier {supplier_id} not found")
    return supplier.products

# --- Purchase Orders ---

@router.post("/orders", response_model=PurchaseOrderResponse, status_code=201)
def create_purchase_order(
    po_in: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    supplier = db.query(Supplier).filter(Supplier.id == po_in.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=400, detail=f"Supplier {po_in.supplier_id} not found")

    # The line items carry a product_id, and it was the one foreign key on this
    # endpoint nobody checked. Measured against the running app: an order for
    # `product_id: 999999` returned HTTP 500 `{"detail": "Internal server error"}`
    # from SQLite's `FOREIGN KEY constraint failed`, while the sibling check three
    # lines above answered a clean 400 naming the missing supplier. Same endpoint,
    # same class of mistake, two different answers.
    #
    # Every id is resolved in one query and *all* the missing ones are reported, so
    # a client fixing a multi-line order does not have to resubmit once per bad id.
    requested_ids = {item.product_id for item in po_in.items}
    existing_ids = {
        row[0] for row in db.query(Product.id).filter(Product.id.in_(requested_ids)).all()
    }
    missing_ids = sorted(requested_ids - existing_ids)
    if missing_ids:
        listed = ", ".join(str(i) for i in missing_ids)
        raise HTTPException(
            status_code=400,
            detail=f"Product {listed} not found" if len(missing_ids) == 1
                   else f"Products not found: {listed}",
        )

    po_number = generate_po_number(db)

    total_amount = 0.0
    po_items = []

    for item_in in po_in.items:
        item_total = item_in.quantity_ordered * item_in.unit_cost
        total_amount += item_total
        po_items.append(POItem(
            product_id=item_in.product_id,
            quantity_ordered=item_in.quantity_ordered,
            unit_cost=item_in.unit_cost
        ))

    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=po_in.supplier_id,
        status=POStatus.draft,
        total_amount=total_amount,
        order_date=po_in.order_date,
        expected_delivery=po_in.expected_delivery,
        items=po_items
    )
    db.add(po)
    db.commit()
    db.refresh(po)

    logger.info("po_created", poc_id="POC-07", phase="P1", po_number=po.po_number, supplier_id=po.supplier_id, total_amount=po.total_amount)
    return po


@router.get("/orders", response_model=List[PurchaseOrderResponse])
def list_orders(
    status: Optional[str] = None,
    supplier_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(PurchaseOrder)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    return query.all()


@router.get("/orders/{order_id}", response_model=PurchaseOrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not po:
        raise HTTPException(status_code=404, detail=f"Purchase Order {order_id} not found")
    return po


@router.patch("/orders/{order_id}/receive", response_model=PurchaseOrderResponse)
def receive_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        po = receive_purchase_order(order_id, db)
        return po
    except ValueError as e:
        detail_msg = str(e)
        status_code = 404 if "not found" in detail_msg.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail_msg)

# --- Dashboard ---

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = get_dashboard_data(db)
    logger.info("dashboard_viewed", poc_id="POC-07", phase="P1", total_products=data["total_products"])
    return data

