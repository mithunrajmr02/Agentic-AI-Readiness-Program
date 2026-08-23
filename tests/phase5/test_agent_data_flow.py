"""Each agent must actually consume the previous agent's output.

Why this file exists
--------------------
Replacing `inventory_auditor`'s entire prompt with an unrelated string left all 33
Phase-5 tests passing. The existing tests assert on the *shape* of what each agent
returns -- that `demand_forecast` has the required keys, that `analysis_status`
advances -- and they feed the LLM a canned reply, so they hold whether or not the
agent ever told the model anything true about the product.

That gap matters more here than in an ordinary unit test. The claim Phase 5 makes
is that four agents form a pipeline: the forecaster reads the product, the reorder
agent reads the forecast, the coordinator reads the recommendation, the auditor
reads all three. If the prompts do not carry that data, the graph is four
independent LLM calls whose outputs happen to be written into one state dict --
the topology would still be correct and every existing assertion would still pass.

So these tests capture the prompt each agent actually sends and check the upstream
facts are in it. They fail if a prompt is replaced, if an input is dropped, or if
an agent is rewired to read the wrong state key.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.agents.multi_agent.state import initial_state

JSON_REPLY = '{"ok": true}'


def _run(agent_name, state, product_payload=None):
    """Invoke one agent with the LLM and API stubbed; return (result, prompt)."""
    with patch("src.agents.multi_agent.agents.requests.get") as mg, \
         patch("src.agents.multi_agent.agents._llm") as ml:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = product_payload or {}
        ml.invoke.return_value = MagicMock(content=JSON_REPLY)

        import src.agents.multi_agent.agents as agents_mod
        result = getattr(agents_mod, agent_name)(state)

        assert ml.invoke.called, f"{agent_name} never called the LLM"
        (messages,), _ = ml.invoke.call_args
        return result, messages[0].content


def test_demand_forecaster_prompt_carries_the_fetched_product(sample_product_data):
    """The forecaster must forecast *this* product, not an empty record."""
    _, prompt = _run("demand_forecaster", initial_state(1),
                     product_payload=sample_product_data)

    assert "SKU-GRO-0001" in prompt
    # The stock figure is what makes a forecast possible at all.
    assert "12" in prompt
    assert "reorder_point" in prompt or "20" in prompt


def test_reorder_agent_prompt_carries_the_forecast(state_after_forecast):
    """The reorder decision must be made against the forecaster's output.

    Without this, the reorder agent would be guessing from the product record
    alone and the forecaster's contribution to the pipeline would be decorative.
    """
    _, prompt = _run("reorder_agent", state_after_forecast)

    forecast = state_after_forecast["demand_forecast"]
    assert "SKU-GRO-0001" in prompt
    assert str(forecast["stockout_risk"]) in prompt          # "high"
    assert str(forecast["days_of_stock_remaining"]) in prompt  # 3
    assert str(forecast["avg_daily_demand"]) in prompt         # 4.0


def test_supplier_coordinator_prompt_carries_the_reorder_recommendation(
        state_after_reorder, sample_product_data):
    """The quote must be for the quantity the reorder agent actually recommended."""
    _, prompt = _run("supplier_coordinator", state_after_reorder,
                     product_payload=sample_product_data)

    recommendation = state_after_reorder["reorder_recommendation"]
    assert str(recommendation["recommended_quantity"]) in prompt   # 100
    assert str(recommendation["urgency"]) in prompt                # within_3_days


def test_inventory_auditor_prompt_carries_all_three_upstream_outputs(
        state_after_reorder):
    """The audit report must be grounded in the forecast, reorder and quote.

    This is the assertion whose absence let a full prompt replacement survive.
    """
    state = {
        **state_after_reorder,
        "supplier_quote": {
            "supplier_id": 7,
            "supplier_code": "SUP-0042",
            "supplier_name": "Northbridge Trading",
            "unit_cost": 280.0,
            "total_order_cost": 28000.0,
            "estimated_lead_time_days": 6,
        },
    }
    _, prompt = _run("inventory_auditor", state)

    # Product identity
    assert "SKU-GRO-0001" in prompt
    # Forecast
    assert "high" in prompt                 # stockout_risk
    # Reorder decision, rendered as a word rather than a boolean
    assert "REQUIRED" in prompt
    assert "within_3_days" in prompt
    # Supplier quote, by code and by cost
    assert "SUP-0042" in prompt
    assert "28000" in prompt
    assert "6-day lead time" in prompt


def test_inventory_auditor_is_told_not_to_recommend_an_order_with_no_supplier(
        state_after_reorder):
    """A missing supplier must reach the model as an instruction, not a blank.

    Given only "Supplier quote: INR 0 for 60 units", the model wrote "Please
    proceed with the supplier order ... currently quoted at Rs 0" for a product
    with no supplier on file -- telling the operator to place an order the
    coordinator had just reported was impossible. The prompt now states the
    situation explicitly. If that text is ever dropped, the model has nothing to
    distinguish "no supplier" from "free", and this test fails.
    """
    state = {**state_after_reorder, "supplier_quote": {"total_order_cost": 0.0}}
    _, prompt = _run("inventory_auditor", state)

    assert "NONE" in prompt
    assert "no purchase order can be raised" in prompt
    # And it must not present zero as a price.
    assert "₹0" not in prompt


def test_auditor_prompt_omits_no_upstream_stage(state_after_reorder):
    """Every upstream stage is represented; none is silently skipped."""
    state = {
        **state_after_reorder,
        "supplier_quote": {"supplier_id": 3, "supplier_code": "SUP-0003",
                           "supplier_name": "Metro", "total_order_cost": 9000.0,
                           "estimated_lead_time_days": 10},
    }
    _, prompt = _run("inventory_auditor", state)

    for label in ("Product:", "Stock:", "Forecast:", "Reorder:", "Supplier quote:"):
        assert label in prompt, f"auditor prompt has no {label!r} section"
