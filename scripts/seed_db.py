# -*- coding: utf-8 -*-
"""
Seed script -- zavantazhuye pochatkovi dani v hltv_ua
Zapusk: python scripts/seed_db.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app import models
from datetime import datetime, timedelta


def get_or_create(db, model, **kwargs):
    obj = db.query(model).filter_by(**kwargs).first()
    if not obj:
        obj = model(**kwargs)
        db.add(obj)
        db.flush()
    return obj


def seed():
    db = SessionLocal()
    try:
        # ── 1. Lookup tables ───────────────────────────────────────────────
        bo1 = get_or_create(db, models.MatchFormat, name="bo1")
        bo3 = get_or_create(db, models.MatchFormat, name="bo3")
        bo5 = get_or_create(db, models.MatchFormat, name="bo5")

        st_live = get_or_create(db, models.MatchStatus, name="live")
        st_up   = get_or_create(db, models.MatchStatus, name="upcoming")
        st_fin  = get_or_create(db, models.MatchStatus, name="finished")

        tier_s = get_or_create(db, models.TournamentTier, name="S")
        tier_a = get_or_create(db, models.TournamentTier, name="A")
        tier_b = get_or_create(db, models.TournamentTier, name="B")
        tier_c = get_or_create(db, models.TournamentTier, name="C")

        db.commit()

        # ── 2. Komandy ─────────────────────────────────────────────────────
        navi  = get_or_create(db, models.Team, hltv_team_id=4608)
        navi.name = "Natus Vincere"; navi.world_rank = 3;  navi.win_rate = "62.50"

        b8    = get_or_create(db, models.Team, hltv_team_id=12345)
        b8.name = "B8";             b8.world_rank   = 45; b8.win_rate   = "48.30"

        monte = get_or_create(db, models.Team, hltv_team_id=11234)
        monte.name = "Monte";       monte.world_rank = 28; monte.win_rate = "55.10"

        gl    = get_or_create(db, models.Team, hltv_team_id=10567)
        gl.name = "GamerLegion";    gl.world_rank   = 18; gl.win_rate   = "58.20"

        forze = get_or_create(db, models.Team, hltv_team_id=6169)
        forze.name = "forZe";       forze.world_rank = 67; forze.win_rate = "43.80"

        db.commit()

        # ── 3. Hravtsi ─────────────────────────────────────────────────────
        players_data = [
            dict(hltv_player_id=18987, team_id=navi.id,  nickname="b1t",
                 full_name="Valerii Vakhovskiy",  rating_3_0="1.210", kd_ratio="1.350", headshot_pct="58.30"),
            dict(hltv_player_id=8918,  team_id=navi.id,  nickname="electroNic",
                 full_name="Denis Sharipov",       rating_3_0="1.150", kd_ratio="1.280", headshot_pct="49.70"),
            dict(hltv_player_id=12928, team_id=navi.id,  nickname="Perfecto",
                 full_name="Ilya Zalutskiy",       rating_3_0="1.080", kd_ratio="1.140", headshot_pct="44.20"),
            dict(hltv_player_id=19536, team_id=navi.id,  nickname="w0nderful",
                 full_name="Mykhailo Mykhailov",   rating_3_0="1.180", kd_ratio="1.220", headshot_pct="55.60"),
            dict(hltv_player_id=20333, team_id=navi.id,  nickname="jL",
                 full_name="Justinas Lekavicius",  rating_3_0="1.120", kd_ratio="1.190", headshot_pct="47.10"),
            dict(hltv_player_id=7998,  team_id=b8.id,    nickname="s1mple",
                 full_name="Oleksandr Kostyliev",  rating_3_0="1.350", kd_ratio="1.520", headshot_pct="62.40"),
            dict(hltv_player_id=16062, team_id=monte.id, nickname="sdy",
                 full_name="Vladyslav Yurchenko",  rating_3_0="1.090", kd_ratio="1.170", headshot_pct="51.30"),
            dict(hltv_player_id=12888, team_id=monte.id, nickname="KaiR0N",
                 full_name="Vladyslav Kayuk",      rating_3_0="1.140", kd_ratio="1.210", headshot_pct="53.80"),
        ]
        for pd in players_data:
            p = get_or_create(db, models.Player, hltv_player_id=pd["hltv_player_id"])
            for k, v in pd.items():
                setattr(p, k, v)
        db.commit()

        # ── 4. Turnyry ─────────────────────────────────────────────────────
        major = db.query(models.Tournament).filter_by(hltv_tournament_id=7902).first()
        if not major:
            major = models.Tournament(
                name="PGL Bucharest Major 2025",
                tier_id=tier_s.id, status_id=st_fin.id,
                start_date=datetime(2025, 3, 1).date(),
                end_date=datetime(2025, 3, 16).date(),
                hltv_tournament_id=7902,
            )
            db.add(major)

        esl = db.query(models.Tournament).filter_by(hltv_tournament_id=7903).first()
        if not esl:
            esl = models.Tournament(
                name="ESL Pro League Season 21",
                tier_id=tier_a.id, status_id=st_up.id,
                start_date=datetime(2025, 5, 1).date(),
                end_date=datetime(2025, 5, 20).date(),
                hltv_tournament_id=7903,
            )
            db.add(esl)

        db.commit()

        # ── 5. Matchi ──────────────────────────────────────────────────────
        now = datetime.now()
        matches_data = [
            dict(hltv_match_id=2380001, tournament_id=major.id,
                 team1_id=navi.id, team2_id=gl.id,    format_id=bo3.id, status_id=st_fin.id,
                 start_time=now - timedelta(days=3), team1_score=2, team2_score=0),
            dict(hltv_match_id=2380002, tournament_id=major.id,
                 team1_id=b8.id,   team2_id=monte.id, format_id=bo3.id, status_id=st_fin.id,
                 start_time=now - timedelta(days=2), team1_score=1, team2_score=2),
            dict(hltv_match_id=2380003, tournament_id=esl.id,
                 team1_id=navi.id, team2_id=monte.id, format_id=bo3.id, status_id=st_up.id,
                 start_time=now + timedelta(days=2), team1_score=0, team2_score=0),
            dict(hltv_match_id=2380004, tournament_id=esl.id,
                 team1_id=b8.id,   team2_id=gl.id,    format_id=bo1.id, status_id=st_up.id,
                 start_time=now + timedelta(days=4), team1_score=0, team2_score=0),
        ]
        for md in matches_data:
            m = get_or_create(db, models.Match, hltv_match_id=md["hltv_match_id"])
            for k, v in md.items():
                setattr(m, k, v)
        db.commit()

        # ── 6. Novyny ──────────────────────────────────────────────────────
        news_data = [
            dict(title="NAVI vyihraly PGL Bucharest Major 2025",
                 content="Natus Vincere pidtverdyly status naikrashchoi komandy Yevropy, zdobuvshы peremohu na PGL Bucharest Major 2025. U finali vony peremohly GamerLegion 2:0. b1t zavershyv turnir z reitynhom 1.38 i zdobuv zvannia MVP.",
                 published_at=now - timedelta(days=3)),
            dict(title="s1mple ta B8 hotuiutsia do ESL Pro League Season 21",
                 content="Lehenda CS2 ta yoho komanda zaiavy ly pro povnu hotovnist do novoho sezonu. Komanda proyshla tyzhnevyi trenuvalnyi zbir u Kyievi ta provela rid uspishnykh skrimiv proty topovykh EU-komand.",
                 published_at=now - timedelta(days=1)),
            dict(title="Monte oholosyly onovlenyi sklad na sezon 2025",
                 content="Ukrainska orhanizatsiia Monte predstavyla novyi roster. Do komandy poveruvsia KaiR0N, a sdy zalyshaiietsia kapitanom. Ochikuietsia, shcho komanda pokrashchyt rezultaty na mizhnarodnii areni.",
                 published_at=now - timedelta(hours=14)),
            dict(title="Analiz: fenomen ukrainskoho CS2 u 2025 rotsi",
                 content="HLTV UA rozbyraie, chomu same Ukraina stala kuzneiu naikrashchykh CS2 talantiv. Vid akademii NAVI do novykh orhanizatsii — ekosystema prodovzhuie zrostaty. Vzhe bilshe 20 ukrainskykh hravtsiv predstavleni v top-50 svitovoho reitynhu.",
                 published_at=now - timedelta(hours=6)),
        ]
        for nd in news_data:
            if not db.query(models.News).filter_by(title=nd["title"]).first():
                db.add(models.News(**nd))
        db.commit()

        print("OK! Dani uspishno zavantazheno!")
        print("  Teams:   " + str(db.query(models.Team).count()))
        print("  Players: " + str(db.query(models.Player).count()))
        print("  Matches: " + str(db.query(models.Match).count()))
        print("  News:    " + str(db.query(models.News).count()))

    except Exception as e:
        db.rollback()
        print("ERROR: " + str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
