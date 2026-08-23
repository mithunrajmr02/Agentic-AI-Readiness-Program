import os
from typing import Optional, List, Dict, Any
import requests
import structlog
from fastmcp import FastMCP

# OpenTelemetry configuration
try:
    from opentelemetry import trace
    tracer = trace.get_tracer("poc-07-mcp")
except Exception:  # pragma: no cover
    class DummySpan:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def set_attribute(self, key, value):
            pass

    class DummyTracer:
        def start_as_current_span(self, name):
            return DummySpan()

    tracer = DummyTracer()

logger = structlog.get_logger()
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
mcp = FastMCP("Inventory Management Server")


def _send(send) -> Any:
    """Run an authenticated request, refreshing the token once on a 401.

    These three helpers used to send no `Authorization` header at all, which only
    worked because the backend served unauthenticated callers as the admin user.
    Now that authentication is enforced, the MCP tools authenticate as the shared
    service account.

    The retry exists because the cached token outlives nothing in particular: the
    backend may have restarted with a different SECRET_KEY, or the token may have
    aged past its 24h expiry mid-session. One forced re-login on a 401 handles
    both without the client having to reason about expiry itself.
    """
    from src import service_auth

    try:
        r = send(service_auth.auth_headers())
        if getattr(r, "status_code", None) == 401:
            service_auth.invalidate()
            r = send(service_auth.auth_headers(force_refresh=True))
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "API unavailable"}
    except Exception as e:
        return {"error": str(e)}


def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Helper to perform HTTP GET request against the Phase 1 backend."""
    return _send(
        lambda headers: requests.get(
            f"{BASE_URL}{path}", params=params or {}, headers=headers, timeout=10
        )
    )


def _post(path: str, payload: Dict[str, Any]) -> Any:
    """Helper to perform HTTP POST request against the Phase 1 backend."""
    return _send(
        lambda headers: requests.post(
            f"{BASE_URL}{path}", json=payload, headers=headers, timeout=10
        )
    )


def _patch(path: str, payload: Dict[str, Any]) -> Any:
    """Helper to perform HTTP PATCH request against the Phase 1 backend."""
    return _send(
        lambda headers: requests.patch(
            f"{BASE_URL}{path}", json=payload, headers=headers, timeout=10
        )
    )


def _parse_id(val: Any, key_name: str = "id") -> Optional[int]:
    """Helper to safely extract integer ID from int, string, or stringified JSON dict."""
    if val is None:
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, dict):
        return val.get(key_name) or val.get("id") or val.get("supplier_id") or val.get("product_id")
    if isinstance(val, str):
        val_str = val.strip()
        if val_str.startswith("{") and "}" in val_str:
            try:
                import json
                d = json.loads(val_str)
                return d.get(key_name) or d.get("id") or d.get("supplier_id") or d.get("product_id")
            except Exception:
                pass
        try:
            return int(val_str)
        except Exception:
            pass
    return val


@mcp.tool()
def update_stock(
    product_id: Any,
    movement_type: str,
    quantity: Any,
    reference_number: Optional[str] = None,
    notes: Optional[str] = None
) -> dict:
    """Update stock for a product by recording a stock movement. movement_type must be one of:
    receipt, sale, adjustment, transfer, return. Positive quantity = stock in, negative = stock out.
    Automatically triggers low_stock alert if available quantity drops below reorder point."""
    pid = _parse_id(product_id, "product_id") or product_id
    qty = int(quantity) if isinstance(quantity, (int, str)) and str(quantity).isdigit() else quantity
    with tracer.start_as_current_span("mcp.tool.update_stock") as span:
        span.set_attribute("poc_id", "POC-07")
        payload = {
            "movement_type": movement_type,
            "quantity": qty,
            "reference_number": reference_number,
            "notes": notes,
        }
        # Backend router accepts PATCH on /products/{product_id}/stock
        result = _patch(f"/products/{pid}/stock", payload)
        # Fallback to POST if server expects POST
        if isinstance(result, dict) and result.get("error") and "405" in str(result.get("error")):
            result = _post(f"/products/{pid}/stock", payload)
        logger.info(
            "mcp_tool_called",
            poc_id="POC-07",
            phase="P4",
            tool="update_stock",
            product_id=pid,
        )
        return result


@mcp.tool()
def create_purchase_order(
    supplier_id: Any,
    order_date: str,
    items: list,
    expected_delivery: Optional[str] = None
) -> dict:
    """Create a new purchase order for a supplier. items should be a list of dicts with 
    product_id, quantity_ordered, unit_cost. PO number is auto-generated as PO-YEAR-NNNN. 
    Initial status is 'draft'."""
    sid = _parse_id(supplier_id, "supplier_id") or supplier_id
    with tracer.start_as_current_span("mcp.tool.create_purchase_order") as span:
        span.set_attribute("poc_id", "POC-07")
        payload = {
            "supplier_id": sid,
            "order_date": order_date,
            "items": items,
            "expected_delivery": expected_delivery,
        }
        result = _post("/orders", payload)
        logger.info(
            "mcp_tool_called",
            poc_id="POC-07",
            phase="P4",
            tool="create_purchase_order",
            supplier_id=sid,
        )
        return result


@mcp.tool()
def get_low_stock_products() -> list:
    """Get all products currently at or below their reorder point. Returns products needing 
    immediate procurement attention, sorted by urgency (out-of-stock first, then lowest 
    available quantity). Use this to prioritize purchase order creation."""
    with tracer.start_as_current_span("mcp.tool.get_low_stock_products") as span:
        span.set_attribute("poc_id", "POC-07")
        result = _get("/stock/low-alerts")
        logger.info(
            "mcp_tool_called",
            poc_id="POC-07",
            phase="P4",
            tool="get_low_stock_products",
        )
        return result


@mcp.tool()
def get_supplier_catalog(supplier_id: Any) -> list:
    """Get a supplier's product catalog with SKUs, product names, and cost prices. 
    Use when creating purchase orders or comparing supplier prices for procurement decisions."""
    sid = _parse_id(supplier_id, "supplier_id") or supplier_id
    with tracer.start_as_current_span("mcp.tool.get_supplier_catalog") as span:
        span.set_attribute("poc_id", "POC-07")
        result = _get(f"/suppliers/{sid}/catalog")
        logger.info(
            "mcp_tool_called",
            poc_id="POC-07",
            phase="P4",
            tool="get_supplier_catalog",
            supplier_id=sid,
        )
        return result


@mcp.tool()
def get_purchase_orders(
    status: Optional[str] = None,
    supplier_id: Optional[Any] = None
) -> list:
    """List purchase orders with optional filtering by status (draft/submitted/acknowledged/received/cancelled)
    or supplier. Returns PO number, supplier, status, total amount, and expected delivery date."""
    sid = _parse_id(supplier_id, "supplier_id") if supplier_id is not None else None
    with tracer.start_as_current_span("mcp.tool.get_purchase_orders") as span:
        span.set_attribute("poc_id", "POC-07")
        params = {}
        if status:
            params["status"] = status
        if sid:
            params["supplier_id"] = sid
        result = _get("/orders", params)
        logger.info(
            "mcp_tool_called",
            poc_id="POC-07",
            phase="P4",
            tool="get_purchase_orders",
        )
        return result


@mcp.tool()
def get_inventory_dashboard() -> dict:
    """Get the inventory management dashboard with overall health metrics: total products,
    low stock count, out of stock count, open purchase orders, and total stock value in ₹."""
    with tracer.start_as_current_span("mcp.tool.get_inventory_dashboard") as span:
        span.set_attribute("poc_id", "POC-07")
        result = _get("/dashboard")
        logger.info(
            "mcp_tool_called",
            poc_id="POC-07",
            phase="P4",
            tool="get_inventory_dashboard",
        )
        return result


if __name__ == "__main__":  # pragma: no cover
    mcp.run()
