from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter()

@router.get("/", response_model=dict)
def compare_players(
    p1: str = Query(..., description="ID of Player 1"),
    p2: str = Query(..., description="ID of Player 2"),
    db: Session = Depends(get_db)
):
    def get_player_data(pid):
        # 1. Profile (Get the name first)
        player = db.execute(text("SELECT name, position, team_id FROM players WHERE player_id = :pid"), {"pid": pid}).fetchone()
        if not player:
            return None
        
        # 2. Stats (Join by NAME because IDs don't match)
        stats = db.execute(text("""
            SELECT 
                SUM(passing_yards) as total_pass, 
                SUM(rushing_yards) as total_rush, 
                SUM(receiving_yards) as total_rec,
                COUNT(*) as games
            FROM (
                SELECT passing_yards, 0 as rushing_yards, 0 as receiving_yards FROM weekly_passing_stats WHERE player_name = :name AND season = 2024
                UNION ALL
                SELECT 0, rushing_yards, 0 FROM weekly_rushing_stats WHERE player_name = :name AND season = 2024
                UNION ALL
                SELECT 0, 0, receiving_yards FROM weekly_receiving_stats WHERE player_name = :name AND season = 2024
            ) as combined
        """), {"name": player.name}).fetchone()

        return {
            "name": player.name,
            "position": player.position,
            "team": str(player.team_id),
            "stats": {
                "games_played": stats.games if stats else 0,
                "passing_yards": stats.total_pass if stats and stats.total_pass else 0,
                "rushing_yards": stats.total_rush if stats and stats.total_rush else 0,
                "receiving_yards": stats.total_rec if stats and stats.total_rec else 0
            }
        }

    data_1 = get_player_data(p1)
    data_2 = get_player_data(p2)

    if not data_1 or not data_2:
        raise HTTPException(status_code=404, detail="One or both players not found")

    return {
        "player_1": data_1,
        "player_2": data_2,
        "comparison": {
            "passing_diff": (data_1["stats"]["passing_yards"] - data_2["stats"]["passing_yards"]),
            "rushing_diff": (data_1["stats"]["rushing_yards"] - data_2["stats"]["rushing_yards"])
        }
    }