from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
import re
from database import get_db

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

# --- PATTERNS ---
COMP_PATTERN = re.compile(
    r'(?:compare\s+|who is better\s+)?([\w\s\.\'-]+?)\s+(?:vs\.?|or|and)\s+([\w\s\.\'-]+)', 
    re.IGNORECASE
)

EXPLICIT_PATTERN = re.compile(
    r'(?:who is|tell me about|stats for|show me)\s+([\w\s\.\'-]+)', 
    re.IGNORECASE
)

DRAFT_KEYWORDS = {"draft", "rank", "leader", "top player", "best player", "waiver"}

def clean_input(text_str):
    if not text_str: return ""
    clean = text_str.lower().strip()
    # The Antidote for button clicks
    clean = re.sub(r'\(.*?\)', '', clean).strip()
    if clean and clean[-1] in "?!.":
        clean = clean.rstrip("?!.")
    return clean.strip()

def get_top_players_by_position(db, position, limit=5):
    """Helper to fetch top players for a specific position"""
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
    clean_msg = clean_input(user_msg)
    
    print(f"\n⚡ IN: '{user_msg}' | 🧹 CLEAN: '{clean_msg}'") 

    # --- 1. DRAFT BOARD (The Restore Fix) ---
    if any(k in clean_msg for k in DRAFT_KEYWORDS):
        print("🔍 INTENT: Draft Board")
        
        # Fetch Top 5 for each major position
        qbs = get_top_players_by_position(db, 'QB')
        rbs = get_top_players_by_position(db, 'RB')
        wrs = get_top_players_by_position(db, 'WR')
        
        return {
            "response": "Here are the projected Top 5 Leaders by position for 2025:",
            "data": {
                "type": "draft_board", # <--- Tells Frontend to use the Table view
                "qbs": qbs,
                "rbs": rbs,
                "wrs": wrs
            }
        }

    # --- 2. COMPARISON ---
    comp_match = COMP_PATTERN.search(clean_msg)
    if comp_match:
        p1_raw = comp_match.group(1).strip()
        p2_raw = comp_match.group(2).strip()
        print(f"🔍 INTENT: Compare '{p1_raw}' vs '{p2_raw}'")

        sql = text("SELECT * FROM players WHERE name ILIKE :p1 OR name ILIKE :p2 LIMIT 2")
        results = db.execute(sql, {"p1": f"%{p1_raw}%", "p2": f"%{p2_raw}%"}).mappings().all()
        
        p1_data = next((r for r in results if p1_raw.lower() in r['name'].lower()), None)
        p2_data = next((r for r in results if p2_raw.lower() in r['name'].lower()), None)
        
        # Fallback
        if not p1_data and len(results) > 0: p1_data = results[0]
        if not p2_data and len(results) > 1: p2_data = results[1]

        if p1_data and p2_data:
            # We need to fetch their 2025 stats to make the comparison useful
            stats_sql = text("SELECT * FROM season_stats WHERE gsis_id IN (:id1, :id2) AND season = 2025")
            stats = db.execute(stats_sql, {"id1": p1_data['gsis_id'], "id2": p2_data['gsis_id']}).mappings().all()
            
            p1_stats = next((s for s in stats if s['gsis_id'] == p1_data['gsis_id']), {})
            p2_stats = next((s for s in stats if s['gsis_id'] == p2_data['gsis_id']), {})

            return {
                "response": f"Comparing {p1_data['name']} and {p2_data['name']}...",
                "data": {
                    "type": "comparison", # <--- Frontend needs to handle this!
                    "player1": {**dict(p1_data), "stats": dict(p1_stats)},
                    "player2": {**dict(p2_data), "stats": dict(p2_stats)}
                }
            }
        else:
            return {"response": f"I found one of them, but not both. Check spelling for '{p1_raw}' and '{p2_raw}'."}

    # --- 3. EXPLICIT & IMPLICIT SEARCH ---
    target_player = None
    explicit_match = EXPLICIT_PATTERN.search(clean_msg)
    
    if explicit_match:
        target_player = explicit_match.group(1).strip()
    elif len(clean_msg.split()) <= 4:
        target_player = clean_msg

    if target_player:
        sql = text("SELECT gsis_id, name FROM players WHERE name ILIKE :search LIMIT 1")
        player = db.execute(sql, {"search": f"%{target_player}%"}).mappings().first()
        
        if player:
            return {
                "response": f"Here is the profile for {player['name']}.",
                "data": {
                    "type": "player_profile",
                    "player_id": player['gsis_id'],
                    "name": player['name']
                }
            }
        
        if explicit_match:
             return {"response": f"I searched for '{target_player}', but I couldn't find them."}

    return {"response": "I didn't catch that. Try 'Who should I draft?', 'Lamar vs Allen', or just 'CMC'."}