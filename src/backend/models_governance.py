"""Governance tables — WS-0 owns the schema; WS-4/5/8 write rows.

15-SHARED-CONTRACTS.md §3 maps ``decisions``, ``approvals`` and
``autonomy_policies`` to this module.

The decisions table carries a single 12-value ``status`` column (∈
vocab.DECISION_STATUS). It deliberately has NO ``analysis_status`` column: the
four-value graded analysis_status is a *derived* projection produced by
``vocab.project_analysis_status`` (§2.5), not stored. Same conventions as the rest
of WS-0: String not Enum, explicit ``clock.now()`` timestamps (no database-side default),
string refs between new tables.
"""
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from src.backend.database import Base

USERS_ID_FK = "users.id"


class Decision(Base):
    """An agent decision and its full audit trail (§3.2). ``decision_id`` is DEC-000123."""

    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(String(20), unique=True, nullable=False, index=True)
    signal_id = Column(String(20), nullable=True, index=True)   # string ref
    run_id = Column(String(20), nullable=True, index=True)      # string ref (RUN-000078)
    action_type = Column(String(30), nullable=False)            # ∈ vocab.ACTION_TYPES
    status = Column(String(20), nullable=False, index=True)     # ∈ vocab.DECISION_STATUS (12 values)
    actor = Column(String(40), nullable=False)                  # "agent:replenishment" | "user:3" | "system"
    proposed_at = Column(DateTime, nullable=False)              # clock.now()
    decided_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    inputs = Column(Text, nullable=True)                        # JSON
    computation = Column(Text, nullable=True)                   # JSON
    policy_citation = Column(Text, nullable=True)               # verbatim manual sentence
    escalation_reason = Column(String(30), nullable=True)       # ∈ vocab.ESCALATION_REASONS
    system_objection = Column(Text, nullable=True)
    autonomy_mode = Column(String(12), nullable=False)          # ∈ vocab.AUTONOMY_MODES
    execution_ref = Column(String(20), nullable=True)           # PO-2026-0042
    reversal_of = Column(String(20), nullable=True)             # another decision_id
    provenance = Column(Text, nullable=True)                    # JSON: field -> ∈ vocab.PROVENANCE


class Approval(Base):
    """A human approval request for a decision (§3.3). ``approval_id`` is APR-000012."""

    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    approval_id = Column(String(20), unique=True, nullable=False, index=True)
    decision_id = Column(String(20), nullable=False, index=True)  # string ref to decisions.decision_id
    requested_at = Column(DateTime, nullable=False)             # clock.now()
    requested_from_role = Column(String(20), nullable=False)    # "manager"
    decided_by_user_id = Column(Integer, ForeignKey(USERS_ID_FK), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    outcome = Column(String(12), nullable=True)                 # approved|rejected|countered|expired
    counter_payload = Column(Text, nullable=True)               # JSON
    rationale = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False)               # clock.now() + SLA
    sla_breached = Column(Boolean, default=False, nullable=False)


class AutonomyPolicy(Base):
    """The policy envelope that bounds autonomous action (§ doc 12)."""

    __tablename__ = "autonomy_policies"

    id = Column(Integer, primary_key=True, index=True)
    scope_type = Column(String(20), nullable=False)             # global|category|product|supplier
    scope_value = Column(String(40), nullable=True)
    mode = Column(String(20), nullable=False)                   # ∈ vocab.AUTONOMY_MODES
    max_order_value = Column(Float, nullable=True)
    max_orders_per_hour = Column(Integer, nullable=True)
    max_value_per_day = Column(Float, nullable=True)
    min_sale_events = Column(Integer, default=10)
    min_history_days = Column(Integer, default=30)
    safety_stock_days = Column(Integer, default=2)
    drift_tolerance_pct = Column(Float, default=20.0)
    kill_switch_engaged = Column(Boolean, default=False, nullable=False)
    kill_switch_reason = Column(Text, nullable=True)
    kill_switch_by_user_id = Column(Integer, ForeignKey(USERS_ID_FK), nullable=True)
    consecutive_failures = Column(Integer, default=0)
    updated_at = Column(DateTime, nullable=True)                # clock.now()
    updated_by_user_id = Column(Integer, ForeignKey(USERS_ID_FK), nullable=True)
