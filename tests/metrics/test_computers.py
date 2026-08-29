"""Tests for metric computers (M-1 to M-22, M-31 to M-36) (WS-17)."""
from src.metrics.registry import compute_category, compute_metric


def test_m1_to_m6_detection_computers(test_db):
    """Test detection computers against seeded test data."""
    m1 = compute_metric(test_db, "M-1")
    assert m1.key == "M-1"
    assert m1.tier == "T1"
    assert m1.value is not None

    m2 = compute_metric(test_db, "M-2")
    assert m2.key == "M-2"

    m3 = compute_metric(test_db, "M-3")
    assert m3.value == 2.0  # 2 seeded signals

    m4 = compute_metric(test_db, "M-4")
    assert m4.value == 2.0  # projected_breach + po_overdue

    m5 = compute_metric(test_db, "M-5")
    assert m5.value == 1.0  # 1 po_overdue signal

    m6 = compute_metric(test_db, "M-6")
    assert m6.value == 1.0  # 1 config change decision executed


def test_m7_to_m13_governance_computers(test_db):
    """Test autonomy & governance computers."""
    m7 = compute_metric(test_db, "M-7")
    assert m7.value == 1.0  # 2 executed / 2 agent

    m8 = compute_metric(test_db, "M-8")
    assert m8.value == round(1.0 / 3.0, 4)  # 1 with escalation_reason out of 3 decisions

    m9 = compute_metric(test_db, "M-9")
    assert m9.value == 1.0  # 1 approval

    m10 = compute_metric(test_db, "M-10")
    assert m10.value is not None

    m11 = compute_metric(test_db, "M-11")
    assert m11.value == round(1.0 / 3.0, 4)  # 1 insufficient_data out of 3 decisions

    m12 = compute_metric(test_db, "M-12")
    assert m12.value == round(2.0 / 3.0, 4)  # 2 decisions with citations out of 3

    m13 = compute_metric(test_db, "M-13")
    assert m13.value == 1.0  # all stock movements have recorded_by


def test_m14_to_m17_method_quality_computers(test_db):
    """Test method quality computers (the reviewer's block)."""
    # M-14: 5 fabricated numeric fields -> 0
    m14 = compute_metric(test_db, "M-14")
    assert m14.value == 0.0, "M-14 must compute to 0.0 after WS-1 lands"

    m15 = compute_metric(test_db, "M-15")
    assert m15.value == 0.0  # 0 LLM violations in seeded run

    # M-16: Ledger invariant integrity
    m16 = compute_metric(test_db, "M-16")
    assert m16.value == 1.0, "Ledger invariant holds for 100% of products"

    # M-17: Unreachable state count
    m17 = compute_metric(test_db, "M-17")
    assert m17.value == 1.0  # 1 unreachable status ('cancelled' only)


def test_m18_to_m22_position_computers(test_db):
    """Test capital and inventory position computers."""
    m18 = compute_metric(test_db, "M-18")
    assert m18.key == "M-18"

    m19 = compute_metric(test_db, "M-19")
    assert m19.key == "M-19"

    # M-20: Stock above requirement: product 1 has on_hand 30, ROP 20, cost_price 280 -> 10 * 280 = 2800.0
    m20 = compute_metric(test_db, "M-20")
    assert m20.value == 2800.0

    m21 = compute_metric(test_db, "M-21")
    assert m21.key == "M-21"

    m22 = compute_metric(test_db, "M-22")
    assert m22.value == 0.0  # 0 consolidate decisions in test seed


def test_m31_to_m36_live_computers(test_db):
    """Test T2 live metric computers return valid metadata."""
    t2_metrics = compute_category(test_db, "t2_live")
    assert len(t2_metrics) == 6
    for m in t2_metrics:
        assert m.tier == "T2"
        assert m.value is None  # Live demonstrated in the room, not stored
        assert m.formula and len(m.formula) > 0
