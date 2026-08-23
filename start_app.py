"""Single-Command Launcher for POC-07 Retail Inventory & Procurement Platform.

Starts all three user-facing services:
    * FastAPI backend            http://localhost:8000
    * React operator SPA         http://localhost:3000   (Phase 1 UI)
    * Streamlit AI dashboard     http://localhost:8501   (Phases 2, 4, 5)

Usage:
    python start_app.py                 # everything
    python start_app.py --no-web        # skip the React SPA
    python start_app.py --no-dashboard  # skip Streamlit
    python start_app.py --seed          # load the demo dataset first
    python start_app.py --ingest        # (re)build the RAG vector store first

First run on a fresh clone:
    python start_app.py --seed --ingest

The React SPA was previously missing from this launcher even though it is the
primary operator interface -- `python start_app.py` brought up the backend and
Streamlit only, so the Phase 1 UI appeared not to exist unless the reader knew
to run `npm run dev` by hand in src/ui/web_react.
"""

import argparse
import os
import shutil
import subprocess
import sys
import time

import requests
from dotenv import load_dotenv

# Force UTF-8 on our own streams before anything prints. This launcher's output
# is full of emoji, and on Windows Python only uses a Unicode-capable writer when
# stdout is an actual console -- redirect it to a pipe or a file and it falls back
# to the locale encoding (cp1252 here), where the very first line raises
#   UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f4e6'
# and the launcher dies before starting a single service. `python start_app.py`
# worked interactively while `python start_app.py > run.log` did not.
for _stream in (sys.stdout, sys.stderr):
    try:
        # line_buffering matters as much as the encoding here. When stdout is a
        # pipe it is block-buffered, so the parent's banner -- the part that tells
        # the operator which URLs to open -- stayed in memory while the child
        # processes wrote straight to the same fd. The log looked like the
        # launcher had printed nothing at all.
        _stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except (AttributeError, ValueError):  # pragma: no cover - non-reconfigurable stream
        pass

load_dotenv()

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
WEB_DIR = os.path.join(REPO_ROOT, "src", "ui", "web_react")
CHROMA_DIR = os.path.join(REPO_ROOT, "chroma_db")
RAG_COLLECTION = "inventory_manual"


def check_backend_healthy(url="http://localhost:8000/health", timeout_secs=30):
    """Wait until FastAPI backend reports healthy status.

    /health is deliberately used rather than an /api/v1 route: every business
    endpoint requires a bearer token and answers 401, which would read as
    'unhealthy' forever.
    """
    start = time.time()
    while time.time() - start < timeout_secs:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5)
    return False


def rag_chunk_count():
    """Return the number of vectors in the RAG collection, or None if unknown.

    Counting is done through chromadb directly so it costs no embedding API
    calls -- the free tier allows only 1000 embeddings/day and re-ingesting on
    every launch would burn through it.
    """
    if not os.path.isdir(CHROMA_DIR):
        return 0
    try:
        import chromadb

        client = chromadb.PersistentClient(path=CHROMA_DIR)
        if RAG_COLLECTION not in [c.name for c in client.list_collections()]:
            return 0
        return client.get_collection(RAG_COLLECTION).count()
    except Exception:
        return None


def product_count():
    """Return the number of products on file, or None if the DB is unreadable.

    A fresh clone has no inventory.db at all, and the only thing the app seeds at
    startup is three suppliers -- no products, stock, or purchase orders. Without
    this check the operator just sees a dashboard reading 0 products and Rs.0 of
    stock and has no way to know a seed step exists.
    """
    db_path = os.path.join(REPO_ROOT, "inventory.db")
    if not os.path.exists(db_path):
        return 0
    try:
        import sqlite3

        con = sqlite3.connect(db_path)
        try:
            row = con.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='products'"
            ).fetchone()
            if not row or not row[0]:
                return 0
            return con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        finally:
            con.close()
    except Exception:
        return None


def run_seed():
    """Populate the demo dataset."""
    print("\n🌱 Seeding demo dataset (src/backend/seed_demo_data.py) ...")
    result = subprocess.run(
        [sys.executable, "-m", "src.backend.seed_demo_data"], cwd=REPO_ROOT
    )
    if result.returncode != 0:
        print("❌ Seeding failed; the dashboard will be empty or inconsistent.")
    return result.returncode == 0


def preflight():
    """Report configuration problems that would otherwise surface as odd runtime errors."""
    problems = []

    if not os.path.exists(os.path.join(REPO_ROOT, ".env")):
        problems.append(
            "No .env file found. Copy the template first:  cp .env.example .env\n"
            "     Phase 1 (backend + React UI) works without it; the AI phases do not."
        )

    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
        problems.append(
            "GOOGLE_API_KEY is not set. The backend and React UI will work fully, but\n"
            "     every LLM/embedding call (Phases 2-5) will fail. Get a key at\n"
            "     https://aistudio.google.com/apikey"
        )

    count = rag_chunk_count()
    if count == 0:
        problems.append(
            "The RAG vector store is empty, so Phase 2 answers will be unusable.\n"
            "     Build it with:  python start_app.py --ingest   (uses ~21 embedding calls)"
        )

    products = product_count()
    if products == 0:
        problems.append(
            "The database holds no products, so the dashboard, low-stock alerts and\n"
            "     every AI phase have nothing to work with. Load the demo dataset with:\n"
            "       python start_app.py --seed"
        )

    if problems:
        print("\n⚠️  Preflight warnings:")
        for p in problems:
            print(f"  -  {p}")
    else:
        chunks = "unknown" if count is None else count
        print(f"\n✅ Preflight OK ({products} products on file, "
              f"RAG vector store holds {chunks} chunks)")
    return problems


def run_ingestion():
    """Rebuild the RAG vector store."""
    print("\n📚 Building RAG vector store (src/rag/ingest.py) ...")
    result = subprocess.run(
        [sys.executable, "-m", "src.rag.ingest"], cwd=REPO_ROOT
    )
    if result.returncode == 0:
        print(f"✅ Ingestion complete ({rag_chunk_count()} chunks).")
    else:
        print(
            "❌ Ingestion failed. A 429 RESOURCE_EXHAUSTED here means the free-tier\n"
            "   embedding quota (1000/day) is spent -- retry after it resets."
        )
    return result.returncode == 0


def start_backend(processes):
    print("\n🚀 Starting FastAPI Backend on http://localhost:8000 ...")
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "src.backend.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
        ],
        cwd=REPO_ROOT,
    )
    processes.append(("FastAPI Backend", proc))

    print("⏳ Waiting for backend API to initialize...")
    if check_backend_healthy():
        print("✅ FastAPI Backend is UP and HEALTHY on http://localhost:8000")
    else:
        print("⚠️ Backend did not report healthy in 30s; continuing anyway.")


def start_react(processes):
    """Launch the Vite dev server for the React operator UI."""
    # shutil.which resolves npm to npm.cmd on Windows; passing a bare "npm" to
    # Popen there raises FileNotFoundError because it is not an .exe.
    npm = shutil.which("npm")
    if npm is None:
        print(
            "\n⚠️ Skipping React SPA: npm is not on PATH. Install Node.js 18+ from\n"
            "   https://nodejs.org to get the Phase 1 operator UI on port 3000."
        )
        return

    if not os.path.isdir(os.path.join(WEB_DIR, "node_modules")):
        print("\n📦 Installing React dependencies (first run only, this takes a minute) ...")
        install = subprocess.run([npm, "install"], cwd=WEB_DIR)
        if install.returncode != 0:
            print("❌ npm install failed; skipping the React SPA.")
            return

    print("\n🖥️ Starting React operator UI on http://localhost:3000 ...")
    proc = subprocess.Popen([npm, "run", "dev"], cwd=WEB_DIR)
    processes.append(("React SPA", proc))


def start_streamlit(processes):
    print("\n🌐 Starting Streamlit AI Dashboard on http://localhost:8501 ...")
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run",
            os.path.join(REPO_ROOT, "src", "ui", "chat_streamlit", "app.py"),
            "--server.port", "8501",
            "--server.headless", "true",
        ],
        cwd=REPO_ROOT,
    )
    processes.append(("Streamlit Dashboard", proc))


def shutdown(processes):
    print("\n🛑 Shutting down all platform services...")
    for name, proc in processes:
        print(f"Terminating {name}...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    print("✅ Shutdown complete.")


def main():
    parser = argparse.ArgumentParser(description="POC-07 unified launcher")
    parser.add_argument("--no-web", action="store_true", help="skip the React operator SPA")
    parser.add_argument("--no-dashboard", action="store_true", help="skip the Streamlit dashboard")
    parser.add_argument("--ingest", action="store_true", help="rebuild the RAG vector store first")
    parser.add_argument("--seed", action="store_true", help="load the demo dataset first")
    args = parser.parse_args()

    print("=" * 70)
    print("📦 POC-07 — Retail Inventory Management & Procurement Platform")
    print("   AI Readiness Training Program | Master Unified Launcher")
    print("=" * 70)

    preflight()

    if args.seed:
        run_seed()

    if args.ingest:
        run_ingestion()

    processes = []
    try:
        start_backend(processes)
        if not args.no_web:
            start_react(processes)
        if not args.no_dashboard:
            start_streamlit(processes)

        print("\n" + "=" * 70)
        print("🎉 Platform is running")
        print("=" * 70)
        started = {name for name, _ in processes}
        if "React SPA" in started:
            print("  🖥️  React Operator UI:       http://localhost:3000")
            print("      Sign in with the seeded manager account (see .env.example)")
        if "Streamlit Dashboard" in started:
            print("  📊 Streamlit AI Dashboard:   http://localhost:8501")
            print("     - Tab 1: Operations Chat Agent (Phase 4 FastMCP)")
            print("     - Tab 2: Reasoning Agent (Phase 3 ReAct)")
            print("     - Tab 3: Inventory Manual & SOPs (Phase 2 RAG)")
            print("     - Tab 4: Multi-Agent Orchestrator (Phase 5 LangGraph)")
        print("  📖 FastAPI Swagger OpenAPI:  http://localhost:8000/docs")
        print("  🔌 Backend Health Endpoint:  http://localhost:8000/health")
        print("=" * 70)
        print("Press Ctrl+C to terminate all services...\n")

        # Keep the parent alive, but notice if a child dies rather than silently
        # reporting that everything is running.
        while True:
            time.sleep(1)
            for name, proc in list(processes):
                if proc.poll() is not None:
                    print(f"\n❌ {name} exited unexpectedly (code {proc.returncode}).")
                    processes.remove((name, proc))
            if not processes:
                print("All services have stopped; exiting.")
                return

    except KeyboardInterrupt:
        shutdown(processes)


if __name__ == "__main__":
    main()
