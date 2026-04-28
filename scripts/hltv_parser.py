# -*- coding: utf-8 -*-
"""
HLTV Parser v3 — two-phase: teams ranking, then team pages for UA players.
Zapusk: python scripts/hltv_parser.py [teams|players|all]
"""
import sys, os, re, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from app.database import SessionLocal
from app import models

BASE       = "https://www.hltv.org"
UA_COUNTRY = "Ukraine"
UA_TEAMS   = [
    {"hltv_id": 4608,  "name": "Natus Vincere"},
    {"hltv_id": 11241, "name": "B8"},
    {"hltv_id": 11811, "name": "Monte"},
]


def make_page(pw):
    browser = pw.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    )
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36",
        locale="uk-UA",
        viewport={"width": 1366, "height": 768},
    )
    return browser, ctx.new_page()


def fetch(page, url, delay=4):
    print("  GET " + url)
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(delay)
    title = page.title()
    if "just a moment" in title.lower():
        print("  !! Cloudflare challenge — skipping")
        return None
    return BeautifulSoup(page.content(), "html.parser")


# ── Phase A: team ranking ────────────────────────────────────────────────────
def run_teams():
    print("=== Phase A: team ranking ===")
    db = SessionLocal()
    with sync_playwright() as pw:
        browser, page = make_page(pw)
        try:
            soup = fetch(page, BASE + "/ranking/teams", delay=4)
            if not soup:
                print("Failed."); return

            teams, saved = [], 0
            for block in soup.select(".ranked-team"):
                try:
                    rank = int(block.select_one(".position").text.strip().replace("#",""))
                    name = block.select_one(".teamLine .name").text.strip()
                    href = block.select_one(".moreLink").get("href","")
                    hltv_id = int(href.split("/")[2])
                    teams.append({"name": name, "world_rank": rank, "hltv_team_id": hltv_id})
                except Exception:
                    pass

            print("  Parsed: " + str(len(teams)) + " teams")
            for td in teams:
                t = db.query(models.Team).filter_by(hltv_team_id=td["hltv_team_id"]).first()
                if not t:
                    t = models.Team(hltv_team_id=td["hltv_team_id"]); db.add(t)
                t.name = td["name"]; t.world_rank = td["world_rank"]
                saved += 1
            db.commit()
            print("  Saved:  " + str(saved))
        finally:
            browser.close(); db.close()


# ── Phase B: players from team pages ─────────────────────────────────────────
def run_players():
    print("=== Phase B: Ukrainian players ===")
    db = SessionLocal()
    with sync_playwright() as pw:
        browser, page = make_page(pw)
        try:
            # Delete old non-UA fake players
            for pid in [8918, 12928, 20333]:   # electroNic, Perfecto, jL
                p = db.query(models.Player).filter_by(hltv_player_id=pid).first()
                if p: db.delete(p)
            db.commit()

            for team_info in UA_TEAMS:
                print("\n  Team: " + team_info["name"])
                url = BASE + "/team/" + str(team_info["hltv_id"]) + "/team"
                soup = fetch(page, url, delay=5)
                if not soup:
                    continue

                for row in soup.select(".players-table tbody tr"):
                    try:
                        # Nickname
                        nick_el = row.select_one(".playersBox-playernick .text-ellipsis")
                        if not nick_el: continue
                        nickname = nick_el.text.strip()

                        # Country
                        flag_img = row.select_one("img.flag")
                        country  = flag_img.get("title","").strip() if flag_img else ""

                        # HLTV player ID  href="/player/18987/b1t"
                        link     = row.select_one("a.playersBox-playernick-image")
                        hltv_pid = None
                        if link:
                            parts = link.get("href","").split("/")
                            try: hltv_pid = int(parts[2])
                            except: pass

                        # Full name from bodyshot img title
                        body_img = row.select_one("img.playerBox-bodyshot")
                        full_name_raw = body_img.get("title","") if body_img else ""
                        full_name = re.sub(r"'[^']+'\s*","",full_name_raw).strip() or None

                        # Rating (strip " **" footnote)
                        rating_el = row.select_one(".rating-cell")
                        rating = rating_el.text.strip().split()[0] if rating_el else None

                        flag = "[UA]" if country == UA_COUNTRY else "    "
                        print("    " + flag + " " + nickname +
                              " (" + (country or "?") + ")" +
                              " id=" + str(hltv_pid) +
                              " rating=" + str(rating))

                        # Only save Ukrainian players
                        if country != UA_COUNTRY or not hltv_pid:
                            continue

                        p = db.query(models.Player).filter_by(hltv_player_id=hltv_pid).first()
                        if not p:
                            p = models.Player(hltv_player_id=hltv_pid); db.add(p)
                        p.nickname = nickname
                        if full_name: p.full_name = full_name
                        if rating:
                            try: p.rating_3_0 = float(rating)
                            except: pass

                        team = db.query(models.Team).filter(
                            models.Team.name.ilike(team_info["name"])
                        ).first()
                        if team: p.team_id = team.id

                    except Exception as e:
                        print("    row err: " + str(e))

                db.commit()
                time.sleep(3)   # polite delay between team pages

        finally:
            browser.close(); db.close()

    print("\nDB summary:")
    db2 = SessionLocal()
    print("  Teams:   " + str(db2.query(models.Team).count()))
    print("  Players: " + str(db2.query(models.Player).count()))
    for p in db2.query(models.Player).order_by(models.Player.rating_3_0.desc()).all():
        t = db2.query(models.Team).filter_by(id=p.team_id).first()
        print("  " + (p.nickname or "?") + " | " + (t.name if t else "?") +
              " | " + str(p.rating_3_0))
    db2.close()


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("teams", "all"):
        run_teams()
        if mode == "all":
            print("\nWaiting 15s before player scrape...")
            time.sleep(15)
    if mode in ("players", "all"):
        run_players()
    print("\nDone!")
