from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
import re

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/")
def chat_handler(request: ChatRequest, db: Session = Depends(get_db)):
    user_msg = request.message.lower().strip()
    
    # --- RULE 1: PLAYER SEARCH ("Who is Lamar?", "Show me Josh Allen") ---
    # We look for keywords or assume it's a name search if short
    # Simple regex to extract potential names could go here, but let's try a direct search first.
    
    # Logic: If the message is a name, try to find them.
    # We'll use a loose search.
    if len(user_msg) > 3 and "compare" not in user_msg:
        # Clean up common phrases
        clean_name = user_msg.replace("who is", "").replace("show me", "").replace("stats for", "").strip()
        
        # SQL: Try to find a player with this name
        sql = text("SELECT * FROM players WHERE name ILIKE :search LIMIT 1")
        player = db.execute(sql, {"search": f"%{clean_name}%"}).fetchone()
        
        if player:
            p_data = dict(player._mapping)
            return {
                "type": "player_card",
                "text": f"Here is the profile for {p_data['name']}.",
                "data": p_data
            }

    # --- RULE 2: COMPARISONS ("Compare Lamar", "Difference 2024 2025") ---
    if "compare" in user_msg:
        # Extract name (naive approach: take everything after 'compare')
        target_name = user_msg.split("compare")[-1].strip()
        
        # 1. Find ID
        sql_find = text("SELECT player_id, name, position FROM players WHERE name ILIKE :search LIMIT 1")
        player = db.execute(sql_find, {"search": f"%{target_name}%"}).fetchone()
        
        if player:
            pid = player.player_id
            pos = player.position
            
            # 2. Call our existing Compare Logic (Manual reuse here for speed)
            # Fetch 2024 & 2025
            table_map = {"QB": "season_passing_stats", "RB": "season_rushing_stats", "WR": "season_receiving_stats", "TE": "season_receiving_stats"}
            table = table_map.get(pos, "season_passing_stats") # Default to passing
            
            sql_stats = text(f"SELECT * FROM {table} WHERE player_id = :pid AND season IN (2024, 2025) ORDER BY season")
            stats = db.execute(sql_stats, {"pid": pid}).mappings().all()
            
            data_map = {row["season"]: dict(row) for row in stats}
            
            return {
                "type": "comparison_card",
                "text": f"Comparing 2024 vs 2025 for {player.name} ({pos})",
                "data": {
                    "player": dict(player._mapping),
                    "2024": data_map.get(2024),
                    "2025": data_map.get(2025)
                }
            }
        
    # --- RULE 3: DRAFT SUGGESTIONS ("Who should I draft?", "Draft QB") ---
    if "draft" in user_msg or "pick" in user_msg:
        # Default to WR if no position specified
        pos = "WR" 
        if "qb" in user_msg: pos = "QB"
        if "rb" in user_msg: pos = "RB"
        if "te" in user_msg: pos = "TE"

        # Reuse the logic from your 'draft.py' route (simplified here)
        # We find players with high WAR (Wins Above Replacement) logic - approximated by total yards for now
        table_map = {"QB": "season_passing_stats", "RB": "season_rushing_stats", "WR": "season_receiving_stats", "TE": "season_receiving_stats"}
        table = table_map.get(pos)
        
        # Sort by value DESC (e.g. passing_yards)
        sort_col = "passing_yards" if pos == "QB" else "rushing_yards" if pos == "RB" else "receiving_yards"
        
        sql = text(f"""
            SELECT p.name, p.team_id, s.{sort_col} as value 
            FROM {table} s
            JOIN players p ON p.player_id = s.player_id
            WHERE s.season = 2024
            ORDER BY s.{sort_col} DESC
            LIMIT 5
        """)
        
        results = db.execute(sql).mappings().all()
        
        return {
            "type": "draft_card",
            "text": f"Here are the top {pos} picks based on 2024 performance:",
            "data": [dict(row) for row in results]
        }
    
    # --- FALLBACK ---
    return {
        "type": "text",
        "text": "I'm not sure I understand. Try asking 'Who is [Player Name]' or 'Compare [Player Name]'.",
        "data": None
    }