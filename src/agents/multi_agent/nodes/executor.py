"""executor -- new node (AD-7), the interrupt target, the only "write".

The real write path -- `inventory_service.execute_decision` /
`check_preconditions` (15-SHARED-CONTRACTS.md §9) -- is WS-9's sole domain
and does not exist in this worktree. WS-8 must not invent a second write
path into `inventory_service.py` or `models.py` (frozen, not owned here),
so this node *simulates* execution to the local ledger (`ledger.py`)
instead of touching the database, and records exactly that it did so.

What IS re-checked here, at execution time rather than trusted from
`policy_gate`'s proposal time (08-AGENTIC-WORKFLOWS.md §5.6 -- a durable
interrupt means arbitrary time passes between proposal and approval):

  * precondition 6 -- idempotency key not already consumed (ledger-backed)
  * a supplier is on file for a reorder that needs one

Preconditions 1-4 and 7 (kill switch, autonomy mode, in-flight PO, supplier
`active` re-read) need modules this stream does not own (`autonomy_policies`,
`src/execution/preconditions.py`, WS-7's supplier register) and are named
gaps, not assumed clear -- see
docs/implementation/integration-requests/WS-8.md.

Uses LangGraph's *dynamic* `interrupt()` rather than a static
`interrupt_before=["executor"]`: only the paths where `authority ==
"requires_approval"` actually need to suspend, and a static interrupt would
pause every path through this node, including ones policy already cleared.
"""
from typing import List

from langgraph.types import interrupt

from src.agents.multi_agent.state import InventoryAnalysisState
from src.agents.multi_agent import ledger as ledger_mod


def _unmet_preconditions(state: InventoryAnalysisState, idempotency_key: str) -> List[str]:
    failed: List[str] = []
    reco = state.get("reorder_recommendation", {}) or {}
    quote = state.get("supplier_quote", {}) or {}
    if reco.get("reorder_required") and not quote.get("supplier_id"):
        failed.append("no_supplier_on_file")
    if ledger_mod.is_key_consumed(idempotency_key):
        failed.append("idempotency_key_already_consumed")
    return failed


def executor(state: InventoryAnalysisState) -> InventoryAnalysisState:
    """Agent 7: suspend for approval when required; otherwise write (simulated)."""
    messages: List[str] = list(state.get("messages", []))
    errors: List[str] = list(state.get("errors", []))
    authority = state.get("authority")

    approval_outcome = None
    if authority == "requires_approval":
        # First pass: raises inside the pregel loop, the run is checkpointed
        # and `.invoke()` returns to the caller with the state as of just
        # before this call. On resume (`resume_pipeline`, same thread_id),
        # this function re-runs from the top and `interrupt()` returns the
        # value passed to `Command(resume=...)` instead of pausing again.
        approval_outcome = interrupt({
            "reason": "requires_approval",
            "policy_citation": state.get("policy_citation"),
            "order_value": state.get("order_value"),
            "product_id": state.get("product_id"),
            "run_id": state.get("run_id"),
        })
        if not approval_outcome or approval_outcome.get("outcome") != "approved":
            messages.append("Executor: not executed — approval was not granted.")
            return {
                **state,
                "decision_status": "rejected",
                "messages": messages,
                "errors": errors,
            }
        messages.append(f"Executor: resumed after approval by {approval_outcome.get('user_id')}.")

    reco = state.get("reorder_recommendation", {}) or {}
    if not reco.get("reorder_required"):
        messages.append("Executor: no action required.")
        return {**state, "decision_status": "executed", "messages": messages, "errors": errors}

    idempotency_key = state.get("idempotency_key") or (
        f"{state.get('product_id')}:{state.get('run_id')}:"
        f"{reco.get('recommended_quantity')}:{(state.get('supplier_quote') or {}).get('supplier_id')}"
    )

    unmet = _unmet_preconditions(state, idempotency_key)
    if unmet:
        messages.append(f"Executor: preconditions failed — {', '.join(unmet)}.")
        return {
            **state,
            "decision_status": "failed",
            "error": unmet[0],
            "idempotency_key": idempotency_key,
            "messages": messages,
            "errors": errors,
        }

    quote = state.get("supplier_quote", {}) or {}
    po_number = ledger_mod.consume_and_record(
        idempotency_key,
        product_id=state.get("product_id"),
        quantity=reco.get("recommended_quantity"),
        supplier_id=quote.get("supplier_id"),
        total_cost=state.get("order_value"),
    )
    messages.append(
        f"Executor: simulated {po_number} recorded — no live write path is owned by this stream."
    )

    return {
        **state,
        "decision_status": "executed",
        "idempotency_key": idempotency_key,
        "po_number": po_number,
        "messages": messages,
        "errors": errors,
    }
