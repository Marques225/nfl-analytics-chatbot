from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.teams import Team

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.get("/")
def get_teams(db: Session = Depends(get_db)):
    return db.query(Team).all()

@router.get("/{team_id}")
def get_team(team_id: int, db: Session = Depends(get_db)):
    return db.query(Team).filter(Team.id == team_id).first()
