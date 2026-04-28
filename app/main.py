from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.routers import teams, matches, players, news

app = FastAPI(
    title="HLTV UA",
    description="Агрегатор матчів, новин та статистики українських CS2 команд і гравців",
    version="1.0.0",
)

# Static files & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include API routers (keep JSON API under /api prefix)
app.include_router(teams.router)
app.include_router(matches.router)
app.include_router(players.router)
app.include_router(news.router)


# ─── HTML pages ───────────────────────────────────────────────────────────────

@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    stats = {
        "teams":   db.query(models.Team).count(),
        "players": db.query(models.Player).count(),
        "matches": db.query(models.Match).count(),
        "news":    db.query(models.News).count(),
    }
    recent_matches = (
        db.query(models.Match)
        .order_by(models.Match.start_time.desc())
        .limit(5)
        .all()
    )
    latest_news = (
        db.query(models.News)
        .order_by(models.News.published_at.desc())
        .limit(4)
        .all()
    )
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "active": "home",
            "stats": stats,
            "recent_matches": recent_matches,
            "latest_news": latest_news,
        },
    )


@app.get("/teams")
def page_teams(request: Request, db: Session = Depends(get_db)):
    team_list = db.query(models.Team).order_by(models.Team.world_rank).all()
    return templates.TemplateResponse(
        "teams.html",
        {"request": request, "active": "teams", "teams": team_list},
    )


@app.get("/matches")
def page_matches(request: Request, db: Session = Depends(get_db)):
    match_list = (
        db.query(models.Match)
        .order_by(models.Match.start_time.desc())
        .all()
    )
    return templates.TemplateResponse(
        "matches.html",
        {"request": request, "active": "matches", "matches": match_list},
    )


@app.get("/players")
def page_players(request: Request, db: Session = Depends(get_db)):
    player_list = (
        db.query(models.Player)
        .order_by(models.Player.rating_3_0.desc())
        .all()
    )
    return templates.TemplateResponse(
        "players.html",
        {"request": request, "active": "players", "players": player_list},
    )


@app.get("/news")
def page_news(request: Request, db: Session = Depends(get_db)):
    articles = (
        db.query(models.News)
        .order_by(models.News.published_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "news.html",
        {"request": request, "active": "news", "news_list": articles},
    )
