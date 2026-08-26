"""Tests for counter-proposals, recomputations, and system objections (WS-4)."""
import json
import pytest

from src.core import clock
from src.governance.approvals import request_approval
from src.governance.counter import counter
from src.governance.decisions import create_decision


@pytest.fixture
def headphone_reorder_decision(db):
    """Fixture mirroring demo scenario D2: recommended 12 headphones, ROP 8, on-hand 4, demand 1.5."""
    return create_decision(
        db,
        signal_id="SIG-000046",
        action_type="raise_po",
        inputs={
            "product_id": 3,
            "product_name": "Sony WH-1000XM5",
            "quantity_on_hand": 4,
            "reorder_point": 8,
            "daily_demand": 1.5,
            "lead_time_days": 11,
            "unit_price": 22000.0,
        },
        computation={
            "reorder_quantity": 12,
            "order_value": 264000.0,
        },
        provenance={"order_value": "computed"},
        verdict={"requires_approval": True, "escalation_reason": "value_threshold", "citation": "manual §10 line 113"},
        status="pending_approval",
    )


def test_counter_proposal_recomputes_and_generates_system_objection(db, headphone_reorder_decision, users):
    approval = request_approval(db, headphone_reorder_decision)
    manager = users["manager"]

    # Manager reduces quantity 12 -> 6
    result = counter(
        db,
        approval_id=approval.approval_id,
        user_id=manager.id,
        payload={"quantity": 6, "note": "Reducing capital exposure"},
    )

    # 1. CounterResult asserts
    assert result.accepted is True
    assert result.recomputed["counter_quantity"] == 6
    assert result.recomputed["available_stock_after"] == 10
    assert result.recomputed["margin_above_rop"] == 2.0
    assert result.recomputed["cover_days_above_rop"] == 1.3
    assert result.recomputed["order_value"] == 132000.0

    # 2. System objection is generated with exact arithmetic (doc 13 §5.5)
    assert result.system_objection is not None
    assert "6 units returns available stock to 10, 2 above the derived reorder point of 8" in result.system_objection
    assert "1.3 days" in result.system_objection
    assert "Recommended quantity remains 12" in result.system_objection

    # 3. Decision updated and objection persisted
    db.refresh(headphone_reorder_decision)
    assert headphone_reorder_decision.status == "countered"
    assert headphone_reorder_decision.system_objection == result.system_objection
    assert headphone_reorder_decision.actor == f"user:{manager.id}"

    # Verify computation JSON contains recompute data
    comp = json.loads(headphone_reorder_decision.computation)
    assert "counter_recompute" in comp
    assert comp["counter_recompute"]["counter_quantity"] == 6


def test_counter_proposal_without_objection_when_quantity_meets_recommendation(db, headphone_reorder_decision, users):
    approval = request_approval(db, headphone_reorder_decision)
    manager = users["manager"]

    # Manager increases quantity 12 -> 15 (safe)
    result = counter(
        db,
        approval_id=approval.approval_id,
        user_id=manager.id,
        payload={"quantity": 15},
    )

    assert result.accepted is True
    assert result.system_objection is None
    assert result.recomputed["counter_quantity"] == 15
    assert result.recomputed["available_stock_after"] == 19
