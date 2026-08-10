# Inventory Management & Procurement Operations Manual
## POC-07 — Retail Inventory Reference Guide

### Section 1: Introduction to Inventory Management

Inventory management is the process of ordering, storing, and using a company's inventory — raw materials, components, and finished products. Effective inventory management ensures products are available when customers need them while minimizing carrying costs and avoiding overstock situations.

This system manages four main activities: product catalog management, stock level tracking, purchase order management, and stock movement recording. All inventory changes are recorded as stock movements for full auditability.

### Section 2: Product Catalog and SKU System

Every product has a unique Stock Keeping Unit (SKU) identifier generated in the format `SKU-{CATEGORY_PREFIX}-{NNNN}`.

Category prefixes:
- GRO: Grocery products
- ELC: Electronics
- CLO: Clothing and apparel
- HHD: Household items
- PRC: Personal care products

Examples: SKU-GRO-0042 (Grocery item #42), SKU-ELC-0015 (Electronics item #15), SKU-CLO-0108 (Clothing item #108), SKU-HHD-0021 (Household item #21), SKU-PRC-0055 (Personal care item #55).

Each product record contains the following mandatory attributes: unit_price (selling price in ₹), cost_price (purchase cost in ₹), unit_of_measure (pieces/kg/litre/box), reorder_point (trigger level for replenishment), and reorder_quantity (standard order size).

### Section 3: Stock Levels and Reorder Points

Every product has an associated StockLevel record tracking three core metrics:
- quantity_on_hand: physical inventory count currently in stock
- quantity_reserved: quantity allocated to pending customer orders
- quantity_available: working stock calculated as quantity_on_hand minus quantity_reserved

The reorder_point is the threshold stock level at which a replenishment order must be initiated. Setting it accurately requires calculating:
`reorder_point = (average daily demand × supplier lead time) + safety stock`

Example: A product selling 10 units per day with a 5-day supplier lead time and 2 days of safety stock requires a reorder point of `(10 × 5) + (10 × 2) = 70 units`.

### Section 4: Stock Alert System

The system automatically generates alerts based on real-time stock conditions:

**Low Stock Alert:** Triggered when `quantity_available ≤ reorder_point`. This serves as a warning — action should be taken within 24-48 hours to raise a purchase order.

**Out of Stock Alert:** Triggered when `quantity_available = 0`. This is a critical alert requiring immediate action. Lost sales occur with every customer request while stock remains at zero.

**Reorder Suggested Alert:** The system may also suggest reorder quantities based on historical consumption patterns.

All stock alerts can be resolved once a purchase order is submitted and received. Resolved alerts remain stored in the audit log for historical reporting.

### Section 5: Purchase Order (PO) Process

Purchase Orders (POs) represent the formal document for placing orders with suppliers. The PO lifecycle consists of five distinct statuses:

1. **Draft:** Created by procurement officer, items added.
2. **Submitted:** Sent to supplier via email or portal notification.
3. **Acknowledged:** Supplier confirms receipt and expected delivery date.
4. **Received:** Goods arrive, warehouse staff marks PO as received, stock levels updated automatically.
5. **Cancelled:** PO cancelled prior to goods receipt.

PO number format: `PO-{YEAR}-{NNNN}`, for example, PO-2026-0042.

When a PO is marked as received, the system automatically performs three actions:
- Creates StockMovement(receipt) records for each line item.
- Updates quantity_on_hand for each received product.
- Resolves any active low_stock or out_of_stock alerts associated with the received products.

### Section 6: Supplier Management

Suppliers have the following key attributes:
- supplier_code: unique supplier identifier in `SUP-{NNNN}` format (e.g., SUP-0001).
- lead_time_days: number of days from order placement to delivery.
- payment_terms_days: net payment window in days (e.g., Net 30 = payment within 30 days).
- is_active: boolean flag indicating whether the supplier can receive new POs.

Supplier selection criteria include price competitiveness, lead time reliability, quality compliance, and payment terms. Procurement staff must verify a supplier is active before raising a PO.

### Section 7: Stock Movement Recording

Every inventory change must be recorded as a StockMovement entry containing a valid movement_type:

- **receipt:** Goods received from a purchase order (positive quantity).
- **sale:** Goods sold to a customer (negative quantity — recorded as negative values).
- **adjustment:** Manual correction following physical count discrepancies.
- **transfer:** Inventory moved between different warehouses or store locations.
- **return:** Customer return or return of defective goods to supplier.

The reference_number links the movement to its source document (PO number, sales order ID, etc.). All movements are timestamped and attributed to the recording staff member.

### Section 8: Inventory Valuation

Inventory is valued at cost price using the FIFO (First In, First Out) methodology. Total stock value across the inventory is calculated as:
`Total Stock Value = SUM(product.cost_price × stock_level.quantity_on_hand)`

The inventory dashboard displays total_stock_value to give management full visibility into working capital tied up in stock. Overstock situation (inventory significantly exceeding reorder needs) increases carrying costs.

### Section 9: Reorder Quantity Calculation

The Economic Order Quantity (EOQ) formula helps determine the optimal order quantity:
`EOQ = √( (2 × annual_demand × ordering_cost) / holding_cost_per_unit )`

In standard retail operations, a practical lead-time rule is frequently applied: order enough stock to cover lead_time plus safety stock period.
Example: If a product sells 5 units/day, supplier lead time is 7 days, and safety stock period is 14 days:
`reorder_quantity = (5 × 7) + (5 × 14) = 35 + 70 = 105 units`.

### Section 10: Procurement Officer Responsibilities

The Procurement Officer (Anita Singh) is responsible for:
1. Monitoring low_stock and out_of_stock alerts daily.
2. Reviewing supplier catalogs for optimal pricing and delivery lead times.
3. Raising POs within 24 hours of a low_stock alert trigger.
4. Confirming supplier acknowledgement and expected delivery dates.
5. Coordinating goods receipt with warehouse staff (Dev Kumar).

**PO Approval Threshold:** Purchase Orders with a total value above ₹50,000 require formal Store Manager approval prior to supplier submission.

### Section 11: Stock Count and Reconciliation

Physical stock counts must be conducted on a scheduled basis:
- **Cycle count:** Continuous counting of a subset of products daily or weekly (high-value items counted weekly).
- **Full count:** Complete physical inventory count performed quarterly.

When a discrepancy is identified between physical count and system stock level:
Record a `StockMovement(adjustment)` with the difference. If positive: physical count was higher than system count (understated count). If negative: system count was higher than physical count (shrinkage, theft, or damage).

### Section 12: Category Management

Each product category exhibits unique demand and handling characteristics:
- **Grocery:** Short shelf life, high sales velocity, requires tight reorder management and expiration tracking.
- **Electronics:** High unit cost, lower sales velocity, longer supplier lead times typical.
- **Clothing:** Seasonal demand patterns, size and variant management critical.
- **Household:** Moderate sales velocity, highly predictable demand patterns.
- **Personal Care:** High sales velocity, strong brand loyalty, competitive market pricing.

### Section 13: Reporting and Analytics

Key inventory performance reports:
- **Slow-moving stock:** Products with no stock movement in 30+ days.
- **Stock turn ratio:** Cost of goods sold / average inventory value (higher ratio indicates better inventory efficiency).
- **Fill rate:** Percentage of customer orders fulfilled immediately without stockouts.
- **Days on hand:** quantity_on_hand / average daily sales.

The Store Manager reviews these reports weekly. Raj Patel (Inventory Analyst) prepares monthly trend reports for executive management.

### Section 14: System Integration

The inventory management system integrates with external systems:
- Point of Sale (POS): automatic recording of sales stock movements upon customer checkout.
- Supplier Portal: electronic PO submission and automated status acknowledgement.
- Finance System: PO amounts flow directly into accounts payable ledger.

When automated integration is unavailable, manual StockMovement records must be created by authorized staff.

### Section 15: Troubleshooting

**Problem: Stock level shows negative**
Cause: Sale recorded before receipt processing, or manual data entry error.
Fix: Record a positive StockMovement(adjustment) to correct the quantity_on_hand, then investigate root cause.

**Problem: Duplicate low_stock alerts**
Cause: Multiple triggers before initial alert was resolved.
Fix: System should verify no unresolved alert exists for the product prior to generating a new alert.

**Problem: PO received but stock not updated**
Cause: `PATCH /api/v1/orders/{id}/receive` API call was skipped or failed silently.
Fix: Inspect API logs, verify PO status is set to "received", and manually trigger receipt workflow if required.

**Problem: SKU not found by supplier**
Cause: Product registered internally but missing from supplier catalog.
Fix: Add product to supplier's catalog mapping and verify supplier_id on the product record.
