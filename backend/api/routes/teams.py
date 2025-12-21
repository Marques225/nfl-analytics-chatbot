from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter()

@router.get("/")
def get_teams(db: Session = Depends(get_db)):
    sql = text("SELECT DISTINCT team_id FROM season_team_stats WHERE season = 2025 ORDER BY team_id")
    results = db.execute(sql).fetchall()
    return [{"team_name": row[0], "team_id": row[0]} for row in results]

# --- THE MISSING ENDPOINT FOR DASHBOARD ---
@router.get("/leaders/{category}")
def get_team_leaders(
    category: str,
    season: int = 2025,
    metric: str = "off_total_yards", 
    limit: int = 5,
    db: Session = Depends(get_db)
):
    # Map frontend metrics to DB columns
    valid_metrics = {
        "off_total_yards": "off_total_yards",
        "off_points": "off_total_tds", # Approx if points missing
        "off_passing_yards": "off_total_yards", # Fallback
        "off_rushing_yards": "off_total_yards", # Fallback
        "def_sacks": "def_sacks_made",
        "def_interceptions": "def_interceptions"
    }
    
    db_col = valid_metrics.get(metric, "off_total_yards")

    sql = text(f"""
        SELECT team_id, {db_col} as value
        FROM season_team_stats 
        WHERE season = :season
        ORDER BY {db_col} DESC
        LIMIT :limit
    """)
    
    try:
        results = db.execute(sql, {"season": season, "limit": limit}).mappings().all()
        return [
            {"rank": i+1, "team": row["team_id"], "value": row["value"], "season": season}
            for i, row in enumerate(results)
        ]
    except Exception as e:
        print(f"Error: {e}")
        return []

@router.get("/{team_id}")
def get_team_stats(team_id: str, db: Session = Depends(get_db)):
    sql = text("SELECT * FROM season_team_stats WHERE team_id = :tid AND season = 2025")
    stats = db.execute(sql, {"tid": team_id}).mappings().first()
    if not stats: raise HTTPException(status_code=404, detail="Team not found")
    return dict(stats)