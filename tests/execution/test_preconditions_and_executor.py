"""The seven preconditions, re-checked at execution time -- not trusted from
proposal time (15-SHARED-CONTRACTS.md §9; 18-INTEGRATION-AND-TESTING.md §4.6).
"""
from types import SimpleNamespace

import pytest

from src.backend.models import Category, POStatus, Product, StockLevel, Supplier
from src.backend.services.inventory_service import receive_purchase_order
from src.backend.services.po_service import create_purchase_order
from src.execution import idempotency
from src.execution.executor import execute_decision
from src.execution.preconditions import (
    AUTONOMY_MODE_FORBIDS,
    DUPLICATE_OPEN_PO,
    IDEMPOTENCY_KEY_CONSUMED,
    KILL_SWITCH_ENGAGED,
    NEED_ALREADY_RESOLVED,
    SUPPLIER_INACTIVE,
    VALUE_OUT_OF_BAND,
    check_preconditions,
)


def _decision(**overrides):
    base = dict(
        product_id=None, supplier_id=None, quantity=10, unit_cost=80.0,
        order_value=800.0, authority_limit=None, autonomy_mode="autonomous",
        kill_switch_engaged=False, idempotency_key=None, expected_delivery=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _supplier(db, active=True):
    supplier = Supplier(name="Acme", supplier_code="SUP-0001", is_active=active)
    db.add(supplier)
    db.flush()
    return supplier


def _product(db, supplier, on_hand=4, reorder_point=10):
    product = Product(
        sku="SKU-GRO-0001", name="Rice", category=Category.grocery,
        unit_price=100.0, cost_price=80.0, reorder_point=reorder_point,
        reorder_quantity=50, supplier_id=supplier.id,
    )
    db.add(product)
    db.flush()
    db.add(StockLevel(product_id=product.id, quantity_on_hand=on_hand, quantity_reserved=0))
    db.commit()
    return product


# --- isolated precondition checks ---

def test_kill_switch_blocks(db_session):
    failed = check_preconditions(db_session, _decision(kill_switch_engaged=True))
    assert failed == [KILL_SWITCH_ENGAGED]


@pytest.mark.parametrize("mode", ["off", "shadow"])
def test_autonomy_mode_off_or_shadow_blocks(db_session, mode):
    failed = check_preconditions(db_session, _decision(autonomy_mode=mode))
    assert failed == [AUTONOMY_MODE_FORBIDS]


def test_value_over_authority_limit_blocks(db_session):
    failed = check_preconditions(db_session, _decision(order_value=5000.0, authority_limit=1000.0))
    assert failed == [VALUE_OUT_OF_BAND]


def test_supplier_inactive_blocks(db_session):
    supplier = _supplier(db_session, active=False)
    failed = check_preconditions(db_session, _decision(supplier_id=supplier.id))
    assert failed == [SUPPLIER_INACTIVE]


def test_idempotency_key_already_consumed_blocks(db_session):
    idempotency.consume_key(db_session, "used-key", execution_ref="PO-2026-0001")
    db_session.commit()
    failed = check_preconditions(db_session, _decision(idempotency_key="used-key"))
    assert failed == [IDEMPOTENCY_KEY_CONSUMED]


# --- the re-check-at-execution-time scenarios ---

def test_duplicate_open_po_blocks_a_second_execution_for_the_same_sku(db_session):
    supplier = _supplier(db_session)
    product = _product(db_session, supplier)

    d1 = _decision(product_id=product.id, supplier_id=supplier.id, idempotency_key="k1")
    result1 = execute_decision(db_session, d1)
    assert result1.ok
    assert result1.execution_ref is not None

    d2 = _decision(product_id=product.id, supplier_id=supplier.id, idempotency_key="k2")
    result2 = execute_decision(db_session, d2)
    assert not result2.ok
    assert result2.failed_precondition == DUPLICATE_OPEN_PO


def test_idempotency_key_blocks_a_replay(db_session):
    supplier = _supplier(db_session)
    product = _product(db_session, supplier)

    decision = _decision(product_id=product.id, supplier_id=supplier.id, idempotency_key="replay-key")
    first = execute_decision(db_session, decision)
    assert first.ok

    # A replay of the identical decision must not create a second PO. It is
    # also, correctly, blocked by the duplicate-open-PO guard -- the first
    # execution's PO is still open -- which is itself the intended layered
    # defence (AD-15): either guard alone is sufficient to stop the replay.
    replay = execute_decision(db_session, decision)
    assert not replay.ok

    from src.backend.models import PurchaseOrder
    assert db_session.query(PurchaseOrder).count() == 1


def test_need_already_resolved_when_delivery_arrives_during_approval_window(db_session):
    """A manager approves a replenishment hours after it was proposed; in the
    meantime a delivery arrived and resolved the need. The executor must
    refuse rather than order anyway (18-INTEGRATION-AND-TESTING.md §4.6).
    """
    supplier = _supplier(db_session)
    product = _product(db_session, supplier, on_hand=4, reorder_point=10)

    decision = _decision(product_id=product.id, supplier_id=supplier.id, idempotency_key="k-need")

    # Proposal-time preconditions were clear.
    assert check_preconditions(db_session, decision) == []

    # A delivery arrives before the approval is acted on.
    inbound_po = create_purchase_order(
        db_session, supplier_id=supplier.id,
        items=[{"product_id": product.id, "quantity_ordered": 10, "unit_cost": 80.0}],
    )
    inbound_po.status = POStatus.submitted
    db_session.commit()
    receive_purchase_order(inbound_po.id, db_session)  # 4 -> 14 on hand

    result = execute_decision(db_session, decision)
    assert not result.ok
    assert result.failed_precondition == NEED_ALREADY_RESOLVED
