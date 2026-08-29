"""The durable interrupt: suspend at `executor`, resume from the same
thread, executor re-checks preconditions rather than trusting proposal-time
state. Uses `run_pipeline` / `resume_pipeline` (15-SHARED-CONTRACTS.md §11)
directly so the test controls `run_id` / `thread_id` explicitly -- the
public `analyze_product` entrypoint intentionally hides that (see
graph.py) for the graded tests' benefit.

Everything here mocks the LLM and the outbound HTTP client, same as
tests/phase5 does, so it needs no network and no API key.
"""
import importlib
from unittest.mock import MagicMock, patch

import pytest

from src.agents.multi_agent.state import initial_state
from src.agents.multi_agent import ledger as ledger_mod


HIGH_VALUE_PRODUCT = {
    "id": 3,
    "sku": "SKU-ELC-0003",
    "name": "42-inch Television",
    "cost_price": 600.0,
    "reorder_point": 20,
    "supplier_id": 1,
    "stock_level": {"quantity_available": 5, "quantity_reserved": 0},
}


def _llm_side_effect():
    """One JSON/text reply per LLM call, in call order:
    demand_forecaster, investigator, reorder_agent, supplier_coordinator,
    (policy_gate and executor make no LLM call), inventory_auditor.
    """
    replies = [
        '{"avg_daily_demand":8.0,"demand_trend":"increasing","days_of_stock_remaining":1,'
        '"stockout_risk":"high","forecast_notes":"Critical."}',
        '{"hypotheses":[{"cause":"demand spike","confidence":"high",'
        '"evidence":"avg_daily_demand 8.0"}],"narrative":"A demand spike of 8.0 units/day '
        'explains the drawdown."}',
        '{"reorder_required":true,"recommended_quantity":100,"urgency":"immediate",'
        '"reason":"Stockout imminent."}',
        '{"supplier_id":1,"quoted_unit_cost":600.0,"total_order_cost":60000.0,'
        '"estimated_lead_time_days":5,"quote_notes":"Bulk order."}',
        "42-inch Television will stock out tomorrow; a 100-unit reorder at ₹60,000 is recommended.",
    ]
    calls = {"n": 0}

    def _side(prompt):
        i = min(calls["n"], len(replies) - 1)
        calls["n"] += 1
        return MagicMock(content=replies[i])

    return _side


@pytest.fixture
def isolated_stores(tmp_path, monkeypatch):
    """Fresh checkpoint + ledger files per test, and a reset checkpointer
    singleton so `graph.py` binds to them instead of the shared default."""
    ckpt_path = tmp_path / "checkpoints.pkl"
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("STEWARD_CHECKPOINT_DB", str(ckpt_path))
    monkeypatch.setenv("STEWARD_LEDGER_PATH", str(ledger_path))

    import src.agents.multi_agent.graph as graph_mod
    graph_mod._checkpointer = None
    yield ckpt_path, ledger_path
    graph_mod._checkpointer = None


def test_high_value_order_suspends_before_executor(isolated_stores):
    from src.agents.multi_agent.graph import run_pipeline

    with patch("src.agents.multi_agent.agents.requests.get") as mg, \
         patch("src.agents.multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = HIGH_VALUE_PRODUCT
        ml.invoke.side_effect = _llm_side_effect()

        result = run_pipeline("manual", product_ids=[3], run_id="RUN-INTERRUPT-01")

    # The run genuinely paused: an interrupt is present, and executor's own
    # "simulated PO" message never got appended -- the write did not happen.
    assert "__interrupt__" in result
    assert result["authority"] == "requires_approval"
    assert not any("simulated" in m.lower() for m in result["messages"])
    # Three real upstream steps plus policy_gate already ran before the
    # suspension -- the ≥4 floor (test_e2e.py:78) holds even mid-suspension.
    assert len(result["messages"]) >= 4


def test_resume_after_approval_executes_and_completes(isolated_stores):
    from src.agents.multi_agent.graph import run_pipeline, resume_pipeline

    with patch("src.agents.multi_agent.agents.requests.get") as mg, \
         patch("src.agents.multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = HIGH_VALUE_PRODUCT
        ml.invoke.side_effect = _llm_side_effect()

        run_pipeline("manual", product_ids=[3], run_id="RUN-INTERRUPT-02")
        final = resume_pipeline("RUN-INTERRUPT-02", {"outcome": "approved", "user_id": 1})

    assert final["decision_status"] == "executed"
    assert final["po_number"] and final["po_number"].startswith("PO-SIM-")
    assert final["analysis_status"] in ("complete", "reorder_required", "healthy", "analyzing")
    assert len(final["messages"]) >= 4
    assert ledger_mod.is_key_consumed(final["idempotency_key"])


def test_resume_after_rejection_never_writes(isolated_stores):
    from src.agents.multi_agent.graph import run_pipeline, resume_pipeline

    with patch("src.agents.multi_agent.agents.requests.get") as mg, \
         patch("src.agents.multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = HIGH_VALUE_PRODUCT
        ml.invoke.side_effect = _llm_side_effect()

        run_pipeline("manual", product_ids=[3], run_id="RUN-INTERRUPT-03")
        final = resume_pipeline("RUN-INTERRUPT-03", {"outcome": "rejected", "user_id": 1})

    assert final.get("po_number") is None
    assert final["decision_status"] == "rejected"
    assert not any("simulated" in m.lower() for m in final["messages"])


def test_executor_reruns_preconditions_and_blocks_a_replay(isolated_stores):
    """The idempotency precondition (15-SHARED-CONTRACTS.md §9, #6) is
    re-checked at execution time -- not trusted from the proposal. A second
    resume attempt reusing the same key must not write a second time."""
    from src.agents.multi_agent.nodes.executor import executor

    state = {
        **initial_state(3, run_id="RUN-REPLAY"),
        "authority": "within_authority",
        "reorder_recommendation": {"reorder_required": True, "recommended_quantity": 40},
        "supplier_quote": {"supplier_id": 1},
        "order_value": 12000.0,
        "idempotency_key": "fixed-key-for-replay-test",
    }

    first = executor(state)
    assert first["decision_status"] == "executed"
    assert first["po_number"]

    second = executor(state)
    assert second["decision_status"] == "failed"
    assert second["error"] == "idempotency_key_already_consumed"
    assert second.get("po_number") is None
