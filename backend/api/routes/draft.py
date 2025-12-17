from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from database import get_db
from schemas import LeaderEntry

router = APIRouter()

@router.get("/", response_model=List[LeaderEntry])
def get_draft_suggestions(
    position: str,
    db: Session = Depends(get_db)
):
    table_map = {
        "QB": ("weekly_passing_stats", "passing_yards"),
        "RB": ("weekly_rushing_stats", "rushing_yards"),
        "WR": ("weekly_receiving_stats", "receiving_yards"),
        "TE": ("weekly_receiving_stats", "receiving_yards")
    }
    
    if position not in table_map:
        return []

    table_name, metric = table_map[position]

    # FIXED: Joining on NAME instead of ID
    sql = text(f"""
        SELECT 
            p.player_id, 
            p.name, 
            p.team_id as team, 
            SUM(w.{metric}) as value
        FROM {table_name} w
        JOIN players p ON p.name = w.player_name
        WHERE w.season = 2024
        GROUP BY p.player_id, p.name, p.team_id
        ORDER BY value DESC
        LIMIT 5
    """)
    
    results = db.execute(sql).fetchall()

    return [
        {
            "rank": i + 1,
            "player_id": str(row.player_id),
            "name": row.name,
            "team": str(row.team),
            "value": row.value
        }
        for i, row in enumerate(results)
    ]