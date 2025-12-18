from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from database import get_db

router = APIRouter()

@router.get("/{team_id}", response_model=dict)
def get_team_details(team_id: str, db: Session = Depends(get_db)):
    # 1. Get Basic Info
    # FIXED: Query 'id' and 'name' (matches your schema)
    team = db.execute(text("SELECT * FROM teams WHERE id = :tid"), {"tid": team_id}).fetchone()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # 2. Get Season Stats History
    stats = db.execute(text("""
        SELECT * FROM season_team_stats 
        WHERE team_id = :tid 
        ORDER BY season DESC
    """), {"tid": team_id}).fetchall()

    return {
        "team_info": {
            "team_id": team.id,
            "team_name": team.name,   # FIXED: Mapped 'name' -> 'team_name'
            "conference": team.conference
        },
        "season_stats": [dict(row._mapping) for row in stats]
    }

@router.get("/leaders/{category}", response_model=List[dict])
def get_team_leaders(
    category: str,
    season: int = 2024,
    metric: str = Query(..., description="Metric to sort by"),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    valid_metrics = [
        "off_games_played", "off_total_yards", "off_passing_yards", "off_rushing_yards", 
        "off_passing_tds", "off_rushing_tds", "off_interceptions_thrown", "off_fumbles_lost",
        "def_total_yards_allowed", "def_passing_yards_allowed", "def_rushing_yards_allowed",
        "def_passing_tds_allowed", "def_rushing_tds_allowed", "def_sacks_made"
    ]

    if metric not in valid_metrics:
        raise HTTPException(status_code=400, detail=f"Invalid metric. Choose from: {valid_metrics}")

    # FIXED SQL:
    # 1. Uses 't.name' instead of 't.team_name'
    # 2. Removed 't.abbreviation' (since the column doesn't exist)
    sql = text(f"""
        SELECT 
            t.name,
            s.{metric} as value
        FROM season_team_stats s
        JOIN teams t ON t.id = s.team_id 
        WHERE s.season = :season
        ORDER BY s.{metric} DESC
        LIMIT :limit
    """)

    try:
        results = db.execute(sql, {"season": season, "limit": limit}).fetchall()
    except Exception as e:
        print(f"Query Error: {e}")
        return []

    return [
        {
            "rank": i + 1,
            "team": row.name, 
            "value": row.value
        }
        for i, row in enumerate(results)
    ]