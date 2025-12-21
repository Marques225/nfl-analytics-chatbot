import pandas as pd
import numpy as np
from database import engine
from sqlalchemy import text

def seed_database():
    print("🚀 STARTING FINAL DATABASE WIPE & RELOAD...")
    
    # --- STEP 0: WIPE THE DATABASE (CLEAN SLATE) ---
    with engine.connect() as conn:
        print("   🗑️ Wiping old tables...")
        conn.execute(text("DROP TABLE IF EXISTS season_stats CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS weekly_stats CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS players CASCADE;"))
        conn.commit()
    print("   ✅ Database Cleaned.")

    # --- STEP 1: PLAYERS (2025 ROSTER) ---
    print("\n1. 📥 Fetching Rosters (2025)...")
    ROSTER_URL = "https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_2025.csv"
    roster_df = pd.read_csv(ROSTER_URL, low_memory=False)
    players_db = roster_df[['gsis_id', 'full_name', 'position', 'team', 'headshot_url', 'espn_id', 'sleeper_id', 'yahoo_id']].copy()
    players_db.rename(columns={'full_name': 'name', 'team': 'team_id'}, inplace=True)
    players_db.drop_duplicates(subset=['gsis_id'], inplace=True)
    players_db.to_sql('players', engine, if_exists='replace', index=False)
    print(f"   ✅ Saved {len(players_db)} players.")

    # --- STEP 2: HISTORY (2023-2024) - USE OFFICIAL FILES ---
    print("\n2. 📥 Fetching History (2023-2024) [Pre-Calculated]...")
    HISTORY_URL = "https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats_{}.parquet"
    history_dfs = []
    
    for year in [2023, 2024]:
        df = pd.read_parquet(HISTORY_URL.format(year))
        # Ensure ID columns match
        df.rename(columns={'player_id': 'gsis_id', 'recent_team': 'team_id'}, inplace=True)
        history_dfs.append(df)
        print(f"   ✅ Loaded {year} history ({len(df)} rows).")

    # --- STEP 3: 2025 (CALCULATE FROM RAW PBP) ---
    print("\n3. ⚙️ Calculating 2025 Stats from Raw Play-by-Play...")
    PBP_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2025.csv.gz"
    pbp_df = pd.read_csv(PBP_URL, compression='gzip', low_memory=False)

    # A. OFFENSE AGGREGATION (With EPA!)
    pass_stats = pbp_df.groupby(['passer_player_id', 'week', 'posteam']).agg({
        'passing_yards': 'sum', 'pass_touchdown': 'sum', 'interception': 'sum', 
        'complete_pass': 'sum', 'pass_attempt': 'sum', 'sack': 'sum', 
        'epa': 'mean', 'cpoe': 'mean', 'air_yards': 'sum'
    }).reset_index().rename(columns={
        'passer_player_id': 'gsis_id', 'posteam': 'team_id', 'pass_touchdown': 'passing_tds',
        'interception': 'interceptions', 'complete_pass': 'completions', 
        'pass_attempt': 'attempts', 'sack': 'sacks', 'epa': 'passing_epa', 
        'air_yards': 'passing_air_yards'
    })

    rush_stats = pbp_df.groupby(['rusher_player_id', 'week']).agg({
        'rushing_yards': 'sum', 'rush_touchdown': 'sum', 'rush_attempt': 'sum', 'epa': 'mean'
    }).reset_index().rename(columns={
        'rusher_player_id': 'gsis_id', 'rush_touchdown': 'rushing_tds', 'rush_attempt': 'carries', 'epa': 'rushing_epa'
    })

    rec_stats = pbp_df.groupby(['receiver_player_id', 'week']).agg({
        'receiving_yards': 'sum', 'pass_touchdown': 'sum', 'pass_attempt': 'count', 
        'epa': 'mean', 'air_yards': 'sum', 'yards_after_catch': 'sum'
    }).reset_index().rename(columns={
        'receiver_player_id': 'gsis_id', 'pass_touchdown': 'receiving_tds', 'pass_attempt': 'targets', 
        'epa': 'receiving_epa', 'air_yards': 'receiving_air_yards', 'yards_after_catch': 'receiving_yards_after_catch'
    })
    rec_stats['receptions'] = rec_stats['targets'] # Approx

    # Merge Offense
    stats_2025 = pd.merge(pass_stats, rush_stats, on=['gsis_id', 'week'], how='outer')
    stats_2025 = pd.merge(stats_2025, rec_stats, on=['gsis_id', 'week'], how='outer')
    
    # Fill standard columns
    stats_2025['season'] = 2025
    stats_2025['season_type'] = 'REG'
    # Fill complex columns with 0 for now (WOPR requires team-level calc which is complex for one script)
    stats_2025['wopr'] = 0 
    stats_2025.fillna(0, inplace=True)
    
    history_dfs.append(stats_2025)

    # --- SAVE WEEKLY STATS ---
    final_weekly = pd.concat(history_dfs)
    final_weekly.to_sql('weekly_stats', engine, if_exists='replace', index=False)
    print("   ✅ Weekly Stats Table Created.")

    # --- STEP 4: TEAM DEFENSE (FIXING THE SACKS NULL) ---
    print("\n4. 🛡️ Calculating Team Defense (Sacks)...")
    def_stats = pbp_df.groupby(['defteam', 'season']).agg({
        'sack': 'sum', 'interception': 'sum', 'fumble_lost': 'sum'
    }).reset_index().rename(columns={'defteam': 'team_id', 'sack': 'def_sacks_made', 'interception': 'def_interceptions', 'fumble_lost': 'def_fumbles_recovered'})
    
    # We save this to a new table or merge it? Let's just create a simple 'team_season_stats' table
    def_stats.to_sql('team_season_stats', engine, if_exists='replace', index=False)
    print("   ✅ Team Defense Table Created (Sacks Fixed).")

    print("\n🎉 FINAL RELOAD COMPLETE.")

if __name__ == "__main__":
    seed_database()