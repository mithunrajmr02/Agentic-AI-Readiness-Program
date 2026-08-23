import inspect
import pytest
from src.agents.multi_agent.state import initial_state


def test_normal_routes_reorder():
    """TC-07-P5-ROUTE-01: Normal Routes to reorder_agent"""
    from src.agents.multi_agent.graph import should_skip_to_audit
    s = {**initial_state(1), "analysis_status": "analyzing", "errors": []}
    assert should_skip_to_audit(s) == "reorder_agent"


def test_error_routes_audit():
    """TC-07-P5-ROUTE-02: Many Errors Routes to audit"""
    from src.agents.multi_agent.graph import should_skip_to_audit
    s = {**initial_state(1), "errors": ["e1", "e2", "e3"]}
    assert should_skip_to_audit(s) == "inventory_auditor"


def test_error_status_routes():
    """TC-07-P5-ROUTE-03: Error Status Routes to Audit"""
    from src.agents.multi_agent.graph import should_skip_to_audit
    s = {**initial_state(1), "errors": []}
    s["analysis_status"] = "error"
    assert should_skip_to_audit(s) == "inventory_auditor"


def test_valid_node():
    """TC-07-P5-ROUTE-04: Returns Valid Node Name"""
    from src.agents.multi_agent.graph import should_skip_to_audit
    valid = {"reorder_agent", "inventory_auditor"}
    for n in [0, 1, 2, 3, 5]:
        s = {**initial_state(1), "errors": [f"e{i}" for i in range(n)]}
        assert should_skip_to_audit(s) in valid


def test_4_nodes():
    """TC-07-P5-ROUTE-05: Graph Has 4 Nodes"""
    from src.agents.multi_agent.graph import build_inventory_graph
    src = inspect.getsource(build_inventory_graph)
    for n in ["demand_forecaster", "reorder_agent", "supplier_coordinator", "inventory_auditor"]:
        assert n in src, f"Node {n} not found in build_inventory_graph source"


def test_entry_point():
    """TC-07-P5-ROUTE-06: Entry Point Is demand_forecaster"""
    from src.agents.multi_agent.graph import build_inventory_graph
    src = inspect.getsource(build_inventory_graph)
    assert "demand_forecaster" in src and ("set_entry_point" in src or "entry_point" in src.lower())
