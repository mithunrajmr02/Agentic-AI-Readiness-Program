"""Tests for blast-radius constraint checks — WS-5.

15-SHARED-CONTRACTS.md §7 / 08-AGENTIC-WORKFLOWS.md §5.5.
"""
from datetime import timedelta
import json
import pytest

from src.backend.models_governance import AutonomyPolicy, Decision
from src.core import clock
from src.policy.blast_radius import check_blast_radius
from src.policy.rules import DecisionContext


def test_blast_radius_within_limits(db):
    policy = AutonomyPolicy(
        scope_type="global",
        mode="autonomous",
        max_orders_per_hour=10,
        max_value_per_day=100000.0,
    )
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=15000.0,
        affected_product_count=1,
    )
    exceeded, count, detail = check_blast_radius(db, ctx, policy)
    assert exceeded is False
    assert count == 1
    assert detail is None


def test_blast_radius_exceeds_hourly_order_limit(db):
    policy = AutonomyPolicy(
        scope_type="global",
        mode="autonomous",
        max_orders_per_hour=3,
        max_value_per_day=500000.0,
    )
    now = clock.now()

    # Seed 3 recent decisions in the past 30 minutes
    for i in range(3):
        d = Decision(
            decision_id=f"DEC-00010{i}",
            action_type="raise_po",
            status="executed",
            actor="agent:replenishment",
            proposed_at=now - timedelta(minutes=10 * (i + 1)),
            autonomy_mode="autonomous",
        )
        db.add(d)
    db.commit()

    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=5000.0,
        affected_product_count=1,
    )
    exceeded, count, detail = check_blast_radius(db, ctx, policy)
    assert exceeded is True
    assert "in the last hour" in detail
    assert "exceeds limit of 3" in detail


def test_blast_radius_exceeds_daily_spend_limit(db):
    policy = AutonomyPolicy(
        scope_type="global",
        mode="autonomous",
        max_orders_per_hour=50,
        max_value_per_day=100000.0,
    )
    now = clock.now()

    # Seed an existing decision of ₹80,000 made 2 hours ago
    d = Decision(
        decision_id="DEC-000200",
        action_type="raise_po",
        status="executed",
        actor="agent:replenishment",
        proposed_at=now - timedelta(hours=2),
        autonomy_mode="autonomous",
        inputs=json.dumps({"value_inr": 80000.0}),
    )
    db.add(d)
    db.commit()

    # Proposing another ₹30,000 -> total ₹110,000 > ₹100,000 limit
    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=30000.0,
        affected_product_count=1,
    )
    exceeded, count, detail = check_blast_radius(db, ctx, policy)
    assert exceeded is True
    assert "24h cumulative value" in detail
    assert "exceeds limit of ₹100,000.00" in detail


def test_blast_radius_ignores_failed_or_rejected_decisions(db):
    policy = AutonomyPolicy(
        scope_type="global",
        mode="autonomous",
        max_orders_per_hour=2,
        max_value_per_day=50000.0,
    )
    now = clock.now()

    # Seed rejected decisions — should not count against hourly quota
    for i in range(5):
        d = Decision(
            decision_id=f"DEC-00030{i}",
            action_type="raise_po",
            status="rejected",
            actor="agent:replenishment",
            proposed_at=now - timedelta(minutes=5),
            autonomy_mode="autonomous",
            inputs=json.dumps({"value_inr": 40000.0}),
        )
        db.add(d)
    db.commit()

    ctx = DecisionContext(
        action_type="raise_po",
        product_id=1,
        value_inr=10000.0,
        affected_product_count=1,
    )
    exceeded, count, detail = check_blast_radius(db, ctx, policy)
    assert exceeded is False
