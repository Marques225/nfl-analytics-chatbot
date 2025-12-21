import pandas as pd
from database import engine
from sqlalchemy import text

def verify_data_integrity():
    print("🕵️ VERIFYING DATABASE INTEGRITY...")
    
    # We must open a connection explicitly for SQLAlchemy 2.0+
    with engine.connect() as conn:
        
        # 1. CHECK DEFENSE (Sacks)
        print("\n--- 1. TEAM DEFENSE CHECK ---")
        # Use text() to safely declare the SQL query
        df_def = pd.read_sql(text("SELECT team_id, def_sacks_made, def_interceptions FROM team_season_stats WHERE season = 2025"), conn)
        
        # Check if we have data
        if len(df_def) > 0:
            null_sacks = df_def['def_sacks_made'].isnull().sum()
            zeros = (df_def['def_sacks_made'] == 0).sum()
            print(f"✅ 2025 Defense Rows: {len(df_def)}")
            print(f"   - NULL Sacks: {null_sacks} (Should be 0)")
            print(f"   - Zero Sacks: {zeros} (Should be low/zero)")
            print("   Sample Data:")
            print(df_def.head(3))
        else:
            print("❌ NO DEFENSE DATA FOUND FOR 2025!")

        # 2. CHECK OFFENSE (EPA & WOPR)
        print("\n--- 2. OFFENSE ADVANCED STATS CHECK ---")
        df_off = pd.read_sql(text("SELECT gsis_id, season, passing_epa, wopr FROM weekly_stats WHERE season = 2025 LIMIT 1000"), conn)
        
        if len(df_off) > 0:
            null_epa = df_off['passing_epa'].isnull().sum()
            print(f"✅ 2025 Offense Rows (Sample): {len(df_off)}")
            print(f"   - NULL EPA: {null_epa} (Should be 0)")
            print(f"   - NULL WOPR: {df_off['wopr'].isnull().sum()}")
            print("   Sample Data:")
            print(df_off[['gsis_id', 'passing_epa', 'wopr']].head(3))
        else:
            print("❌ NO OFFENSE DATA FOUND FOR 2025!")

if __name__ == "__main__":
    verify_data_integrity()