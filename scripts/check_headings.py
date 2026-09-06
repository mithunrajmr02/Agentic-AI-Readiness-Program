import os
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.abspath("."))
from src.backend.routers.auth import create_access_token

def test_headings():
    t = create_access_token({"sub": "admin@retail.com", "role": "manager"})
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_init_script(f"""
            window.localStorage.setItem('steward.access_token', '{t}');
            window.localStorage.setItem('poc07.access_token', '{t}');
        """)
        page = context.new_page()
        page.on("console", lambda m: print("CONSOLE:", m.type, m.text))
        page.on("pageerror", lambda e: print("PAGEERROR:", e))
        page.goto("http://localhost:3000/approvals/APR-000012", wait_until="networkidle")
        h1s = page.locator("h1").all_inner_texts()
        print("H1s on /approvals/APR-000012:", h1s)
        browser.close()

if __name__ == "__main__":
    test_headings()
