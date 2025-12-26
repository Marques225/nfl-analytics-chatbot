import os
import sys
from sqlalchemy import text
from transformers import pipeline

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import engine

class RAGEngine:
    def __init__(self):
        print("🧠 Loading AI Model (Google Flan-T5)...")
        self.pipeline = pipeline("text2text-generation", model="google/flan-t5-small")
        print("✅ Model Loaded.")

    def retrieve_player_stats(self, player_name):
        try:
            with engine.connect() as conn:
                find_sql = text("SELECT gsis_id, name, position, team_id FROM players WHERE name ILIKE :name LIMIT 1")
                player = conn.execute(find_sql, {"name": f"%{player_name}%"}).mappings().first()

                if not player: return None

                stats_sql = text("""
                    SELECT fantasy_points, passing_yards, passing_tds, rushing_yards, rushing_tds, receiving_yards, receiving_tds
                    FROM season_stats 
                    WHERE gsis_id = :id AND season = 2025
                """)
                stats = conn.execute(stats_sql, {"id": player['gsis_id']}).mappings().first()

                if not stats: return None

                # 🧠 TRICK THE AI: 
                # 1. We label Fantasy Points as "Score" so it matches the user's question.
                # 2. We put it FIRST so it pays most attention to it.
                context = (
                    f"Player: {player['name']}\n"
                    f"Official Score: {stats['fantasy_points']} points\n"  # <--- RENAMED LABEL
                    f"Team: {player['team_id']}\n"
                    f"Passing: {stats['passing_yards']} yards\n"
                    f"Rushing: {stats['rushing_yards']} yards\n"
                    f"Receiving: {stats['receiving_yards']} yards"
                )
                return context

        except Exception as e:
            print(f"❌ DB Error: {e}")
            return None

    def generate_answer(self, player_name, user_question):
        context = self.retrieve_player_stats(player_name)
        if not context:
            return f"I couldn't find 2025 stats for {player_name}."

        # 🧠 PROMPT ENGINEERING: 
        # Explicitly tell it to write a full sentence.
        prompt = (
            f"Context:\n{context}\n\n"
            f"Question: {user_question}\n"
            "Task: Answer in a complete sentence. If asked for points or score, use the 'Official Score' value."
        )

        output = self.pipeline(prompt, max_length=100, do_sample=False)
        return output[0]['generated_text']

rag = RAGEngine()