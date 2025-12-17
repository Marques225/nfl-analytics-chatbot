from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from database import get_db
from schemas import LeaderEntry

router = APIRouter()

# --- 1. Season Leaders (Unchanged) ---
@router.get("/{season}/{category}", response_model=List[LeaderEntry])
def get_season_leaders(
    season: int,
    category: str,
    metric: str = Query(..., description="Metric to sort by"),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    valid_tables = {
        "passing": "season_passing_stats",
        "rushing": "season_rushing_stats",
        "receiving": "season_receiving_stats"
    }
    
    if category not in valid_tables:
        return []

    table_name = valid_tables[category]
    
    sql = text(f"""
        SELECT 
            p.player_id,
            p.name,
            p.team_id as team,
            s.{metric} as value
        FROM {table_name} s
        JOIN players p ON p.player_id = s.player_id
        WHERE s.season = :season
        ORDER BY s.{metric} DESC
        LIMIT :limit OFFSET :skip
    """)
    
    try:
        results = db.execute(sql, {"season": season, "limit": limit, "skip": skip}).fetchall()
    except Exception as e:
        print(f"Query Error: {e}")
        return []

    return [
        {
            "rank": skip + i + 1,
            "player_id": str(row.player_id),
            "name": row.name,
            "team": str(row.team),
            "value": row.value
        }
        for i, row in enumerate(results)
    ]

# --- 2. Weekly Leaders (FIXED JOIN) ---
@router.get("/{season}/{week}/{category}", response_model=List[LeaderEntry])
def get_weekly_leaders(
    season: int,
    week: int,
    category: str,
    metric: str = Query(..., description="Metric to sort by"),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    valid_tables = {
        "passing": "weekly_passing_stats",
        "rushing": "weekly_rushing_stats",
        "receiving": "weekly_receiving_stats"
    }
    
    if category not in valid_tables:
        return []

    table_name = valid_tables[category]
    
    # FIXED: Joining on NAME
    sql = text(f"""
        SELECT 
            p.player_id,
            p.name,
            p.team_id as team,
            w.{metric} as value
        FROM {table_name} w
        JOIN players p ON p.name = w.player_name
        WHERE w.season = :season AND w.week = :week
        ORDER BY w.{metric} DESC
        LIMIT :limit
    """)
    
    try:
        results = db.execute(sql, {"season": season, "week": week, "limit": limit}).fetchall()
    except Exception as e:
        print(f"Query Error: {e}")
        return []

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