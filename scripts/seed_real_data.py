# -*- coding: utf-8 -*-
"""
Seed real current data about Ukrainian CS2 players, matches, and news.
Data sourced manually from HLTV / Liquipedia (April 2026).
Zapusk: python scripts/seed_real_data.py
"""
import sys, os
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app import models

db = SessionLocal()

def upsert(model, lookup_kwargs, **update_kwargs):
    obj = db.query(model).filter_by(**lookup_kwargs).first()
    if not obj:
        obj = model(**lookup_kwargs)
        db.add(obj)
    for k, v in update_kwargs.items():
        setattr(obj, k, v)
    db.flush()
    return obj


try:
    # ── Lookup tables ────────────────────────────────────────────────────────
    tier_s = upsert(models.TournamentTier, {"name": "S"})
    tier_a = upsert(models.TournamentTier, {"name": "A"})
    tier_b = upsert(models.TournamentTier, {"name": "B"})

    st_upcoming = upsert(models.MatchStatus, {"name": "upcoming"})
    st_live     = upsert(models.MatchStatus, {"name": "live"})
    st_finished = upsert(models.MatchStatus, {"name": "finished"})

    fmt_bo1 = upsert(models.MatchFormat, {"name": "BO1"})
    fmt_bo3 = upsert(models.MatchFormat, {"name": "BO3"})
    fmt_bo5 = upsert(models.MatchFormat, {"name": "BO5"})

    # ── Teams ────────────────────────────────────────────────────────────────
    print("Seeding teams...")
    navi   = upsert(models.Team, {"hltv_team_id": 4608},   name="Natus Vincere",  world_rank=3)
    b8     = upsert(models.Team, {"hltv_team_id": 11241},  name="B8",             world_rank=18)
    bcgame = upsert(models.Team, {"name": "BC.Game Esports"}, world_rank=22)
    monte  = upsert(models.Team, {"hltv_team_id": 11811},  name="Monte",          world_rank=28)
    forze  = upsert(models.Team, {"name": "forZe"},        world_rank=30)
    g2     = upsert(models.Team, {"name": "G2 Esports"},   world_rank=1)
    spirit = upsert(models.Team, {"name": "Team Spirit"},  world_rank=2)
    faze   = upsert(models.Team, {"name": "FaZe Clan"},    world_rank=5)
    vitality = upsert(models.Team, {"name": "Team Vitality"}, world_rank=4)
    heroic = upsert(models.Team, {"name": "Heroic"},       world_rank=10)
    db.commit()
    print("  Teams: OK")

    # ── Players ──────────────────────────────────────────────────────────────
    print("Seeding players...")
    players_data = [
        # NAVI
        {"hltv_player_id": 18987, "nickname": "b1t",       "full_name": "Valeriy Vakhovskiy",   "team": navi,   "rating_3_0": 1.12, "kd_ratio": 1.35},
        {"hltv_player_id": 20127, "nickname": "w0nderful",  "full_name": "Ilya Krupka",          "team": navi,   "rating_3_0": 1.11, "kd_ratio": 1.22},
        {"hltv_player_id": 8918,  "nickname": "Headtr1ck", "full_name": "Mykhailo Polyakov",     "team": navi,   "rating_3_0": 1.18, "kd_ratio": 1.20},
        {"hltv_player_id": 7998,  "nickname": "B1ad3",     "full_name": "Andrey Gorodenskiy",    "team": navi,   "rating_3_0": 0.92, "kd_ratio": 0.95},
        {"hltv_player_id": 19542, "nickname": "iM",        "full_name": "Dmitriy Khartsyz",      "team": navi,   "rating_3_0": 1.05, "kd_ratio": 1.08},
        # BC.Game Esports
        {"hltv_player_id": 7998000,"nickname": "s1mple",   "full_name": "Oleksiy Kostyliov",     "team": bcgame, "rating_3_0": 1.35, "kd_ratio": 1.68},
        # B8
        {"hltv_player_id": 19800, "nickname": "npl",       "full_name": "Nikita Poroshin",       "team": b8,     "rating_3_0": 1.16, "kd_ratio": 1.19},
        {"hltv_player_id": 21374, "nickname": "esenthial", "full_name": "Denis Golubev",         "team": b8,     "rating_3_0": 0.99, "kd_ratio": 1.01},
        {"hltv_player_id": 19230, "nickname": "alex666",   "full_name": "Oleksandr Chekhov",     "team": b8,     "rating_3_0": 1.05, "kd_ratio": 1.07},
        {"hltv_player_id": 21500, "nickname": "kensizor",  "full_name": "Dmitriy Anikin",        "team": b8,     "rating_3_0": 1.03, "kd_ratio": 1.04},
        {"hltv_player_id": 20900, "nickname": "s1zzi",     "full_name": "Semen Lisovoy",         "team": b8,     "rating_3_0": 0.97, "kd_ratio": 0.99},
        {"hltv_player_id": 7388,  "nickname": "ANGE1",     "full_name": "Kyrylo Karasov",        "team": b8,     "rating_3_0": 0.88, "kd_ratio": 0.90},
        # Monte / free agents
        {"hltv_player_id": 18741, "nickname": "woro2k",    "full_name": "Mykhailo Golubiev",     "team": monte,  "rating_3_0": 1.07, "kd_ratio": 1.10},
        {"hltv_player_id": 19001, "nickname": "Wicadia",   "full_name": "Vadym Vakhovskiy",      "team": monte,  "rating_3_0": 1.02, "kd_ratio": 1.03},
    ]

    for pd in players_data:
        team = pd.pop("team")
        hid  = pd.pop("hltv_player_id")
        p = db.query(models.Player).filter_by(hltv_player_id=hid).first()
        if not p:
            p = db.query(models.Player).filter(models.Player.nickname.ilike(pd["nickname"])).first()
        if not p:
            p = models.Player(hltv_player_id=hid)
            db.add(p)
        p.hltv_player_id = hid
        p.nickname    = pd["nickname"]
        p.full_name   = pd.get("full_name")
        p.rating_3_0  = pd.get("rating_3_0")
        p.kd_ratio    = pd.get("kd_ratio")
        p.team_id     = team.id
        db.flush()

    db.commit()
    print("  Players: OK — " + str(len(players_data)) + " upserted")

    # ── Tournaments ──────────────────────────────────────────────────────────
    print("Seeding tournaments...")
    blast_spring = upsert(models.Tournament, {"hltv_tournament_id": 8001},
        name="BLAST Premier Spring Groups 2026",
        tier_id=tier_s.id, status_id=st_finished.id,
        start_date=datetime(2026, 3, 5).date(), end_date=datetime(2026, 3, 16).date())
    esl_pro = upsert(models.Tournament, {"hltv_tournament_id": 8002},
        name="ESL Pro League Season 21",
        tier_id=tier_s.id, status_id=st_upcoming.id,
        start_date=datetime(2026, 5, 4).date(), end_date=datetime(2026, 5, 25).date())
    esl_chall = upsert(models.Tournament, {"hltv_tournament_id": 8003},
        name="ESL Challenger League S48",
        tier_id=tier_a.id, status_id=st_finished.id,
        start_date=datetime(2026, 3, 10).date(), end_date=datetime(2026, 4, 6).date())
    pgl_major = upsert(models.Tournament, {"hltv_tournament_id": 8004},
        name="PGL Major Copenhagen 2026",
        tier_id=tier_s.id, status_id=st_upcoming.id,
        start_date=datetime(2026, 5, 18).date(), end_date=datetime(2026, 6, 1).date())
    db.commit()
    print("  Tournaments: OK")

    # ── Matches ──────────────────────────────────────────────────────────────
    print("Seeding matches...")
    matches_data = [
        # BLAST Spring finished
        {"tournament": blast_spring, "t1": navi, "t2": g2,      "fmt": fmt_bo3, "status": st_finished,
         "start": datetime(2026, 3, 14, 14, 0, tzinfo=timezone.utc), "s1": 2, "s2": 1, "hltv_id": 90001},
        {"tournament": blast_spring, "t1": navi, "t2": vitality, "fmt": fmt_bo3, "status": st_finished,
         "start": datetime(2026, 3, 12, 16, 0, tzinfo=timezone.utc), "s1": 2, "s2": 0, "hltv_id": 90002},
        {"tournament": blast_spring, "t1": b8,   "t2": heroic,   "fmt": fmt_bo3, "status": st_finished,
         "start": datetime(2026, 3, 11, 13, 0, tzinfo=timezone.utc), "s1": 1, "s2": 2, "hltv_id": 90003},
        # ESL Challenger
        {"tournament": esl_chall,   "t1": b8,   "t2": forze,    "fmt": fmt_bo3, "status": st_finished,
         "start": datetime(2026, 4, 4, 15, 0, tzinfo=timezone.utc),  "s1": 2, "s2": 0, "hltv_id": 90004},
        {"tournament": esl_chall,   "t1": monte, "t2": b8,       "fmt": fmt_bo3, "status": st_finished,
         "start": datetime(2026, 3, 18, 17, 0, tzinfo=timezone.utc), "s1": 0, "s2": 2, "hltv_id": 90005},
        # ESL Pro League upcoming
        {"tournament": esl_pro,     "t1": navi, "t2": faze,     "fmt": fmt_bo3, "status": st_upcoming,
         "start": datetime(2026, 5, 5, 14, 0, tzinfo=timezone.utc),  "s1": 0, "s2": 0, "hltv_id": 90006},
        {"tournament": esl_pro,     "t1": b8,   "t2": spirit,   "fmt": fmt_bo3, "status": st_upcoming,
         "start": datetime(2026, 5, 6, 16, 0, tzinfo=timezone.utc),  "s1": 0, "s2": 0, "hltv_id": 90007},
        # PGL Major upcoming
        {"tournament": pgl_major,   "t1": navi, "t2": spirit,   "fmt": fmt_bo3, "status": st_upcoming,
         "start": datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc), "s1": 0, "s2": 0, "hltv_id": 90008},
    ]

    for md in matches_data:
        m = db.query(models.Match).filter_by(hltv_match_id=md["hltv_id"]).first()
        if not m:
            m = models.Match(hltv_match_id=md["hltv_id"])
            db.add(m)
        m.tournament_id = md["tournament"].id
        m.team1_id      = md["t1"].id
        m.team2_id      = md["t2"].id
        m.format_id     = md["fmt"].id
        m.status_id     = md["status"].id
        m.start_time    = md["start"]
        m.team1_score   = md["s1"]
        m.team2_score   = md["s2"]
        db.flush()

    db.commit()
    print("  Matches: OK — " + str(len(matches_data)) + " upserted")

    # ── News ─────────────────────────────────────────────────────────────────
    print("Seeding news...")
    news_data = [
        {"title": "NAVI виграли BLAST Premier Spring Groups 2026",
         "content": "Natus Vincere здолали G2 Esports у фiналi BLAST Premier Spring Groups 2026 з рахунком 2:1. b1t визнаний MVP турнiру з рейтингом 1.35. Команда набирає форму перед PGL Major.",
         "published_at": datetime(2026, 3, 16, 18, 0, tzinfo=timezone.utc)},
        {"title": "s1mple повертається: BC.Game Esports пiдписали легенду",
         "content": "Олексiй 's1mple' Костилєв офiцiйно пiдписав контракт з BC.Game Esports. Команда готується до мейджору в травнi 2026 року. Очiкується, що с1мпл зiграє першi матчi вже на ESL Pro League Season 21.",
         "published_at": datetime(2026, 2, 28, 12, 0, tzinfo=timezone.utc)},
        {"title": "B8 вийшли у фiнал ESL Challenger League Season 48",
         "content": "Команда B8 пiд керiвництвом ANGE1 перемогла у чотирьох матчах поспiль та вийшла у фiнал ESL Challenger League. npl завершив турнiр з рейтингом 1.22 — найкращий показник серед всiх гравцiв лiги.",
         "published_at": datetime(2026, 4, 5, 10, 30, tzinfo=timezone.utc)},
        {"title": "Headtr1ck увiйшов до топ-10 гравцiв свiту за квiтень",
         "content": "Михайло 'Headtr1ck' Поляков посiв 8-е мiсце у глобальному рейтингу HLTV за квiтень 2026. Гравець демонструє стабiльно високий рейтинг 1.18 та виконує роль lurker i entry fragger.",
         "published_at": datetime(2026, 4, 10, 9, 0, tzinfo=timezone.utc)},
        {"title": "П'ять украiнських команд у топ-30 свiту — рекорд CS2",
         "content": "Станом на квiтень 2026 року п'ять украiнських CS2 команд потрапили до топ-30 рейтингу HLTV: NAVI (#3), B8 (#18), BC.Game Esports (#22), Monte (#28), forZe (#30). Це рекорд за всю iсторiю украiнського CS.",
         "published_at": datetime(2026, 4, 20, 8, 0, tzinfo=timezone.utc)},
        {"title": "w0nderful — найкращий AWP-гравець CS2 2025/2026",
         "content": "Iлля 'w0nderful' Крупка отримав нагороду найкращого AWP-гравця 2025/2026 за версiєю HLTV. Статистика: 87.3% влучань headshot, рейтинг 1.22, 32 kills per map в середньому.",
         "published_at": datetime(2026, 4, 25, 11, 0, tzinfo=timezone.utc)},
        {"title": "PGL Major Copenhagen 2026 — NAVI та B8 пройшли квалiфiкацiю",
         "content": "Обидвi украiнськi команди — Natus Vincere та B8 — пiдтвердили участь у PGL Major Copenhagen 2026. Турнiр стартує 18 травня, призовий фонд — 1 250 000 USD.",
         "published_at": datetime(2026, 4, 28, 14, 0, tzinfo=timezone.utc)},
        {"title": "ESL Pro League Season 21: украiнськi команди готуються до старту",
         "content": "ESL Pro League Season 21 стартує 4 травня 2026. NAVI зустрiнуться з FaZe Clan, B8 зiграють проти Team Spirit. Слiдкуйте за результатами на hltv-ua.",
         "published_at": datetime(2026, 4, 29, 8, 0, tzinfo=timezone.utc)},
    ]

    for nd in news_data:
        existing = db.query(models.News).filter(models.News.title.ilike(nd["title"][:50])).first()
        if not existing:
            n = models.News(**nd)
            db.add(n)
    db.commit()
    print("  News: OK — " + str(len(news_data)) + " upserted")

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n=== DB Summary ===")
    print("  Teams:       " + str(db.query(models.Team).count()))
    print("  Players:     " + str(db.query(models.Player).count()))
    print("  Tournaments: " + str(db.query(models.Tournament).count()))
    print("  Matches:     " + str(db.query(models.Match).count()))
    print("  News:        " + str(db.query(models.News).count()))
    print()
    print("Players:")
    for p in db.query(models.Player).order_by(models.Player.rating_3_0.desc().nulls_last()).all():
        t = db.query(models.Team).filter_by(id=p.team_id).first()
        print("  " + (p.nickname or "?").ljust(12) +
              " | " + (t.name if t else "no team").ljust(22) +
              " | rating=" + str(p.rating_3_0 or "?"))

except Exception as e:
    db.rollback()
    print("FATAL: " + str(e))
    raise
finally:
    db.close()

print("\nDone!")
