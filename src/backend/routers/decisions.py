"""Decisions REST API router — WS-4.

15-SHARED-CONTRACTS.md §12 / 12-DATA-AND-API-CHANGES.md §5.2.
Provides read-only access to the append-only decisions ledger.
There is NO POST endpoint on /api/decisions — decisions are created
by the pipeline/governance engine, never directly via external HTTP POST.
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.backend.contracts import success_envelope
from src.backend.database import get_db
from src.backend.models_analytics import AgentRun
from src.backend.models_governance import Decision
from src.governance.decisions import get_decision
from src.governance.ledger import format_decision_record, list_decisions

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


@router.get("", response_model=None)
def get_decisions(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by decision status"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    actor: Optional[str] = Query(None, description="Filter by actor"),
    signal_id: Optional[str] = Query(None, description="Filter by originating signal ID"),
    run_id: Optional[str] = Query(None, description="Filter by agent run ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List decisions from the immutable ledger."""
    decisions = list_decisions(
        db,
        status=status_filter,
        action_type=action_type,
        actor=actor,
        signal_id=signal_id,
        run_id=run_id,
        limit=limit,
        offset=offset,
    )

    data = [format_decision_record(d) for d in decisions]
    return success_envelope(
        data=data,
        provenance={"decisions": "retrieved"},
        data_disclosure="synthetic",
    )


@router.get("/{decision_id}", response_model=None)
def get_decision_by_id(
    decision_id: str,
    db: Session = Depends(get_db),
):
    """Get full audit details for a specific decision."""
    decision = get_decision(db, decision_id)
    if decision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision '{decision_id}' not found",
        )

    return success_envelope(
        data=format_decision_record(decision),
        provenance={"decision": "retrieved"},
        data_disclosure="synthetic",
    )


@router.get("/{decision_id}/run", response_model=None)
def get_decision_run(
    decision_id: str,
    db: Session = Depends(get_db),
):
    """Get the node execution trace and telemetry from the linked agent run."""
    decision = get_decision(db, decision_id)
    if decision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision '{decision_id}' not found",
        )

    if not decision.run_id:
        return success_envelope(
            data={"run": None, "message": "Decision was not created by an agent run"},
            provenance={"run": "retrieved"},
            data_disclosure="synthetic",
        )

    run = db.query(AgentRun).filter(AgentRun.run_id == decision.run_id).first()
    if run is None:
        return success_envelope(
            data={
                "run_id": decision.run_id,
                "node_trace": None,
                "status": "not_found",
            },
            provenance={"run": "retrieved"},
            data_disclosure="synthetic",
        )

    node_trace = None
    if run.node_trace:
        try:
            node_trace = json.loads(run.node_trace)
        except Exception:
            node_trace = run.node_trace

    run_data = {
        "id": run.id,
        "run_id": run.run_id,
        "trigger": run.trigger,
        "signal_id": run.signal_id,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "node_trace": node_trace,
        "llm_calls": run.llm_calls,
        "llm_tokens": run.llm_tokens,
        "llm_errors": run.llm_errors,
        "llm_numeric_violation": run.llm_numeric_violation,
        "violation_detail": run.violation_detail,
        "messages_count": run.messages_count,
        "error": run.error,
    }

    return success_envelope(
        data=run_data,
        provenance={"run": "retrieved"},
        data_disclosure="synthetic",
    )
