from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db, engine
from app import models
from app.routers import teams, matches, players, news

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(teams.router)
app.include_router(matches.router)
app.include_router(players.router)
app.include_router(news.router)


@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    stats = {
        "teams": db.query(models.Team).count(),
        "players": db.query(models.Player).count(),
        "matches": db.query(models.Match).count(),
        "news": db.query(models.News).count(),
    }
    recent_matches = db.query(models.Match).order_by(models.Match.start_time.desc()).limit(5).all()
    latest_news = db.query(models.News).order_by(models.News.published_at.desc()).limit(4).all()

    all_matches = db.query(models.Match).all()
    match_by_status = {"upcoming": 0, "live": 0, "finished": 0}
    for m in all_matches:
        if m.status:
            s = m.status.name
            if s in match_by_status:
                match_by_status[s] += 1

    return templates.TemplateResponse("index.html", {
        "request": request,
        "active": "home",
        "stats": stats,
        "recent_matches": recent_matches,
        "latest_news": latest_news,
        "match_by_status": match_by_status,
    })


@app.get("/teams")
def page_teams(request: Request, db: Session = Depends(get_db)):
    teams_list = db.query(models.Team).order_by(models.Team.world_rank).all()
    return templates.TemplateResponse("teams.html", {
        "request": request,
        "active": "teams",
        "teams": teams_list,
    })


@app.get("/matches")
def page_matches(request: Request, db: Session = Depends(get_db)):
    matches_list = db.query(models.Match).order_by(models.Match.start_time.desc()).all()
    return templates.TemplateResponse("matches.html", {
        "request": request,
        "active": "matches",
        "matches": matches_list,
    })


@app.get("/players")
def page_players(request: Request, db: Session = Depends(get_db)):
    players_list = db.query(models.Player).order_by(models.Player.rating_3_0.desc()).all()
    return templates.TemplateResponse("players.html", {
        "request": request,
        "active": "players",
        "players": players_list,
    })


@app.get("/news")
def page_news(request: Request, db: Session = Depends(get_db)):
    articles = db.query(models.News).order_by(models.News.published_at.desc()).all()
    return templates.TemplateResponse("news.html", {
        "request": request,
        "active": "news",
        "news_list": articles,
    })
