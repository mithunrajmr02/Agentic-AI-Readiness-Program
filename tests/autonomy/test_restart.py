"""AD-6's entire justification: the interrupt survives a REAL process
restart, not a mocked one (18-INTEGRATION-AND-TESTING.md §4.3, and the
WS-8 launch brief: "Test the durable interrupt across a REAL process
restart, not a mock").

Two separate `python -c` subprocesses share nothing but the checkpoint and
ledger file paths on disk. Process A runs up to the interrupt and exits;
process B is a fresh interpreter that resumes and completes the write.
If `DurableFileSaver` (checkpoint.py) were merely in-memory, process B
would have no thread history to resume and this would fail outright.
"""
import json
import subprocess
import sys
import textwrap

PRODUCT = {
    "id": 3, "sku": "SKU-ELC-0003", "name": "42-inch Television",
    "cost_price": 600.0, "reorder_point": 20, "supplier_id": 1,
    "stock_level": {"quantity_available": 5, "quantity_reserved": 0},
}

REPLIES = [
    '{"avg_daily_demand":8.0,"demand_trend":"increasing","days_of_stock_remaining":1,'
    '"stockout_risk":"high","forecast_notes":"Critical."}',
    '{"hypotheses":[{"cause":"demand spike","confidence":"high",'
    '"evidence":"avg_daily_demand 8.0"}],"narrative":"A demand spike of 8.0 units/day."}',
    '{"reorder_required":true,"recommended_quantity":100,"urgency":"immediate",'
    '"reason":"Stockout imminent."}',
    '{"supplier_id":1,"quoted_unit_cost":600.0,"total_order_cost":60000.0,'
    '"estimated_lead_time_days":5,"quote_notes":"Bulk order."}',
    "Reorder recommended for the television.",
]

_MOCK_SETUP = """
import json
from unittest.mock import MagicMock, patch
patcher_get = patch("src.agents.multi_agent.agents.requests.get")
patcher_llm = patch("src.agents.multi_agent.agents._llm")
mg = patcher_get.start()
ml = patcher_llm.start()
mg.return_value.status_code = 200
mg.return_value.json.return_value = %(product)s
_replies = %(replies)s
_calls = {"n": 0}
def _side(prompt):
    i = min(_calls["n"], len(_replies) - 1)
    _calls["n"] += 1
    return MagicMock(content=_replies[i])
ml.invoke.side_effect = _side
""" % {"product": json.dumps(PRODUCT), "replies": json.dumps(REPLIES)}


def _run(script: str, ckpt_path, ledger_path, cwd) -> str:
    env_setup = textwrap.dedent(f"""
        import os, sys
        os.environ["STEWARD_CHECKPOINT_DB"] = {str(ckpt_path)!r}
        os.environ["STEWARD_LEDGER_PATH"] = {str(ledger_path)!r}
        sys.path.insert(0, {str(cwd)!r})
    """)
    full = env_setup + _MOCK_SETUP + textwrap.dedent(script)
    proc = subprocess.run(
        [sys.executable, "-c", full],
        cwd=str(cwd), capture_output=True, text=True, timeout=60,
    )
    if proc.returncode != 0:
        raise AssertionError(f"subprocess failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    return proc.stdout


def test_interrupt_survives_a_real_process_restart(tmp_path):
    import os
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ckpt_path = tmp_path / "restart_checkpoints.pkl"
    ledger_path = tmp_path / "restart_ledger.jsonl"

    # Process A: run up to the interrupt, print proof it suspended, exit.
    stage_a = """
        from src.agents.multi_agent.graph import run_pipeline
        result = run_pipeline("manual", product_ids=[3], run_id="RUN-RESTART-01")
        assert "__interrupt__" in result, "process A did not suspend"
        assert result["authority"] == "requires_approval"
        print("STAGE_A_SUSPENDED")
    """
    out_a = _run(stage_a, ckpt_path, ledger_path, repo_root)
    assert "STAGE_A_SUSPENDED" in out_a

    # Process B: a genuinely separate interpreter, no shared memory with A.
    # It only knows the run by its id and the checkpoint file on disk.
    stage_b = """
        from src.agents.multi_agent.graph import resume_pipeline
        from src.agents.multi_agent import ledger as ledger_mod
        final = resume_pipeline("RUN-RESTART-01", {"outcome": "approved", "user_id": 1})
        assert final["decision_status"] == "executed", final.get("decision_status")
        assert final["po_number"], "no PO recorded after resume"
        assert ledger_mod.is_key_consumed(final["idempotency_key"])
        print("STAGE_B_EXECUTED:" + final["po_number"])
    """
    out_b = _run(stage_b, ckpt_path, ledger_path, repo_root)
    assert "STAGE_B_EXECUTED:PO-SIM-" in out_b
