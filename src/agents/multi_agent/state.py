import uuid
from typing import TypedDict, List, Dict, Any, Optional


class InventoryAnalysisState(TypedDict, total=False):
    # ---- original 4-node fields (WS-8 preserves these verbatim: graded
    # tests in tests/phase5/test_state.py, test_agents.py and
    # test_agent_data_flow.py assert on them by name and by value) ----
    product_id: int
    product_data: Dict[str, Any]           # Product + stock details
    demand_forecast: Dict[str, Any]        # Demand Forecaster output
    reorder_recommendation: Dict[str, Any] # Reorder Agent output
    supplier_quote: Dict[str, Any]         # Supplier Coordinator output
    audit_report: str                      # Inventory Auditor final report
    analysis_status: str                   # "analyzing" | "reorder_required" | "healthy" | "complete" | "error"
    errors: List[str]
    messages: List[str]

    # ---- AD-7 extension: the 8-node governed pipeline (new nodes:
    # investigator, policy_gate, executor, recorder). Keys mirror
    # docs/implementation/15-SHARED-CONTRACTS.md §11's InventoryState,
    # narrowed to what this worktree can actually populate -- see
    # docs/implementation/integration-requests/WS-8.md for the gaps ----
    trigger: str                    # "scheduled" | "event" | "manual" | "backtest"
    run_id: str                     # RUN-xxxxxxxx
    signal_id: Optional[str]

    data_sufficiency: str            # "sufficient" | "thin" | "insufficient" | "none" | "unknown"
    hypotheses: List[Any]            # investigator output, ranked
    narrative: Optional[str]         # investigator output; None on failure/violation

    authority: str                   # "within_authority" | "requires_approval" | "forbidden" | "unknown"
    policy_limit: Optional[float]
    policy_citation: Optional[str]
    policy_section: Optional[str]
    order_value: Optional[float]

    idempotency_key: Optional[str]
    po_number: Optional[str]
    decision_status: str             # the internal lifecycle; analysis_status stays the graded projection

    actor: str


def initial_state(product_id: int, *, trigger: str = "manual", run_id: Optional[str] = None) -> InventoryAnalysisState:
    """Factory returning fresh, unmutated state initialized with defaults."""
    return InventoryAnalysisState(
        product_id=product_id,
        product_data={},
        demand_forecast={},
        reorder_recommendation={},
        supplier_quote={},
        audit_report="",
        analysis_status="analyzing",
        errors=[],
        messages=[],
        trigger=trigger,
        run_id=run_id or f"RUN-{uuid.uuid4().hex[:8]}",
        signal_id=None,
        data_sufficiency="unknown",
        hypotheses=[],
        narrative=None,
        authority="unknown",
        policy_limit=None,
        policy_citation=None,
        policy_section=None,
        order_value=None,
        idempotency_key=None,
        po_number=None,
        decision_status="analysing",
        actor="agent:steward",
    )
