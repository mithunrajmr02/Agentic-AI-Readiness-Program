import os
import requests
import logging
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

logger = logging.getLogger("agent.tools")

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")

def _api_get(endpoint: str) -> Any:
    """Helper to make GET requests to the Phase 1 API."""
    url = f"{API_BASE}{endpoint}"
    logger.info(f"API GET: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API Request failed: {e}")
        return {"error": f"API Request failed: {str(e)}"}

def _api_post(endpoint: str, data: dict) -> Any:
    """Helper to make POST requests to the Phase 1 API."""
    url = f"{API_BASE}{endpoint}"
    logger.info(f"API POST: {url}")
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API Request failed: {e}")
        return {"error": f"API Request failed: {str(e)}"}


@tool
def get_product_stock(sku: str) -> str:
    """Check the stock quantity, price, and category of a specific product using its SKU."""
    def _execute():
        res = _api_get("/products")
        if isinstance(res, dict) and "error" in res:
            return res["error"]
        for p in res:
            if p.get("sku") == sku:
                return str(p)
        return f"Product with SKU {sku} not found."
        
    if tracer:
        with tracer.start_as_current_span("tool_get_product_stock"):
            return _execute()
    return _execute()


@tool
def get_low_stock_alerts() -> str:
    """Retrieve a list of all products that have stock quantities at or below their reorder points."""
    def _execute():
        res = _api_get("/stock/low-alerts")
        if isinstance(res, dict) and "error" in res:
            return res["error"]
        if isinstance(res, list):
            return _summarize_if_long(res)
        return str(res)
        
    if tracer:
        with tracer.start_as_current_span("tool_get_low_stock_alerts"):
            return _execute()
    return _execute()


@tool
def create_purchase_order(supplier_code: str, items: List[Dict[str, Any]]) -> str:
    """Create a new purchase order. 'items' must be a list of dictionaries with keys sku and quantity."""
    def _execute():
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
        
    if tracer:
        with tracer.start_as_current_span("tool_create_purchase_order"):
            return _execute()
    return _execute()


@tool
def get_supplier_info(supplier_code: str) -> str:
    """Check supplier details such as lead time and payment terms."""
    def _execute():
        res = _api_get("/suppliers")
        if isinstance(res, dict) and "error" in res:
            return res["error"]
        for s in res:
            if s.get("supplier_code") == supplier_code:
                return str(s)
        return f"Supplier with code {supplier_code} not found."
        
    if tracer:
        with tracer.start_as_current_span("tool_get_supplier_info"):
            return _execute()
    return _execute()


@tool
def rag_knowledge_base(query: str) -> str:
    """Search the employee inventory manual for policies, lifecycle stages, formulas, or general guidelines."""
    def _execute():
        res = ask_question(query)
        if isinstance(res, dict) and "answer" in res:
            return res["answer"]
        return str(res)
        
    if tracer:
        with tracer.start_as_current_span("tool_rag_knowledge_base"):
            return _execute()
    return _execute()
