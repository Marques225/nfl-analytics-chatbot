from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
import logging
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

def safe_float(value, decimals=2):
    try:
        if value is None: return 0.0
        f_val = float(value)
        if math.isnan(f_val) or math.isinf(f_val): return 0.0
        return round(f_val, decimals)
    except:
        return 0.0

def calculate_fantasy(stats):
    if not stats: return 0.0
    db_pts = safe_float(stats.get('fantasy_points', 0))
    if db_pts > 0: return db_pts
    
    pass_pts = (safe_float(stats.get('passing_yards')) / 25) + (safe_float(stats.get('passing_tds')) * 4) - (safe_float(stats.get('interceptions')) * 2)
    rush_pts = (safe_float(stats.get('rushing_yards')) / 10) + (safe_float(stats.get('rushing_tds')) * 6)
    rec_pts = (safe_float(stats.get('receiving_yards')) / 10) + (safe_float(stats.get('receiving_tds')) * 6) + (safe_float(stats.get('receptions')) * 1)
    return round(pass_pts + rush_pts + rec_pts, 2)

def get_player_stats(db, name):
    sql_p = text("SELECT * FROM players WHERE name ILIKE :name LIMIT 1")
    p = db.execute(sql_p, {"name": f"%{name}%"}).mappings().first()
    if not p: return None, None
    pid = p.get('gsis_id') or p.get('player_id')
    sql_s = text("SELECT * FROM season_stats WHERE gsis_id = :pid AND season = 2025")
    s = db.execute(sql_s, {"pid": pid}).mappings().first()
    return dict(p), (dict(s) if s else {})

def get_fantasy_leaders(db, position_filter, limit=3):
    sql = text(f"""
        SELECT p.name, p.team_id, p.gsis_id, s.*
        FROM season_stats s
        JOIN players p ON s.gsis_id = p.gsis_id
        WHERE s.season = 2025 AND p.position IN :pos
        ORDER BY (s.passing_yards + s.rushing_yards + s.receiving_yards) DESC
        LIMIT 30
    """)
    raw_players = db.execute(sql, {"pos": tuple(position_filter)}).mappings().all()
    processed = []
    for p in raw_players:
        p_dict = dict(p)
        f_pts = calculate_fantasy(p_dict)
        processed.append({
            "name": p_dict['name'],
            "team": p_dict['team_id'],
            "player_id": p_dict['gsis_id'],
            "val": p_dict.get('passing_yards', 0) + p_dict.get('rushing_yards', 0) + p_dict.get('receiving_yards', 0),
            "fantasy": f_pts
        })
    processed.sort(key=lambda x: x['fantasy'], reverse=True)
    return processed[:limit]

@router.post("/")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    msg = request.message.lower().strip()
    logger.info(f"💬 Received: {msg}")
    
    answer = ""
    structured_data = None

    try:
        # LOGIC 1: DRAFT ADVICE (Tables)
        if "who should i draft" in msg and " or " not in msg:
            qbs = get_fantasy_leaders(db, ["QB"], 3)
            rbs = get_fantasy_leaders(db, ["RB"], 3)
            wrs = get_fantasy_leaders(db, ["WR", "TE"], 3)
            
            structured_data = {
                "type": "draft_board",
                "qbs": qbs,
                "rbs": rbs,
                "wrs": wrs
            }
            answer = "Here are the top Fantasy Leaders for 2025:"

        # LOGIC 2: COMPARE
        elif "draft" in msg or "compare" in msg or " or " in msg:
            if " or " in msg: parts = msg.split(" or ")
            elif " vs " in msg: parts = msg.split(" vs ")
            else: parts = []

            if len(parts) >= 2:
                # --- THE FIX IS HERE ---
                # We added replacements for "should i draft" and "should i"
                n1 = parts[0].replace("who should i draft", "") \
                             .replace("should i draft", "") \
                             .replace("should i", "") \
                             .replace("compare", "") \
                             .replace("draft", "") \
                             .strip()
                n2 = parts[1].replace("?", "").strip()
                
                p1, s1 = get_player_stats(db, n1)
                p2, s2 = get_player_stats(db, n2)
                
                if p1 and p2:
                    fp1 = calculate_fantasy(s1)
                    fp2 = calculate_fantasy(s2)
                    winner = p1['name'] if fp1 >= fp2 else p2['name']
                    diff = round(abs(fp1 - fp2), 1)
                    answer = (f"**2025 Comparison:**\n"
                              f"🏈 **{p1['name']}**: {fp1} FPts\n"
                              f"🏈 **{p2['name']}**: {fp2} FPts\n\n"
                              f"👉 Pick **{winner}** (+{diff}).")
                else:
                    answer = "I couldn't find stats for one of those players."
            else:
                answer = "Try: 'Draft Lamar Jackson or Patrick Mahomes'."

        # LOGIC 3: WHO IS
        elif "who is" in msg or "tell me about" in msg:
            name = msg.replace("who is", "").replace("tell me about", "").replace("?", "").strip()
            p, s = get_player_stats(db, name)
            if p:
                if s:
                    pts = calculate_fantasy(s)
                    answer = f"{p['name']} ({p['team_id']}): {s.get('passing_yards',0)+s.get('rushing_yards',0)+s.get('receiving_yards',0)} Yds | {pts} FPts."
                else:
                    answer = f"{p['name']} is on the {p['team_id']} roster."
                
                structured_data = {
                    "type": "player_profile",
                    "player_id": p['gsis_id'],
                    "name": p['name'],
                    "team": p['team_id']
                }
            else:
                answer = f"I couldn't find '{name}'."
        else:
            answer = "Ask 'Who should I draft?' for leaders, or 'Draft X or Y' to compare."

    except Exception as e:
        logger.error(f"Chat Error: {e}")
        answer = "I encountered an error."

    return {
        "response": answer,
        "text": answer,
        "data": structured_data
    }