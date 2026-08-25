"""Analytics & telemetry tables — WS-0 owns the schema; WS-3/8/10/17 write rows.

15-SHARED-CONTRACTS.md §3 maps ``signals``, ``agent_runs`` and
``metric_snapshots`` to this module. Conventions enforced here:
  * no SQLAlchemy ``Enum`` — every status-like column is a plain ``String``
    (the frozen enum cage, CI invariant #2);
  * no database-side default on any timestamp column — callers pass
    ``clock.now()`` explicitly (CI invariant #3);
  * references to *new* tables are string business-refs (no FK constraint);
    integer FKs point only at the pre-existing tables.
"""
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from src.backend.database import Base

PRODUCTS_ID_FK = "products.id"
SUPPLIERS_ID_FK = "suppliers.id"
PURCHASE_ORDERS_ID_FK = "purchase_orders.id"
USERS_ID_FK = "users.id"


class Signal(Base):
    """A detected condition worth acting on (§3.1). ``signal_id`` is SIG-000045."""

    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(String(20), unique=True, nullable=False, index=True)
    signal_type = Column(String(20), nullable=False)   # ∈ vocab.SIGNAL_TYPES
    severity = Column(String(10), nullable=False)       # ∈ vocab.SEVERITIES
    product_id = Column(Integer, ForeignKey(PRODUCTS_ID_FK), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey(SUPPLIERS_ID_FK), nullable=True, index=True)
    po_id = Column(Integer, ForeignKey(PURCHASE_ORDERS_ID_FK), nullable=True, index=True)
    raised_at = Column(DateTime, nullable=False)        # clock.now()
    detected_from = Column(String(255), nullable=False)  # human-readable provenance
    evidence = Column(Text, nullable=True)              # JSON string
    sufficiency = Column(String(12), nullable=False)    # ∈ vocab.SUFFICIENCY
    dedup_key = Column(String(100), nullable=False, index=True)
    status = Column(String(12), nullable=False)         # open|superseded|resolved|expired
    resolution = Column(Text, nullable=True)


class AgentRun(Base):
    """One execution of the replenishment graph (§ doc 12). ``run_id`` is RUN-000078."""

    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(20), unique=True, nullable=False, index=True)
    trigger = Column(String(20), nullable=False)
    triggered_by_user_id = Column(Integer, ForeignKey(USERS_ID_FK), nullable=True)
    signal_id = Column(String(20), nullable=True, index=True)  # string ref to signals.signal_id
    graph_thread_id = Column(String(60), nullable=True)
    started_at = Column(DateTime, nullable=False)       # clock.now()
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False)         # running|suspended|completed|failed
    node_trace = Column(Text, nullable=True)            # JSON string
    llm_calls = Column(Integer, default=0)
    llm_tokens = Column(Integer, default=0)
    llm_errors = Column(Integer, default=0)
    llm_numeric_violation = Column(Boolean, default=False)
    violation_detail = Column(Text, nullable=True)
    messages_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)


class MetricSnapshot(Base):
    """A computed impact metric at a point in time (§ doc 12).

    ``value`` is nullable because every T3 metric stores ``None`` (CI invariant
    #8) and any insufficient/none computation is ``None`` (invariant #9) — never 0.
    """

    __tablename__ = "metric_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    metric_key = Column(String(20), nullable=False, index=True)
    value = Column(Float, nullable=True)                # None for T3 / insufficient
    computed_at = Column(DateTime, nullable=False)      # clock.now()
    window_start = Column(DateTime, nullable=True)
    window_end = Column(DateTime, nullable=True)
    scope_type = Column(String(20), nullable=False)
    scope_value = Column(String(40), nullable=True)
    tier = Column(String(4), nullable=False)            # ∈ vocab.METRIC_TIERS
    data_disclosure = Column(String(12), nullable=False)  # ∈ vocab.DATA_DISCLOSURE
