import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

BASE = "https://www.hltv.org"

# Real HLTV IDs (from ranking scrape)
UA_TEAM_IDS = [
    (4608,  "Natus Vincere"),
    (11241, "B8"),
    (11811, "Monte"),
]

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    )
    page = context.new_page()

    tid, tname = 4608, "Natus Vincere"
    url = BASE + "/team/" + str(tid) + "/team"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)
    print("Page title:", page.title())

    soup = BeautifulSoup(page.content(), "html.parser")

    # Dump all table rows fully
    print("\n=== All rows in .players-table ===")
    for i, row in enumerate(soup.select(".players-table tr")):
        print("Row", i, ":", row.get_text(" | ", strip=True)[:120])
        for tag in row.select("[class]"):
            print("  cls:", tag.get("class"), "| text:", tag.text.strip()[:40])

    # Try direct JS evaluation
    print("\n=== JS evaluation of player names ===")
    players_js = page.evaluate("""() => {
        const rows = document.querySelectorAll('.players-table tbody tr');
        return Array.from(rows).map(r => ({
            text: r.innerText,
            nicks: Array.from(r.querySelectorAll('.nick, .player-nick, .statsNickname, a')).map(a => a.innerText).join(' / '),
            country: Array.from(r.querySelectorAll('img')).map(i => i.title + '|' + i.src).join('; ')
        }));
    }""")
    for p in players_js:
        print(" TEXT:", p["text"][:80])
        print(" NICKS:", p["nicks"][:80])
        print(" IMG:", p["country"][:120])
        print()

    browser.close()
