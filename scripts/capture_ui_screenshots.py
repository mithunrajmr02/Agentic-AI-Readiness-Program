"""
Wave 2 UI Screenshot Automation Script
Generates a valid JWT token, injects it into localStorage via context init script,
navigates through every screen, and captures high-resolution full-page screenshots.
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.abspath("."))
from src.backend.routers.auth import create_access_token

SCREENSHOTS_DIR = os.path.abspath("screenshots/wave2")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def capture_all():
    token = create_access_token(data={"sub": "admin@retail.com", "role": "manager"})
    print(f"Generated auth token: {token[:20]}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 960})

        # Inject token into localStorage for http://127.0.0.1:3000
        context.add_init_script(f"""
            window.localStorage.setItem('poc07.access_token', '{token}');
        """)

        page = context.new_page()

        screens = [
            ("01_control_tower.png", "http://127.0.0.1:3000/tower"),
            ("02_signals_inbox.png", "http://127.0.0.1:3000/signals"),
            ("03_signal_detail.png", "http://127.0.0.1:3000/signals/SIG-000045"),
            ("04_approvals_queue.png", "http://127.0.0.1:3000/approvals"),
            ("05_approval_detail.png", "http://127.0.0.1:3000/approvals/APR-000012"),
            ("06_decisions_log.png", "http://127.0.0.1:3000/decisions"),
            ("07_decision_detail.png", "http://127.0.0.1:3000/decisions/DEC-000123"),
            ("08_inventory.png", "http://127.0.0.1:3000/inventory"),
            ("09_receiving.png", "http://127.0.0.1:3000/receiving"),
            ("10_suppliers.png", "http://127.0.0.1:3000/suppliers"),
            ("11_impact.png", "http://127.0.0.1:3000/impact"),
            ("12_autonomy_settings.png", "http://127.0.0.1:3000/settings/autonomy"),
            ("13_scenarios.png", "http://127.0.0.1:3000/settings/scenarios"),
        ]

        for filename, url in screens:
            print(f"Navigating to {url}...")
            try:
                page.goto(url, wait_until="networkidle")
                time.sleep(1.0)
                target_path = os.path.join(SCREENSHOTS_DIR, filename)
                page.screenshot(path=target_path, full_page=True)
                print(f"  Captured: {target_path}")
            except Exception as e:
                print(f"  Failed {filename}: {e}")

        browser.close()
        print("\nAll screenshots successfully saved to:", SCREENSHOTS_DIR)

if __name__ == "__main__":
    capture_all()
