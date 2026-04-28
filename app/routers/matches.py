from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/api/matches", tags=["Matches"])


@router.get("/")
def get_matches(db: Session = Depends(get_db)):
    return db.query(models.Match).order_by(models.Match.start_time.desc()).all()


@router.get("/{match_id}")
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match
