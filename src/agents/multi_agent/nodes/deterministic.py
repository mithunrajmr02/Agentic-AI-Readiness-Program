"""Deterministic production nodes for the governed replenishment graph.

The legacy named functions in ``agents.py`` remain an externally tested Phase-5
compatibility surface.  The graph itself uses these nodes: arithmetic and
supplier choice come only from WS-1 and WS-7, never from an LLM response.
"""
from dataclasses import asdict
from math import ceil

from src.agents.multi_agent.state import InventoryAnalysisState
from src.analytics.demand import compute_daily_demand
from src.analytics.reorder import derive_reorder_point, derive_reorder_quantity
from src.backend.database import SessionLocal
from src.backend.models import Product, StockLevel
from src.core.vocab import project_analysis_status
from src.sourcing.selection import select_supplier


def _computed(value):
    return asdict(value)


def deterministic_demand_forecaster(state: InventoryAnalysisState) -> InventoryAnalysisState:
    """Entry node: load facts and compute demand before any LLM can run."""
    messages = list(state.get("messages", []))
    errors = list(state.get("errors", []))
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == state.get("product_id")).first()
        stock = db.query(StockLevel).filter(StockLevel.product_id == state.get("product_id")).first()
        demand = compute_daily_demand(db, state.get("product_id"))
        reorder_point = derive_reorder_point(db, state.get("product_id"))
        available = stock.quantity_available if stock else 0
        days = None if demand.value in (None, 0) else round(available / demand.value, 2)
        risk = "unknown" if demand.value is None else ("high" if available <= (reorder_point.value or 0) else "none")
        product_data = {} if product is None else {
            "id": product.id, "sku": product.sku, "name": product.name,
            "cost_price": product.cost_price, "reorder_point": product.reorder_point,
            "supplier_id": product.supplier_id,
            "stock_level": {"quantity_available": available, "quantity_reserved": stock.quantity_reserved if stock else 0},
        }
        computed = {**state.get("computed", {}), "daily_demand": _computed(demand), "reorder_point": _computed(reorder_point)}
        messages.extend([
            f"Demand Forecaster: loaded {demand.sample_size} sale events across {demand.inputs.get('distinct_sale_days', 0)} days.",
            f"Demand Forecaster: computed daily demand={demand.value}; reorder point={reorder_point.value}.",
            f"Demand Forecaster: data sufficiency is {demand.sufficiency}.",
        ])
        return {**state, "product_data": product_data,
                "demand_forecast": {"avg_daily_demand": demand.value, "days_of_stock_remaining": days, "stockout_risk": risk,
                                    "demand_trend": "computed", "forecast_notes": demand.formula},
                "computed": computed, "data_sufficiency": demand.sufficiency,
                "messages": messages, "errors": errors}
    except Exception as exc:
        errors.append(f"Demand computation error: {exc}")
        messages.extend(["Demand Forecaster: source data could not be loaded.", "Demand Forecaster: no demand value was computed.", "Demand Forecaster: data sufficiency is none."])
        return {**state, "data_sufficiency": "none", "messages": messages, "errors": errors}
    finally:
        db.close()


def deterministic_reorder_agent(state: InventoryAnalysisState) -> InventoryAnalysisState:
    """Derive the practical manual §9 reorder quantity, without an LLM."""
    messages = list(state.get("messages", []))
    db = SessionLocal()
    try:
        quantity = derive_reorder_quantity(db, state.get("product_id"))
        available = (state.get("product_data", {}).get("stock_level", {}) or {}).get("quantity_available", 0)
        point = (state.get("computed", {}).get("reorder_point", {}) or {}).get("value")
        required = quantity.value is not None and (point is None or available <= point)
        recommended = ceil(quantity.value) if required else 0
        recommendation = {"reorder_required": required, "recommended_quantity": recommended,
                          "urgency": "immediate" if required else "not_required", "reason": quantity.formula}
        messages.append(f"Reorder Agent: computed quantity={recommended}; required={required}.")
        return {**state, "reorder_recommendation": recommendation,
                "computed": {**state.get("computed", {}), "reorder_quantity": _computed(quantity)},
                "analysis_status": "reorder_required" if required else "healthy", "messages": messages}
    finally:
        db.close()


def deterministic_supplier_coordinator(state: InventoryAnalysisState) -> InventoryAnalysisState:
    """Choose an active supplier from WS-7's source-of-truth catalog."""
    messages = list(state.get("messages", []))
    recommendation = state.get("reorder_recommendation", {}) or {}
    if not recommendation.get("reorder_required"):
        messages.append("Supplier Coordinator: no supplier selection is needed.")
        return {**state, "supplier_choice": None, "messages": messages}
    db = SessionLocal()
    try:
        choice = select_supplier(db, state.get("product_id"), int(recommendation["recommended_quantity"]))
        data = choice.to_dict()
        data["total_order_cost"] = round(choice.unit_price * int(recommendation["recommended_quantity"]), 2)
        messages.append(f"Supplier Coordinator: selected active supplier {choice.supplier_id} from catalog evidence.")
        return {**state, "supplier_choice": data, "supplier_quote": data, "messages": messages}
    finally:
        db.close()


def deterministic_inventory_auditor(state: InventoryAnalysisState) -> InventoryAnalysisState:
    """Produce a factual post-decision record; it never invents a narrative."""
    messages = list(state.get("messages", []))
    decision_status = state.get("decision_status", "executed")
    action = "raise_po" if (state.get("reorder_recommendation", {}) or {}).get("reorder_required") else "no_action"
    report = f"Decision {decision_status}; action={action}; execution={state.get('execution')}."
    messages.append("Inventory Auditor: recorded deterministic decision evidence.")
    return {**state, "audit_report": report, "analysis_status": project_analysis_status(decision_status, action), "messages": messages}
