import os
import requests
import structlog
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool

# Assuming OpenTelemetry is set up
try:
    from opentelemetry import trace
    tracer = trace.get_tracer("POC-07-Tools-Tracer")
except ImportError:
    tracer = None

from src.agents.summarizer import _summarize_if_long
from src.rag.rag_chain import ask_question

# structlog rather than stdlib `logging`, so these events join the same
# structured stream as the backend and the MCP server instead of being the one
# component that logs unparseable prose.
logger = structlog.get_logger("agent.tools")

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")


@contextmanager
def _tool_span(tool_name: str):
    """Open a span for one tool invocation and emit the mandated `tool_called` event.

    Phase 3 requires both a `poc_id`-tagged span and a
    `logger.info("tool_called", poc_id=..., phase="P3", tool=...)` record per tool
    (phase3-context-engineering.md, lines 45-54 and the observability checklist).
    Neither was present: `grep -rn tool_called` over the agent package returned
    nothing at all, and while every tool did open a span, none set a single
    attribute -- so a trace showed that *a* tool ran but not which POC or phase it
    belonged to.

    The event is emitted on entry, not on the happy path only. A tool that raises
    or returns an API error is still a tool that was called, and those are the
    invocations an operator most needs to see in the log.
    """
    logger.info("tool_called", poc_id="POC-07", phase="P3", tool=tool_name)
    if tracer is None:
        yield
        return
    with tracer.start_as_current_span(f"tool_{tool_name}") as span:
        try:
            span.set_attribute("poc_id", "POC-07")
            span.set_attribute("phase", "P3")
            span.set_attribute("tool", tool_name)
        except Exception:  # pragma: no cover - a no-op tracer has no attributes
            pass
        yield



def _send(send) -> Any:
    """Run an authenticated request, refreshing the service token once on a 401.

    The Phase 3 agent tools previously called the API anonymously; that only
    worked while `get_current_user` treated a missing token as the admin user.
    See src/service_auth.py for why the token comes from a real login.
    """
    from src import service_auth

    try:
        response = send(service_auth.auth_headers())
        if getattr(response, "status_code", None) == 401:
            service_auth.invalidate()
            response = send(service_auth.auth_headers(force_refresh=True))
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API Request failed: {e}")
        return {"error": f"API Request failed: {str(e)}"}


def _api_get(endpoint: str) -> Any:
    """Helper to make GET requests to the Phase 1 API."""
    url = f"{API_BASE}{endpoint}"
    logger.info(f"API GET: {url}")
    return _send(lambda headers: requests.get(url, headers=headers, timeout=10))

def _api_post(endpoint: str, data: dict) -> Any:
    """Helper to make POST requests to the Phase 1 API."""
    url = f"{API_BASE}{endpoint}"
    logger.info(f"API POST: {url}")
    return _send(lambda headers: requests.post(url, json=data, headers=headers, timeout=10))


@tool
def get_product_stock(sku: str) -> str:
    """Check the stock quantity, price, and category of a specific product using its SKU."""
    with _tool_span("get_product_stock"):
        res = _api_get("/products")
        if isinstance(res, dict) and "error" in res:
            return res["error"]
        for p in res:
            if p.get("sku") == sku:
                return str(p)
        return f"Product with SKU {sku} not found."


@tool
def get_low_stock_alerts() -> str:
    """Retrieve a list of all products that have stock quantities at or below their reorder points."""
    with _tool_span("get_low_stock_alerts"):
        res = _api_get("/stock/low-alerts")
        if isinstance(res, dict) and "error" in res:
            return res["error"]
        if isinstance(res, list):
            return _summarize_if_long(res)
        return str(res)


@tool
def create_purchase_order(supplier_code: str, items: List[Dict[str, Any]]) -> str:
    """Create a new purchase order. 'items' must be a list of dictionaries with keys sku and quantity."""
    with _tool_span("create_purchase_order"):
        # Find supplier ID
        suppliers = _api_get("/suppliers")
        if isinstance(suppliers, dict) and "error" in suppliers:
            return suppliers["error"]
        supplier = next((s for s in suppliers if s.get("supplier_code") == supplier_code), None)
        if not supplier:
            return f"Supplier with code {supplier_code} not found."
            
        supplier_id = supplier["id"]
        
        # Find products to get their IDs and cost_price
        products = _api_get("/products")
        if isinstance(products, dict) and "error" in products:
            return products["error"]
            
        po_items = []
        for item in items:
            sku = item.get("sku")
            quantity = item.get("quantity")
            if not sku or not quantity:
                return f"Invalid item format: {item}. Must contain 'sku' and 'quantity'."
                
            product = next((p for p in products if p.get("sku") == sku), None)
            if not product:
                return f"Product with SKU {sku} not found."
                
            po_items.append({
                "product_id": product["id"],
                "quantity_ordered": quantity,
                "unit_cost": product.get("cost_price", 0.0)
            })
            
        from datetime import datetime, timedelta
        
        data = {
            "supplier_id": supplier_id,
            "order_date": datetime.now().date().isoformat(),
            "expected_delivery": (datetime.now() + timedelta(days=supplier.get("lead_time_days", 7))).date().isoformat(),
            "items": po_items
        }
        
        res = _api_post("/orders", data=data)
        if isinstance(res, dict) and "error" in res:
            return res["error"]
        return str(res)


@tool
def get_supplier_info(supplier_code: str) -> str:
    """Check supplier details such as lead time and payment terms."""
    with _tool_span("get_supplier_info"):
        res = _api_get("/suppliers")
        if isinstance(res, dict) and "error" in res:
            return res["error"]
        for s in res:
            if s.get("supplier_code") == supplier_code:
                return str(s)
        return f"Supplier with code {supplier_code} not found."


@tool
def get_supplier_catalog(supplier: str) -> str:
    """List every product a supplier sells, with cost prices. Accepts a supplier code like SUP-0001 or a numeric supplier id.

    Use this to answer questions such as "what can we buy from SUP-0002 and at what
    cost" before deciding where to place a purchase order.
    """
    with _tool_span("get_supplier_catalog"):
        # The endpoint is keyed on the numeric id, but a conversation names a
        # supplier by its code ("SUP-0002") far more often than by its primary key,
        # and the two sibling supplier tools both take a code. Accepting either
        # spares the agent a guess it has no way to get right.
        reference = str(supplier).strip()
        supplier_id = None
        supplier_label = reference

        if reference.isdigit():
            supplier_id = int(reference)
        else:
            suppliers = _api_get("/suppliers")
            if isinstance(suppliers, dict) and "error" in suppliers:
                return suppliers["error"]
            match = next(
                (s for s in suppliers if s.get("supplier_code", "").upper() == reference.upper()),
                None,
            )
            if not match:
                return f"Supplier with code {reference} not found."
            supplier_id = match["id"]
            supplier_label = f"{match.get('name', reference)} ({match.get('supplier_code')})"

        res = _api_get(f"/suppliers/{supplier_id}/catalog")
        if isinstance(res, dict) and "error" in res:
            return res["error"]
        if not isinstance(res, list):
            return str(res)
        if not res:
            return f"Supplier {supplier_label} has no products on file."

        lines = [f"Catalog for supplier {supplier_label} ({len(res)} products):"]
        for p in res:
            stock = p.get("stock_level") or {}
            lines.append(
                f"- {p.get('sku')}: {p.get('name')} | cost INR {p.get('cost_price')}"
                f" per {p.get('unit_of_measure')} | on hand {stock.get('quantity_on_hand', 'unknown')}"
            )
        return "\n".join(lines)


@tool
def get_dashboard_stats() -> str:
    """Get overall inventory KPIs: total products, low-stock count, out-of-stock count, open purchase orders, and the total value of current inventory.

    This is the tool to use for portfolio-wide questions such as "what is the total
    value of our current inventory?" -- it needs no arguments.
    """
    with _tool_span("get_dashboard_stats"):
        res = _api_get("/dashboard")
        if isinstance(res, dict) and "error" in res:
            return res["error"]
        if not isinstance(res, dict):
            return str(res)
        # Spelled out rather than handed over as a raw dict, because the numbers are
        # the answer here and the model should not have to infer that
        # `total_stock_value` is rupees or that `low_stock_count` counts products.
        return (
            f"Inventory dashboard: {res.get('total_products')} products tracked; "
            f"{res.get('low_stock_count')} at or below reorder point; "
            f"{res.get('out_of_stock_count')} out of stock; "
            f"{res.get('open_po_count')} open purchase orders; "
            f"total value of current inventory INR {res.get('total_stock_value')}."
        )


@tool
def rag_knowledge_base(query: str) -> str:
    """Search the employee inventory manual for policies, lifecycle stages, formulas, or general guidelines."""
    with _tool_span("rag_knowledge_base"):
        res = ask_question(query)
        if isinstance(res, dict) and "answer" in res:
            return res["answer"]
        return str(res)
