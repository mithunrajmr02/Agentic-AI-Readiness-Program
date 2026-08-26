"""Data sufficiency evaluation and the frozen Computed return shape (WS-1).

15-SHARED-CONTRACTS.md §5.1, §5.4.
Every business number in the system is returned wrapped in :class:`Computed`.
"""
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.core.vocab import SUFFICIENCY


@dataclass(frozen=True)
class Computed:
    """The frozen analytics return shape (15-SHARED-CONTRACTS.md §5.1).

    Invariants:
    - ``value is None`` whenever ``sufficiency in ('insufficient', 'none')``. Never 0.0.
    - Immutable (frozen).
    """

    value: Optional[float]
    sufficiency: str  # ∈ SUFFICIENCY
    inputs: dict[str, Any]
    formula: str  # "(demand × lead_time) + (demand × safety_days)"
    citation: Optional[str]  # "manual §3 line 35"
    sample_size: int
    span_days: int

    def __post_init__(self):
        if self.sufficiency not in SUFFICIENCY:
            raise ValueError(
                f"Invalid sufficiency '{self.sufficiency}'. Must be one of {SUFFICIENCY}"
            )
        if self.sufficiency in ("insufficient", "none") and self.value is not None:
            raise ValueError(
                f"Computed value must be None when sufficiency is '{self.sufficiency}', got {self.value}"
            )


def score_sufficiency(db: Session, product_id: int) -> Computed:
    """Assess sales history sufficiency for a product.

    15-SHARED-CONTRACTS.md §5.2, §5.4.
    Thresholds:
    - sufficient: >= 14 sale events across >= 21 distinct days
    - thin: >= 5 sale events across >= 7 distinct days
    - insufficient: >= 1 sale event, below thin
    - none: 0 sale events
    """
    from src.analytics.demand import compute_daily_demand

    demand = compute_daily_demand(db, product_id)
    val: Optional[float] = None
    if demand.sufficiency == "sufficient":
        val = 1.0
    elif demand.sufficiency == "thin":
        val = 0.5

    return Computed(
        value=val,
        sufficiency=demand.sufficiency,
        inputs=demand.inputs,
        formula="score_sufficiency(sales_count, distinct_days)",
        citation="manual §4 line 45",
        sample_size=demand.sample_size,
        span_days=demand.span_days,
    )
