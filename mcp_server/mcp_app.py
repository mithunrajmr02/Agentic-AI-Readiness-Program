"""Facade module exposing FastMCP application and tools."""
import requests
import structlog
from src.mcp_server.mcp_app import (
    mcp,
    tracer,
    BASE_URL,
    _get,
    _post,
    _patch,
    update_stock,
    create_purchase_order,
    get_low_stock_products,
    get_supplier_catalog,
    get_purchase_orders,
    get_inventory_dashboard,
)

__all__ = [
    "requests",
    "structlog",
    "mcp",
    "tracer",
    "BASE_URL",
    "_get",
    "_post",
    "_patch",
    "update_stock",
    "create_purchase_order",
    "get_low_stock_products",
    "get_supplier_catalog",
    "get_purchase_orders",
    "get_inventory_dashboard",
]

if __name__ == "__main__":
    mcp.run()
