import os
import requests
from sqlalchemy import text
from database import engine

MODEL_SERVICE_URL = "http://127.0.0.1:8001/generate"

class TradeAgent:
    def __init__(self):
        print("💼 Trade Agent Initialized.")

    def find_player(self, conn, name):
        """
        SMART LOOKUP: Finds player by name, prioritizing highest fantasy points.
        """
        sql = text("""
            SELECT p.gsis_id, p.name, p.position, p.team_id, s.fantasy_points
            FROM players p
            LEFT JOIN season_stats s ON p.gsis_id = s.gsis_id AND s.season = 2025
            WHERE p.name ILIKE :name
            ORDER BY s.fantasy_points DESC NULLS LAST
            LIMIT 1
        """)
        return conn.execute(sql, {"name": f"%{name}%"}).mappings().first()

    def analyze_trade(self, give_name, receive_name):
        try:
            with engine.connect() as conn:
                # 1. IDENTIFY PLAYERS
                p_give = self.find_player(conn, give_name)
                p_receive = self.find_player(conn, receive_name)

                if not p_give or not p_receive:
                    return None, "I couldn't identify one of those players. Try using full names."

                # 2. POSITION GUARDRAIL (New!)
                if p_give['position'] != p_receive['position']:
                    return {
                        "give": dict(p_give),
                        "receive": dict(p_receive),
                        "diff": 0,
                        "verdict": "MISMATCH"
                    }, f"Trade Rejected: You cannot trade a {p_give['position']} ({p_give['name']}) for a {p_receive['position']} ({p_receive['name']}). Positions must match."

                # 3. MATH
                val_give = p_give['fantasy_points'] or 0
                val_receive = p_receive['fantasy_points'] or 0
                net_diff = val_receive - val_give
                
                # 4. VERDICT
                if net_diff > 20:
                    verdict = "WIN"
                    advice_context = f"You gain {net_diff:.1f} points. This is a clear upgrade."
                elif net_diff < -20:
                    verdict = "LOSS"
                    advice_context = f"You lose {abs(net_diff):.1f} points. Do not accept this."
                else:
                    verdict = "FAIR"
                    advice_context = f"The difference is only {net_diff:.1f} points. It is a fair trade."

                # 5. AI ADVICE GENERATION
                # We send the context to the AI to get a clean sentence.
                ai_prompt = (
                    f"Context: {advice_context}\n"
                    f"Task: Write one short, decisive sentence advising the user."
                )
                
                try:
                    # We bypass the 'find_player' in RAG by using a special name or just ensuring the RAG handles it.
                    # Actually, we can just hit the generate endpoint directly if we trust it, 
                    # but let's use the standard flow with a dummy name to skip DB lookup if we implemented that "TradeBot" bypass.
                    # Since we added "TradeBot" bypass in rag_system.py, we use that here.
                    resp = requests.post(MODEL_SERVICE_URL, json={"player_name": "TradeBot", "question": ai_prompt})
                    if resp.status_code == 200:
                        # CLEANUP: Sometimes Flan-T5 repeats the prompt. We assume the answer is the last sentence.
                        raw_answer = resp.json().get("answer", "")
                        # Fallback if empty
                        advice_text = raw_answer if raw_answer else advice_context
                    else:
                        advice_text = advice_context
                except:
                    advice_text = advice_context

                return {
                    "give": dict(p_give),
                    "receive": dict(p_receive),
                    "diff": net_diff,
                    "verdict": verdict
                }, advice_text

        except Exception as e:
            print(f"❌ Trade Error: {e}")
            return None, "Error analyzing trade."

trade_agent = TradeAgent()