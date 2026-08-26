"""Tests for projected breach detector (WS-3)."""
from datetime import timedelta

from src.backend.models import MovementType, StockMovement
from src.core import clock
from src.signals.detectors import projected_breach


def test_projected_breach_fires_when_velocity_depletes_stock_in_lead_time(db, sample_data):
    """When on-hand is above ROP but high sales velocity will breach safety stock in lead time."""
    p_rice = sample_data["products"]["rice"]
    # Rice has 150 on hand, ROP is 40.
    # Current demand is ~8.3 units/day (250 / 30).
    # With 5 days lead time + 2 safety days: required = 8.3 * 7 = 58.3.
    # Let's adjust stock level on hand to 50 (50 > 40, but 50 - 5*8.3 = 8.5 <= 2*8.3=16.6).
    sl = sample_data["stock"]["sl1"]
    sl.quantity_on_hand = 50
    db.commit()

    candidate = projected_breach.detect(db, p_rice.id)

    assert candidate is not None
    assert candidate.signal_type == "projected_breach"
    assert candidate.product_id == p_rice.id
    assert candidate.evidence["quantity_on_hand"] == 50
    assert candidate.evidence["configured_reorder_point"] == 40
    assert candidate.evidence["lead_time_days"] == 5


def test_projected_breach_does_not_fire_on_abundant_cover(db, sample_data):
    """When on hand provides plentiful days of cover (150 on hand vs 8.3 units/day), no breach."""
    p_rice = sample_data["products"]["rice"]
    sl = sample_data["stock"]["sl1"]
    sl.quantity_on_hand = 150
    db.commit()

    candidate = projected_breach.detect(db, p_rice.id)
    assert candidate is None


def test_projected_breach_does_not_fire_when_already_in_threshold_breach(db, sample_data):
    """If stock is <= reorder point, threshold_breach detector owns it."""
    p_rice = sample_data["products"]["rice"]
    sl = sample_data["stock"]["sl1"]
    sl.quantity_on_hand = 35  # <= 40
    db.commit()

    candidate = projected_breach.detect(db, p_rice.id)
    assert candidate is None


def test_projected_breach_does_not_fire_without_sufficient_demand_data(db, sample_data):
    """If sales history is insufficient/none (e.g. Colgate), projected breach cannot fire."""
    p_colgate = sample_data["products"]["colgate"]
    candidate = projected_breach.detect(db, p_colgate.id)
    assert candidate is None
