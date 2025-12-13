from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.players import Player

router = APIRouter(prefix="/players", tags=["Players"])

@router.get("/")
def get_players(db: Session = Depends(get_db)):
    return db.query(Player).limit(50).all()

@router.get("/{player_id}")
def get_player(player_id: int, db: Session = Depends(get_db)):
    return db.query(Player).filter(Player.id == player_id).first()
