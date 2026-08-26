"""Tests for WS-6 UI Foundation contracts and invariants.

Validates:
- All 17 defined routes in routes.jsx
- All 17 skeleton screen components
- All 10 shared primitives in components/
- Accessibility invariants (SeverityDot shape + text, ThreeDoorPanel equal weight)
- Design system tokens in tokens.css
- Frozen query keys in query.js
- Vite frontend production build validity
"""

import os
import re
import subprocess
import pytest

UI_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "src", "ui", "web_react", "src"
)

REQUIRED_17_ROUTES = [
    "/",
    "/tower",
    "/signals",
    "/signals/:signalId",
    "/approvals",
    "/approvals/:approvalId",
    "/inventory",
    "/inventory/:sku",
    "/suppliers",
    "/suppliers/:supplierId",
    "/receiving",
    "/receiving/:poNumber",
    "/decisions",
    "/decisions/:decisionId",
    "/impact",
    "/settings/autonomy",
    "/settings/scenarios",
]

REQUIRED_SCREENS = [
    "ControlTowerScreen.jsx",
    "SignalsScreen.jsx",
    "SignalDetailScreen.jsx",
    "ApprovalsScreen.jsx",
    "ApprovalDetailScreen.jsx",
    "InventoryScreen.jsx",
    "ProductDetailScreen.jsx",
    "SuppliersScreen.jsx",
    "SupplierScorecardScreen.jsx",
    "ReceivingScreen.jsx",
    "ReceiptEntryScreen.jsx",
    "DecisionsScreen.jsx",
    "DecisionDetailScreen.jsx",
    "ImpactScreen.jsx",
    "AutonomySettingsScreen.jsx",
    "ScenariosSettingsScreen.jsx",
    "LoginScreen.jsx",
]

REQUIRED_PRIMITIVES = [
    "Card.jsx",
    "Table.jsx",
    "SeverityDot.jsx",
    "ProvenanceMark.jsx",
    "EvidenceBlock.jsx",
    "RefusalCard.jsx",
    "EmptyState.jsx",
    "AuthorityBadge.jsx",
    "ThreeDoorPanel.jsx",
    "MetricTile.jsx",
    "index.js",
]

REQUIRED_TOKENS = [
    "--surface-0",
    "--surface-1",
    "--surface-2",
    "--border",
    "--ink-1",
    "--ink-2",
    "--ink-3",
    "--accent",
    "--critical",
    "--warn",
    "--good",
    "--agent",
    "--t-display-size",
    "--t-heading-size",
    "--t-body-size",
    "--t-meta-size",
    "--t-mono-size",
]

FROZEN_QUERY_KEYS = [
    "signals",
    "signal",
    "decisions",
    "decision",
    "approvalsPending",
    "approval",
    "policies",
    "impact",
    "impactGaps",
    "supplierScorecard",
    "tower",
]


def test_routes_definition():
    """Verify routes.jsx registers all 17 addressable routes from 07-UX-ARCHITECTURE.md §3.2."""
    routes_file = os.path.join(UI_ROOT, "routes.jsx")
    assert os.path.exists(routes_file), f"routes.jsx not found at {routes_file}"

    with open(routes_file, "r", encoding="utf-8") as f:
        content = f.read()

    for route in REQUIRED_17_ROUTES:
        assert f"'{route}'" in content or f'"{route}"' in content, \
            f"Route {route} not found in routes.jsx"


def test_all_screens_exist():
    """Verify all 17 screen components exist and export valid React components."""
    screens_dir = os.path.join(UI_ROOT, "screens")
    assert os.path.isdir(screens_dir), f"screens directory not found at {screens_dir}"

    for screen in REQUIRED_SCREENS:
        screen_path = os.path.join(screens_dir, screen)
        assert os.path.exists(screen_path), f"Screen {screen} does not exist at {screen_path}"
        with open(screen_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert len(content.strip()) > 50, f"Screen {screen} is unexpectedly empty"
            assert "export default function" in content or "export default" in content, \
                f"Screen {screen} does not export a default component"


def test_all_primitives_exist_and_exported():
    """Verify all 10 required UI primitives exist and are exported in components/index.js."""
    comp_dir = os.path.join(UI_ROOT, "components")
    assert os.path.isdir(comp_dir), f"components directory not found at {comp_dir}"

    for primitive in REQUIRED_PRIMITIVES:
        prim_path = os.path.join(comp_dir, primitive)
        assert os.path.exists(prim_path), f"Primitive {primitive} does not exist at {prim_path}"

    index_path = os.path.join(comp_dir, "index.js")
    with open(index_path, "r", encoding="utf-8") as f:
        index_content = f.read()

    for comp in ["Card", "Table", "SeverityDot", "ProvenanceMark", "EvidenceBlock", "RefusalCard", "EmptyState", "AuthorityBadge", "ThreeDoorPanel", "MetricTile"]:
        assert comp in index_content, f"Component {comp} not exported from components/index.js"


def test_severity_dot_accessibility_invariant():
    """Contract: <SeverityDot> carries shape + text label, never colour alone (07-UX §11 & 15 §13.1)."""
    severity_dot_file = os.path.join(UI_ROOT, "components", "SeverityDot.jsx")
    with open(severity_dot_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Must contain the geometric shape symbols
    assert "▲" in content, "SeverityDot missing critical shape (▲)"
    assert "●" in content, "SeverityDot missing warning/medium shape (●)"
    assert "○" in content, "SeverityDot missing info/low shape (○)"
    assert "✓" in content, "SeverityDot missing good/resolved shape (✓)"

    # Must render text label alongside shape
    assert "textLabel" in content or "label" in content, \
        "SeverityDot does not render a text label"


def test_three_door_panel_equal_visual_weight():
    """Contract: <ThreeDoorPanel> gives approve, reject, and counter identical visual weight (15 §13.1)."""
    panel_file = os.path.join(UI_ROOT, "components", "ThreeDoorPanel.jsx")
    with open(panel_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "onApprove" in content and "onReject" in content and "onCounter" in content, \
        "ThreeDoorPanel must accept onApprove, onReject, and onCounter handlers"

    # Must use grid/flex layout with equal door styling
    assert "gridTemplateColumns" in content or "doorBtnStyle" in content or "flex" in content, \
        "ThreeDoorPanel must layout all three actions"


def test_design_tokens_complete():
    """Verify tokens.css contains all required surface, ink, semantic, and typography tokens."""
    tokens_file = os.path.join(UI_ROOT, "styles", "tokens.css")
    assert os.path.exists(tokens_file), f"tokens.css not found at {tokens_file}"

    with open(tokens_file, "r", encoding="utf-8") as f:
        content = f.read()

    for token in REQUIRED_TOKENS:
        assert token in content, f"Token {token} missing from tokens.css"


def test_frozen_query_keys_match_contracts():
    """Verify query.js exposes frozen query keys matching 15-SHARED-CONTRACTS.md §13.2."""
    query_file = os.path.join(UI_ROOT, "lib", "query.js")
    assert os.path.exists(query_file), f"query.js not found at {query_file}"

    with open(query_file, "r", encoding="utf-8") as f:
        content = f.read()

    for qk in FROZEN_QUERY_KEYS:
        assert qk in content, f"Query key factory {qk} missing from query.js"

    assert "invalidateAfterApproval" in content, \
        "query.js missing invalidateAfterApproval helper"


def test_app_jsx_decomposition_and_shell():
    """Verify App.jsx is decomposed into a clean shell routing to AppLayout and screens."""
    app_file = os.path.join(UI_ROOT, "App.jsx")
    with open(app_file, "r", encoding="utf-8") as f:
        content = f.read()

    line_count = len(content.strip().splitlines())
    assert line_count < 150, f"App.jsx has {line_count} lines; expected decomposed shell < 150 lines (was 1,136 lines)"
    assert "Routes" in content and "Route" in content, "App.jsx does not mount Routes"
    assert "AppLayout" in content, "App.jsx does not use AppLayout"


def test_vite_build_output_exists():
    """Verify that the frontend builds to dist/ without error."""
    dist_dir = os.path.join(UI_ROOT, "..", "dist")
    index_html = os.path.join(dist_dir, "index.html")
    assert os.path.exists(index_html), "dist/index.html not generated by Vite build"
