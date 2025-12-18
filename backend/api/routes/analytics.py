from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter()

@router.get("/compare-seasons/{player_id}", response_model=dict)
def compare_seasons(
    player_id: str,
    position: str = Query(..., description="Player position (QB, RB, WR, TE)"),
    db: Session = Depends(get_db)
):
    """
    Compares a player's stats between 2024 (Previous) and 2025 (Current).
    """
    # 1. Determine which table to query
    table_map = {
        "QB": "season_passing_stats",
        "RB": "season_rushing_stats",
        "WR": "season_receiving_stats",
        "TE": "season_receiving_stats"
    }
    
    if position not in table_map:
        raise HTTPException(status_code=400, detail="Invalid position. Use QB, RB, WR, or TE.")
    
    table_name = table_map[position]

    # 2. Query for 2024 and 2025
    # FIXED: Changed years to 2024 and 2025
    sql = text(f"""
        SELECT season, * FROM {table_name} 
        WHERE player_id = :pid AND season IN (2024, 2025)
        ORDER BY season ASC
    """)
    
    try:
        results = db.execute(sql, {"pid": player_id}).mappings().all()
    except Exception as e:
        print(f"Query Error: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    if not results:
        # It's possible the ETL loaded weekly stats but hasn't aggregated Season Stats for 2025 yet.
        # But let's assume it has.
        raise HTTPException(status_code=404, detail="No stats found for this player in 2024 or 2025")

    # 3. Format the Data
    data_map = {row["season"]: dict(row) for row in results}
    
    season_prev = data_map.get(2024)
    season_curr = data_map.get(2025)
    
    response = {
        "player_id": player_id,
        "position": position,
        "2024": season_prev,
        "2025": season_curr,
        "diff": {}
    }

    # 4. Calculate Differences (Current - Previous)
    if season_prev and season_curr:
        metrics = []
        if position == "QB":
            metrics = ["passing_yards", "passing_tds", "interceptions", "sacks"]
        elif position == "RB":
            metrics = ["rushing_yards", "rushing_tds", "attempts"]
        else:
            metrics = ["receiving_yards", "receiving_tds"] 

        for m in metrics:
            val_prev = season_prev.get(m, 0) or 0
            val_curr = season_curr.get(m, 0) or 0
            response["diff"][m] = val_curr - val_prev

    return response