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
        try:
            with engine.connect() as conn:
                # 1. FIND PLAYER (Using Popularity Sort)
                find_sql = text("""
                    SELECT p.gsis_id, p.name, p.position, p.team_id, s.fantasy_points
                    FROM players p
                    LEFT JOIN season_stats s ON p.gsis_id = s.gsis_id AND s.season = :season
                    WHERE p.name ILIKE :name
                    ORDER BY s.fantasy_points DESC NULLS LAST
                    LIMIT 1
                """)
                player = conn.execute(find_sql, {"name": f"%{player_name}%", "season": season}).mappings().first()

                if not player: return None

                # 2. GET STATS
                stats_sql = text("""
                    SELECT * FROM season_stats 
                    WHERE gsis_id = :id AND season = :season
                    ORDER BY fantasy_points DESC
                    LIMIT 1
                """)
                stats = conn.execute(stats_sql, {"id": player['gsis_id'], "season": season}).mappings().first()

                if not stats: 
                    return f"Info: {player['name']} has no recorded stats for the {season} season."

                # --- 3. SENTENCE CONSTRUCTION (The Fix) ---
                # We pre-build the natural sentence here so the AI can't mess it up.
                
                if intent == "touchdowns":
                    p_td = stats['passing_tds'] or 0
                    r_td = stats['rushing_tds'] or 0
                    rec_td = stats['receiving_tds'] or 0
                    total = p_td + r_td + rec_td
                    return f"In {season}, {player['name']} scored {total} total touchdowns ({r_td} rushing, {rec_td} receiving, {p_td} passing)."

                elif intent == "rushing":
                    return f"In {season}, {player['name']} rushed for {stats['rushing_yards']} yards and {stats['rushing_tds']} touchdowns."

                elif intent == "passing":
                    return f"In {season}, {player['name']} threw for {stats['passing_yards']} yards and {stats['passing_tds']} touchdowns."

                elif intent == "receiving":
                    return f"In {season}, {player['name']} caught {stats['receiving_yards']} receiving yards and {stats['receiving_tds']} touchdowns."

                else: # Points / General
                    return f"In {season}, {player['name']} scored {stats['fantasy_points']} fantasy points."

        except Exception as e:
            print(f"❌ DB Error: {e}")
            return None

    def generate_answer(self, player_name, user_question):
        # 0. BYPASS FOR TRADEBOT
        if player_name == "TradeBot":
            output = self.pipeline(user_question, max_length=100, do_sample=False)
            return output[0]['generated_text']

        # 1. DETECT SEASON
        target_season = 2025
        year_match = re.search(r'202[0-9]', user_question)
        if year_match: target_season = int(year_match.group(0))
        elif "last year" in user_question.lower(): target_season = 2024
        elif "two years ago" in user_question.lower(): target_season = 2023

        # 2. DETECT INTENT
        q_lower = user_question.lower()
        intent = "general"
        if "touchdown" in q_lower or " td" in q_lower: intent = "touchdowns"
        elif "rush" in q_lower or "run" in q_lower: intent = "rushing"
        elif "pass" in q_lower or "throw" in q_lower: intent = "passing"
        elif "receiv" in q_lower or "catch" in q_lower: intent = "receiving"
        elif "point" in q_lower or "score" in q_lower: intent = "points"
        
        # 3. GET CONTEXT
        context = self.retrieve_precise_data(player_name, target_season, intent)
        if not context: return f"I couldn't find stats for {player_name} in {target_season}."
        
        # If it's an Info message (no stats), return it directly
        if context.startswith("Info:"): return context

        # 4. GENERATE RESPONSE
        # We give the AI the full sentence and tell it to repeat/polish it.
        prompt = (
            f"Fact: {context}\n"
            f"Question: {user_question}\n"
            "Task: Write a complete natural sentence using the Fact above. Include the player name and year."
        )
        
        # Increased max_length slightly to allow for the full sentence
        output = self.pipeline(prompt, max_length=80, repetition_penalty=1.2, do_sample=False)
        return output[0]['generated_text']

rag = RAGEngine()