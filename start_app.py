"""Single-Command Launcher for POC-07 Retail Inventory & Procurement Platform.

Starts both the FastAPI Backend (Port 8000) and the Streamlit Multi-Agent Dashboard (Port 8501).
Usage:
    python start_app.py
"""

import os
import sys
import time
import signal
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))

def check_backend_healthy(url="http://localhost:8000/health", timeout_secs=15):
    """Wait until FastAPI backend reports healthy status."""
    start = time.time()
    while time.time() - start < timeout_secs:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

def main():
    print("=" * 70)
    print("📦 POC-07 — Retail Inventory Management & Procurement Platform")
    print("   AI Readiness Training Program | Master Unified Launcher")
    print("=" * 70)
    
    processes = []
    
    try:
        # 1. Start FastAPI Backend Service
        print("\n🚀 [1/2] Starting FastAPI Backend on http://localhost:8000 ...")
        backend_cmd = [
            sys.executable, "-m", "uvicorn",
            "src.backend.main:app",
            "--host", "0.0.0.0",
            "--port", "8000"
        ]
        backend_proc = subprocess.Popen(backend_cmd, cwd=REPO_ROOT)
        processes.append(("FastAPI Backend", backend_proc))
        
        # Verify backend health
        print("⏳ Waiting for backend API to initialize...")
        if check_backend_healthy():
            print("✅ FastAPI Backend is UP and HEALTHY on http://localhost:8000")
        else:
            print("⚠️ Backend starting slowly, proceeding with UI launch...")

        # 2. Start Streamlit Multi-Agent & RAG Dashboard
        print("\n🌐 [2/2] Starting Streamlit Unified UI on http://localhost:8501 ...")
        streamlit_cmd = [
            sys.executable, "-m", "streamlit", "run",
            os.path.join(REPO_ROOT, "src", "ui", "chat_streamlit", "app.py"),
            "--server.port", "8501",
            "--server.headless", "true"
        ]
        streamlit_proc = subprocess.Popen(streamlit_cmd, cwd=REPO_ROOT)
        processes.append(("Streamlit Dashboard", streamlit_proc))

        print("\n" + "=" * 70)
        print("🎉 All Services Started Successfully!")
        print("=" * 70)
        print("  📖 FastAPI Swagger OpenAPI:  http://localhost:8000/docs")
        print("  🔌 Backend Health Endpoint:  http://localhost:8000/health")
        print("  🖥️ Streamlit Web Dashboard:  http://localhost:8501")
        print("     - Tab 1: Operations Chat Agent (Phase 4 FastMCP)")
        print("     - Tab 2: Inventory Manual & SOPs (Phase 2 RAG)")
        print("     - Tab 3: Multi-Agent Orchestrator (Phase 5 LangGraph)")
        print("=" * 70)
        print("Press Ctrl+C to terminate all services...\n")

        # Keep parent process alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down all platform services...")
        for name, proc in processes:
            print(f"Terminating {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("✅ Shutdown complete.")

if __name__ == "__main__":
    main()
