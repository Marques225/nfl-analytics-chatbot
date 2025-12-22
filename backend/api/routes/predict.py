from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from ml.predictor import predictor

router = APIRouter()

@router.get("/{player_name}")
def predict_performance(player_name: str, db: Session = Depends(get_db)):
    # 1. Find Player
    sql_p = text("SELECT * FROM players WHERE name ILIKE :name LIMIT 1")
    player = db.execute(sql_p, {"name": f"%{player_name}%"}).mappings().first()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
        
    pid = player.get('gsis_id')
    
    # 2. Get 2025 Stats (Current Form)
    sql_s = text("SELECT * FROM season_stats WHERE gsis_id = :pid AND season = 2025")
    stats = db.execute(sql_s, {"pid": pid}).mappings().first()
    
    if not stats:
        return {"player": player['name'], "projection": "No 2025 stats available to base prediction on."}

    # 3. Run Prediction
    projection = predictor.predict_next_game(dict(stats))
    
    return {
        "player": player['name'],
        "team": player['team_id'],
        "projected_fantasy_points": projection,
        "note": "Projection based on 2025 per-game averages using Linear Regression model."
    }