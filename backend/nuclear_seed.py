import pandas as pd
import numpy as np
from database import engine
from sqlalchemy import text
import time

# --- HELPER: Force Unique Columns ---
def clean_df(df):
    """Removes duplicate columns and resets index to prevent concat crashes."""
    # 1. Drop duplicate columns (keep first)
    df = df.loc[:, ~df.columns.duplicated()]
    # 2. Reset Index (drop old index)
    df = df.reset_index(drop=True)
    return df

def nuclear_reload():
    print("☢️ STARTING NUCLEAR DATABASE RESET & RELOAD (BULLETPROOF MODE)...")
    
    # GLOBAL COLUMN LIST (The Source of Truth)
    # We will force every single dataframe to match this exact schema.
    KEEP_COLS = [
        'gsis_id', 'season', 'week', 'team_id', 
        'completions', 'attempts', 'passing_yards', 'passing_tds', 'interceptions', 'sacks', 'passing_epa',
        'carries', 'rushing_yards', 'rushing_tds', 'rushing_epa',
        'targets', 'receptions', 'receiving_yards', 'receiving_tds', 'receiving_epa',
        'wopr', 'target_share', 'air_yards_share', 'fantasy_points'
    ]

    # --- STEP 1: WIPE EVERYTHING ---
    with engine.connect() as conn:
        print("   🗑️ Wiping ALL tables...")
        conn.execute(text("DROP TABLE IF EXISTS season_stats CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS weekly_stats CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS team_season_stats CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS players CASCADE;"))
        conn.commit()
    print("   ✅ Database Wiped.")

    # --- STEP 2: LOAD PLAYERS (2025 ROSTER) ---
    print("\n1. 📥 Fetching Rosters (2025)...")
    ROSTER_URL = "https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_2025.csv"
    try:
        roster_df = pd.read_csv(ROSTER_URL, low_memory=False)
        players_db = roster_df[['gsis_id', 'full_name', 'position', 'team', 'headshot_url', 'espn_id', 'sleeper_id', 'yahoo_id']].copy()
        players_db.rename(columns={'full_name': 'name', 'team': 'team_id'}, inplace=True)
        players_db.drop_duplicates(subset=['gsis_id'], inplace=True)
        players_db.to_sql('players', engine, if_exists='replace', index=False)
        print(f"   ✅ Saved {len(players_db)} players.")
    except Exception as e:
        print(f"   ❌ Error loading rosters: {e}")
        return

    # --- STEP 3: LOAD HISTORY (2023-2024) ---
    print("\n2. 📥 Fetching History (2023-2024)...")
    HISTORY_URL = "https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats_{}.parquet"
    
    all_weekly = []
    
    for year in [2023, 2024]:
        try:
            df = pd.read_parquet(HISTORY_URL.format(year))
            print(f"   - Processing {year}...")
            
            # Clean BEFORE renaming
            df = clean_df(df)
            
            # Rename
            df = df.rename(columns={
                'player_id': 'gsis_id', 
                'recent_team': 'team_id',
                'fantasy_points_ppr': 'fantasy_points'
            })
            
            # Ensure all needed columns exist
            for col in KEEP_COLS:
                if col not in df.columns:
                    df[col] = 0
                else:
                    df[col] = df[col].fillna(0)
            
            # STRICT SELECTION (Drop extras)
            df = df[KEEP_COLS]
            
            # Clean AGAIN just to be safe
            df = clean_df(df)
            
            all_weekly.append(df)
            
        except Exception as e:
            print(f"     ⚠️ Failed {year}: {e}")

    # --- STEP 4: GENERATE 2025 (CALC WOPR & SHARES) ---
    print("\n3. ⚙️ Calculating 2025 Stats (Include Advanced)...")
    PBP_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2025.csv.gz"
    pbp_df = pd.read_csv(PBP_URL, compression='gzip', low_memory=False)

    # A. Team Totals
    team_passing = pbp_df.groupby(['posteam', 'week'])['air_yards'].sum().reset_index().rename(columns={'air_yards': 'team_air_yards', 'posteam': 'team_id'})
    team_targets = pbp_df[pbp_df['play_type']=='pass'].groupby(['posteam', 'week']).size().reset_index(name='team_targets').rename(columns={'posteam': 'team_id'})
    
    # B. Receiving Stats
    rec_stats = pbp_df.groupby(['receiver_player_id', 'week', 'posteam']).agg({
        'receiving_yards': 'sum', 'pass_touchdown': 'sum', 'air_yards': 'sum', 'epa': 'mean'
    }).reset_index().rename(columns={
        'receiver_player_id': 'gsis_id', 'posteam': 'team_id', 'pass_touchdown': 'receiving_tds', 
        'epa': 'receiving_epa', 'air_yards': 'receiving_air_yards'
    })
    
    # Safe Merge helpers
    targets_df = pbp_df.groupby(['receiver_player_id', 'week']).size().reset_index(name='targets')
    receptions_df = pbp_df[pbp_df['complete_pass']==1].groupby(['receiver_player_id', 'week']).size().reset_index(name='receptions')
    
    rec_stats = pd.merge(rec_stats, targets_df, left_on=['gsis_id', 'week'], right_on=['receiver_player_id', 'week'], how='left')
    rec_stats = pd.merge(rec_stats, receptions_df, left_on=['gsis_id', 'week'], right_on=['receiver_player_id', 'week'], how='left')
    
    # Merge Team Context
    rec_stats = pd.merge(rec_stats, team_passing, on=['team_id', 'week'], how='left')
    rec_stats = pd.merge(rec_stats, team_targets, on=['team_id', 'week'], how='left')
    
    rec_stats = rec_stats.fillna(0)
    rec_stats['target_share'] = np.where(rec_stats['team_targets'] > 0, rec_stats['targets'] / rec_stats['team_targets'], 0)
    rec_stats['air_yards_share'] = np.where(rec_stats['team_air_yards'] > 0, rec_stats['receiving_air_yards'] / rec_stats['team_air_yards'], 0)
    rec_stats['wopr'] = (1.5 * rec_stats['target_share']) + (0.7 * rec_stats['air_yards_share'])

    # C. Passing & Rushing
    pass_stats = pbp_df.groupby(['passer_player_id', 'week', 'posteam']).agg({
        'passing_yards': 'sum', 'pass_touchdown': 'sum', 'interception': 'sum', 
        'complete_pass': 'sum', 'pass_attempt': 'sum', 'sack': 'sum', 'epa': 'mean'
    }).reset_index().rename(columns={
        'passer_player_id': 'gsis_id', 'posteam': 'team_id', 'pass_touchdown': 'passing_tds',
        'interception': 'interceptions', 'complete_pass': 'completions', 'pass_attempt': 'attempts', 
        'sack': 'sacks', 'epa': 'passing_epa'
    })
    
    rush_stats = pbp_df.groupby(['rusher_player_id', 'week']).agg({
        'rushing_yards': 'sum', 'rush_touchdown': 'sum', 'rush_attempt': 'sum', 'epa': 'mean'
    }).reset_index().rename(columns={
        'rusher_player_id': 'gsis_id', 'rush_touchdown': 'rushing_tds', 'rush_attempt': 'carries', 'epa': 'rushing_epa'
    })

    # D. MERGE ALL POSITIONS
    # Clean duplicates before merging
    pass_stats = clean_df(pass_stats)
    rush_stats = clean_df(rush_stats)
    rec_stats = clean_df(rec_stats)

    stats_2025 = pd.merge(pass_stats, rush_stats, on=['gsis_id', 'week'], how='outer')
    stats_2025 = pd.merge(stats_2025, rec_stats, on=['gsis_id', 'week'], how='outer')
    
    # E. Fix Team ID (The likely culprit of duplicates)
    # We consolidate team_id_x, team_id_y, team_id into one 'team_id'
    cols = stats_2025.columns
    team_cols = [c for c in cols if 'team_id' in c]
    
    # Coalesce team_id
    if team_cols:
        final_team = stats_2025[team_cols[0]]
        for col in team_cols[1:]:
            final_team = final_team.fillna(stats_2025[col])
        stats_2025['team_id'] = final_team
        
        # Drop the messy columns
        stats_2025 = stats_2025.drop(columns=team_cols)
        # Add pure team_id back
        stats_2025['team_id'] = final_team

    stats_2025['season'] = 2025
    
    # Fill missing columns
    for col in KEEP_COLS:
        if col not in stats_2025.columns:
            stats_2025[col] = 0
            
    stats_2025 = stats_2025.fillna(0)
    
    # F. FINAL CLEAN: Select ONLY KEEP_COLS
    stats_2025 = stats_2025[KEEP_COLS]
    stats_2025 = clean_df(stats_2025)
    
    all_weekly.append(stats_2025)

    # --- SAVE WEEKLY STATS ---
    print(f"   -> Concatenating {len(all_weekly)} DataFrames...")
    final_weekly = pd.concat(all_weekly, ignore_index=True)
    
    final_weekly.to_sql('weekly_stats', engine, if_exists='replace', index=False)
    print(f"   ✅ Saved {len(final_weekly)} Weekly Stats (2023-2025).")

    # --- STEP 5: RE-CREATE SEASON STATS ---
    print("\n4. 🔄 Aggregating Season Stats (2023-2025)...")
    season_df = final_weekly.groupby(['gsis_id', 'season', 'team_id']).agg({
        'passing_yards': 'sum', 'passing_tds': 'sum', 'interceptions': 'sum', 'passing_epa': 'mean',
        'rushing_yards': 'sum', 'rushing_tds': 'sum', 'rushing_epa': 'mean',
        'receiving_yards': 'sum', 'receiving_tds': 'sum', 'receiving_epa': 'mean', 'receptions': 'sum',
        'wopr': 'mean', 'target_share': 'mean'
    }).reset_index()
    season_df.to_sql('season_stats', engine, if_exists='replace', index=False)
    print(f"   ✅ Saved {len(season_df)} Season Stats.")

    # --- STEP 6: TEAM DEFENSE (2025) ---
    print("\n5. 🛡️ Calculating Team Defense (2025)...")
    def_stats_25 = pbp_df.groupby(['defteam', 'season']).agg({
        'sack': 'sum', 'interception': 'sum', 'fumble_lost': 'sum'
    }).reset_index().rename(columns={'defteam': 'team_id', 'sack': 'def_sacks_made', 'interception': 'def_interceptions', 'fumble_lost': 'def_fumbles_recovered'})
    def_stats_25.to_sql('team_season_stats', engine, if_exists='replace', index=False)
    print("   ✅ Team Defense (2025) Calculated & Saved.")

    print("\n🎉 NUCLEAR RELOAD COMPLETE.")

if __name__ == "__main__":
    nuclear_reload()