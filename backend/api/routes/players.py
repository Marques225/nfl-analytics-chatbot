from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from sqlalchemy import text

router = APIRouter()

@router.get("/", response_model=List[dict])
def get_players(
    skip: int = 0, 
    limit: int = 10, 
    search: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    if search:
        sql = text("SELECT * FROM players WHERE name ILIKE :search LIMIT :limit OFFSET :skip")
        params = {"search": f"%{search}%", "limit": limit, "skip": skip}
    else:
        sql = text("SELECT * FROM players LIMIT :limit OFFSET :skip")
        params = {"limit": limit, "skip": skip}

    results = db.execute(sql, params).mappings().all()
    # Ensure 'player_id' exists for the frontend link
    return [dict(row) | {"player_id": row["gsis_id"]} for row in results]

@router.get("/{player_id}", response_model=dict)
def get_player_details(player_id: str, db: Session = Depends(get_db)):
    # 1. Get Player Info
    player = db.execute(text("SELECT * FROM players WHERE gsis_id = :pid"), {"pid": player_id}).fetchone()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # 2. Get Season Stats (The New Fat Table)
    sql_stats = text("""
        SELECT * FROM season_stats 
        WHERE gsis_id = :pid 
        ORDER BY season DESC
    """)
    season_stats = db.execute(sql_stats, {"pid": player_id}).mappings().all()
    stats_data = [dict(row) for row in season_stats]

    # 3. COMPATIBILITY LAYER (The Fix)
    # The frontend might be looking for "passing_yards" directly on the object for the current season.
    # Let's grab the most recent season (2025) and flatten it into the main object.
    
    latest_stats = stats_data[0] if stats_data else {}
    
    response = {
        "player_info": dict(player._mapping) | {"player_id": player.gsis_id},
        "season_stats": stats_data,
        
        # Flattened fields for older frontend code:
        "passing_yards": latest_stats.get("passing_yards", 0),
        "rushing_yards": latest_stats.get("rushing_yards", 0),
        "receiving_yards": latest_stats.get("receiving_yards", 0),
        "passing_tds": latest_stats.get("passing_tds", 0),
        "rushing_tds": latest_stats.get("rushing_tds", 0),
        "receiving_tds": latest_stats.get("receiving_tds", 0),
        "team": player.team_id,
        "position": player.position
    }
    
    return response