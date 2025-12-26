from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
import re
import requests 
import time
from database import get_db, engine

router = APIRouter()
MODEL_SERVICE_URL = "http://127.0.0.1:8001/generate"

class ChatRequest(BaseModel):
    message: str

# --- 1. ADVANCED ENTITY KNOWLEDGE BASE ---
# We load players into memory, SORTED BY FANTASY POINTS.
# This ensures "Jackson" matches Lamar (Rank 1) before Trishton (Rank 500).
PLAYER_KNOWLEDGE_BASE = []

def refresh_knowledge_base():
    global PLAYER_KNOWLEDGE_BASE
    try:
        with engine.connect() as conn:
            # Fetch Name, ID, Position, and Points. Sort by Points DESC.
            sql = text("""
                SELECT p.name, p.gsis_id, s.fantasy_points
                FROM players p
                LEFT JOIN season_stats s ON p.gsis_id = s.gsis_id AND s.season = 2025
                WHERE p.position IN ('QB', 'RB', 'WR', 'TE')
                ORDER BY s.fantasy_points DESC NULLS LAST
                LIMIT 500
            """)
            results = conn.execute(sql).fetchall()
            # Store as tuple: (Name, ID)
            PLAYER_KNOWLEDGE_BASE = [(r[0], r[1]) for r in results]
            print(f"✅ Knowledge Base Loaded: {len(PLAYER_KNOWLEDGE_BASE)} players indexed by popularity.")
    except Exception as e:
        print(f"⚠️ KB Load Failed: {e}")

# Load on startup
refresh_knowledge_base()

def find_best_entity_match(user_text):
    """
    Scans the user text for known player names using the Weighted List.
    """
    user_text_lower = user_text.lower()
    
    # 1. Check Full Names (Highest Confidence)
    for name, pid in PLAYER_KNOWLEDGE_BASE:
        if name.lower() in user_text_lower:
            return name, pid
            
    # 2. Check Last Names (Medium Confidence)
    # Since the list is sorted by Popularity, "Jackson" will match Lamar first.
    for name, pid in PLAYER_KNOWLEDGE_BASE:
        parts = name.split()
        if len(parts) > 1:
            last_name = parts[-1].lower()
            # Ensure the last name is a distinct word (avoid matching "son" in "season")
            if f" {last_name} " in f" {user_text_lower} " or user_text_lower.endswith(last_name):
                return name, pid
                
    # 3. Check First Names (Low Confidence, e.g. "Saquon")
    for name, pid in PLAYER_KNOWLEDGE_BASE:
        first_name = name.split()[0].lower()
        if f" {first_name} " in f" {user_text_lower} ":
            return name, pid
            
    return None, None

# --- HELPERS ---
def get_top_players_by_position(db, position, limit=5):
    sql = text("""
        SELECT p.name, p.gsis_id as player_id, p.team_id as team, s.fantasy_points as fantasy
        FROM season_stats s
        JOIN players p ON s.gsis_id = p.gsis_id
        WHERE s.season = 2025 AND p.position = :pos
        ORDER BY s.fantasy_points DESC
        LIMIT :limit
    """)
    return db.execute(sql, {"pos": position, "limit": limit}).mappings().all()

@router.post("/")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    user_msg = request.message
    
    print(f"\n⚡ IN: '{user_msg}'") 

    # --- A. INTENT: DRAFT / LISTS ---
    msg_lower = user_msg.lower()
    if "top" in msg_lower or "best" in msg_lower or "draft" in msg_lower or "leader" in msg_lower:
        print("🔍 INTENT: Draft/Leader Board")
        pos = None
        if "qb" in msg_lower or "quarterback" in msg_lower: pos = "QB"
        elif "rb" in msg_lower or "running" in msg_lower: pos = "RB"
        elif "wr" in msg_lower or "receiver" in msg_lower: pos = "WR"
        
        return {
            "response": f"Here are the top {pos if pos else 'players'} for 2025:",
            "data": {
                "type": "draft_board", 
                "qbs": get_top_players_by_position(db, 'QB') if not pos or pos=='QB' else None,
                "rbs": get_top_players_by_position(db, 'RB') if not pos or pos=='RB' else None,
                "wrs": get_top_players_by_position(db, 'WR') if not pos or pos=='WR' else None
            }
        }

    # --- B. INTENT: COMPARISON ---
    if " vs " in msg_lower or " or " in msg_lower:
         return {"response": "Comparison feature active."}

    # --- C. INTENT: PLAYER QUESTIONS (RAG) ---
    # Use the Knowledge Base to find the player
    matched_name, matched_id = find_best_entity_match(user_msg)
    
    if matched_name:
        print(f"🧠 SMART MATCH: '{user_msg}' -> Found '{matched_name}'")
        
        # 1. Profile Check (User just typed the name)
        # Remove common punctuation/spaces
        clean_input = re.sub(r'[^a-zA-Z\s]', '', user_msg).strip()
        if clean_input.lower() == matched_name.lower() or clean_input.lower() == matched_name.split()[-1].lower():
             return {
                "response": f"Here is the profile for {matched_name}:",
                "data": {"type": "player_profile", "player_id": matched_id, "name": matched_name}
            }
            
        # 2. Question -> RAG
        try:
            resp = requests.post(MODEL_SERVICE_URL, json={"player_name": matched_name, "question": user_msg})
            if resp.status_code == 200:
                ai_response = resp.json().get("answer", "No answer generated.")
            else:
                ai_response = "I'm having trouble connecting to my brain service."
        except:
            ai_response = "My brain (Model Service) is offline."
            
        return {"response": ai_response, "data": {"type": "text_only"}}

    return {"response": "I didn't catch that. Try 'Lamar stats' or 'Top QBs'."}