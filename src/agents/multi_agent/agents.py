import os
import re
import json
import requests
import structlog
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
try:
    from langchain_core.messages import HumanMessage
except ImportError:  # pragma: no cover
    from langchain.schema import HumanMessage
from langsmith import traceable

from src.agents.multi_agent.state import InventoryAnalysisState

# OpenTelemetry configuration
try:
    from opentelemetry import trace
    tracer = trace.get_tracer("poc-07-multi-agent")
except Exception:  # pragma: no cover
    class DummySpan:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def set_attribute(self, key, value):
            pass

    class DummyTracer:
        def start_as_current_span(self, name):
            return DummySpan()

    tracer = DummyTracer()

from dotenv import load_dotenv
load_dotenv()

logger = structlog.get_logger()
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
# This module already had the correct fallback; it now shares it with the other
# four call sites rather than restating it. See src/model_config.py.
from src.model_config import api_key as _resolve_api_key, chat_model as _resolve_chat_model

_api_key = _resolve_api_key()
_model_name = _resolve_chat_model()
_llm = ChatGoogleGenerativeAI(model=_model_name, google_api_key=_api_key, temperature=0.2)


def _authed_get(url: str):
    """GET the Phase 1 API as the service account, retrying once on a 401.

    All three of this module's API reads previously went out with no credentials,
    which the backend accepted by treating anonymous callers as the admin user.
    That bypass is gone, so the LangGraph agents now authenticate; without this
    every agent would fetch nothing and the pipeline would narrate an analysis of
    an empty product record. Returns the response object so callers keep their
    existing `status_code` / `raise_for_status` / `json()` handling.
    """
    from src import service_auth

    response = requests.get(url, headers=service_auth.auth_headers(), timeout=10)
    if getattr(response, "status_code", None) == 401:
        service_auth.invalidate()
        response = requests.get(
            url, headers=service_auth.auth_headers(force_refresh=True), timeout=10
        )
    return response


def _extract_text(res_or_content: Any) -> str:
    """Extract clean string text from strings, lists, dicts, and LangChain Message objects."""
    if res_or_content is None:
        return ""
    if isinstance(res_or_content, str):
        return res_or_content
    if hasattr(res_or_content, "content"):
        return _extract_text(res_or_content.content)
    if isinstance(res_or_content, list):
        parts = []
        for item in res_or_content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            elif hasattr(item, "text"):
                parts.append(str(item.text))
        return "".join(parts)
    if isinstance(res_or_content, dict) and "text" in res_or_content:
        return str(res_or_content["text"])
    return str(res_or_content)


def _safe_json(text: Any) -> dict:
    """Robust JSON extraction from LLM response text, handling markdown fences and surrounding commentary."""
    if not text:
        return {}
    
    extracted = _extract_text(text)
    if not extracted:
        return {}
    
    cleaned = extracted.strip()
    # Strip markdown code fences if present
    if "```json" in cleaned:
        cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.MULTILINE)
    if "```" in cleaned:
        cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start >= 0 and end > start:
        candidate = cleaned[start:end]
        try:
            val = json.loads(candidate)
            if isinstance(val, dict):
                return val
        except Exception:
            pass

    try:
        val = json.loads(cleaned)
        if isinstance(val, dict):
            return val
    except Exception:
        pass
    return {}


def _as_float(value: Any, default: float = 0.0) -> float:
    """Coerce an LLM-supplied or API-supplied number, falling back on nonsense."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _fetch_supplier(supplier_id: Any, errors: List[str]) -> Dict[str, Any]:
    """Look up the real supplier record so a quote's identity and lead time are facts.

    There is no `GET /suppliers/{id}` route, so this filters the collection.

    Tolerates a non-list payload on purpose: the Phase-5 tests patch
    `requests.get` with one MagicMock whose `.json()` returns a *product* dict
    for every URL, so this must degrade to "unknown supplier" rather than raise.
    """
    if not supplier_id:
        return {}
    try:
        r = _authed_get(f"{BASE_URL}/suppliers")
        if getattr(r, "status_code", None) != 200:
            errors.append(f"Supplier lookup failed: HTTP {getattr(r, 'status_code', 'unknown')}")
            return {}
        payload = r.json()
        if not isinstance(payload, list):
            return {}
        for s in payload:
            if isinstance(s, dict) and s.get("id") == supplier_id:
                return s
        errors.append(
            f"Product names supplier {supplier_id} but no such supplier exists in the register"
        )
        return {}
    except Exception as e:
        errors.append(f"Supplier lookup error: {str(e)}")
        return {}


def _invoke_llm(prompt_text: str):
    """Send one prompt to the chat model and return the raw response object.

    This used to begin with a mock probe:

        if hasattr(_llm, "return_value") and hasattr(_llm.return_value, "invoke"):
            res = _llm.return_value.invoke(...)

    `return_value` is a `unittest.mock` attribute, so that branch asked "am I
    running under a test?" -- production behaviour was conditioned on the test
    harness. It was also unreachable outside tests: `_llm` is a
    ChatGoogleGenerativeAI *instance* built once at module import (line 46) and
    is never called, so a real `_llm` has no `.return_value`.

    It existed to accommodate a mis-written patch. The Phase-5 tests set
    `ml.return_value.invoke.return_value`, which configures `_llm().invoke()` --
    a call path this module does not use -- rather than `ml.invoke.return_value`,
    which configures the call it actually makes. The tests were corrected instead;
    leaving the probe in place meant the exception-path tests would have kept
    passing even if `_llm.invoke` were never reached at all.
    """
    return _llm.invoke([HumanMessage(content=prompt_text)])



@traceable(project_name="AI-Readiness-POC-07-P5")
def demand_forecaster(state: InventoryAnalysisState) -> InventoryAnalysisState:
    """Agent 1: Fetch product data and forecast demand velocity and stockout risk."""
    with tracer.start_as_current_span("agent.demand_forecaster.activate") as span:
        product_id = state.get("product_id")
        span.set_attribute("poc_id", "POC-07")
        span.set_attribute("agent.name", "demand_forecaster")
        span.set_attribute("agent.product_id", str(product_id))

        errors: List[str] = list(state.get("errors", []))
        messages: List[str] = list(state.get("messages", []))
        product_data: Dict[str, Any] = {}

        try:
            r = _authed_get(f"{BASE_URL}/products/{product_id}")
            r.raise_for_status()
            product_data = r.json()
        except Exception as e:
            errors.append(f"Product fetch error: {str(e)}")

        prompt = f"""Analyze product inventory data and forecast demand. Respond with JSON only.
Product data: {json.dumps(product_data)}

JSON response:
{{
  "avg_daily_demand": <number or 0>,
  "demand_trend": "increasing|stable|decreasing|unknown",
  "days_of_stock_remaining": <number or 0>,
  "stockout_risk": "high|medium|low|none|unknown",
  "forecast_notes": "<one sentence>"
}}"""

        demand_forecast: Dict[str, Any] = {}
        try:
            resp = _invoke_llm(prompt)
            demand_forecast = _safe_json(resp.content) or {
                "avg_daily_demand": 0,
                "demand_trend": "unknown",
                "days_of_stock_remaining": 0,
                "stockout_risk": "unknown",
                "forecast_notes": "Insufficient data."
            }
        except Exception as e:
            errors.append(f"Demand LLM error: {str(e)}")
            demand_forecast = {
                "avg_daily_demand": 0,
                "demand_trend": "unknown",
                "days_of_stock_remaining": 0,
                "stockout_risk": "unknown",
                "forecast_notes": f"Error: {str(e)}"
            }

        risk = demand_forecast.get("stockout_risk", "unknown")
        trend = demand_forecast.get("demand_trend", "unknown")
        messages.append(f"Demand Forecaster: risk={risk}, trend={trend}")
        
        logger.info("agent_complete", poc_id="POC-07", phase="P5", agent="demand_forecaster", product_id=product_id)
        
        return {
            **state,
            "product_data": product_data,
            "demand_forecast": demand_forecast,
            "errors": errors,
            "messages": messages
        }


@traceable(project_name="AI-Readiness-POC-07-P5")
def reorder_agent(state: InventoryAnalysisState) -> InventoryAnalysisState:
    """Agent 2: Determine if reorder is needed and recommend replenishment quantity."""
    with tracer.start_as_current_span("agent.reorder_agent.activate") as span:
        span.set_attribute("poc_id", "POC-07")
        span.set_attribute("agent.name", "reorder_agent")

        errors: List[str] = list(state.get("errors", []))
        messages: List[str] = list(state.get("messages", []))

        prompt = f"""Determine if reorder is needed. Respond with JSON only.
Product: {json.dumps(state.get('product_data', {}))}
Demand forecast: {json.dumps(state.get('demand_forecast', {}))}

JSON response:
{{
  "reorder_required": <true|false>,
  "recommended_quantity": <number or 0>,
  "urgency": "immediate|within_3_days|within_week|not_required",
  "reason": "<explanation>"
}}"""

        reorder_recommendation: Dict[str, Any] = {}
        try:
            resp = _invoke_llm(prompt)
            reorder_recommendation = _safe_json(resp.content) or {
                "reorder_required": False,
                "recommended_quantity": 0,
                "urgency": "not_required",
                "reason": "Analysis unavailable."
            }
        except Exception as e:
            errors.append(f"Reorder LLM error: {str(e)}")
            reorder_recommendation = {
                "reorder_required": False,
                "recommended_quantity": 0,
                "urgency": "not_required",
                "reason": f"Error: {str(e)}"
            }

        is_reorder_req = bool(reorder_recommendation.get("reorder_required"))
        new_status = "reorder_required" if is_reorder_req else state.get("analysis_status", "analyzing")
        
        urgency = reorder_recommendation.get("urgency", "not_required")
        messages.append(f"Reorder Agent: required={is_reorder_req}, urgency={urgency}")
        
        logger.info("agent_complete", poc_id="POC-07", phase="P5", agent="reorder_agent", reorder_required=is_reorder_req)
        
        return {
            **state,
            "reorder_recommendation": reorder_recommendation,
            "analysis_status": new_status,
            "errors": errors,
            "messages": messages
        }


@traceable(project_name="AI-Readiness-POC-07-P5")
def supplier_coordinator(state: InventoryAnalysisState) -> InventoryAnalysisState:
    """Agent 3: Find best supplier catalog and generate procurement quote for recommended quantity."""
    with tracer.start_as_current_span("agent.supplier_coordinator.activate") as span:
        span.set_attribute("poc_id", "POC-07")
        span.set_attribute("agent.name", "supplier_coordinator")

        errors: List[str] = list(state.get("errors", []))
        messages: List[str] = list(state.get("messages", []))
        supplier_quote: Dict[str, Any] = {}

        # Fetch supplier catalog if supplier_id available
        product_data = state.get("product_data", {})
        supplier_id = product_data.get("supplier_id")
        catalog = []
        if supplier_id:
            try:
                r = _authed_get(f"{BASE_URL}/suppliers/{supplier_id}/catalog")
                if r.status_code == 200:
                    catalog = r.json()
            except Exception as e:
                errors.append(f"Supplier fetch error: {str(e)}")

        # The supplier register is the authority on who the vendor is and how
        # long they take. Neither is something to ask a language model for.
        supplier = _fetch_supplier(supplier_id, errors)

        recommended_qty = int(_as_float(
            state.get("reorder_recommendation", {}).get("recommended_quantity"), 0.0))
        unit_cost = _as_float(product_data.get("cost_price"), 0.0)
        sku = product_data.get("sku") or f"product {state.get('product_id')}"

        prompt = f"""Generate a supplier quote. Respond with JSON only.
Product: {json.dumps(product_data)}
Reorder recommendation: {json.dumps(state.get('reorder_recommendation', {}))}
Supplier catalog: {json.dumps(catalog[:5] if isinstance(catalog, list) else [])}
Supplier of record: {json.dumps(supplier) if supplier else "NONE -- no supplier is linked to this product"}

The identity, unit cost and lead time are taken from the inventory database and
will overwrite whatever you return, so do not invent them. Write `quote_notes`
as one or two sentences of procurement advice grounded only in the facts above,
and say so plainly if there is no supplier to order from.

JSON response:
{{
  "supplier_id": <number or null>,
  "quoted_unit_cost": <number or 0>,
  "total_order_cost": <number or 0>,
  "estimated_lead_time_days": <number or 7>,
  "quote_notes": "<recommendation>"
}}"""

        try:
            resp = _invoke_llm(prompt)
            supplier_quote = _safe_json(resp.content) or {
                "supplier_id": supplier_id,
                "quoted_unit_cost": 0,
                "total_order_cost": 0,
                "estimated_lead_time_days": 7,
                "quote_notes": "Quote unavailable."
            }
        except Exception as e:
            errors.append(f"Supplier LLM error: {str(e)}")
            supplier_quote = {
                "supplier_id": supplier_id,
                "quoted_unit_cost": 0,
                "total_order_cost": 0,
                "estimated_lead_time_days": 7,
                "quote_notes": f"Error: {str(e)}"
            }

        # --- Ground the quote in database facts -------------------------------
        # Only the narrative survives from the model; every hard fact is derived.
        #
        # This is not defensive tidying. Asked to quote a product with no
        # supplier on file, the model returned `supplier_id: 101` -- the register
        # holds ids 1-5, so that vendor does not exist -- at a unit cost of 580.0
        # against a real cost_price of 600.0, and captioned it "Bulk discount
        # applied for order of 60 bags. Price valid for 30 days." Three runs out
        # of three, identical, with errors: [] and analysis_status "complete".
        # The Streamlit tab renders this dict verbatim through st.json, so an
        # invented vendor and an invented price were being presented to an
        # operator as a procurement quote. It also blocked the one thing the
        # recommendation is for: POST /orders would reject supplier 101.
        #
        # `quoted_unit_cost` is the product's standard cost, not a vendor-issued
        # price -- there is no supplier-price entity in the schema to draw a real
        # quote from. `cost_basis` says so on the record rather than letting the
        # number pass for something it is not.
        notes = supplier_quote.get("quote_notes") or "No quote notes returned."

        if supplier_id:
            # A supplier is on file, so the two facts that matter for a usable
            # estimate are already in hand: the vendor id (from the product) and
            # the cost basis (from the product). Enrich with the register's own
            # name / lead time / terms when it can be read; when it cannot, quote
            # anyway and mark the gaps unknown rather than withholding a usable
            # number over a transient read failure.
            resolved = bool(supplier)
            supplier_quote = {
                "supplier_id": supplier_id,
                "supplier_code": supplier.get("supplier_code") if resolved else None,
                "supplier_name": supplier.get("name") if resolved else None,
                "quoted_unit_cost": unit_cost,
                "total_order_cost": round(unit_cost * recommended_qty, 2),
                "estimated_lead_time_days": supplier.get("lead_time_days") if resolved else None,
                "payment_terms_days": supplier.get("payment_terms_days") if resolved else None,
                "cost_basis": "product.cost_price (standard cost) x recommended_quantity",
                "quote_notes": notes if resolved else (
                    f"Supplier {supplier_id} could not be read from the register, so lead time "
                    f"and payment terms are unknown and the estimate below is unconfirmed. {notes}"
                ),
            }
        else:
            # No supplier on file. Do not invent one, and do not infer one from
            # purchase history either -- a past PO is evidence, not a standing
            # vendor relationship, and choosing the vendor is the buyer's call.
            supplier_quote = {
                "supplier_id": None,
                "supplier_code": None,
                "supplier_name": None,
                "quoted_unit_cost": 0.0,
                "total_order_cost": 0.0,
                "estimated_lead_time_days": None,
                "payment_terms_days": None,
                "cost_basis": "unavailable - no supplier linked to this product",
                "quote_notes": (
                    f"No supplier is linked to {sku}, so no quote can be issued and no "
                    f"purchase order can be raised. Link a supplier to this product first. "
                    f"{notes}"
                ),
            }

        total_cost = _as_float(supplier_quote.get("total_order_cost"), 0.0)
        messages.append(f"Supplier Coordinator: supplier={supplier_quote.get('supplier_id')}, cost=INR {total_cost:.0f}")

        logger.info(
            "agent_complete", poc_id="POC-07", phase="P5", agent="supplier_coordinator",
            supplier_id=supplier_id, supplier_resolved=bool(supplier),
            quoted_total=total_cost, recommended_quantity=recommended_qty,
        )

        return {
            **state,
            "supplier_quote": supplier_quote,
            "errors": errors,
            "messages": messages
        }


@traceable(project_name="AI-Readiness-POC-07-P5")
def inventory_auditor(state: InventoryAnalysisState) -> InventoryAnalysisState:
    """Agent 4: Generate comprehensive inventory audit report synthesizing all previous steps."""
    with tracer.start_as_current_span("agent.inventory_auditor.activate") as span:
        span.set_attribute("poc_id", "POC-07")
        span.set_attribute("agent.name", "inventory_auditor")

        messages: List[str] = list(state.get("messages", []))
        errors: List[str] = list(state.get("errors", []))
        product = state.get("product_data", {})
        forecast = state.get("demand_forecast", {})
        reorder = state.get("reorder_recommendation", {})
        quote = state.get("supplier_quote", {})

        stock = product.get("stock_level", {}) if isinstance(product.get("stock_level"), dict) else {}
        qty_avail = stock.get("quantity_available", 0)
        reorder_pt = product.get("reorder_point", 0)

        # Tell the auditor *why* the quote reads the way it does, not just the
        # number. Given only "Supplier quote: INR 0 for 60 units" it wrote, for a
        # product with no supplier on file: "Please proceed with the supplier
        # order for 60 units, currently quoted at Rs 0, to maintain optimal stock
        # levels." That instructs the operator to place an order the supplier
        # coordinator had, in the panel directly above, just said could not be
        # placed -- and at a price of zero. A bare figure carries no reason, so
        # the model supplied one. Passing the actual situation removes the need.
        quote_total = _as_float(quote.get("total_order_cost"), 0.0)
        rec_qty = reorder.get("recommended_quantity", 0)
        if quote.get("supplier_id"):
            lead = quote.get("estimated_lead_time_days")
            supplier_line = (
                f"Supplier quote: {quote.get('supplier_code') or 'supplier #' + str(quote.get('supplier_id'))}"
                f" ({quote.get('supplier_name') or 'name unavailable'}) — ₹{quote_total:.0f} for "
                f"{rec_qty} units"
                + (f", {int(lead)}-day lead time." if isinstance(lead, (int, float))
                   else ", lead time unknown.")
            )
        else:
            supplier_line = (
                "Supplier quote: NONE. No supplier is linked to this product, so no quote exists "
                "and no purchase order can be raised. Do not tell anyone to place, approve or "
                "proceed with an order, and do not quote a price -- state that a supplier must be "
                "assigned to this SKU first."
            )

        prompt = f"""Generate a concise inventory audit report. 3-4 sentences. Be specific.
Product: {product.get('sku', 'Unknown')} — {product.get('name', '')}
Stock: {qty_avail} available, reorder point: {reorder_pt}
Forecast: {forecast.get('days_of_stock_remaining', 0)} days remaining, risk: {forecast.get('stockout_risk', 'unknown')}
Reorder: {'REQUIRED' if reorder.get('reorder_required') else 'Not required'} — urgency: {reorder.get('urgency', 'N/A')}
{supplier_line}"""

        audit_report = "Inventory audit complete."
        try:
            resp = _invoke_llm(prompt)
            audit_report = _extract_text(resp).strip()
        except Exception as e:
            audit_report = f"Audit error: {str(e)}"

        messages.append(f"Inventory Auditor: report generated ({len(audit_report)} chars)")
        
        logger.info("agent_complete", poc_id="POC-07", phase="P5", agent="inventory_auditor", report_length=len(audit_report))
        
        return {
            **state,
            "audit_report": audit_report,
            "analysis_status": "complete",
            "messages": messages,
            "errors": errors
        }
