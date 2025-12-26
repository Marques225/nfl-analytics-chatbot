from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
import re
from database import get_db
from ml.rag_system import rag 

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

# --- PATTERNS ---
COMP_PATTERN = re.compile(
    r'(?:compare\s+|who is better\s+)?([\w\s\.\'-]+?)\s+(?:vs\.?|or|and)\s+([\w\s\.\'-]+)', 
    re.IGNORECASE
)

QUESTION_PATTERN = re.compile(
    r'(how many|what is|did|does|stats for)\s+([\w\s\.\'-]+)',
    re.IGNORECASE
)

DRAFT_KEYWORDS = {"draft", "rank", "leader", "top player", "best player", "waiver"}

def clean_input(text_str):
    if not text_str: return ""
    clean = text_str.lower().strip()
    clean = re.sub(r'\(.*?\)', '', clean).strip()
    if clean and clean[-1] in "?!.":
        clean = clean.rstrip("?!.")
    return clean.strip()

def extract_player_name(text_chunk):
    stopwords = ["fantasy", "points", "did", "does", "he", "she", "score", "get", "have", "make", "in", "the", "year", "season"]
    words = text_chunk.split()
    filtered_words = [w for w in words if w.lower() not in stopwords]
    return " ".join(filtered_words).strip()

def get_top_players_by_position(db, position, limit=5):
    """Helper for Draft Board"""
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
    
    print(f"\n⚡ IN: '{user_msg}'") 

    # --- 1. DRAFT BOARD ---
    if any(k in clean_msg for k in DRAFT_KEYWORDS):
        print("🔍 INTENT: Draft Board")
        qbs = get_top_players_by_position(db, 'QB')
        rbs = get_top_players_by_position(db, 'RB')
        wrs = get_top_players_by_position(db, 'WR')
        
        return {
            "response": "Here are the projected Top 5 Fantasy Leaders for 2025:",
            "data": {
                "type": "draft_board", 
                "qbs": qbs, "rbs": rbs, "wrs": wrs
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
        
        if not p1_data and len(results) > 0: p1_data = results[0]
        if not p2_data and len(results) > 1: p2_data = results[1]

        if p1_data and p2_data:
            stats_sql = text("SELECT * FROM season_stats WHERE gsis_id IN (:id1, :id2) AND season = 2025")
            stats = db.execute(stats_sql, {"id1": p1_data['gsis_id'], "id2": p2_data['gsis_id']}).mappings().all()
            
            p1_stats = next((s for s in stats if s['gsis_id'] == p1_data['gsis_id']), {})
            p2_stats = next((s for s in stats if s['gsis_id'] == p2_data['gsis_id']), {})

            return {
                "response": f"Comparing {p1_data['name']} and {p2_data['name']}...",
                "data": {
                    "type": "comparison",
                    "player1": {**dict(p1_data), "stats": dict(p1_stats)},
                    "player2": {**dict(p2_data), "stats": dict(p2_stats)}
                }
            }
        else:
            return {"response": f"I found one of them, but not both. Check spelling."}

    # --- 3. RAG / INTELLIGENT Q&A ---
    q_match = QUESTION_PATTERN.search(user_msg)
    if q_match:
        raw_capture = q_match.group(2)
        potential_player = extract_player_name(raw_capture)
        print(f"🧠 RAG INTENT. Subject: '{potential_player}'")
        ai_response = rag.generate_answer(potential_player, user_msg)
        return {"response": ai_response, "data": {"type": "text_only"}}

    # --- 4. EXPLICIT SEARCH (THE FIX) ---
    target_player = clean_msg
    sql = text("SELECT gsis_id, name FROM players WHERE name ILIKE :search LIMIT 1")
    player = db.execute(sql, {"search": f"%{target_player}%"}).mappings().first()
    
    if player:
        # FIX: We removed 'rag.generate_answer' here.
        # Now it just returns a clean, simple message with the button.
        return {
            "response": f"Here is the profile for {player['name']}:",
            "data": {
                "type": "player_profile", 
                "player_id": player['gsis_id'], 
                "name": player['name']
            }
        }

    return {"response": "I didn't catch that. Try 'How many points did Lamar score?'"}