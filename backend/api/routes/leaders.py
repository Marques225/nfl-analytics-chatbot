from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter()

@router.get("/")
def get_leaders(category: str = "passing", season: int = 2025, db: Session = Depends(get_db)):
    # 1. Map frontend category to DB column
    col_map = {
        "passing": "passing_yards",
        "rushing": "rushing_yards",
        "receiving": "receiving_yards",
        "fantasy": "fantasy_points"
    }
    
    sort_col = col_map.get(category, "passing_yards")
    
    # 2. Query (Safe Join)
    # We join players and stats. We use COALESCE to turn NULLs into 0 for sorting.
    sql = text(f"""
        SELECT p.name, p.team_id, COALESCE(s.{sort_col}, 0) as value, p.headshot_url
        FROM season_stats s
        JOIN players p ON s.gsis_id = p.gsis_id
        WHERE s.season = :season
        ORDER BY value DESC
        LIMIT 5
    """)
    
    try:
        results = db.execute(sql, {"season": season}).mappings().all()
        
        return [
            {
                "rank": i+1,
                "name": row["name"],
                "team": row["team_id"],
                "value": row["value"],
                "image": row["headshot_url"]
            }
            for i, row in enumerate(results)
        ]
    except Exception as e:
        print(f"Error fetching leaders: {e}")
        return []