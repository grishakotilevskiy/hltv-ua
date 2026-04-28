import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

BASE = "https://www.hltv.org"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    )
    page = context.new_page()
    page.goto(BASE + "/team/4608/team", wait_until="domcontentloaded", timeout=30000)
    time.sleep(4)
    soup = BeautifulSoup(page.content(), "html.parser")

    rows = soup.select(".players-table tbody tr")
    print("Rows:", len(rows))

    # Dump full HTML of first player row to see flag structure
    if rows:
        print("\n=== HTML of row 1 (b1t) ===")
        print(rows[1].prettify()[:2000])

    browser.close()
