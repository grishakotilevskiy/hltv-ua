"""Fetch B8 and Monte team pages in fresh browser sessions with delays."""
import sys, os, re, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from app.database import SessionLocal
from app import models

BASE = "https://www.hltv.org"
UA_COUNTRY = "Ukraine"

TEAMS = [
    {"hltv_id": 11241, "name": "B8"},
    {"hltv_id": 11811, "name": "Monte"},
]


def scrape_team(hltv_id, team_name):
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="uk-UA", viewport={"width": 1366, "height": 768},
        )
        page = ctx.new_page()
        url = BASE + "/team/" + str(hltv_id) + "/team"
        print("  GET " + url)
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(6)
        title = page.title()
        print("  Title: " + title)
        if "just a moment" in title.lower():
            print("  Cloudflare — failed")
            browser.close()
            return []

        soup = BeautifulSoup(page.content(), "html.parser")
        for row in soup.select(".players-table tbody tr"):
            try:
                nick_el = row.select_one(".playersBox-playernick .text-ellipsis")
                if not nick_el: continue
                nickname = nick_el.text.strip()
                flag_img = row.select_one("img.flag")
                country  = flag_img.get("title","").strip() if flag_img else ""
                link     = row.select_one("a.playersBox-playernick-image")
                hltv_pid = None
                if link:
                    parts = link.get("href","").split("/")
                    try: hltv_pid = int(parts[2])
                    except: pass
                body_img = row.select_one("img.playerBox-bodyshot")
                full_raw  = body_img.get("title","") if body_img else ""
                full_name = re.sub(r"'[^']+'\s*","",full_raw).strip() or None
                rating_el = row.select_one(".rating-cell")
                rating = rating_el.text.strip().split()[0] if rating_el else None

                flag = "[UA]" if country == UA_COUNTRY else "    "
                print("    " + flag + " " + nickname + " (" + (country or "?") + ") id=" + str(hltv_pid) + " rating=" + str(rating))

                if country == UA_COUNTRY and hltv_pid:
                    results.append({"nickname": nickname, "full_name": full_name,
                                    "hltv_player_id": hltv_pid, "rating_3_0": rating,
                                    "team_name": team_name})
            except Exception as e:
                print("    err: " + str(e))
        browser.close()
    return results


def save(players, team_name):
    db = SessionLocal()
    try:
        team = db.query(models.Team).filter(models.Team.name.ilike(team_name)).first()
        for pd in players:
            p = db.query(models.Player).filter_by(hltv_player_id=pd["hltv_player_id"]).first()
            if not p:
                p = models.Player(hltv_player_id=pd["hltv_player_id"]); db.add(p)
            p.nickname = pd["nickname"]
            if pd.get("full_name"): p.full_name = pd["full_name"]
            if pd.get("rating_3_0"):
                try: p.rating_3_0 = float(pd["rating_3_0"])
                except: pass
            if team: p.team_id = team.id
        db.commit()
        print("  Saved " + str(len(players)) + " UA players")
    finally:
        db.close()


for team_info in TEAMS:
    print("\n=== " + team_info["name"] + " ===")
    players = scrape_team(team_info["hltv_id"], team_info["name"])
    if players:
        save(players, team_info["name"])
    print("Waiting 20s...")
    time.sleep(20)

print("\nFinal DB:")
db = SessionLocal()
for p in db.query(models.Player).order_by(models.Player.rating_3_0.desc()).all():
    t = db.query(models.Team).filter_by(id=p.team_id).first()
    print(" ", p.nickname, "|", t.name if t else "?", "| rating:", p.rating_3_0)
db.close()
