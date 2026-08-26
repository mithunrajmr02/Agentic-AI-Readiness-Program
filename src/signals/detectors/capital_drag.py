"""Capital drag / excess inventory / slow-moving stock detector (WS-3).

Grounding: manual §13 line 136 ("Slow-moving stock: Products with no stock movement in 30+ days");
manual §13 line 139 (days on hand = quantity_on_hand / average daily sales).
Fires when excessive capital is tied up in stock beyond normal operational needs (>60 days cover)
or when stocked items have had zero movement for 30+ days.
"""
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.backend.models import Product, StockLevel, StockMovement
from src.core import clock
from src.signals.analytics_adapter import compute_daily_demand
from src.signals.dedup import dedup_key_for
from src.signals.detectors.base import SignalCandidate


SIGNAL_TYPE = "capital_drag"
EXCESS_DAYS_ON_HAND_THRESHOLD = 60.0
INACTIVE_DAYS_THRESHOLD = 30


def detect(
    db: Session,
    product_id: int,
    excess_doh_threshold: float = EXCESS_DAYS_ON_HAND_THRESHOLD,
    inactive_days_threshold: int = INACTIVE_DAYS_THRESHOLD,
) -> Optional[SignalCandidate]:
    """Check whether a product represents capital drag due to excess or dead inventory."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    stock = db.query(StockLevel).filter(StockLevel.product_id == product_id).first()
    if not stock:
        return None

    on_hand = stock.quantity_on_hand or 0
    if on_hand <= 0:
        return None  # No capital tied up if zero stock

    cost_price = product.cost_price or 0.0
    tied_up_capital = round(on_hand * cost_price, 2)

    # 1. Check days on hand against velocity
    demand = compute_daily_demand(db, product_id)
    has_excess_doh = False
    days_cover: Optional[float] = None

    if demand.value is not None and demand.value > 0:
        days_cover = round(on_hand / demand.value, 1)
        if days_cover > excess_doh_threshold:
            has_excess_doh = True

    # 2. Check dormancy (no movements in >= 30 days)
    last_movement = (
        db.query(StockMovement)
        .filter(StockMovement.product_id == product_id)
        .order_by(desc(StockMovement.recorded_at))
        .first()
    )

    is_dormant = False
    days_inactive = 0
    now_dt = clock.now()

    if last_movement and last_movement.recorded_at:
        days_inactive = (now_dt - last_movement.recorded_at).days
        if days_inactive >= inactive_days_threshold:
            is_dormant = True
    elif not last_movement:
        # Product created but never had any movement, holding positive stock
        days_inactive = 30
        is_dormant = True

    if has_excess_doh or is_dormant:
        if tied_up_capital >= 50000.0 or (days_cover is not None and days_cover >= 120.0):
            severity = "high"
        elif tied_up_capital >= 15000.0 or (days_cover is not None and days_cover >= 60.0):
            severity = "medium"
        else:
            severity = "low"

        if has_excess_doh and is_dormant:
            detected_from = (
                f"Capital drag: {product.name} has {days_cover} days on hand and "
                f"zero movement in {days_inactive} days (₹{tied_up_capital:,.2f} tied up)"
            )
        elif has_excess_doh:
            detected_from = (
                f"Capital drag: {product.name} has {days_cover} days of stock cover "
                f"(exceeds {excess_doh_threshold}d threshold; ₹{tied_up_capital:,.2f} tied up)"
            )
        else:
            detected_from = (
                f"Slow-moving stock: {product.name} has had zero movement in {days_inactive} days "
                f"with {on_hand} units on hand (₹{tied_up_capital:,.2f} tied up)"
            )

        evidence = {
            "product_id": product.id,
            "sku": product.sku,
            "product_name": product.name,
            "quantity_on_hand": on_hand,
            "cost_price": cost_price,
            "tied_up_capital": tied_up_capital,
            "average_daily_demand": demand.value,
            "days_of_cover": days_cover,
            "days_inactive": days_inactive,
            "has_excess_doh": has_excess_doh,
            "is_dormant": is_dormant,
            "formula": "days_on_hand > 60 or days_inactive >= 30",
            "citation": "manual §13 line 136, §13 line 139",
        }

        return SignalCandidate(
            signal_type=SIGNAL_TYPE,
            severity=severity,
            product_id=product.id,
            supplier_id=product.supplier_id,
            po_id=None,
            detected_from=detected_from,
            evidence=evidence,
            sufficiency=demand.sufficiency if demand.value is not None else "sufficient",
            dedup_key=dedup_key_for(SIGNAL_TYPE, product_id=product.id),
        )

    return None


def detect_all(db: Session) -> list[SignalCandidate]:
    """Scan all products for excess/stagnant inventory capital drag."""
    products = db.query(Product.id).all()
    results = []
    for (pid,) in products:
        candidate = detect(db, pid)
        if candidate:
            results.append(candidate)
    return results
