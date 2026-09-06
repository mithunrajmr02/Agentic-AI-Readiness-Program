"""
Automated Screenshot Generator for STEWARD / POC-07 Inventory & Procurement System.
Launches the FastAPI backend and React frontend (via Vite preview),
navigates to every core route using Playwright with real JWT authentication,
and captures clean, high-resolution full-page screenshots.
"""
import os
import sys
import time
import subprocess
import urllib.request
import shutil
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.abspath("."))
from src.backend.routers.auth import create_access_token

BASE_DIR = os.path.abspath(".")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
FRONTEND_DIR = os.path.join(BASE_DIR, "src", "ui", "web_react")
PYTHON_EXE = sys.executable

def wait_for_url(url, timeout=25):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status in (200, 404, 304):
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    print("--- 1. Cleaning up old screenshot directories ---")
    old_dirs = ["audit", "manual_chrome_qa", "qa", "wave2"]
    for d in old_dirs:
        target = os.path.join(SCREENSHOTS_DIR, d)
        if os.path.exists(target):
            shutil.rmtree(target)
            print(f"Removed old directory: {target}")

    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    print("\n--- 2. Starting FastAPI backend on port 8000 ---")
    backend_env = os.environ.copy()
    backend_env["PYTHONPATH"] = BASE_DIR
    backend_proc = subprocess.Popen(
        [PYTHON_EXE, "-m", "uvicorn", "src.backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BASE_DIR,
        env=backend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    print("--- 3. Starting React Vite preview on port 3000 ---")
    # Build if dist does not exist
    dist_dir = os.path.join(FRONTEND_DIR, "dist")
    if not os.path.exists(dist_dir):
        subprocess.run(["npm", "run", "build"], cwd=FRONTEND_DIR, shell=True, check=True)

    frontend_proc = subprocess.Popen(
        ["npx", "vite", "preview", "--port", "3000", "--host", "127.0.0.1"],
        cwd=FRONTEND_DIR,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        print("Waiting for backend (http://127.0.0.1:8000/docs)...")
        if not wait_for_url("http://127.0.0.1:8000/docs", timeout=20):
            raise RuntimeError("Backend failed to start on port 8000")
        print("Backend is ready!")

        print("Waiting for frontend (http://127.0.0.1:3000)...")
        if not wait_for_url("http://127.0.0.1:3000", timeout=20):
            raise RuntimeError("Frontend failed to start on port 3000")
        print("Frontend is ready!")

        token = create_access_token(data={"sub": "admin@retail.com", "role": "manager"})
        print(f"Generated JWT manager token: {token[:25]}...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 960},
                device_scale_factor=1.5
            )

            # Pre-inject authentication tokens
            context.add_init_script(f"""
                window.localStorage.setItem('steward.access_token', '{token}');
                window.localStorage.setItem('poc07.access_token', '{token}');
            """)

            page = context.new_page()

            # First capture login screen in clean context without token
            login_ctx = browser.new_context(
                viewport={"width": 1440, "height": 960},
                device_scale_factor=1.5
            )
            login_page = login_ctx.new_page()
            login_page.goto("http://127.0.0.1:3000/login", wait_until="networkidle")
            time.sleep(1.0)
            login_path = os.path.join(SCREENSHOTS_DIR, "01_login.png")
            login_page.screenshot(path=login_path, full_page=True)
            print(f"Captured: {login_path}")
            login_ctx.close()

            # Now capture authenticated screens
            screens = [
                ("02_control_tower.png", "http://127.0.0.1:3000/tower"),
                ("03_signals_inbox.png", "http://127.0.0.1:3000/signals"),
                ("04_signal_detail.png", "http://127.0.0.1:3000/signals/SIG-000045"),
                ("05_approvals_queue.png", "http://127.0.0.1:3000/approvals"),
                ("06_approval_detail.png", "http://127.0.0.1:3000/approvals/APR-000012"),
                ("07_inventory.png", "http://127.0.0.1:3000/inventory"),
                ("08_product_detail.png", "http://127.0.0.1:3000/inventory/SKU-ELEC-0001"),
                ("09_suppliers.png", "http://127.0.0.1:3000/suppliers"),
                ("10_supplier_scorecard.png", "http://127.0.0.1:3000/suppliers/1"),
                ("11_receiving.png", "http://127.0.0.1:3000/receiving"),
                ("12_receipt_entry.png", "http://127.0.0.1:3000/receiving/PO-2026-0001"),
                ("13_decisions.png", "http://127.0.0.1:3000/decisions"),
                ("14_decision_detail.png", "http://127.0.0.1:3000/decisions/DEC-000123"),
                ("15_impact.png", "http://127.0.0.1:3000/impact"),
                ("16_autonomy.png", "http://127.0.0.1:3000/settings/autonomy"),
                ("17_scenarios.png", "http://127.0.0.1:3000/settings/scenarios"),
            ]

            for filename, url in screens:
                print(f"Navigating to {url}...")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=10000)
                    time.sleep(2.0)  # wait for React Query data fetch and render
                    target_path = os.path.join(SCREENSHOTS_DIR, filename)
                    page.screenshot(path=target_path, full_page=True)
                    print(f"  Successfully captured: {filename}")
                except Exception as e:
                    print(f"  Error capturing {filename}: {e}")

            browser.close()
            print("\nAll fresh screenshots captured successfully!")

    finally:
        print("\n--- Shutting down servers ---")
        backend_proc.terminate()
        frontend_proc.terminate()
        try:
            backend_proc.wait(timeout=3)
            frontend_proc.wait(timeout=3)
        except Exception:
            backend_proc.kill()
            frontend_proc.kill()
        print("Servers stopped cleanly.")

if __name__ == "__main__":
    main()
