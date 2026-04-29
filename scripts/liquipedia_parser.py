# -*- coding: utf-8 -*-
"""
Liquipedia Parse API parser — Ukrainian CS2 players & teams.

API: https://liquipedia.net/counterstrike/api.php
No auth required. Rate limit: 1 req / 2 sec.

Zapusk: python scripts/liquipedia_parser.py
"""
import sys, os, re, time, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app import models

BASE    = "https://liquipedia.net/counterstrike/api.php"
DELAY   = 5.0   # seconds between requests (Liquipedia rate limit)
HEADERS = {
    "User-Agent": "HLTV-UA/1.0 (University CS2 aggregator; educational use)",
    "Accept-Encoding": "gzip",
}


def api(params, max_retries=5):
    params.setdefault("format", "json")
    for attempt in range(max_retries):
        time.sleep(DELAY + attempt * 2)   # 2s, 4s, 6s, 8s, 10s
        r = requests.get(BASE, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 30))
            wait = max(wait, 30)   # at least 30s
            print("    [429] rate limited — waiting " + str(wait) + "s...")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Max retries exceeded for " + str(params))


def wikitext_field(text, field):
    """Extract |field=value from wikitext."""
    m = re.search(
        r'\|\s*' + re.escape(field) + r'\s*=\s*([^\|\n\}]+)',
        text, re.IGNORECASE
    )
    if not m:
        return None
    raw = m.group(1).strip()
    # Remove wikilinks [[Link|Display]] or [[Display]]
    raw = re.sub(r'\[\[(?:[^\]|]+\|)?([^\]]+)\]\]', r'\1', raw)
    # Remove templates {{...}}
    raw = re.sub(r'\{\{[^\}]+\}\}', '', raw)
    # Remove HTML tags
    raw = re.sub(r'<[^>]+>', '', raw)
    return raw.strip() or None


# ── 1. Get all Ukrainian player names ─────────────────────────────────────────
def get_ua_player_names():
    print("Fetching Ukrainian player list from Liquipedia...")
    names = []
    params = {
        "action":  "query",
        "list":    "categorymembers",
        "cmtitle": "Category:Ukrainian_Players",
        "cmlimit": "50",
    }
    page_num = 1
    while True:
        data = api(params)
        members = data.get("query", {}).get("categorymembers", [])
        for m in members:
            title = m.get("title", "")
            if ":" not in title:  # skip subcategories like Category:...
                names.append(title)
        print("  page " + str(page_num) + ": +" + str(len(members)) + " players")
        page_num += 1

        cont = data.get("continue", {}).get("cmcontinue")
        if not cont:
            break
        params["cmcontinue"] = cont

    print("  Total: " + str(len(names)) + " Ukrainian players found")
    return names


# ── 2. Parse individual player page ───────────────────────────────────────────
def parse_player(page_title):
    try:
        data = api({
            "action": "parse",
            "page":   page_title,
            "prop":   "wikitext",
        })
        wt = data.get("parse", {}).get("wikitext", {}).get("*", "")
        if not wt:
            return None

        team        = wikitext_field(wt, "team")
        team2       = wikitext_field(wt, "team2")   # some use team2
        status      = wikitext_field(wt, "status")
        full_name   = wikitext_field(wt, "name")
        nationality = wikitext_field(wt, "nationality")
        birth_date  = wikitext_field(wt, "birth_date") or wikitext_field(wt, "birthdate")

        # Use team or team2
        active_team = team or team2

        return {
            "nickname":    page_title,
            "full_name":   full_name,
            "team_name":   active_team,
            "nationality": nationality,
            "birth_date":  birth_date,
            "status":      status,
        }
    except Exception as e:
        print("    error parsing " + page_title + ": " + str(e))
        return None


# ── 3. Get or create team in DB ───────────────────────────────────────────────
def get_or_create_team(db, team_name):
    if not team_name:
        return None
    # Normalize
    name = team_name.strip()
    t = db.query(models.Team).filter(
        models.Team.name.ilike(name)
    ).first()
    if not t:
        t = models.Team(name=name)
        db.add(t)
        db.flush()
        print("    + new team: " + name)
    return t


# ── 4. Save player to DB ──────────────────────────────────────────────────────
def save_player(db, data):
    if not data:
        return False

    nickname = data["nickname"]

    # Only active Ukrainian players
    status      = (data.get("status") or "").lower()
    nationality = (data.get("nationality") or "").lower()

    is_ua     = "ukraine" in nationality or not nationality  # blank = assume UA (from UA category)
    is_active = status in ("active", "") or not status

    if not is_ua:
        return False

    team = get_or_create_team(db, data.get("team_name"))

    # Find existing player by nickname (case-insensitive)
    p = db.query(models.Player).filter(
        models.Player.nickname.ilike(nickname)
    ).first()
    if not p:
        p = models.Player()
        db.add(p)

    p.nickname = nickname
    if data.get("full_name"):
        p.full_name = data["full_name"]
    if team:
        p.team_id = team.id

    return True


# ── 5. Patch known data ───────────────────────────────────────────────────────
def patch_known_data(db):
    """Fix known data that Liquipedia might miss (HLTV ratings etc.)"""
    # s1mple - BC.Game Esports (confirmed from Liquipedia)
    s1 = db.query(models.Player).filter(models.Player.nickname.ilike("s1mple")).first()
    if s1:
        bc = get_or_create_team(db, "BC.Game Esports")
        if bc and s1.team_id != bc.id:
            s1.team_id = bc.id
            print("  Patched s1mple -> BC.Game Esports")

    # Known HLTV ratings from our Playwright scrape (Phase B data)
    known_ratings = {
        "b1t":       ("1.12", "1.35"),
        "w0nderful": ("1.11", "1.22"),
        "npl":       ("1.16", None),
        "alex666":   ("1.05", None),
        "kensizor":  ("1.03", None),
        "esenthial": ("0.99", None),
        "s1zzi":     ("0.97", None),
    }
    for nick, (rating, kd) in known_ratings.items():
        p = db.query(models.Player).filter(models.Player.nickname.ilike(nick)).first()
        if p:
            if rating: p.rating_3_0 = float(rating)
            if kd:     p.kd_ratio   = float(kd)

    db.commit()


# ── Main ─────────────────────────────────────────────────────────────────────
def run():
    print("=== Liquipedia Parser for Ukrainian CS2 Players ===\n")
    db = SessionLocal()
    try:
        # 1. Get names
        names = get_ua_player_names()

        # 2. Fetch each player page
        print("\nFetching player pages (2s delay each)...")
        saved = 0
        skipped = 0
        errors = 0

        for i, name in enumerate(names):
            print("[" + str(i+1) + "/" + str(len(names)) + "] " + name, end=" ... ")
            data = parse_player(name)
            if data:
                status = (data.get("status") or "").lower()
                team   = data.get("team_name") or ""
                print("team=" + (team[:25] if team else "none") + " status=" + (status or "?"), end=" ")
                result = save_player(db, data)
                if result:
                    print("SAVED")
                    saved += 1
                else:
                    print("skip")
                    skipped += 1
            else:
                print("ERROR")
                errors += 1

            # Commit every 10 players
            if (i + 1) % 10 == 0:
                db.commit()

        db.commit()

        # 3. Patch known data
        print("\nPatching known ratings and teams...")
        patch_known_data(db)

        # 4. Summary
        print("\n=== Summary ===")
        print("  Saved:   " + str(saved))
        print("  Skipped: " + str(skipped))
        print("  Errors:  " + str(errors))
        print()
        print("Ukrainian players in DB:")
        for p in db.query(models.Player).order_by(models.Player.rating_3_0.desc().nulls_last()).all():
            t = db.query(models.Team).filter_by(id=p.team_id).first()
            print("  " + (p.nickname or "?").ljust(15) +
                  " | " + (t.name if t else "no team").ljust(20) +
                  " | rating=" + str(p.rating_3_0 or "?"))

    except KeyboardInterrupt:
        db.commit()
        print("\nInterrupted - partial data saved.")
    except Exception as e:
        db.rollback()
        print("FATAL: " + str(e))
        raise
    finally:
        db.close()

    print("\nDone!")


if __name__ == "__main__":
    run()
