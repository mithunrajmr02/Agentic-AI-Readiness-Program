import structlog
from langgraph.graph import StateGraph, END
from langsmith import traceable

from src.agents.multi_agent.state import InventoryAnalysisState, initial_state
from src.agents.multi_agent.agents import (
    demand_forecaster,
    reorder_agent,
    supplier_coordinator,
    inventory_auditor,
    tracer,
)

logger = structlog.get_logger()

def _safe_log(event: str, **kwargs):
    try:
        logger.info(event, **kwargs)
    except Exception:
        pass


def should_skip_to_audit(state: InventoryAnalysisState) -> str:
    """Supervisor routing condition: skip intermediate steps to audit on error or failure threshold."""
    with tracer.start_as_current_span("supervisor.route") as span:
        errors = state.get("errors", [])
        status = state.get("analysis_status")
        span.set_attribute("poc_id", "POC-07")
        span.set_attribute("supervisor.from_agent", "demand_forecaster")
        span.set_attribute("supervisor.error_count", len(errors))
        span.set_attribute("supervisor.status", str(status))

        if len(errors) >= 3 or status == "error":
            reason = f"Short-circuit to auditor: errors={len(errors)}, status={status}"
            span.set_attribute("supervisor.to_agent", "inventory_auditor")
            span.set_attribute("supervisor.routing_reason", reason)
            _safe_log("supervisor_routed", poc_id="POC-07", phase="P5", target="inventory_auditor", reason=reason)
            return "inventory_auditor"

        reason = "Normal flow to reorder_agent"
        span.set_attribute("supervisor.to_agent", "reorder_agent")
        span.set_attribute("supervisor.routing_reason", reason)
        _safe_log("supervisor_routed", poc_id="POC-07", phase="P5", target="reorder_agent", reason=reason)
        return "reorder_agent"


def build_inventory_graph():
    """Constructs and compiles the multi-agent StateGraph for inventory auditing and procurement."""
    graph = StateGraph(InventoryAnalysisState)
    
    # 1. Register 4 specialized agent nodes
    graph.add_node("demand_forecaster", demand_forecaster)
    graph.add_node("reorder_agent", reorder_agent)
    graph.add_node("supplier_coordinator", supplier_coordinator)
    graph.add_node("inventory_auditor", inventory_auditor)
    
    # 2. Define entry point
    graph.set_entry_point("demand_forecaster")
    
    # 3. Add conditional routing edge after demand_forecaster
    graph.add_conditional_edges(
        "demand_forecaster",
        should_skip_to_audit,
        {
            "reorder_agent": "reorder_agent",
            "inventory_auditor": "inventory_auditor",
        }
    )
    
    # 4. Add serial pipeline edges
    graph.add_edge("reorder_agent", "supplier_coordinator")
    graph.add_edge("supplier_coordinator", "inventory_auditor")
    graph.add_edge("inventory_auditor", END)
    
    return graph.compile()


@traceable(project_name="AI-Readiness-POC-07-P5")
def analyze_product(product_id: int) -> InventoryAnalysisState:
    """Public programmatic entrypoint to execute the full multi-agent inventory analysis graph."""
    with tracer.start_as_current_span("graph.execute") as span:
        span.set_attribute("poc_id", "POC-07")
        span.set_attribute("graph.input_node", "demand_forecaster")
        span.set_attribute("graph.product_id", str(product_id))

        app = build_inventory_graph()
        init = initial_state(product_id)
        
        _safe_log("graph_execution_started", poc_id="POC-07", phase="P5", product_id=product_id)
        final_state = app.invoke(init)
        
        span.set_attribute("graph.final_status", final_state.get("analysis_status", "unknown"))
        span.set_attribute("graph.messages_count", len(final_state.get("messages", [])))
        span.set_attribute("graph.errors_count", len(final_state.get("errors", [])))
        
        _safe_log(
            "graph_execution_completed",
            poc_id="POC-07",
            phase="P5",
            product_id=product_id,
            status=final_state.get("analysis_status"),
            audit_report_len=len(final_state.get("audit_report", "")),
        )
        return final_state
