from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from schemas import TeamProfile

router = APIRouter()

@router.get("/{team_id}", response_model=TeamProfile)
def get_team(team_id: int, db: Session = Depends(get_db)):
    # 1. Get Basic Team Info
    team_query = text("SELECT id, name, city, conference, division FROM teams WHERE id = :tid")
    team = db.execute(team_query, {"tid": team_id}).fetchone()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # 2. Get Season Stats
    stats_query = text("""
        SELECT season, off_total_yards, off_passing_yards, off_rushing_yards,
               def_total_yards_allowed, def_sacks_made
        FROM season_team_stats
        WHERE team_id = :tid
        ORDER BY season DESC
    """)
    stats = db.execute(stats_query, {"tid": team_id}).fetchall()

    return {
        "id": team.id,
        "name": team.name,
        "city": team.city,
        "conference": team.conference,
        "division": team.division,
        "season_stats": [row._mapping for row in stats]
    }