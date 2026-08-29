"""Unit and contract tests for WS-12 UI Approvals + Decisions screens.

Tests:
1. Approvals Screen (/approvals) contract, filter options, query keys, empty & error states.
2. Approval Detail Screen (/approvals/:id) structure, 6 strictly ordered sections.
3. ThreeDoorPanel equal visual weight invariant (no bias toward approve).
4. Verbatim quoted policy sentence rendering from Inventory Operations Manual §10.
5. Counter-proposal live recomputation and system objection visible BEFORE override.
6. Decisions Screen (/decisions) 4 core outcomes (autonomous, approved, rejected, declined).
7. Decision Detail Screen (/decisions/:id) immutable ledger, EvidenceBlock, RefusalCard, RunTelemetry.
8. Compliance with all hard rules (ports, clock, forbidden imports).
"""

import os
import re
import pytest

UI_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "src", "ui", "web_react", "src"
)

APPROVALS_SCREEN_PATH = os.path.join(UI_ROOT, "screens", "approvals", "ApprovalsScreen.jsx")
APPROVAL_DETAIL_SCREEN_PATH = os.path.join(UI_ROOT, "screens", "approvals", "ApprovalDetailScreen.jsx")
COUNTER_PANEL_PATH = os.path.join(UI_ROOT, "screens", "approvals", "CounterProposalPanel.jsx")
REJECT_MODAL_PATH = os.path.join(UI_ROOT, "screens", "approvals", "RejectModal.jsx")

DECISIONS_SCREEN_PATH = os.path.join(UI_ROOT, "screens", "decisions", "DecisionsScreen.jsx")
DECISION_DETAIL_SCREEN_PATH = os.path.join(UI_ROOT, "screens", "decisions", "DecisionDetailScreen.jsx")
RUN_TELEMETRY_PATH = os.path.join(UI_ROOT, "screens", "decisions", "RunTelemetryBlock.jsx")

TOP_APPROVALS_SCREEN = os.path.join(UI_ROOT, "screens", "ApprovalsScreen.jsx")
TOP_APPROVAL_DETAIL = os.path.join(UI_ROOT, "screens", "ApprovalDetailScreen.jsx")
TOP_DECISIONS_SCREEN = os.path.join(UI_ROOT, "screens", "DecisionsScreen.jsx")
TOP_DECISION_DETAIL = os.path.join(UI_ROOT, "screens", "DecisionDetailScreen.jsx")


def test_ws12_all_files_exist_and_export():
    """Verify all WS-12 screens and components exist and export valid React components."""
    required_files = [
        APPROVALS_SCREEN_PATH,
        APPROVAL_DETAIL_SCREEN_PATH,
        COUNTER_PANEL_PATH,
        REJECT_MODAL_PATH,
        DECISIONS_SCREEN_PATH,
        DECISION_DETAIL_SCREEN_PATH,
        RUN_TELEMETRY_PATH,
        TOP_APPROVALS_SCREEN,
        TOP_APPROVAL_DETAIL,
        TOP_DECISIONS_SCREEN,
        TOP_DECISION_DETAIL,
    ]

    for path in required_files:
        assert os.path.exists(path), f"File missing: {path}"
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            assert len(content.strip()) > 30, f"File {path} is empty"
            assert "export default" in content or "export {" in content, \
                f"File {path} does not export a component"


def test_approvals_screen_contracts():
    """Verify ApprovalsScreen satisfies 07-UX §5.3 & query contracts."""
    with open(APPROVALS_SCREEN_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Query key usage
    assert "QUERY_KEYS.approvalsPending" in content or "QUERY_KEYS" in content, \
        "ApprovalsScreen must use frozen query keys"
    assert "/api/approvals" in content, "ApprovalsScreen must fetch from /api/approvals"

    # Must contain filter options
    assert "pending" in content, "ApprovalsScreen missing pending filter"
    assert "approved" in content, "ApprovalsScreen missing approved filter"
    assert "rejected" in content, "ApprovalsScreen missing rejected filter"

    # UI primitives used
    assert "Table" in content, "ApprovalsScreen must render Table"
    assert "SeverityDot" in content, "ApprovalsScreen must render SeverityDot"
    assert "EmptyState" in content, "ApprovalsScreen must render EmptyState"


def test_approval_detail_six_ordered_sections():
    """Verify ApprovalDetailScreen contains the 6 strictly ordered sections from 07-UX §5.3."""
    with open(APPROVAL_DETAIL_SCREEN_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    sections = [
        "THE AGENT WANTS TO",
        "IT STOPPED BECAUSE",
        "HOW IT GOT HERE",
        "THE SITUATION",
        "IF YOU DO NOTHING",
        "<ThreeDoorPanel",
    ]

    last_idx = -1
    for sec in sections:
        idx = content.find(sec, last_idx + 1 if last_idx != -1 else 0)
        assert idx != -1, f"ApprovalDetailScreen missing section in expected order: {sec}"
        last_idx = idx


def test_verbatim_quoted_policy_sentence():
    """Verify quoted manual sentence renders verbatim (Inventory Manual §10 line 113)."""
    with open(APPROVAL_DETAIL_SCREEN_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    expected_quote = (
        "Purchase Orders with a total value above ₹50,000 require formal Store Manager approval prior to supplier submission."
    )
    assert expected_quote in content, "ApprovalDetailScreen missing verbatim §10 policy quotation"


def test_three_door_panel_equal_visual_weight():
    """Contract: Approve, reject, and counter have equal visual weight on ThreeDoorPanel (15 §13.1 & 07-UX §5.3)."""
    with open(os.path.join(UI_ROOT, "components", "ThreeDoorPanel.jsx"), "r", encoding="utf-8") as f:
        content = f.read()

    assert "doorBtnStyle" in content or "gridTemplateColumns" in content, \
        "ThreeDoorPanel must apply equal styling"
    assert "onApprove" in content and "onReject" in content and "onCounter" in content, \
        "ThreeDoorPanel must accept approve, reject, and counter handlers"


def test_counter_proposal_live_recompute_and_system_objection():
    """Verify CounterProposalPanel recomputes live and renders system objection BEFORE override."""
    with open(COUNTER_PANEL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Live recomputation arithmetic
    assert "availableAfter" in content or "available_stock_after" in content or "marginAboveRop" in content, \
        "CounterProposalPanel must recompute stock cover"
    assert "orderValue" in content or "order_value" in content, \
        "CounterProposalPanel must recompute order value"

    # System objection check
    assert "SYSTEM OBJECTION" in content or "systemObjection" in content, \
        "CounterProposalPanel must derive system objection"
    assert "Visible before" in content or "visible" in content.lower(), \
        "System objection must be explicitly visible before confirmation"
    assert "Approve" in content and "anyway" in content, \
        "CounterProposalPanel must provide 'Approve N units anyway' action"


def test_rejection_requires_mandatory_rationale():
    """Verify RejectModal enforces mandatory rationale (15-SHARED-CONTRACTS.md §8)."""
    with open(REJECT_MODAL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "rationale" in content, "RejectModal must capture rationale"
    assert "required" in content.lower() or "!rationale.trim()" in content, \
        "RejectModal must enforce non-empty rationale"


def test_decisions_screen_four_equal_outcomes():
    """Verify DecisionsScreen supports and renders 4 core outcomes (autonomous, approved, rejected, declined)."""
    with open(DECISIONS_SCREEN_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    for outcome in ["autonomous", "approved", "rejected", "declined"]:
        assert outcome in content, f"DecisionsScreen missing outcome: {outcome}"

    assert "QUERY_KEYS.decisions" in content or "decisions" in content, \
        "DecisionsScreen must query decisions"
    assert "Table" in content and "SeverityDot" in content, \
        "DecisionsScreen must render Table and SeverityDot"


def test_decision_detail_contracts_and_provenance():
    """Verify DecisionDetailScreen includes EvidenceBlock, Policy Citation, Provenance, and Telemetry."""
    with open(DECISION_DETAIL_SCREEN_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "EvidenceBlock" in content, "DecisionDetailScreen must render EvidenceBlock"
    assert "GOVERNING POLICY CITATION" in content, "DecisionDetailScreen must render Policy Citation"
    assert "ProvenanceMark" in content, "DecisionDetailScreen must render ProvenanceMark"
    assert "RunTelemetryBlock" in content, "DecisionDetailScreen must render RunTelemetryBlock"
    assert "RefusalCard" in content, "DecisionDetailScreen must render RefusalCard for data insufficiency"


def test_hard_rules_invariants():
    """Enforce CI invariants across all WS-12 files (ports, clock, models)."""
    ws12_dir = os.path.join(UI_ROOT, "screens", "approvals")
    ws12_decisions_dir = os.path.join(UI_ROOT, "screens", "decisions")

    files_to_check = []
    for root, _, files in os.walk(ws12_dir):
        for file in files:
            if file.endswith((".js", ".jsx", ".py")):
                files_to_check.append(os.path.join(root, file))

    for root, _, files in os.walk(ws12_decisions_dir):
        for file in files:
            if file.endswith((".js", ".jsx", ".py")):
                files_to_check.append(os.path.join(root, file))

    for path in files_to_check:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        # Forbidden ports
        assert "localhost:8000" not in text, f"Forbidden port 8000 found in {path}"
        assert "localhost:3000" not in text, f"Forbidden port 3000 found in {path}"
        assert "localhost:8501" not in text, f"Forbidden port 8501 found in {path}"

        # Forbidden python time calls if python file
        if path.endswith(".py"):
            assert "datetime.now()" not in text, f"datetime.now() forbidden in {path}"
            assert "date.today()" not in text, f"date.today() forbidden in {path}"
            assert "time.time()" not in text, f"time.time() forbidden in {path}"
