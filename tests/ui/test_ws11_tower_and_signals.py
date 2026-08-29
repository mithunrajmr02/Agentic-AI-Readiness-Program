"""Tests for WS-11 UI Control Tower and Signals screens.

Validates:
- ControlTowerScreen.jsx: NEEDS YOU, HANDLED WHILE YOU WERE AWAY, POSITION SUMMARY, telemetry scan, synthetic disclosure.
- SignalsScreen.jsx: filterable table, search, quick chips, accessible SeverityDot, telemetry scan.
- SignalDetailScreen.jsx: EvidenceBlock arithmetic with section 3 citation, bounded agent narrative, linked decisions, RefusalCard for D4.
- Invariants and contracts from 15-SHARED-CONTRACTS.md section 13 and 07-UX-ARCHITECTURE.md section 5.1-5.2.
"""

import os
import pytest

UI_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "src", "ui", "web_react", "src"
)
SCREENS_DIR = os.path.join(UI_ROOT, "screens")


def test_control_tower_screen_structure():
    screen_path = os.path.join(SCREENS_DIR, "ControlTowerScreen.jsx")
    assert os.path.exists(screen_path), f"ControlTowerScreen.jsx not found at {screen_path}"

    with open(screen_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Priority Zone 1: NEEDS YOU
    assert "NEEDS YOU" in code
    assert "APR-000012" in code
    assert "SIG-000047" in code
    assert "SIG-000046" in code
    assert "Nothing Needs You" in code

    # Proving Zone 2: HANDLED WHILE YOU WERE AWAY
    assert "HANDLED WHILE YOU WERE AWAY" in code
    assert "DEC-000123" in code
    assert "DEC-000124" in code
    assert "ProvenanceMark" in code

    # Context Zone 3: POSITION SUMMARY
    assert "POSITION SUMMARY" in code
    assert "Open Signals" in code
    assert "Pending Approvals" in code
    assert "Total Inventory Value" in code
    assert "threshold_breach" in code and "config_drift" in code

    # Disclosure and Action
    assert "Demonstration Data Disclosure" in code
    assert "Scan Telemetry Now" in code or "scanMutation" in code


def test_signals_screen_structure():
    screen_path = os.path.join(SCREENS_DIR, "SignalsScreen.jsx")
    assert os.path.exists(screen_path), f"SignalsScreen.jsx not found at {screen_path}"

    with open(screen_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "Signals Inbox" in code
    assert "Scan Telemetry Now" in code
    assert "All Signals" in code
    assert "Open Only" in code
    assert "Critical" in code
    assert "Config Drift" in code
    assert "Projected Breach" in code
    assert "PO Overdue" in code
    assert "Data Insufficient" in code
    assert "SeverityDot" in code
    assert "ProvenanceMark" in code
    assert "EmptyState" in code
    assert "Table" in code


def test_signal_detail_screen_structure():
    screen_path = os.path.join(SCREENS_DIR, "SignalDetailScreen.jsx")
    assert os.path.exists(screen_path), f"SignalDetailScreen.jsx not found at {screen_path}"

    with open(screen_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "Back to Signals Inbox" in code
    assert "SeverityDot" in code
    assert "EvidenceBlock" in code
    assert "Inventory Manual" in code
    assert "reorder_point =" in code
    assert "WHAT" in code and "HAPPENING" in code
    assert "ProvenanceMark" in code
    assert "DEC-000123" in code
    assert "DEC-000126" in code and "DEC-000127" in code
    assert "RefusalCard" in code
    assert "Dismiss Signal" in code
    assert "dismissMutation" in code
