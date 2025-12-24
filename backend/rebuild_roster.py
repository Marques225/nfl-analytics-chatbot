import pandas as pd
from database import engine
from sqlalchemy import text

def rebuild_player_directory():
    print("📖 STARTING PLAYER DIRECTORY REBUILD (OFFICIAL LATEST_TEAM FIX)...")

    # 1. Get Active IDs from Stats
    print("   🔍 Scanning 'season_stats'...")
    try:
        with engine.connect() as conn:
            active_ids = pd.read_sql(text("SELECT DISTINCT gsis_id FROM season_stats"), conn)
            active_id_list = active_ids['gsis_id'].tolist()
            print(f"   ✅ Found {len(active_id_list)} players with stats.")
    except Exception as e:
        print(f"   ❌ Error reading stats: {e}")
        return

    # 2. Download Roster
    print("   📥 Downloading Official NFL Roster...")
    url = "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv"
    try:
        roster_df = pd.read_csv(url, low_memory=False)
        roster_df = roster_df[roster_df['gsis_id'].isin(active_id_list)]
        
        # --- THE FIX: EXACT COLUMN MAPPING ---
        # We explicitly map 'latest_team' because we confirmed it exists in check_columns.py
        rename_map = {
            'display_name': 'name',
            'latest_team': 'team_id',   # <--- The Critical Fix
            'headshot': 'headshot_url'  
        }
        roster_df = roster_df.rename(columns=rename_map)

        # 3. Handle Missing ID Columns
        if 'sleeper_id' not in roster_df.columns:
            roster_df['sleeper_id'] = "N/A"
        if 'yahoo_id' not in roster_df.columns:
            roster_df['yahoo_id'] = "N/A"

        # 4. Select Final Columns
        required_cols = ['gsis_id', 'name', 'position', 'team_id', 'headshot_url', 'espn_id', 'sleeper_id', 'yahoo_id']
        
        # Ensure any other missing columns are filled
        for col in required_cols:
            if col not in roster_df.columns:
                print(f"   ⚠️ Warning: Column '{col}' missing. Defaulting to N/A.")
                roster_df[col] = "N/A"

        clean_df = roster_df[required_cols].copy().fillna("N/A")

        # 5. Upload
        print(f"   💾 Updating 'players' table with {len(clean_df)} valid players...")
        clean_df.to_sql('players', engine, if_exists='replace', index=False)
        print("✅ REBUILD COMPLETE. Teams are now linked.")

    except Exception as e:
        print(f"   ⚠️ Error: {e}")

if __name__ == "__main__":
    rebuild_player_directory()