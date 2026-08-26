"""Signal Engine orchestration and lifecycle management (WS-3).

15-SHARED-CONTRACTS.md §2.3 / §3.1 / §6.
Orchestrates detector execution, deduplication, state transitions, and
event publication for all seven anomaly classes.
"""
import json
from typing import Any, Optional

import structlog
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.backend.database import SessionLocal
from src.backend.models_analytics import Signal
from src.core import clock, events
from src.core.ids import next_id
from src.signals.dedup import dedup_key_for
from src.signals.detectors import ALL_DETECTORS, SignalCandidate

logger = structlog.get_logger()


def raise_signal(
    db: Session,
    *,
    signal_type: str,
    severity: str,
    product_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    po_id: Optional[int] = None,
    detected_from: str,
    evidence: dict[str, Any],
    sufficiency: str = "sufficient",
    dedup_key: Optional[str] = None,
) -> Signal:
    """Record a newly detected signal or update an existing open signal (dedup).

    If an open signal with the same dedup key already exists, updates its
    timestamp, severity, and evidence payload instead of inserting a duplicate row.
    Publishes a ``signal.raised`` event on the in-process bus.
    """
    final_dedup_key = dedup_key or dedup_key_for(
        signal_type, product_id=product_id, supplier_id=supplier_id, po_id=po_id
    )

    # Check for existing open signal with the same dedup_key
    existing_open = (
        db.query(Signal)
        .filter(
            Signal.dedup_key == final_dedup_key,
            Signal.status == "open",
        )
        .first()
    )

    evidence_json = json.dumps(evidence) if isinstance(evidence, dict) else str(evidence)

    if existing_open:
        existing_open.severity = severity
        existing_open.detected_from = detected_from
        existing_open.evidence = evidence_json
        existing_open.sufficiency = sufficiency
        existing_open.raised_at = clock.now()
        db.commit()
        db.refresh(existing_open)
        signal = existing_open
    else:
        sig_ref = next_id("SIG")
        signal = Signal(
            signal_id=sig_ref,
            signal_type=signal_type,
            severity=severity,
            product_id=product_id,
            supplier_id=supplier_id,
            po_id=po_id,
            raised_at=clock.now(),
            detected_from=detected_from,
            evidence=evidence_json,
            sufficiency=sufficiency,
            dedup_key=final_dedup_key,
            status="open",
            resolution=None,
        )
        db.add(signal)
        db.commit()
        db.refresh(signal)

    # Emit synchronous event
    events.emit(
        "signal.raised",
        {
            "signal_id": signal.signal_id,
            "signal_type": signal.signal_type,
            "product_id": signal.product_id,
            "supplier_id": signal.supplier_id,
            "po_id": signal.po_id,
            "severity": signal.severity,
        },
    )

    return signal


def resolve_signal(
    db: Session,
    signal_id: str,
    resolution: Optional[str] = None,
) -> Optional[Signal]:
    """Resolve an open signal with a recorded reason and emit ``signal.resolved``."""
    query = db.query(Signal)
    if signal_id.startswith("SIG-"):
        signal = query.filter(Signal.signal_id == signal_id).first()
    elif signal_id.isdigit():
        signal = query.filter(Signal.id == int(signal_id)).first()
    else:
        signal = query.filter(Signal.signal_id == signal_id).first()

    if not signal:
        return None

    signal.status = "resolved"
    signal.resolution = resolution or "Resolved by operator"
    db.commit()
    db.refresh(signal)

    events.emit(
        "signal.resolved",
        {
            "signal_id": signal.signal_id,
            "resolution": signal.resolution,
        },
    )

    return signal


def get_signal(db: Session, signal_id: str) -> Optional[Signal]:
    """Fetch a single signal by its business identifier (SIG-000045) or database ID."""
    if signal_id.startswith("SIG-"):
        return db.query(Signal).filter(Signal.signal_id == signal_id).first()
    if signal_id.isdigit():
        return db.query(Signal).filter((Signal.id == int(signal_id)) | (Signal.signal_id == signal_id)).first()
    return db.query(Signal).filter(Signal.signal_id == signal_id).first()


def list_signals(
    db: Session,
    *,
    status: Optional[str] = None,
    signal_type: Optional[str] = None,
    severity: Optional[str] = None,
    product_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    po_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Signal]:
    """Filter signals with pagination ordered by most recently raised."""
    q = db.query(Signal)

    if status:
        q = q.filter(Signal.status == status)
    if signal_type:
        q = q.filter(Signal.signal_type == signal_type)
    if severity:
        q = q.filter(Signal.severity == severity)
    if product_id is not None:
        q = q.filter(Signal.product_id == product_id)
    if supplier_id is not None:
        q = q.filter(Signal.supplier_id == supplier_id)
    if po_id is not None:
        q = q.filter(Signal.po_id == po_id)

    return q.order_by(desc(Signal.raised_at)).offset(offset).limit(limit).all()


def run_detectors(
    db: Session,
    *,
    product_ids: Optional[list[int]] = None,
) -> list[Signal]:
    """Execute anomaly detectors and persist/update resulting signals.

    If ``product_ids`` is specified, product-scoped detectors run only for
    those products.
    """
    candidates: list[SignalCandidate] = []

    # Product-scoped detectors
    product_detectors = [
        ALL_DETECTORS["threshold_breach"],
        ALL_DETECTORS["projected_breach"],
        ALL_DETECTORS["config_drift"],
        ALL_DETECTORS["capital_drag"],
        ALL_DETECTORS["data_insufficient"],
    ]

    if product_ids is not None:
        for pid in product_ids:
            for d in product_detectors:
                c = d.detect(db, pid)
                if c:
                    candidates.append(c)
    else:
        for d in product_detectors:
            candidates.extend(d.detect_all(db))

    # PO and Supplier detectors (run on full scans or when not restricting to specific products)
    if product_ids is None:
        candidates.extend(ALL_DETECTORS["po_overdue"].detect_all(db))
        candidates.extend(ALL_DETECTORS["supplier_drift"].detect_all(db))

    raised: list[Signal] = []
    for c in candidates:
        sig = raise_signal(
            db,
            signal_type=c.signal_type,
            severity=c.severity,
            product_id=c.product_id,
            supplier_id=c.supplier_id,
            po_id=c.po_id,
            detected_from=c.detected_from,
            evidence=c.evidence,
            sufficiency=c.sufficiency,
            dedup_key=c.dedup_key,
        )
        raised.append(sig)

    return raised


# --- Event Bus Handlers -------------------------------------------------------

_session_factory = SessionLocal


def set_session_factory(factory) -> None:
    """Override database session factory (useful for isolated tests)."""
    global _session_factory
    _session_factory = factory


def _get_session(payload: Optional[dict] = None) -> tuple[Session, bool]:
    """Get session and whether it should be closed by the handler."""
    if payload and "db" in payload and payload["db"] is not None:
        return payload["db"], False
    return _session_factory(), True


def _on_stock_movement_recorded(payload: dict) -> None:
    """Event handler for ``stock.movement_recorded``."""
    product_id = payload.get("product_id")
    if product_id is None:
        return
    session, should_close = _get_session(payload)
    try:
        run_detectors(session, product_ids=[int(product_id)])
    except Exception as exc:
        logger.exception("signal_handler_failed", event="stock.movement_recorded", error=str(exc))
    finally:
        if should_close:
            session.close()


def _on_stock_level_changed(payload: dict) -> None:
    """Event handler for ``stock.level_changed``."""
    product_id = payload.get("product_id")
    if product_id is None:
        return
    session, should_close = _get_session(payload)
    try:
        run_detectors(session, product_ids=[int(product_id)])
    except Exception as exc:
        logger.exception("signal_handler_failed", event="stock.level_changed", error=str(exc))
    finally:
        if should_close:
            session.close()


def _on_po_received(payload: dict) -> None:
    """Event handler for ``po.received`` — resolves open overdue signals."""
    po_id = payload.get("po_id")
    if po_id is None:
        return
    session, should_close = _get_session(payload)
    try:
        dedup_key = dedup_key_for("po_overdue", po_id=int(po_id))
        open_signals = (
            session.query(Signal)
            .filter(
                Signal.dedup_key == dedup_key,
                Signal.status == "open",
            )
            .all()
        )
        for sig in open_signals:
            resolve_signal(session, sig.signal_id, resolution=f"Purchase order {po_id} received")
    except Exception as exc:
        logger.exception("signal_handler_failed", event="po.received", error=str(exc))
    finally:
        if should_close:
            session.close()


def _on_decision_executed(payload: dict) -> None:
    """Event handler for ``decision.executed``."""
    signal_id = payload.get("signal_id")
    decision_id = payload.get("decision_id")
    if not signal_id:
        return
    session, should_close = _get_session(payload)
    try:
        resolve_signal(
            session,
            signal_id,
            resolution=f"Resolved by decision execution ({decision_id})",
        )
    except Exception as exc:
        logger.exception("signal_handler_failed", event="decision.executed", error=str(exc))
    finally:
        if should_close:
            session.close()


def setup_event_handlers() -> None:
    """Register all signal engine event subscribers on the bus."""
    events.subscribe("stock.movement_recorded", _on_stock_movement_recorded)
    events.subscribe("stock.level_changed", _on_stock_level_changed)
    events.subscribe("po.received", _on_po_received)
    events.subscribe("decision.executed", _on_decision_executed)
