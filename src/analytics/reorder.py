"""Reorder point and reorder quantity derivation (WS-1).

15-SHARED-CONTRACTS.md §5.1, §5.2, §5.3 and manual §3 line 35, §9 line 102.
Pure functions deriving replenishment thresholds from sales demand and supplier lead times.
"""
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.analytics.demand import compute_daily_demand
from src.analytics.leadtime import measured_lead_time
from src.analytics.sufficiency import Computed
from src.backend.models import Product, Supplier


def derive_reorder_point(
    db: Session,
    product_id: int,
    *,
    use_measured_lead_time: bool = False,
    safety_stock_days: int = 2,
) -> Computed:
    """Derive implied reorder point: (demand * lead_time) + (demand * safety_days).

    15-SHARED-CONTRACTS.md §5.2, §5.3.
    manual §3 line 35 worked example: (10 * 5) + (10 * 2) = 70.
    """
    demand = compute_daily_demand(db, product_id)
    if demand.value is None or demand.sufficiency in ("insufficient", "none"):
        return Computed(
            value=None,
            sufficiency=demand.sufficiency,
            inputs={"product_id": product_id, "demand_inputs": demand.inputs},
            formula="(demand × lead_time) + (demand × safety_days)",
            citation="manual §3 line 35",
            sample_size=demand.sample_size,
            span_days=demand.span_days,
        )

    product = db.query(Product).filter(Product.id == product_id).first()
    supplier_lead_time = 5  # default fallback
    if product and product.supplier_id:
        if use_measured_lead_time:
            measured = measured_lead_time(db, product.supplier_id)
            if measured.value is not None:
                supplier_lead_time = int(round(measured.value))
            else:
                supplier = (
                    db.query(Supplier)
                    .filter(Supplier.id == product.supplier_id)
                    .first()
                )
                if supplier and supplier.lead_time_days:
                    supplier_lead_time = supplier.lead_time_days
        else:
            supplier = (
                db.query(Supplier)
                .filter(Supplier.id == product.supplier_id)
                .first()
            )
            if supplier and supplier.lead_time_days:
                supplier_lead_time = supplier.lead_time_days

    lead_time_demand = demand.value * supplier_lead_time
    safety_stock = demand.value * safety_stock_days
    derived_rop = round(lead_time_demand + safety_stock, 2)

    inputs: dict[str, Any] = {
        "product_id": product_id,
        "daily_demand": demand.value,
        "lead_time_days": supplier_lead_time,
        "safety_stock_days": safety_stock_days,
        "lead_time_demand": lead_time_demand,
        "safety_stock": safety_stock,
    }

    return Computed(
        value=derived_rop,
        sufficiency=demand.sufficiency,
        inputs=inputs,
        formula="(demand × lead_time) + (demand × safety_days)",
        citation="manual §3 line 35",
        sample_size=demand.sample_size,
        span_days=demand.span_days,
    )


def derive_reorder_quantity(
    db: Session,
    product_id: int,
    *,
    lead_time_days: Optional[int] = None,
    safety_days: int = 14,
) -> Computed:
    """Derive standard reorder quantity: (demand * lead_time) + (demand * safety_days).

    manual §9 line 102 worked example: (5 * 7) + (5 * 14) = 105.
    """
    demand = compute_daily_demand(db, product_id)
    if demand.value is None or demand.sufficiency in ("insufficient", "none"):
        return Computed(
            value=None,
            sufficiency=demand.sufficiency,
            inputs={"product_id": product_id, "demand_inputs": demand.inputs},
            formula="(demand × lead_time) + (demand × safety_days)",
            citation="manual §9 line 102",
            sample_size=demand.sample_size,
            span_days=demand.span_days,
        )

    if lead_time_days is None:
        product = db.query(Product).filter(Product.id == product_id).first()
        lt = 7  # default
        if product and product.supplier_id:
            supplier = (
                db.query(Supplier)
                .filter(Supplier.id == product.supplier_id)
                .first()
            )
            if supplier and supplier.lead_time_days:
                lt = supplier.lead_time_days
        lead_time_days = lt

    lead_demand = demand.value * lead_time_days
    safety_demand = demand.value * safety_days
    derived_roq = round(lead_demand + safety_demand, 2)

    inputs: dict[str, Any] = {
        "product_id": product_id,
        "daily_demand": demand.value,
        "lead_time_days": lead_time_days,
        "safety_days": safety_days,
        "lead_demand": lead_demand,
        "safety_demand": safety_demand,
    }

    return Computed(
        value=derived_roq,
        sufficiency=demand.sufficiency,
        inputs=inputs,
        formula="(demand × lead_time) + (demand × safety_days)",
        citation="manual §9 line 102",
        sample_size=demand.sample_size,
        span_days=demand.span_days,
    )


def derive_reorder_point_from(
    demand: float,
    lead_time: int,
    safety_days: int = 2,
) -> Computed:
    """Pure arithmetic helper for reorder point without DB (18-INTEGRATION-AND-TESTING.md §4.1)."""
    lead_time_demand = demand * lead_time
    safety_stock = demand * safety_days
    derived_rop = round(lead_time_demand + safety_stock, 2)
    return Computed(
        value=derived_rop,
        sufficiency="sufficient" if demand > 0 else "none",
        inputs={
            "daily_demand": demand,
            "lead_time_days": lead_time,
            "safety_stock_days": safety_days,
            "lead_time_demand": lead_time_demand,
            "safety_stock": safety_stock,
        },
        formula="(demand × lead_time) + (demand × safety_days)",
        citation="manual §3 line 35",
        sample_size=1,
        span_days=0,
    )


def order_quantity_from(
    demand: float,
    lead_time: int,
    safety_days: int = 14,
) -> Computed:
    """Pure arithmetic helper for order quantity without DB (18-INTEGRATION-AND-TESTING.md §4.1)."""
    lead_demand = demand * lead_time
    safety_demand = demand * safety_days
    derived_roq = round(lead_demand + safety_demand, 2)
    return Computed(
        value=derived_roq,
        sufficiency="sufficient" if demand > 0 else "none",
        inputs={
            "daily_demand": demand,
            "lead_time_days": lead_time,
            "safety_days": safety_days,
            "lead_demand": lead_demand,
            "safety_demand": safety_demand,
        },
        formula="(demand × lead_time) + (demand × safety_days)",
        citation="manual §9 line 102",
        sample_size=1,
        span_days=0,
    )

