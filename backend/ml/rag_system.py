import os
import sys
import re
from sqlalchemy import text
from transformers import pipeline

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import engine

class RAGEngine:
    def __init__(self):
        print("🧠 Loading AI Model (Google Flan-T5)...")
        self.pipeline = pipeline("text2text-generation", model="google/flan-t5-small")
        print("✅ Model Loaded.")

    def retrieve_precise_data(self, player_name, season, intent):
        """
        Fetches ONLY the data relevant to the intent and formats it as a Fact.
        """
        try:
            with engine.connect() as conn:
                # 1. FIND PLAYER (Popularity Sort)
                find_sql = text("""
                    SELECT p.gsis_id, p.name, p.position, p.team_id, s.fantasy_points
                    FROM players p
                    LEFT JOIN season_stats s ON p.gsis_id = s.gsis_id AND s.season = :season
                    WHERE p.name ILIKE :name
                    ORDER BY s.fantasy_points DESC NULLS LAST
                    LIMIT 1
                """)
                player = conn.execute(find_sql, {"name": f"%{player_name}%", "season": season}).mappings().first()

                if not player: 
                    return None

                # 2. GET STATS (Order by points to avoid 0-stat duplicates)
                stats_sql = text("""
                    SELECT * FROM season_stats 
                    WHERE gsis_id = :id AND season = :season
                    ORDER BY fantasy_points DESC
                    LIMIT 1
                """)
                stats = conn.execute(stats_sql, {"id": player['gsis_id'], "season": season}).mappings().first()

                if not stats: 
                    return f"Info: {player['name']} has no stats for {season}."

                # --- 3. SURGICAL CONTEXT ---
                
                # INTENT: TOUCHDOWNS
                if intent == "touchdowns":
                    p_td = stats['passing_tds'] or 0
                    r_td = stats['rushing_tds'] or 0
                    rec_td = stats['receiving_tds'] or 0
                    total = p_td + r_td + rec_td
                    return (
                        f"Fact: In {season}, {player['name']} had {total} Total Touchdowns "
                        f"({r_td} rushing, {rec_td} receiving, {p_td} passing)."
                    )

                # INTENT: RUSHING (High Priority)
                elif intent == "rushing":
                    if stats['rushing_yards'] == 0 and stats['rushing_tds'] == 0:
                        return f"Fact: In {season}, {player['name']} had 0 recorded rushing stats."
                    return (
                        f"Fact: In {season}, {player['name']} rushed for {stats['rushing_yards']} yards and {stats['rushing_tds']} touchdowns."
                    )

                # INTENT: PASSING (High Priority)
                elif intent == "passing":
                    if stats['passing_yards'] == 0 and stats['passing_tds'] == 0:
                         return f"Fact: In {season}, {player['name']} had 0 recorded passing stats."
                    return (
                        f"Fact: In {season}, {player['name']} passed for {stats['passing_yards']} yards and {stats['passing_tds']} touchdowns."
                    )

                # INTENT: RECEIVING (High Priority)
                elif intent == "receiving":
                    if stats['receiving_yards'] == 0 and stats['receiving_tds'] == 0:
                         return f"Fact: In {season}, {player['name']} had 0 recorded receiving stats."
                    return (
                        f"Fact: In {season}, {player['name']} caught {stats['receiving_yards']} yards and {stats['receiving_tds']} touchdowns."
                    )

                # INTENT: POINTS (Lowest Priority - Fallback)
                elif intent == "points":
                    return (
                        f"Fact: In {season}, {player['name']} scored {stats['fantasy_points']} Fantasy Points."
                    )

                # INTENT: GENERAL
                else:
                    return (
                        f"Fact: In {season}, {player['name']} scored {stats['fantasy_points']} fantasy points."
                    )

        except Exception as e:
            print(f"❌ DB Error: {e}")
            return None

    def generate_answer(self, player_name, user_question):
        # 1. DETECT SEASON
        target_season = 2025
        year_match = re.search(r'202[0-9]', user_question)
        if year_match:
            target_season = int(year_match.group(0))
        elif "last year" in user_question.lower():
             target_season = 2024
        elif "two years ago" in user_question.lower():
             target_season = 2023

        # 2. DETECT INTENT (RE-WEIGHTED PRIORITY)
        q_lower = user_question.lower()
        intent = "general"
        
        # Priority 1: Touchdowns
        if "touchdown" in q_lower or " td" in q_lower:
            intent = "touchdowns"
        
        # Priority 2: Specific Stats (Overrides "Score")
        elif "rush" in q_lower or "run" in q_lower:
            intent = "rushing"
        elif "pass" in q_lower or "throw" in q_lower:
            intent = "passing"
        elif "receiv" in q_lower or "catch" in q_lower or "caught" in q_lower:
            intent = "receiving"
            
        # Priority 3: Points/Score (Only if no specific stat matched above)
        elif "point" in q_lower or "score" in q_lower:
            intent = "points"
        
        # 3. GET CONTEXT
        context = self.retrieve_precise_data(player_name, target_season, intent)
        
        if not context: return f"I couldn't find stats for {player_name} in {target_season}."
        if context.startswith("Info:"): return context

        # 4. GENERATE (LOOP PREVENTION ADDED)
        prompt = (
            f"{context}\n\n"
            f"Question: {user_question}\n"
            "Task: State the fact clearly in one sentence."
        )

        # Added repetition_penalty=1.2 to kill the glitch loops
        output = self.pipeline(prompt, max_length=60, repetition_penalty=1.2, do_sample=False)
        return output[0]['generated_text']

rag = RAGEngine()