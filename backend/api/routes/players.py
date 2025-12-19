from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from schemas import Player  # Ensure Player schema is imported
from sqlalchemy import text

router = APIRouter()

@router.get("/", response_model=List[dict])
def get_players(
    skip: int = 0, 
    limit: int = 10, 
    search: Optional[str] = None, # <--- NEW: Search Parameter
    db: Session = Depends(get_db)
):
    if search:
        # Case-insensitive search for name
        sql = text("SELECT * FROM players WHERE name ILIKE :search LIMIT :limit OFFSET :skip")
        params = {"search": f"%{search}%", "limit": limit, "skip": skip}
    else:
        sql = text("SELECT * FROM players LIMIT :limit OFFSET :skip")
        params = {"limit": limit, "skip": skip}

    results = db.execute(sql, params).mappings().all()
    return [dict(row) for row in results]

# ... (keep your get_player_details endpoint below this) ...
@router.get("/{player_id}", response_model=dict)
def get_player_details(player_id: str, db: Session = Depends(get_db)):
    # ... (Keep existing code for single player details) ...
    # Make sure this function stays exactly as it was!
    # If you need me to paste the whole file to be safe, let me know.
    # Below is the logic we wrote previously:
    player = db.execute(text("SELECT * FROM players WHERE player_id = :pid"), {"pid": player_id}).fetchone()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    season_stats = db.execute(text("SELECT * FROM season_passing_stats WHERE player_id = :pid ORDER BY season"), {"pid": player_id}).fetchall()
    if not season_stats:
         season_stats = db.execute(text("SELECT * FROM season_rushing_stats WHERE player_id = :pid ORDER BY season"), {"pid": player_id}).fetchall()
    if not season_stats:
         season_stats = db.execute(text("SELECT * FROM season_receiving_stats WHERE player_id = :pid ORDER BY season"), {"pid": player_id}).fetchall()

    return {
        "player_info": dict(player._mapping),
        "season_stats": [dict(row._mapping) for row in season_stats]
    }