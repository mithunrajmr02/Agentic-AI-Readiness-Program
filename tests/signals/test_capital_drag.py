"""Tests for capital drag / slow-moving inventory detector (WS-3)."""
from src.signals.detectors import capital_drag


def test_capital_drag_fires_on_dormant_excess_inventory(db, sample_data):
    """Product 4 (Detergent) has 500 units on hand with zero sales in 30+ days."""
    p_detergent = sample_data["products"]["detergent"]
    candidate = capital_drag.detect(db, p_detergent.id)

    assert candidate is not None
    assert candidate.signal_type == "capital_drag"
    assert candidate.product_id == p_detergent.id
    assert candidate.evidence["quantity_on_hand"] == 500
    assert candidate.evidence["tied_up_capital"] == 500 * 450.0  # 225,000 INR
    assert candidate.severity == "high"
    assert "manual §13 line 136" in candidate.evidence["citation"]


def test_capital_drag_does_not_fire_on_active_turning_stock(db, sample_data):
    """Product 1 (Rice) has 150 on hand with daily sales ~8.33 -> 18 days cover (< 60 threshold)."""
    p_rice = sample_data["products"]["rice"]
    candidate = capital_drag.detect(db, p_rice.id)
    assert candidate is None


def test_capital_drag_does_not_fire_on_zero_stock(db, sample_data):
    """Product 2 (Headphones) is out of stock (0 units), so no capital drag exists."""
    p_headphones = sample_data["products"]["headphones"]
    candidate = capital_drag.detect(db, p_headphones.id)
    assert candidate is None
