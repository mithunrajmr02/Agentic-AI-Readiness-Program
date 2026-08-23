"""Reproducible demo dataset for POC-07.

Run it with:

    python -m src.backend.seed_demo_data

Why this exists
---------------
`inventory.db` is gitignored, and the only seeding the application performed at
startup was `seed_default_suppliers()` (src/backend/main.py:18), which inserts
three suppliers and nothing else. A fresh clone therefore came up with:

    suppliers 3 | products 0 | stock_levels 0 | purchase_orders 0 | movements 0

so on first launch the React dashboard showed 0 products and a total stock value
of Rs.0, `GET /api/v1/stock/low-alerts` returned an empty list, the Phase 4 chat
agent had nothing to answer questions about, and the Phase 5 orchestrator's
default target (product 1) did not exist. Every business record the project had
been demonstrated against lived only in one developer's untracked database, which
also meant the numbers in the submission documents could not be reproduced by a
reviewer.

Design notes
------------
* Idempotent. Every entity is matched on its natural key (supplier_code, sku,
  po_number) and skipped if already present, so re-running is safe and the script
  composes with `seed_default_suppliers()` in either order -- whichever runs first
  creates SUP-0001..0003, the other one notices they exist.

* Business logic is reused, not re-implemented. Stock arrives through
  `receive_purchase_order()` and alert rows are produced by
  `check_stock_alerts()` -- the same functions the API calls. A fixture that
  hand-wrote `stock_levels` and `stock_alerts` rows would drift from the real
  code paths and could make broken logic look healthy.

* Stock levels are derived from the movement ledger rather than asserted
  independently, so `sum(stock_movements.quantity) == stock_levels.quantity_on_hand`
  holds by construction. That invariant is what makes the movement history
  trustworthy, and it is checked at the end of this script.

* Supplier codes deliberately skip SUP-0004. Codes come from a vendor master in
  real deployments and do not track row ids; keeping id 4 paired with SUP-0005
  means the supplier lookup in the React order table
  (src/ui/web_react/src/App.jsx) stays honest -- the earlier code synthesised
  `SUP-000${po.supplier_id}` and silently attributed orders to the wrong vendor,
  a bug that is invisible whenever ids and codes happen to run in lockstep.

* To start over, delete inventory.db and relaunch; the app recreates the schema
  and the default admin account. There is intentionally no destructive flag here.

The dataset it produces
-----------------------
5 products across 4 categories, 4 suppliers (each with at least one product, so
`GET /api/v1/suppliers/{id}/catalog` returns rows for all of them), 4 purchase
orders spanning received/submitted/draft, and a movement ledger exercising all
five movement types. Resulting dashboard:

    total_products 5 | low_stock_count 1 | out_of_stock_count 2
    open_po_count 3   | total_stock_value 203700.0
"""

from datetime import date, timedelta

import structlog

from src.backend.database import Base, SessionLocal, engine
from src.backend.models import (
    Category,
    MovementType,
    POItem,
    POStatus,
    Product,
    PurchaseOrder,
    StockLevel,
    StockMovement,
    Supplier,
)
from src.backend.services.inventory_service import (
    check_stock_alerts,
    receive_purchase_order,
)

logger = structlog.get_logger()

TODAY = date.today()

SUPPLIERS = [
    dict(supplier_code="SUP-0001", name="Reliable Wholesale Ltd",
         contact_email="orders@reliablewholesale.com",
         payment_terms_days=30, lead_time_days=7),
    dict(supplier_code="SUP-0002", name="Apex Logistics & Supplies",
         contact_email="contact@apexlogistics.com",
         payment_terms_days=15, lead_time_days=3),
    dict(supplier_code="SUP-0003", name="Metro Goods Distribution",
         contact_email="sales@metrogoods.com",
         payment_terms_days=45, lead_time_days=10),
    dict(supplier_code="SUP-0005", name="Global Logistics Corp",
         contact_email="procurement@globallogistics.com",
         payment_terms_days=45, lead_time_days=5),
]

# `opening_stock` becomes the first receipt movement for the product. Products
# left at 0 are the out-of-stock cases the dashboard and alert endpoint need.
PRODUCTS = [
    dict(sku="SKU-GRO-0001", name="Organic Basmati Rice 10kg",
         category=Category.grocery, unit_price=850.0, cost_price=600.0,
         unit_of_measure="bags", reorder_point=15, reorder_quantity=60,
         supplier_code="SUP-0005", opening_stock=100),
    dict(sku="SKU-ELC-0001", name="Sony WH-1000XM5 Wireless Headphones",
         category=Category.electronics, unit_price=29990.0, cost_price=22000.0,
         unit_of_measure="units", reorder_point=10, reorder_quantity=25,
         supplier_code="SUP-0002", opening_stock=4),
    dict(sku="SKU-ELC-0002", name="Samsung 55-inch 4K QLED Smart TV",
         category=Category.electronics, unit_price=54990.0, cost_price=41000.0,
         unit_of_measure="units", reorder_point=5, reorder_quantity=15,
         supplier_code="SUP-0002", opening_stock=0),
    dict(sku="SKU-HHD-0001", name="Ariel Matic Liquid Detergent 2L",
         category=Category.household, unit_price=450.0, cost_price=310.0,
         unit_of_measure="bottles", reorder_point=20, reorder_quantity=100,
         supplier_code="SUP-0001", opening_stock=50),
    dict(sku="SKU-PRC-0001", name="Colgate Total Dental Cream 150g",
         category=Category.personal_care, unit_price=130.0, cost_price=90.0,
         unit_of_measure="tubes", reorder_point=30, reorder_quantity=120,
         supplier_code="SUP-0003", opening_stock=0),
]

PURCHASE_ORDERS = [
    # Received, so it contributes a receipt movement and +50 bags of stock.
    dict(po_number="PO-2026-0001", supplier_code="SUP-0005",
         status=POStatus.received, order_date=TODAY - timedelta(days=9),
         expected_delivery=TODAY - timedelta(days=2),
         items=[dict(sku="SKU-GRO-0001", quantity_ordered=50, unit_cost=600.0)]),
    # Replenishing the headphones, which are below their reorder point.
    dict(po_number="PO-2026-0002", supplier_code="SUP-0002",
         status=POStatus.draft, order_date=TODAY - timedelta(days=1),
         expected_delivery=TODAY + timedelta(days=5),
         items=[dict(sku="SKU-ELC-0001", quantity_ordered=10, unit_cost=22000.0)]),
    # Replenishing the out-of-stock television; exercises `submitted`.
    dict(po_number="PO-2026-0003", supplier_code="SUP-0002",
         status=POStatus.submitted, order_date=TODAY - timedelta(days=1),
         expected_delivery=TODAY + timedelta(days=6),
         items=[dict(sku="SKU-ELC-0002", quantity_ordered=15, unit_cost=41000.0)]),
    # Reorder quantity for the out-of-stock toothpaste, from its own supplier.
    dict(po_number="PO-2026-0004", supplier_code="SUP-0003",
         status=POStatus.draft, order_date=TODAY,
         expected_delivery=TODAY + timedelta(days=10),
         items=[dict(sku="SKU-PRC-0001", quantity_ordered=120, unit_cost=90.0)]),
]

# Applied in order, after PO-2026-0001 has been received. Tells a coherent story
# for the grocery line and covers every MovementType member.
MOVEMENTS = [
    dict(sku="SKU-GRO-0001", movement_type=MovementType.receipt, quantity=120,
         reference_number="RCV-2026-0142", notes="Weekly replenishment"),
    dict(sku="SKU-GRO-0001", movement_type=MovementType.sale, quantity=-18,
         reference_number="SALE-10421", notes="Counter sale - festive demand"),
    dict(sku="SKU-GRO-0001", movement_type=MovementType.sale, quantity=-25,
         reference_number="SALE-10455", notes="Bulk order - local restaurant"),
    dict(sku="SKU-GRO-0001", movement_type=MovementType.adjustment, quantity=-11,
         reference_number="CYCLE-08", notes="Cycle count shrinkage: 11 bags damaged in transit"),
    dict(sku="SKU-GRO-0001", movement_type=MovementType.returnm, quantity=6,
         reference_number="RET-2091", notes="Customer return - unopened"),
    dict(sku="SKU-GRO-0001", movement_type=MovementType.sale, quantity=-40,
         reference_number="SALE-10502", notes="Weekend clearance"),
    dict(sku="SKU-GRO-0001", movement_type=MovementType.transfer, quantity=-15,
         reference_number="TRF-BLR-002", notes="Transferred to Bengaluru outlet"),
]


def _seed_suppliers(db):
    created = 0
    for spec in SUPPLIERS:
        if db.query(Supplier).filter(Supplier.supplier_code == spec["supplier_code"]).first():
            continue
        db.add(Supplier(is_active=True, **spec))
        created += 1
    db.commit()
    return created


def _record_movement(db, product, movement_type, quantity, reference_number, notes):
    """Append to the ledger and move the stock level by the same amount."""
    stock = db.query(StockLevel).filter(StockLevel.product_id == product.id).first()
    if not stock:
        stock = StockLevel(product_id=product.id, quantity_on_hand=0, quantity_reserved=0)
        db.add(stock)
        db.flush()

    stock.quantity_on_hand = (stock.quantity_on_hand or 0) + quantity
    db.add(StockMovement(
        product_id=product.id,
        movement_type=movement_type,
        quantity=quantity,
        reference_number=reference_number,
        notes=notes,
        recorded_by="seed",
    ))
    check_stock_alerts(product, stock, db)


def _seed_products(db):
    created = 0
    for spec in PRODUCTS:
        if db.query(Product).filter(Product.sku == spec["sku"]).first():
            continue

        supplier = db.query(Supplier).filter(
            Supplier.supplier_code == spec["supplier_code"]
        ).first()
        if not supplier:
            raise RuntimeError(f"supplier {spec['supplier_code']} missing; seed suppliers first")

        product = Product(
            sku=spec["sku"], name=spec["name"], category=spec["category"],
            unit_price=spec["unit_price"], cost_price=spec["cost_price"],
            unit_of_measure=spec["unit_of_measure"],
            reorder_point=spec["reorder_point"],
            reorder_quantity=spec["reorder_quantity"],
            supplier_id=supplier.id,
        )
        db.add(product)
        db.flush()

        opening = spec["opening_stock"]
        if opening:
            _record_movement(db, product, MovementType.receipt, opening,
                             f"INIT-{product.sku[-4:]}", "Opening warehouse stock")
        else:
            # No opening receipt, but the product still needs a stock row so the
            # dashboard counts it as out of stock rather than skipping it -- the
            # dashboard loop ignores products whose stock_level is None.
            stock = StockLevel(product_id=product.id, quantity_on_hand=0, quantity_reserved=0)
            db.add(stock)
            db.flush()
            check_stock_alerts(product, stock, db)
        created += 1
    db.commit()
    return created


def _seed_purchase_orders(db):
    created = 0
    to_receive = []
    for spec in PURCHASE_ORDERS:
        if db.query(PurchaseOrder).filter(
            PurchaseOrder.po_number == spec["po_number"]
        ).first():
            continue

        supplier = db.query(Supplier).filter(
            Supplier.supplier_code == spec["supplier_code"]
        ).first()
        if not supplier:
            raise RuntimeError(f"supplier {spec['supplier_code']} missing; seed suppliers first")

        # A received PO is inserted as draft and then put through
        # receive_purchase_order(), so its stock arrives via the real code path.
        insert_status = POStatus.draft if spec["status"] == POStatus.received else spec["status"]

        po = PurchaseOrder(
            po_number=spec["po_number"],
            supplier_id=supplier.id,
            status=insert_status,
            order_date=spec["order_date"],
            expected_delivery=spec["expected_delivery"],
            total_amount=0.0,
        )
        db.add(po)
        db.flush()

        total = 0.0
        for item in spec["items"]:
            product = db.query(Product).filter(Product.sku == item["sku"]).first()
            if not product:
                raise RuntimeError(f"product {item['sku']} missing; seed products first")
            db.add(POItem(
                po_id=po.id,
                product_id=product.id,
                quantity_ordered=item["quantity_ordered"],
                unit_cost=item["unit_cost"],
            ))
            total += item["quantity_ordered"] * item["unit_cost"]

        # Derived from the line items rather than restated, so the header can
        # never disagree with what was ordered.
        po.total_amount = total
        created += 1
        if spec["status"] == POStatus.received:
            to_receive.append(po.id)

    db.commit()

    for po_id in to_receive:
        receive_purchase_order(po_id, db)
    return created


def _seed_movements(db):
    created = 0
    for spec in MOVEMENTS:
        product = db.query(Product).filter(Product.sku == spec["sku"]).first()
        if not product:
            raise RuntimeError(f"product {spec['sku']} missing; seed products first")

        # Reference numbers are unique per movement in this fixture, so they double
        # as the idempotency key.
        if db.query(StockMovement).filter(
            StockMovement.product_id == product.id,
            StockMovement.reference_number == spec["reference_number"],
        ).first():
            continue

        _record_movement(db, product, spec["movement_type"], spec["quantity"],
                         spec["reference_number"], spec["notes"])
        created += 1
    db.commit()
    return created


def verify(db):
    """Confirm the ledger and the stock levels agree, and report the dashboard."""
    from sqlalchemy import func

    from src.backend.services.inventory_service import get_dashboard_data

    problems = []
    for product in db.query(Product).all():
        ledger = db.query(func.coalesce(func.sum(StockMovement.quantity), 0)).filter(
            StockMovement.product_id == product.id
        ).scalar()
        stock = db.query(StockLevel).filter(StockLevel.product_id == product.id).first()
        on_hand = stock.quantity_on_hand if stock else None
        if on_hand != ledger:
            problems.append(f"{product.sku}: stock_levels={on_hand} but ledger sums to {ledger}")

    orphans = db.query(Product).filter(Product.supplier_id.is_(None)).count()
    if orphans:
        problems.append(f"{orphans} product(s) have no supplier_id")

    for po in db.query(PurchaseOrder).all():
        items_total = sum((i.quantity_ordered or 0) * (i.unit_cost or 0.0) for i in po.items)
        if abs((po.total_amount or 0.0) - items_total) > 0.01:
            problems.append(
                f"{po.po_number}: total_amount={po.total_amount} but items sum to {items_total}"
            )

    return problems, get_dashboard_data(db)


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        suppliers = _seed_suppliers(db)
        products = _seed_products(db)
        orders = _seed_purchase_orders(db)
        movements = _seed_movements(db)

        print(f"suppliers created:       {suppliers}")
        print(f"products created:        {products}")
        print(f"purchase orders created: {orders}")
        print(f"movements created:       {movements}")

        problems, dashboard = verify(db)
        print("\ndashboard after seeding:")
        for key, value in dashboard.items():
            print(f"  {key:20} {value}")

        if problems:
            print("\nINTEGRITY PROBLEMS:")
            for problem in problems:
                print(f"  - {problem}")
            raise SystemExit(1)
        print("\nintegrity checks passed (ledger == stock levels, PO totals == line items,"
              " every product has a supplier)")

        logger.info("demo_data_seeded", poc_id="POC-07", phase="P1",
                    suppliers=suppliers, products=products,
                    purchase_orders=orders, movements=movements)
    finally:
        db.close()


if __name__ == "__main__":
    main()
