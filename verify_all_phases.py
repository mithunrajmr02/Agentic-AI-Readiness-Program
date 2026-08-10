"""
Unified Multi-Phase Runner & Verifier for POC-07 Inventory Management & Procurement System.

Executes and validates:
1. Phase 1 REST API Backend & Unit/API Tests (FastAPI + SQLite)
2. Phase 2 Document Ingestion & RAG Test Suite (ChromaDB + Gemini 2.0 Flash)
3. Generates unified status report
"""

import os
import sys
import subprocess
from datetime import datetime

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
PYTHON_EXE = os.path.join(REPO_ROOT, "phase1", "venv", "Scripts", "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable


def header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def run_phase1_tests():
    header("PHASE 1: Running Automated Test Suite (CRUD REST API)")
    phase1_dir = os.path.join(REPO_ROOT, "phase1")
    cmd = [PYTHON_EXE, "-m", "pytest", "tests/", "-v"]
    print(f"Executing: {' '.join(cmd)} in {phase1_dir}")
    res = subprocess.run(cmd, cwd=phase1_dir)
    return res.returncode == 0


def run_phase2_tests():
    header("PHASE 2: Running Automated Test Suite (RAG Application)")
    cmd = [PYTHON_EXE, "-m", "pytest", "phase2/tests/test_phase2.py", "-v"]
    print(f"Executing: {' '.join(cmd)} in {REPO_ROOT}")
    res = subprocess.run(cmd, cwd=REPO_ROOT)
    return res.returncode == 0


def run_phase2_ingestion():
    header("PHASE 2: Executing Document Ingestion (inventory_manual.md -> ChromaDB)")
    ingest_script = os.path.join(REPO_ROOT, "phase2", "rag", "ingest.py")
    cmd = [PYTHON_EXE, ingest_script]
    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=REPO_ROOT)
    return res.returncode == 0


def generate_submission_artifacts():
    header("Generating Phase 2 Submission Deliverables & Quality Reports")
    artifact_script = os.path.join(REPO_ROOT, "phase2", "generate_submission_artifacts.py")
    cmd = [PYTHON_EXE, artifact_script]
    res = subprocess.run(cmd, cwd=REPO_ROOT)
    return res.returncode == 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    header("STARTING UNIFIED MULTI-PHASE SYSTEM VERIFICATION (POC-07)")
    print(f"Execution Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Environment: {PYTHON_EXE}")

    p1_ok = run_phase1_tests()
    p2_ingest_ok = run_phase2_ingestion()
    p2_ok = run_phase2_tests()
    artifacts_ok = generate_submission_artifacts()

    header("UNIFIED MULTI-PHASE VERIFICATION SUMMARY")
    print(f"Phase 1 REST API Tests:       {'PASSED' if p1_ok else 'FAILED'}")
    print(f"Phase 2 ChromaDB Ingestion:    {'PASSED' if p2_ingest_ok else 'FAILED'}")
    print(f"Phase 2 RAG Application Tests: {'PASSED' if p2_ok else 'FAILED'}")
    print(f"Phase 2 Submission Artifacts:  {'PASSED' if artifacts_ok else 'FAILED'}")

    if p1_ok and p2_ingest_ok and p2_ok and artifacts_ok:
        print("\nALL PHASES VERIFIED SUCCESSFULLY! SYSTEM IS 100% PRODUCTION READY!")
    else:
        print("\nSOME VERIFICATIONS FAILED. PLEASE REVIEW LOGS.")



if __name__ == "__main__":
    main()
