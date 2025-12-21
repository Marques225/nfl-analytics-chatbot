from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
import logging

from api.nlp.parser import QueryParser
from api.nlp.retrieval import RetrievalEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    msg = request.message
    logger.info(f"NLP Processing: {msg}")
    
    parser = QueryParser()
    intent, params = parser.parse(msg)
    
    engine = RetrievalEngine(db)
    response_text = ""
    structured_data = None

    try:
        # --- INTENT: RANKING ---
        if intent == "ranking":
            metric = params["metric"]
            pos = params["position"]
            limit = params["limit"]
            
            # LOGIC SPLIT:
            # 1. If user asked for specific position ("Best QBs"), give single list.
            # 2. If user asked general ("Who should I draft?"), give the FULL BOARD.
            
            if pos:
                # Specific Position Request
                leaders = engine.get_rankings(position=pos, metric=metric, limit=limit)
                if leaders:
                    response_text = f"Here are the top {limit} {pos}s sorted by {metric.replace('_', ' ')}:"
                    # Reuse the qbs/rbs keys so the table renders, but put data where it belongs
                    structured_data = {
                        "type": "draft_board",
                        "qbs": leaders if pos == 'QB' else [],
                        "rbs": leaders if pos == 'RB' else [],
                        "wrs": leaders if pos in ['WR', 'TE'] else [],
                        "generic": leaders if pos not in ['QB', 'RB', 'WR', 'TE'] else []
                    }
                else:
                    response_text = "No data found."
            else:
                # General "Who should I draft" Request -> RESTORE DAY 11 BEHAVIOR
                board = engine.get_draft_board()
                response_text = "Here are the top Fantasy Leaders for 2025:"
                structured_data = {
                    "type": "draft_board",
                    "qbs": board['qbs'],
                    "rbs": board['rbs'],
                    "wrs": board['wrs']
                }

        # --- INTENT: COMPARE ---
        elif intent == "compare":
            names = params["player_names"]
            
            # Robust Fallback (just in case parser misses "and")
            if len(names) < 2:
                lower_msg = msg.lower()
                if " or " in lower_msg: names = lower_msg.split(" or ")
                elif " vs " in lower_msg: names = lower_msg.split(" vs ")
                elif " and " in lower_msg: names = lower_msg.split(" and ")
                # reclean
                names = [n.replace("compare", "").replace("draft", "").replace("who should i", "").strip() for n in names]
            
            # Limit to first 2 found
            names = [n for n in names if len(n) > 1][:2]

            if len(names) >= 2:
                p1 = engine.get_player_stats(names[0])
                p2 = engine.get_player_stats(names[1])
                
                if p1 and p2:
                    diff = round(abs(p1['fantasy'] - p2['fantasy']), 1)
                    winner = p1['info']['name'] if p1['fantasy'] >= p2['fantasy'] else p2['info']['name']
                    
                    response_text = (f"**Comparison:**\n"
                                     f"🏈 **{p1['info']['name']}**: {p1['fantasy']} FPts\n"
                                     f"🏈 **{p2['info']['name']}**: {p2['fantasy']} FPts\n\n"
                                     f"👉 Better Pick: **{winner}** (+{diff})")
                else:
                    # Specific error so we know who failed
                    response_text = f"I couldn't find stats for '{names[0]}' or '{names[1]}'."
            else:
                response_text = "To compare, name two players (e.g., 'Lamar vs Mahomes')."

        # --- INTENT: SEARCH ---
        elif intent == "search":
            name_query = params["player_names"][0] if params["player_names"] else msg.replace("who is", "").strip()
            data = engine.get_player_stats(name_query)
            if data:
                p = data['info']
                s = data['stats']
                response_text = f"{p['name']} ({p['team_id']}): {data['fantasy']} Fantasy Points."
                structured_data = {
                    "type": "player_profile",
                    "player_id": p['gsis_id'],
                    "name": p['name'],
                    "team": p['team_id']
                }
            else:
                response_text = f"I couldn't find '{name_query}'."

        else:
            response_text = "Try 'Who should I draft?' or 'Compare X and Y'."

    except Exception as e:
        logger.error(f"NLP Error: {e}")
        response_text = "I ran into an issue processing that query."

    return {
        "response": response_text,
        "text": response_text,
        "data": structured_data
    }