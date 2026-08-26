"""Analytics adapter for signals engine (WS-3).

15-SHARED-CONTRACTS.md §5.
Provides consumption of deterministic demand, lead time, and sufficiency
metrics. If the WS-1 `src.analytics` module is present, delegates directly to it.
Otherwise, provides a deterministic local implementation that strictly adheres
to the frozen Computed dataclass and sufficiency contracts.
"""
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.core import clock
from src.core.vocab import SUFFICIENCY


@dataclass(frozen=True)
class Computed:
    """The frozen analytics return shape (15-SHARED-CONTRACTS.md §5.1).

    Invariant: ``value is None`` whenever ``sufficiency in ('insufficient', 'none')``.
    Never 0.0.
    """

    value: Optional[float]
    sufficiency: str  # ∈ SUFFICIENCY
    inputs: dict[str, Any]
    formula: str
    citation: Optional[str]
    sample_size: int
    span_days: int


def _is_sale_movement(m) -> bool:
    """Check if movement represents a customer sale."""
    mt = getattr(m, "movement_type", None)
    if mt is None:
        return False
    name = getattr(mt, "name", str(mt))
    val = getattr(mt, "value", str(mt))
    return name.lower() == "sale" or val.lower() == "sale"


def compute_daily_demand(db: Session, product_id: int, window_days: int = 30) -> Computed:
    """Compute average daily sales demand for a product over a time window."""
    try:
        from src import analytics  # type: ignore

        if hasattr(analytics, "compute_daily_demand"):
            return analytics.compute_daily_demand(db, product_id, window_days=window_days)
    except ImportError:
        pass

    from src.backend.models import StockMovement

    current_dt = clock.now()
    window_start = current_dt - timedelta(days=window_days)

    movements = (
        db.query(StockMovement)
        .filter(
            StockMovement.product_id == product_id,
            StockMovement.recorded_at >= window_start,
            StockMovement.recorded_at <= current_dt,
        )
        .all()
    )

    sale_movements = [m for m in movements if _is_sale_movement(m)]
    sample_size = len(sale_movements)

    distinct_days = {
        m.recorded_at.date() for m in sale_movements if m.recorded_at is not None
    }
    distinct_day_count = len(distinct_days)

    # 15-SHARED-CONTRACTS.md §5.4 Sufficiency thresholds
    if sample_size >= 14 and distinct_day_count >= 21:
        sufficiency_status = "sufficient"
    elif sample_size >= 5 and distinct_day_count >= 7:
        sufficiency_status = "thin"
    elif sample_size >= 1:
        sufficiency_status = "insufficient"
    else:
        sufficiency_status = "none"

    inputs = {
        "product_id": product_id,
        "window_days": window_days,
        "sale_events_count": sample_size,
        "distinct_sale_days": distinct_day_count,
    }

    if sufficiency_status in ("insufficient", "none"):
        return Computed(
            value=None,
            sufficiency=sufficiency_status,
            inputs=inputs,
            formula="sum(sale_quantities) / window_days",
            citation="manual §3 line 33",
            sample_size=sample_size,
            span_days=window_days,
        )

    total_units_sold = sum(abs(m.quantity) for m in sale_movements)
    avg_daily_demand = round(total_units_sold / float(window_days), 4)
    inputs["total_units_sold"] = total_units_sold

    return Computed(
        value=avg_daily_demand,
        sufficiency=sufficiency_status,
        inputs=inputs,
        formula="sum(sale_quantities) / window_days",
        citation="manual §3 line 33",
        sample_size=sample_size,
        span_days=window_days,
    )


def measured_lead_time(db: Session, supplier_id: int) -> Computed:
    """Compute measured lead time and on-time performance from completed POs."""
    try:
        from src import analytics  # type: ignore

        if hasattr(analytics, "measured_lead_time"):
            return analytics.measured_lead_time(db, supplier_id)
    except ImportError:
        pass

    from src.backend.models import PurchaseOrder

    pos = (
        db.query(PurchaseOrder)
        .filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.received_date.isnot(None),
        )
        .all()
    )

    lead_times: list[int] = []
    on_time_count = 0

    for po in pos:
        if po.received_date and po.order_date:
            lt = (po.received_date - po.order_date).days
            lead_times.append(lt)
            if po.expected_delivery and po.received_date <= po.expected_delivery:
                on_time_count += 1

    sample_size = len(lead_times)
    inputs = {
        "supplier_id": supplier_id,
        "sample_size": sample_size,
    }

    if sample_size == 0:
        return Computed(
            value=None,
            sufficiency="none",
            inputs=inputs,
            formula="avg(received_date - order_date)",
            citation="manual §6 line 74",
            sample_size=0,
            span_days=0,
        )

    avg_lt = round(sum(lead_times) / float(sample_size), 2)
    on_time_rate = round(on_time_count / float(sample_size), 4)
    inputs["avg_lead_time_days"] = avg_lt
    inputs["on_time_rate"] = on_time_rate

    sufficiency_status = "sufficient" if sample_size >= 3 else "thin"

    return Computed(
        value=avg_lt,
        sufficiency=sufficiency_status,
        inputs=inputs,
        formula="avg(received_date - order_date)",
        citation="manual §6 line 74",
        sample_size=sample_size,
        span_days=0,
    )


def derive_reorder_point(
    db: Session,
    product_id: int,
    *,
    use_measured_lead_time: bool = False,
    safety_stock_days: int = 2,
) -> Computed:
    """Derive implied reorder point: (demand * lead_time) + (demand * safety_days).

    manual §3 line 35 worked example: (10 * 5) + (10 * 2) = 70.
    """
    try:
        from src import analytics  # type: ignore

        if hasattr(analytics, "derive_reorder_point"):
            return analytics.derive_reorder_point(
                db, product_id, use_measured_lead_time=use_measured_lead_time
            )
    except ImportError:
        pass

    from src.backend.models import Product, Supplier

    demand = compute_daily_demand(db, product_id)
    if demand.value is None or demand.sufficiency in ("insufficient", "none"):
        return Computed(
            value=None,
            sufficiency=demand.sufficiency,
            inputs={"product_id": product_id, "demand_inputs": demand.inputs},
            formula="(demand * lead_time) + (demand * safety_days)",
            citation="manual §3 line 35",
            sample_size=demand.sample_size,
            span_days=demand.span_days,
        )

    product = db.query(Product).filter(Product.id == product_id).first()
    supplier_lead_time = 5  # default baseline
    if product and product.supplier_id:
        if use_measured_lead_time:
            measured = measured_lead_time(db, product.supplier_id)
            if measured.value is not None:
                supplier_lead_time = int(round(measured.value))
            else:
                supplier = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
                if supplier and supplier.lead_time_days:
                    supplier_lead_time = supplier.lead_time_days
        else:
            supplier = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
            if supplier and supplier.lead_time_days:
                supplier_lead_time = supplier.lead_time_days

    # manual §3 line 35: (demand * lead_time) + (demand * safety_days)
    lead_time_demand = demand.value * supplier_lead_time
    safety_stock = demand.value * safety_stock_days
    derived_rop = round(lead_time_demand + safety_stock, 2)

    inputs = {
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
        formula="(demand * lead_time) + (demand * safety_days)",
        citation="manual §3 line 35",
        sample_size=demand.sample_size,
        span_days=demand.span_days,
    )


def score_sufficiency(db: Session, product_id: int) -> Computed:
    """Return data sufficiency assessment for a product's history."""
    demand = compute_daily_demand(db, product_id)
    return Computed(
        value=1.0 if demand.sufficiency == "sufficient" else (0.5 if demand.sufficiency == "thin" else None),
        sufficiency=demand.sufficiency,
        inputs=demand.inputs,
        formula="score_sufficiency(sales_count, distinct_days)",
        citation="manual §4 line 45",
        sample_size=demand.sample_size,
        span_days=demand.span_days,
    )


def days_on_hand(db: Session, product_id: int) -> Computed:
    """Compute days of inventory cover given current on-hand and daily velocity."""
    from src.backend.models import StockLevel

    demand = compute_daily_demand(db, product_id)
    stock = db.query(StockLevel).filter(StockLevel.product_id == product_id).first()
    on_hand = stock.quantity_on_hand if stock else 0

    if demand.value is None or demand.value <= 0:
        return Computed(
            value=None,
            sufficiency=demand.sufficiency,
            inputs={"product_id": product_id, "on_hand": on_hand},
            formula="on_hand / daily_demand",
            citation="manual §13 line 139",
            sample_size=demand.sample_size,
            span_days=demand.span_days,
        )

    doh = round(on_hand / demand.value, 2)
    return Computed(
        value=doh,
        sufficiency=demand.sufficiency,
        inputs={"product_id": product_id, "on_hand": on_hand, "daily_demand": demand.value},
        formula="on_hand / daily_demand",
        citation="manual §13 line 139",
        sample_size=demand.sample_size,
        span_days=demand.span_days,
    )
