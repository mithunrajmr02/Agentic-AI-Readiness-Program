"""Frozen status vocabularies and the analysis-status projection.

15-SHARED-CONTRACTS.md §2.4 / §2.5. These tuples are the enum cage: the system
stores status-like values as plain strings (never SQLAlchemy ``Enum``), and these
are the only permitted members. Seventeen workstreams import them; treat every
tuple here as frozen.
"""

# --- §2.4 Frozen vocabularies (verbatim) --------------------------------------

SIGNAL_TYPES = (
    "threshold_breach",
    "projected_breach",
    "po_overdue",
    "config_drift",
    "supplier_drift",
    "capital_drag",
    "data_insufficient",
)

SEVERITIES = ("critical", "high", "medium", "low")

DECISION_STATUS = (
    "proposed",
    "policy_checked",
    "auto_approved",
    "pending_approval",
    "approved",
    "rejected",
    "countered",
    "executing",
    "executed",
    "failed",
    "expired",
    "insufficient_data",
)

AUTONOMY_MODES = ("off", "shadow", "assisted", "autonomous")

ACTION_TYPES = (
    "raise_po",
    "adjust_reorder_point",
    "adjust_reorder_quantity",
    "switch_supplier",
    "consolidate_po",
    "expedite_po",
    "no_action",
)

ESCALATION_REASONS = (
    "value_threshold",
    "insufficient_evidence",
    "non_cheapest_supplier",
    "config_change",
    "blast_radius",
    "policy_off",
    "kill_switch",
)

SUFFICIENCY = ("sufficient", "thin", "insufficient", "none")

PROVENANCE = ("computed", "retrieved", "generated")

DATA_DISCLOSURE = ("synthetic", "mixed", "real")

METRIC_TIERS = ("T1", "T2", "T3")


# --- §2.5 Analysis-status projection ------------------------------------------

# The four graded values the legacy pipeline / UI understands.
ANALYSIS_STATUS = ("analyzing", "reorder_required", "healthy", "complete")

_ANALYZING = frozenset({"proposed", "policy_checked", "executing"})
_REORDER_REQUIRED = frozenset({"pending_approval", "approved", "auto_approved"})
_COMPLETE = frozenset({"rejected", "expired", "failed", "countered", "insufficient_data"})


def project_analysis_status(decision_status: str, action_type: str) -> str:
    """Map the 12-value internal vocabulary onto the 4 graded values.

    This is a display and compatibility mapping only; nothing in the system
    branches on analysis_status. All internal logic reads the twelve-value
    ``status`` column. ``executed`` is the one status that splits on the action:
    an executed ``no_action`` is a clean bill of health (``healthy``), while an
    executed replenishment action is a reorder that happened (``reorder_required``).

    Being a display projection, it never raises: an unrecognised status maps to
    the safe terminal value ``complete``.
    """
    if decision_status in _ANALYZING:
        return "analyzing"
    if decision_status in _REORDER_REQUIRED:
        return "reorder_required"
    if decision_status == "executed":
        return "healthy" if action_type == "no_action" else "reorder_required"
    if decision_status in _COMPLETE:
        return "complete"
    return "complete"
