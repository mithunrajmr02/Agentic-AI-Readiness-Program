"""
FastMCP Server for Retail Inventory & Procurement System (Phase 4).
Exposes backend endpoints and tools to LLMs via Model Context Protocol (MCP).
"""

import os
import logging
from src.mcp_server.mcp_app import mcp

logger = logging.getLogger("mcp_server")


def get_server_status() -> dict:
    """Return status of the MCP server."""
    return {
        "status": "ready",
        "name": mcp.name,
        "version": "1.0.0",
        "phase": "Phase 4 Completed",
    }


if __name__ == "__main__":  # pragma: no cover
    print(f"Starting {mcp.name} FastMCP Server...")
    mcp.run()
