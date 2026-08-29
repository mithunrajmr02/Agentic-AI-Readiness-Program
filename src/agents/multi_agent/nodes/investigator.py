"""investigator -- new node (AD-7), the second of the two LLM touchpoints.

Per 08-AGENTIC-WORKFLOWS.md §5.2: ranks plausible causes for the observed
demand/stock picture from a fixed evidence packet, and is the one node
where a numeric-token validator runs -- the direct, structural response to
the hallucination class preserved verbatim at
`src/agents/multi_agent/agents.py:389-406` (WS-8's preservation
requirement): the model inventing `supplier_id: 101` and a fabricated
₹580.00 price against a real ₹600.00, in 3 of 3 runs. A narrative here can
describe the numbers it is given; it may not introduce new ones.

Also derives `data_sufficiency` for `policy_gate`'s rule 4 (data quality
escalates regardless of value) -- from `demand_forecast`, since the real
`compute_daily_demand`/`score_sufficiency` (WS-1, 15-SHARED-CONTRACTS.md
§5) do not exist in this worktree yet. See
docs/implementation/integration-requests/WS-8.md.

Deliberately calls through `agents_mod._invoke_llm` / `agents_mod._safe_json`
rather than importing `_llm` by name: the Phase-5 test suite patches
`src.agents.multi_agent.agents._llm`, and only a call that resolves that
name from the module's own globals at call time observes the patch.
"""
import json
import re
from typing import Any, Dict, List

from src.agents.multi_agent import agents as agents_mod
from src.agents.multi_agent.state import InventoryAnalysisState

_NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")


def _numbers_in(text: str) -> set:
    if not text:
        return set()
    return {tok.replace(",", "") for tok in _NUMBER_RE.findall(text)}


def _evidence_packet(state: InventoryAnalysisState) -> Dict[str, Any]:
    """The only facts `investigator` may reason over. No raw DB access
    (08-AGENTIC-WORKFLOWS.md §5.2) -- everything here already passed
    through `demand_forecaster`."""
    forecast = state.get("demand_forecast", {}) or {}
    product = state.get("product_data", {}) or {}
    stock = product.get("stock_level", {}) if isinstance(product.get("stock_level"), dict) else {}
    return {
        "sku": product.get("sku"),
        "avg_daily_demand": forecast.get("avg_daily_demand"),
        "days_of_stock_remaining": forecast.get("days_of_stock_remaining"),
        "stockout_risk": forecast.get("stockout_risk"),
        "quantity_available": stock.get("quantity_available"),
        "reorder_point": product.get("reorder_point"),
    }


def _sufficiency_from_forecast(forecast: Dict[str, Any]) -> str:
    """A local proxy for WS-1's `score_sufficiency` (15-SHARED-CONTRACTS.md
    §5.4's thresholds need sale-event history this worktree has no access
    to from here). Never returns a numeric value for "no data" -- only ever
    a verdict -- consistent with §5.1's `value is None` rule even though no
    `Computed.value` is produced by this stand-in at all."""
    risk = forecast.get("stockout_risk", "unknown")
    demand = forecast.get("avg_daily_demand")
    try:
        demand = float(demand)
    except (TypeError, ValueError):
        demand = None
    if risk in ("unknown", None) and not demand:
        return "none"
    if demand and demand > 0:
        return "sufficient"
    return "thin"


def investigator(state: InventoryAnalysisState) -> InventoryAnalysisState:
    """Agent 5: rank causal hypotheses; narrate only what the evidence supports.

    Skipped, cheaply, when the forecast itself carries no signal -- there is
    nothing to investigate and no reason to spend a model call on it
    (08-AGENTIC-WORKFLOWS.md §7.1, rate-limit mitigation #2).
    """
    messages: List[str] = list(state.get("messages", []))
    errors: List[str] = list(state.get("errors", []))
    forecast = state.get("demand_forecast", {}) or {}
    sufficiency = _sufficiency_from_forecast(forecast)

    if sufficiency in ("insufficient", "none"):
        messages.append(
            f"Investigator: skipped — data sufficiency '{sufficiency}' is too low to investigate."
        )
        return {
            **state,
            "data_sufficiency": sufficiency,
            "narrative": None,
            "hypotheses": [],
            "messages": messages,
            "errors": errors,
        }

    packet = _evidence_packet(state)
    permitted_numbers = set()
    for value in packet.values():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            permitted_numbers.add(str(value))
            if float(value).is_integer():
                permitted_numbers.add(str(int(value)))

    prompt = f"""Rank plausible causes for this product's stock/demand situation.
Use ONLY the numbers given below. Do not invent a number, id or price that is
not present here. Respond with JSON only.

Evidence: {json.dumps(packet)}

JSON response:
{{
  "hypotheses": [{{"cause": "<short label>", "confidence": "high|medium|low", "evidence": "<one sentence citing only the numbers above>"}}],
  "narrative": "<2-3 sentence plain-language summary>"
}}"""

    hypotheses: List[Any] = []
    narrative = None
    try:
        resp = agents_mod._invoke_llm(prompt)
        parsed = agents_mod._safe_json(getattr(resp, "content", resp))
        hypotheses = parsed.get("hypotheses", []) if isinstance(parsed, dict) else []
        candidate = parsed.get("narrative") if isinstance(parsed, dict) else None

        if candidate:
            # Numeric-token validator (08-AGENTIC-WORKFLOWS.md §8.2): a
            # number in the narrative absent from the evidence packet is
            # exactly the failure class at agents.py:389-406, so the
            # narrative is dropped and the violation recorded rather than
            # passed downstream.
            unknown = _numbers_in(candidate) - permitted_numbers
            if unknown:
                errors.append(f"llm_numeric_violation: {sorted(unknown)}")
            else:
                narrative = candidate
    except Exception as e:
        errors.append(f"Investigator LLM error: {str(e)}")

    messages.append(
        f"Investigator: {len(hypotheses)} hypothesis(es) ranked; "
        f"narrative={'present' if narrative else 'unavailable'}."
    )

    return {
        **state,
        "data_sufficiency": sufficiency,
        "hypotheses": hypotheses,
        "narrative": narrative,
        "messages": messages,
        "errors": errors,
    }
