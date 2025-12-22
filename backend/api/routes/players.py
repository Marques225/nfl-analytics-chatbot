from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
import logging
from scipy import stats # You might need to pip install scipy if you haven't, but we can do simple math without it too. Let's stick to simple math to avoid huge installs.

router = APIRouter()
logger = logging.getLogger(__name__)

def calculate_fantasy(stats):
    if not stats: return 0.0
    try:
        if stats.get('fantasy_points'): return float(stats.get('fantasy_points'))
        p_yds = float(stats.get('passing_yards', 0) or 0)
        p_tds = float(stats.get('passing_tds', 0) or 0)
        ints = float(stats.get('interceptions', 0) or 0)
        r_yds = float(stats.get('rushing_yards', 0) or 0)
        r_tds = float(stats.get('rushing_tds', 0) or 0)
        rec_yds = float(stats.get('receiving_yards', 0) or 0)
        rec_tds = float(stats.get('receiving_tds', 0) or 0)
        recs = float(stats.get('receptions', 0) or 0)
        return round((p_yds/25) + (p_tds*4) - (ints*2) + (r_yds/10) + (r_tds*6) + (rec_yds/10) + (rec_tds*6) + recs, 2)
    except:
        return 0.0

@router.get("/")
def search_players(search: str = "", limit: int = 10, db: Session = Depends(get_db)):
    sql = text("SELECT * FROM players WHERE name ILIKE :search ORDER BY name ASC LIMIT :limit")
    results = db.execute(sql, {"search": f"%{search}%", "limit": limit}).mappings().all()
    return [dict(r) for r in results]

@router.get("/{player_id}")
def get_player_profile(player_id: str, db: Session = Depends(get_db)):
    # 1. Get Player Info
    sql_p = text("SELECT * FROM players WHERE gsis_id = :pid LIMIT 1")
    player = db.execute(sql_p, {"pid": player_id}).mappings().first()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # 2. Get History
    pid = player['gsis_id']
    sql_s = text("SELECT * FROM season_stats WHERE gsis_id = :pid ORDER BY season ASC")
    stats = db.execute(sql_s, {"pid": pid}).mappings().all()
    season_stats = [dict(s) for s in stats]
    
    # 3. Calculate Comparison (Deltas)
    comparison = {}
    percentile_rank = "N/A"
    
    if len(season_stats) >= 1:
        current = season_stats[-1] # Most recent season (2025)
        
        # --- NEW: Percentile Logic ---
        # Get ALL players' fantasy points for 2025 to rank this player
        sql_rank = text("SELECT fantasy_points FROM season_stats WHERE season = 2025")
        all_scores = [float(r['fantasy_points'] or 0) for r in db.execute(sql_rank).mappings().all()]
        
        if all_scores:
            my_score = float(current.get('fantasy_points', 0))
            # Sort scores
            all_scores.sort()
            # Find index
            rank = sum(1 for x in all_scores if x < my_score)
            percentile = (rank / len(all_scores)) * 100
            percentile_rank = f"Top {100 - int(percentile)}%" # e.g., "Top 5%"

        # Delta Logic (from before)
        if len(season_stats) >= 2:
            previous = season_stats[-2]
            comparison = {
                "season_diff": f"{current['season']} vs {previous['season']}",
                "passing_yards_delta": float(current.get('passing_yards', 0)) - float(previous.get('passing_yards', 0)),
                "rushing_yards_delta": float(current.get('rushing_yards', 0)) - float(previous.get('rushing_yards', 0)),
                "fantasy_points_delta": round(calculate_fantasy(current) - calculate_fantasy(previous), 2),
                "percentile": percentile_rank # <--- Added this
            }
        else:
            # If only 1 season exists, we can still show percentile
            comparison = {
                "season_diff": "No previous season",
                "percentile": percentile_rank
            }

    return {
        "player_info": dict(player),
        "season_stats": season_stats,
        "comparison": comparison
    }