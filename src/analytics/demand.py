"""Daily sales demand calculation (WS-1).

15-SHARED-CONTRACTS.md §5.1, §5.2, §5.4 and manual §3 line 33.
Pure function querying StockMovement records over a rolling time window.
"""
from datetime import timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.analytics.sufficiency import Computed
from src.backend.models import MovementType, StockMovement
from src.core import clock


def _is_sale_movement(m: Any) -> bool:
    """Check if a stock movement represents a customer sale."""
    mt = getattr(m, "movement_type", None)
    if mt is None:
        return False
    if isinstance(mt, MovementType):
        return mt == MovementType.sale
    name = getattr(mt, "name", str(mt))
    val = getattr(mt, "value", str(mt))
    return name.lower() == "sale" or val.lower() == "sale"


def compute_daily_demand(
    db: Session, product_id: int, window_days: int = 30
) -> Computed:
    """Compute average daily sales demand for a product over a time window.

    15-SHARED-CONTRACTS.md §5.2, §5.4.
    Pure read query against stock_movements. Returns :class:`Computed` with
    verdict:
    - 'sufficient': >= 14 sale events across >= 21 distinct days -> value is float
    - 'thin': >= 5 sale events across >= 7 distinct days -> value is float
    - 'insufficient': >= 1 sale event, below thin -> value is None
    - 'none': 0 sale events -> value is None
    """
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

    if sample_size >= 14 and distinct_day_count >= 21:
        sufficiency_status = "sufficient"
    elif sample_size >= 5 and distinct_day_count >= 7:
        sufficiency_status = "thin"
    elif sample_size >= 1:
        sufficiency_status = "insufficient"
    else:
        sufficiency_status = "none"

    inputs: dict[str, Any] = {
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
