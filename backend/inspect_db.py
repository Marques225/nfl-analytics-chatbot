from database import engine
from sqlalchemy import text
import pandas as pd

def inspect_ghosts():
    print("🕵️‍♂️ INSPECTING DATABASE CONTENTS...")
    
    with engine.connect() as conn:
        # 1. Check the first 5 rows of the players table
        print("\n--- FIRST 5 PLAYERS IN DB ---")
        query = text("SELECT gsis_id, name, position, team_id FROM players LIMIT 5")
        df = pd.read_sql(query, conn)
        print(df)
        
        # 2. Check specifically for McCaffrey
        print("\n--- SEARCHING FOR CMC ---")
        cmc_query = text("SELECT * FROM players WHERE name ILIKE '%McCaffrey%'")
        cmc = pd.read_sql(cmc_query, conn)
        
        if cmc.empty:
            print("❌ Christian McCaffrey NOT found in 'players' table.")
            # 3. Check if we have 'Nameless' players
            null_check = text("SELECT count(*) FROM players WHERE name = 'N/A' OR name IS NULL")
            count = conn.execute(null_check).scalar()
            print(f"⚠️ Found {count} players with 'N/A' as their name.")
        else:
            print("✅ Found McCaffrey:")
            print(cmc[['gsis_id', 'name', 'team_id']])

if __name__ == "__main__":
    inspect_ghosts()