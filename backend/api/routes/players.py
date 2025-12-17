from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from schemas import PlayerProfile, PlayerStats

router = APIRouter()

@router.get("/{player_id}", response_model=PlayerProfile)
def get_player(player_id: str, db: Session = Depends(get_db)):
    # FIXED: Query uses 'player_id'
    player_query = text("SELECT player_id as id, name, position, team_id as team FROM players WHERE player_id = :pid")
    player = db.execute(player_query, {"pid": player_id}).fetchone()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # FIXED: Changed 'pfr_player_id' to 'player_id' in both SELECTs below
    stats_query = text("""
        SELECT season, week, passing_yards, rushing_yards, receiving_yards
        FROM weekly_passing_stats WHERE player_id = :pid
        UNION ALL
        SELECT season, week, 0, rushing_yards, 0
        FROM weekly_rushing_stats WHERE player_id = :pid
        ORDER BY season DESC, week DESC
        LIMIT 5
    """)
    stats = db.execute(stats_query, {"pid": player_id}).fetchall()

    return {
        "id": player.id,
        "name": player.name,
        "position": player.position,
        "team": str(player.team),
        "recent_stats": [
            {
                "season": row.season,
                "week": row.week,
                "passing_yards": row.passing_yards or 0,
                "rushing_yards": row.rushing_yards or 0,
                "receiving_yards": row.receiving_yards or 0
            }
            for row in stats
        ]
    }