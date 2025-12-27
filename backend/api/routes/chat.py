from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
import re
import requests 
from database import get_db, engine
from ml.trade_agent import trade_agent
from api.auth import get_current_user 

router = APIRouter()
MODEL_SERVICE_URL = "http://127.0.0.1:8001/generate"

class ChatRequest(BaseModel):
    message: str

# --- KNOWLEDGE BASE ---
PLAYER_KNOWLEDGE_BASE = []
def refresh_knowledge_base():
    global PLAYER_KNOWLEDGE_BASE
    try:
        with engine.connect() as conn:
            # We explicitly fetch top 500 players so common names like "Josh" default to the best one (Josh Allen)
            sql = text("""
                SELECT p.name, p.gsis_id FROM players p
                LEFT JOIN season_stats s ON p.gsis_id = s.gsis_id AND s.season = 2025
                WHERE p.position IN ('QB', 'RB', 'WR', 'TE')
                ORDER BY s.fantasy_points DESC NULLS LAST LIMIT 500
            """)
            PLAYER_KNOWLEDGE_BASE = [(r[0], r[1]) for r in conn.execute(sql).fetchall()]
            print(f"✅ Knowledge Base Loaded: {len(PLAYER_KNOWLEDGE_BASE)} players.")
    except: pass
refresh_knowledge_base()

def find_best_entity_match(user_text):
    user_text_lower = user_text.lower()
    
    # 1. Check Full Name (Exact Substring) - Highest Priority
    for name, pid in PLAYER_KNOWLEDGE_BASE:
        if name.lower() in user_text_lower: return name, pid
        
    # 2. Check Last Name (Exact Word)
    user_words = user_text_lower.split()
    for name, pid in PLAYER_KNOWLEDGE_BASE:
        if name.split()[-1].lower() in user_words: return name, pid
        
    # 3. Check First Name (Exact Word) - NEW FIX
    # This enables "Saquon", "Lamar", "Patrick" to work
    for name, pid in PLAYER_KNOWLEDGE_BASE:
        if name.split()[0].lower() in user_words: return name, pid
        
    return None, None

def get_top_players_by_position(db, position, limit=5):
    sql = text("""
        SELECT p.name, p.gsis_id as player_id, p.team_id as team, s.fantasy_points as fantasy
        FROM season_stats s JOIN players p ON s.gsis_id = p.gsis_id
        WHERE s.season = 2025 AND p.position = :pos ORDER BY s.fantasy_points DESC LIMIT :limit
    """)
    return db.execute(sql, {"pos": position, "limit": limit}).mappings().all()

# --- ENDPOINT ---
@router.post("/")
def chat_endpoint(request: ChatRequest, 
                  db: Session = Depends(get_db), 
                  user: dict = Depends(get_current_user)):
    
    user_msg = request.message
    msg_lower = user_msg.lower()
    print(f"🔒 User: {user['email']} | Msg: {user_msg}") 

    # --- A. INTENT: TRADE ANALYZER ---
    trade_match = re.search(r"trade\s+(.+?)\s+for\s+(.+)", msg_lower)
    if trade_match:
        p_give_raw = trade_match.group(1).strip()
        p_receive_raw = trade_match.group(2).strip()
        data, advice = trade_agent.analyze_trade(p_give_raw, p_receive_raw)
        if data:
            return {"response": advice, "data": {"type": "trade_analysis", "player1": data['give'], "player2": data['receive'], "diff": data['diff'], "verdict": data['verdict']}}
        else:
             return {"response": advice}

    # --- B. INTENT: DRAFT / LISTS ---
    if any(k in msg_lower for k in ["top", "best", "draft", "leader"]):
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

    # --- C. INTENT: COMPARISON (FIXED) ---
    # Now checks for "compare", " vs ", " or ", " and "
    # AND ensures we actually found 2 players.
    if " vs " in msg_lower or " or " in msg_lower or "compare " in msg_lower or " better" in msg_lower:
        # Split by common separators: vs, or, and, comma
        parts = re.split(r'\s+(?:vs\.?|or|and|,)\s+', msg_lower)
        
        # We need to find at least 2 valid names in these parts
        found_ids = []
        found_names = []
        
        # Scan extracted chunks for names
        for p in parts:
            name, pid = find_best_entity_match(p)
            if pid and pid not in found_ids:
                found_ids.append(pid)
                found_names.append(name)
                
        # If we found at least 2, trigger comparison
        if len(found_ids) >= 2:
            id1, id2 = found_ids[0], found_ids[1]
            n1, n2 = found_names[0], found_names[1]
            
            sql_stats = text("SELECT * FROM season_stats WHERE gsis_id IN (:id1, :id2) AND season = 2025")
            stats_rows = db.execute(sql_stats, {"id1": id1, "id2": id2}).mappings().all()
            
            s1 = next((s for s in stats_rows if s['gsis_id'] == id1), {})
            s2 = next((s for s in stats_rows if s['gsis_id'] == id2), {})
            
            sql_p = text("SELECT * FROM players WHERE gsis_id IN (:id1, :id2)")
            p_rows = db.execute(sql_p, {"id1": id1, "id2": id2}).mappings().all()
            
            pd1 = next((p for p in p_rows if p['gsis_id'] == id1), {})
            pd2 = next((p for p in p_rows if p['gsis_id'] == id2), {})

            return {
                "response": f"Comparing {n1} and {n2}...",
                "data": {
                    "type": "comparison",
                    "player1": {**dict(pd1), "stats": dict(s1)},
                    "player2": {**dict(pd2), "stats": dict(s2)}
                }
            }

    # --- D. INTENT: RAG ---
    matched_name, matched_id = find_best_entity_match(user_msg)
    if matched_name:
        clean_input = re.sub(r'[^a-zA-Z\s]', '', user_msg).strip()
        clean_lower = clean_input.lower()
        name_lower = matched_name.lower()

        # Check if user typed JUST the name OR "who is [name]"
        if clean_lower == name_lower or clean_lower == f"who is {name_lower}":
             return {
                 "response": f"Here is the profile for {matched_name}:",
                 "data": {"type": "player_profile", "player_id": matched_id, "name": matched_name}
             }
        
        # Otherwise, ask the AI
        try:
            resp = requests.post(MODEL_SERVICE_URL, json={"player_name": matched_name, "question": user_msg})
            ai_res = resp.json().get("answer", "Error.") if resp.status_code == 200 else "Error."
        except: ai_res = "Service offline."
        return {"response": ai_res, "data": {"type": "text_only"}}

    return {"response": "Try 'Trade Lamar for CMC' or 'How many points did Saquon score?'"}