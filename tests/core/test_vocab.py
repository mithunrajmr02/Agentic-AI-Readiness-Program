"""Contract tests for src/core/vocab.py.

These assert the FROZEN vocabularies verbatim (15-SHARED-CONTRACTS.md §2.4) and
the 12→4 analysis-status projection (§2.5). Seventeen downstream workstreams
build against these exact values; a single edited tuple member must fail here.
"""
from src.core import vocab


def test_signal_types_frozen():
    assert vocab.SIGNAL_TYPES == (
        "threshold_breach",
        "projected_breach",
        "po_overdue",
        "config_drift",
        "supplier_drift",
        "capital_drag",
        "data_insufficient",
    )


def test_severities_frozen():
    assert vocab.SEVERITIES == ("critical", "high", "medium", "low")


def test_decision_status_frozen():
    assert vocab.DECISION_STATUS == (
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


def test_autonomy_modes_frozen():
    assert vocab.AUTONOMY_MODES == ("off", "shadow", "assisted", "autonomous")


def test_action_types_frozen():
    assert vocab.ACTION_TYPES == (
        "raise_po",
        "adjust_reorder_point",
        "adjust_reorder_quantity",
        "switch_supplier",
        "consolidate_po",
        "expedite_po",
        "no_action",
    )


def test_escalation_reasons_frozen():
    assert vocab.ESCALATION_REASONS == (
        "value_threshold",
        "insufficient_evidence",
        "non_cheapest_supplier",
        "config_change",
        "blast_radius",
        "policy_off",
        "kill_switch",
    )


def test_sufficiency_frozen():
    assert vocab.SUFFICIENCY == ("sufficient", "thin", "insufficient", "none")


def test_provenance_frozen():
    assert vocab.PROVENANCE == ("computed", "retrieved", "generated")


def test_data_disclosure_frozen():
    assert vocab.DATA_DISCLOSURE == ("synthetic", "mixed", "real")


def test_metric_tiers_frozen():
    assert vocab.METRIC_TIERS == ("T1", "T2", "T3")


# --- project_analysis_status: the 12→4 display/compatibility projection (§2.5) ---
# The 4 graded values are: analyzing, reorder_required, healthy, complete.

def test_analysis_status_analyzing_group():
    for status in ("proposed", "policy_checked", "executing"):
        assert vocab.project_analysis_status(status, "raise_po") == "analyzing"


def test_analysis_status_reorder_required_group():
    for status in ("pending_approval", "approved", "auto_approved"):
        assert vocab.project_analysis_status(status, "raise_po") == "reorder_required"


def test_analysis_status_executed_with_action_is_reorder_required():
    assert vocab.project_analysis_status("executed", "raise_po") == "reorder_required"


def test_analysis_status_executed_no_action_is_healthy():
    assert vocab.project_analysis_status("executed", "no_action") == "healthy"


def test_analysis_status_terminal_non_executed_group_is_complete():
    for status in ("rejected", "expired", "failed", "countered"):
        assert vocab.project_analysis_status(status, "raise_po") == "complete"


def test_analysis_status_insufficient_data_is_complete():
    assert vocab.project_analysis_status("insufficient_data", "no_action") == "complete"


def test_analysis_status_only_ever_returns_the_four_graded_values():
    graded = {"analyzing", "reorder_required", "healthy", "complete"}
    for status in vocab.DECISION_STATUS:
        for action in vocab.ACTION_TYPES:
            assert vocab.project_analysis_status(status, action) in graded
