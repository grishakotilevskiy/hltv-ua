from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/news", tags=["News"])


@router.get("/")
def get_news(db: Session = Depends(get_db)):
    return db.query(models.News).order_by(models.News.published_at.desc()).all()


@router.get("/{news_id}")
def get_news_item(news_id: int, db: Session = Depends(get_db)):
    item = db.query(models.News).filter(models.News.id == news_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="News not found")
    return item
