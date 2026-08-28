"""policy_gate -- new node (AD-7), deterministic governance verdict.

Local stand-in for WS-5's `evaluate(db, DecisionContext) -> PolicyVerdict`
(15-SHARED-CONTRACTS.md §7), which does not exist in this worktree --
there is no `src/policy/` module to consume. Only the two rules this
stream can source honestly are implemented: the manual's own approval
threshold (§10 line 113, "above ₹50,000") and data-sufficiency escalation
(08-AGENTIC-WORKFLOWS.md §5.5, rule 4 — low confidence escalates
regardless of value). Kill switch, blast-radius caps, autonomy mode and
non-cheapest-supplier escalation all need tables/modules this stream does
not own (`autonomy_policies`, WS-3's signals, WS-7's `SupplierChoice`) --
see docs/implementation/integration-requests/WS-8.md.

Fail-safe holds regardless of what is missing: anything this node cannot
evaluate escalates. It never silently approves an order it did not check.
"""
from typing import List

from src.agents.multi_agent.state import InventoryAnalysisState

POLICY_LIMIT_INR = 50_000.0
POLICY_CITATION = "Purchase orders above \u20b950,000 require manager approval before submission."
POLICY_SECTION = "manual \u00a710 line 113 (PO Approval Threshold)"


def policy_gate(state: InventoryAnalysisState) -> InventoryAnalysisState:
    """Agent 6: allow, escalate, or refuse -- mechanically, not by prompt."""
    messages: List[str] = list(state.get("messages", []))
    errors: List[str] = list(state.get("errors", []))

    reco = state.get("reorder_recommendation", {}) or {}
    quote = state.get("supplier_quote", {}) or {}
    try:
        order_value = float(quote.get("total_order_cost") or 0.0)
    except (TypeError, ValueError):
        order_value = 0.0

    if not reco.get("reorder_required"):
        authority = "within_authority"
        reason = "No reorder recommended; nothing to authorise."
    elif state.get("data_sufficiency") in ("insufficient", "none"):
        authority = "requires_approval"
        reason = "Data sufficiency too low to authorise automatically (rule 4)."
    elif order_value > POLICY_LIMIT_INR:
        authority = "requires_approval"
        reason = f"Order value \u20b9{order_value:,.0f} exceeds the \u20b950,000 threshold (rule 8)."
    else:
        authority = "within_authority"
        reason = f"Order value \u20b9{order_value:,.0f} is within the \u20b950,000 threshold."

    messages.append(f"Policy Gate: authority={authority} ({reason})")

    return {
        **state,
        "authority": authority,
        "policy_limit": POLICY_LIMIT_INR,
        "policy_citation": POLICY_CITATION,
        "policy_section": POLICY_SECTION,
        "order_value": order_value,
        "messages": messages,
        "errors": errors,
    }
