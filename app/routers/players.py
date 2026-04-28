from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/api/players", tags=["Players"])


@router.get("/")
def get_players(db: Session = Depends(get_db)):
    return db.query(models.Player).order_by(models.Player.rating_3_0.desc()).all()


@router.get("/{player_id}")
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
