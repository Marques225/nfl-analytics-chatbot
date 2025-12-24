import sys
import os
import random
import pandas as pd
from sqlalchemy import text

# --- 1. ROBUST PATH SETUP (The Fix) ---
# Get the absolute path of THIS script (backend/ml/generate_data.py)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to find 'backend' root
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
# Add backend to sys.path so we can import 'database'
sys.path.append(BACKEND_DIR)

from database import engine

def generate_synthetic_data():
    print("🤖 GENERATING TRAINING DATA FROM DATABASE...")
    
    # Define exact save path
    SAVE_PATH = os.path.join(BACKEND_DIR, "data", "qa_dataset.txt")
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    
    # 1. Fetch Top 50 Players
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT p.name, p.position, p.team_id, s.season, s.fantasy_points 
                FROM season_stats s
                JOIN players p ON s.gsis_id = p.gsis_id
                WHERE s.season = 2025
                ORDER BY s.fantasy_points DESC
                LIMIT 50
            """)
            df = pd.read_sql(query, conn)
            
        if df.empty:
            print("❌ ERROR: Database returned 0 players. Check your 'season_stats' table.")
            return

    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")
        return

    training_pairs = []

    # 2. Create Sentence Templates
    for _, row in df.iterrows():
        name = row['name']
        team = row['team_id']
        pos = row['position']
        pts = row['fantasy_points']
        
        # Fact 1: Team & Position
        training_pairs.append(f"Question: Who is {name}? Answer: {name} is a {pos} for the {team}.")
        
        # Fact 2: Fantasy Points
        training_pairs.append(f"Question: How many points did {name} score in 2025? Answer: {name} scored {pts} fantasy points.")

    # 3. Save to File
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        for line in training_pairs:
            f.write(line + "\n")
            
    print(f"✅ Generated {len(training_pairs)} training sentences.")
    print(f"💾 Saved to: {SAVE_PATH}")

if __name__ == "__main__":
    generate_synthetic_data()