# POC-07: Inventory Management & Procurement System
## Retail Domain

**Phase Weight Distribution:** P1=15% | P2=20% | P3=20% | P4=25% | P5=20%
**Duration:** 25 working days | **Domain:** Retail Operations & Supply Chain

---

## 1. Business Context

India's retail sector manages millions of SKUs across organized and unorganized retail. Efficient inventory management — knowing what's on shelf, what's running low, and when to reorder — directly impacts revenue (stockouts lose sales) and working capital (overstock ties up cash). This POC builds the inventory management and procurement platform: tracking stock levels, raising purchase orders, managing supplier catalogs, and alerting on low-stock conditions.

---

## 2. Domain Personas

| Persona | Role | Uses the System To |
|---------|------|-------------------|
| **Priya Sharma** | Store Manager | Monitor stock levels, approve purchase orders |
| **Raj Patel** | Inventory Analyst | Analyze stock trends, set reorder points, audit movements |
| **Anita Singh** | Procurement Officer | Raise and track purchase orders with suppliers |
| **Dev Kumar** | Warehouse Staff | Record stock movements (in/out), update physical counts |

---

## 3. Core Entities & Data Model

### Product
| Field | Type | Description |
|-------|------|-------------|
| id | Integer (PK) | Auto-generated |
| sku | String (unique) | e.g., SKU-GRO-0042 |
| name | String | Product name |
| category | Enum | grocery / electronics / clothing / household / personal_care |
| unit_price | Float | Selling price in ₹ |
| cost_price | Float | Purchase cost in ₹ |
| unit_of_measure | String | pieces / kg / litre / box |
| reorder_point | Integer | Stock level that triggers reorder alert |
| reorder_quantity | Integer | Quantity to order when reordering |
| supplier_id | FK → Supplier | Primary supplier |

### StockLevel
| Field | Type | Description |
|-------|------|-------------|
| id | Integer (PK) | Auto-generated |
| product_id | FK → Product | Product |
| warehouse_id | FK → Warehouse | Location |
| quantity_on_hand | Integer | Current physical stock |
| quantity_reserved | Integer | Reserved for pending orders |
| quantity_available | Integer | on_hand - reserved |
| last_updated | DateTime | Last stock update |

### StockMovement
| Field | Type | Description |
|-------|------|-------------|
| id | Integer (PK) | Auto-generated |
| product_id | FK → Product | Product moved |
| movement_type | Enum | receipt / sale / adjustment / transfer / return |
| quantity | Integer | Units moved (positive = in, negative = out) |
| reference_number | String | PO number or sale reference |
| notes | String (nullable) | Reason for adjustment |
| recorded_at | DateTime | Timestamp |
| recorded_by | String | Staff member |

### PurchaseOrder
| Field | Type | Description |
|-------|------|-------------|
| id | Integer (PK) | Auto-generated |
| po_number | String (unique) | e.g., PO-2026-0042 |
| supplier_id | FK → Supplier | Supplier |
| status | Enum | draft / submitted / acknowledged / received / cancelled |
| total_amount | Float | Total order value in ₹ |
| order_date | Date | When PO was raised |
| expected_delivery | Date | Expected delivery date |
| received_date | Date (nullable) | Actual receipt date |
| items | Relationship → POItem | Line items |

### POItem
| Field | Type | Description |
|-------|------|-------------|
| id | Integer (PK) | Auto-generated |
| po_id | FK → PurchaseOrder | Parent PO |
| product_id | FK → Product | Product ordered |
| quantity_ordered | Integer | Units requested |
| unit_cost | Float | Agreed cost per unit |
| quantity_received | Integer (nullable) | Actually received |

### Supplier
| Field | Type | Description |
|-------|------|-------------|
| id | Integer (PK) | Auto-generated |
| name | String | Supplier name |
| supplier_code | String (unique) | e.g., SUP-0001 |
| contact_email | String | Contact email |
| payment_terms_days | Integer | Net payment days |
| lead_time_days | Integer | Typical delivery lead time |
| is_active | Boolean | Active supplier flag |

### Alert (Stock)
| Field | Type | Description |
|-------|------|-------------|
| id | Integer (PK) | Auto-generated |
| product_id | FK → Product | Product |
| alert_type | Enum | low_stock / out_of_stock / overstock / reorder_suggested |
| message | String | Alert description |
| is_resolved | Boolean | Alert acknowledged |
| triggered_at | DateTime | Alert creation time |

---

## 4. Business Rules

1. **Low stock alert:** quantity_available ≤ reorder_point → create low_stock alert
2. **Out of stock:** quantity_available = 0 → create out_of_stock alert (critical)
3. **PO number format:** PO-{YEAR}-{NNNN} e.g., PO-2026-0042
4. **SKU format:** SKU-{CATEGORY_PREFIX}-{NNNN} e.g., SKU-GRO-0042
5. **Stock movement:** quantity_on_hand updated after every StockMovement record
6. **Receiving PO:** PATCH /orders/{id}/receive triggers StockMovement(receipt) for each POItem

---

## 5. REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/products | List products (filter by category, low_stock=true) |
| POST | /api/v1/products | Create new product |
| GET | /api/v1/products/{id} | Get product with stock level |
| PATCH | /api/v1/products/{id}/stock | Update stock quantity (record movement) |
| POST | /api/v1/orders | Create purchase order |
| GET | /api/v1/orders | List orders (filter by status, supplier) |
| GET | /api/v1/orders/{id} | Get PO with line items |
| PATCH | /api/v1/orders/{id}/receive | Mark PO received, update stock |
| GET | /api/v1/stock/low-alerts | Get all low stock and out-of-stock products |
| GET | /api/v1/suppliers/{id}/catalog | Get supplier's products with cost prices |
| GET | /api/v1/dashboard | Inventory dashboard |
| POST | /api/v1/auth/register | Register user |
| POST | /api/v1/auth/login | Login |

---

## 6. Phase 5 Agents

**Agents:** Demand Forecaster → Reorder Agent → Supplier Coordinator → Inventory Auditor

**State:** `InventoryAnalysisState` with fields: product_id, product_data, demand_forecast, reorder_recommendation, supplier_quote, audit_report, analysis_status, errors, messages

---

## 7. Glossary

| Term | Definition |
|------|-----------|
| SKU | Stock Keeping Unit — unique product identifier |
| Reorder Point | Stock level at which replenishment should begin |
| Lead Time | Days from PO submission to stock receipt |
| Stockout | Zero inventory — unable to fulfill demand |
| Overstock | Excess inventory — capital tied up unnecessarily |
| FIFO | First In, First Out — inventory accounting method |
| Safety Stock | Buffer inventory held to prevent stockouts |
| PO | Purchase Order — formal request to supplier to supply goods |
| Stock Movement | Any change in inventory quantity |
| Capacity Factor | Ratio of actual output to maximum possible output |
