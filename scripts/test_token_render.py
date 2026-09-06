import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.abspath("."))
from src.backend.routers.auth import create_access_token

token = create_access_token({"sub": "admin@retail.com", "role": "manager"})

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    context.add_init_script(f"""
        window.localStorage.setItem('steward.access_token', '{token}');
    """)
    page = context.new_page()
    page.goto("http://localhost:3000/tower", wait_until="networkidle")
    time.sleep(1.0)
    print("Page URL:", page.url)
    print("Page content length:", len(page.content()))
    print("Header count:", page.locator("header").count())
    print("Sidebar count:", page.locator("aside.sidebar").count())
    print("Main heading text:", page.locator("h1, h2").all_text_contents())
    page.screenshot(path="screenshots/qa/02_tower.png", full_page=True)
    browser.close()
