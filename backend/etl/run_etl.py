import pandas as pd
from sqlalchemy import create_engine, text
import os
import sys

# Setup Paths & DB Connection
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def calculate_fantasy_points(row):
    """Standard PPR Fantasy Calculation"""
    pass_pts = (row.get('passing_yards', 0) / 25) + (row.get('passing_tds', 0) * 4) - (row.get('interceptions', 0) * 2)
    rush_pts = (row.get('rushing_yards', 0) / 10) + (row.get('rushing_tds', 0) * 6)
    rec_pts = (row.get('receiving_yards', 0) / 10) + (row.get('receiving_tds', 0) * 6) + (row.get('receptions', 0) * 1)
    fum_pts = (row.get('fumbles_lost', 0) * -2)
    return round(pass_pts + rush_pts + rec_pts + fum_pts, 2)

def run_pipeline():
    print("🚀 STARTING WEEKLY UPDATE (SURGICAL SWAP)...")
    
    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL not found.")
        return

    engine = create_engine(DATABASE_URL)

    # --- STEP 1: FETCH STATS (Raw 2025 PBP) ---
    print("📥 Downloading Raw 2025 Play-by-Play Data...")
    # We use PARQUET (faster/stable) instead of the old broken CSV libraries
    PBP_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2025.parquet"
    
    try:
        cols = [
            'season', 'week', 'passer_player_id', 'passer_player_name', 'rusher_player_id', 'rusher_player_name',
            'receiver_player_id', 'receiver_player_name', 'passing_yards', 'rushing_yards', 'receiving_yards',
            'pass_touchdown', 'rush_touchdown', 'interception', 'fumble_lost', 'sack', 'complete_pass', 'posteam'
        ]
        df_pbp = pd.read_parquet(PBP_URL, columns=cols)
    except Exception as e:
        print(f"❌ Stats Download Failed: {e}")
        return

    # --- STEP 2: FETCH ROSTER (Fix UNK Positions) ---
    print("📥 Downloading Official 2025 Roster...")
    ROSTER_URL = "https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_2025.parquet"
    try:
        roster_cols = ['gsis_id', 'position', 'full_name']
        df_roster = pd.read_parquet(ROSTER_URL, columns=roster_cols)
    except:
        df_roster = pd.DataFrame(columns=['gsis_id', 'position', 'full_name'])

    # --- STEP 3: AGGREGATE ---
    print("⚙️  Calculating 2025 Stats...")
    
    # Passing
    pass_stats = df_pbp.groupby(['passer_player_id', 'passer_player_name', 'posteam', 'season']).agg({
        'passing_yards': 'sum', 'pass_touchdown': 'sum', 'interception': 'sum', 'sack': 'sum'
    }).reset_index().rename(columns={
        'passer_player_id': 'gsis_id', 'passer_player_name': 'player_name', 'posteam': 'team_id',
        'pass_touchdown': 'passing_tds', 'sack': 'sacks_taken', 'interception': 'interceptions'
    })
    
    # Rushing
    rush_stats = df_pbp.groupby(['rusher_player_id', 'rusher_player_name', 'posteam', 'season']).agg({
        'rushing_yards': 'sum', 'rush_touchdown': 'sum', 'fumble_lost': 'sum'
    }).reset_index().rename(columns={
        'rusher_player_id': 'gsis_id', 'rusher_player_name': 'player_name', 'posteam': 'team_id',
        'rush_touchdown': 'rushing_tds', 'fumble_lost': 'fumbles_lost'
    })
    
    # Receiving
    rec_stats = df_pbp.groupby(['receiver_player_id', 'receiver_player_name', 'posteam', 'season']).agg({
        'receiving_yards': 'sum', 'pass_touchdown': 'sum', 'complete_pass': 'sum'
    }).reset_index().rename(columns={
        'receiver_player_id': 'gsis_id', 'receiver_player_name': 'player_name', 'posteam': 'team_id',
        'pass_touchdown': 'receiving_tds', 'complete_pass': 'receptions'
    })
    
    # Merge
    merged = pd.merge(pass_stats, rush_stats, on=['gsis_id', 'season', 'team_id'], how='outer', suffixes=('_p', '_r'))
    merged['player_name'] = merged['player_name_p'].combine_first(merged['player_name_r'])
    merged = merged.drop(columns=['player_name_p', 'player_name_r'])
    
    merged = pd.merge(merged, rec_stats, on=['gsis_id', 'season', 'team_id'], how='outer', suffixes=('', '_rec'))
    merged['player_name'] = merged['player_name'].combine_first(merged['player_name_rec'])
    merged = merged.drop(columns=['player_name_rec'])
    
    merged = merged.fillna(0)
    
    # --- STEP 4: ENRICH (Roster Merge) ---
    final_df = pd.merge(merged, df_roster, on='gsis_id', how='left')
    final_df['position'] = final_df['position'].fillna('UNK')
    final_df['player_name'] = final_df['full_name'].combine_first(final_df['player_name'])
    final_df = final_df.drop(columns=['full_name'])
    
    final_df['fantasy_points'] = final_df.apply(calculate_fantasy_points, axis=1)
    final_df = final_df[final_df['fantasy_points'] != 0]

    # --- STEP 5: THE SURGICAL SWAP (Crucial Change) ---
    print(f"💾 Saving {len(final_df)} updated 2025 records...")
    
    with engine.connect() as conn:
        # 1. Delete ONLY 2025 data (Keep 2023/2024 safe)
        print("   -> Removing old 2025 data...")
        conn.execute(text("DELETE FROM season_stats WHERE season = 2025"))
        conn.commit()
        
        # 2. Append NEW 2025 data
        print("   -> Inserting fresh 2025 data...")
        final_df.to_sql('season_stats', engine, if_exists='append', index=False)
        
    print("✅ WEEKLY UPDATE COMPLETE. History preserved.")

if __name__ == "__main__":
    run_pipeline()