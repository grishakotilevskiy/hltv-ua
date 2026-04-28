from fastapi import FastAPI
from app.routers import teams, matches, players, news

app = FastAPI(
    title="HLTV UA",
    description="Агрегатор матчів, новин та статистики українських CS2 команд і гравців",
    version="1.0.0",
)

app.include_router(teams.router)
app.include_router(matches.router)
app.include_router(players.router)
app.include_router(news.router)


@app.get("/")
def root():
    return {
        "project": "HLTV UA",
        "description": "Агрегатор українського CS2 контенту",
        "endpoints": ["/teams", "/matches", "/players", "/news"],
    }
