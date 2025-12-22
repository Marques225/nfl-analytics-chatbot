import pandas as pd
import numpy as np
from database import engine
from sqlalchemy import text

def calculate_fantasy_points(row):
    """Standard PPR Fantasy Calculation"""
    pass_pts = (row.get('passing_yards', 0) / 25) + (row.get('passing_tds', 0) * 4) - (row.get('interceptions', 0) * 2)
    rush_pts = (row.get('rushing_yards', 0) / 10) + (row.get('rushing_tds', 0) * 6)
    rec_pts = (row.get('receiving_yards', 0) / 10) + (row.get('receiving_tds', 0) * 6) + (row.get('receptions', 0) * 1)
    fum_pts = (row.get('fumbles_lost', 0) * -2)
    return round(pass_pts + rush_pts + rec_pts + fum_pts, 2)

def run_fix():
    print("🚑 STARTING ROBUST DATA REPAIR (2023-2025)...")
    
    YEARS = [2023, 2024, 2025]
    BASE_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{}.csv.gz"
    
    all_stats = []

    for year in YEARS:
        print(f"\n📥 Downloading {year} Data...")
        try:
            # Load specific columns to save memory & ensure accuracy
            cols = [
                'season', 'passer_player_id', 'passer_player_name', 'rusher_player_id', 'rusher_player_name',
                'receiver_player_id', 'receiver_player_name', 'passing_yards', 'rushing_yards', 'receiving_yards',
                'pass_touchdown', 'rush_touchdown', 'interception', 'fumble_lost', 'sack', 'complete_pass'
            ]
            df = pd.read_csv(BASE_URL.format(year), compression='gzip', usecols=lambda c: c in cols, low_memory=False)
            
            # --- 1. PASSING STATS ---
            # Group by Passer ID. Sum 'pass_touchdown' for TDs.
            pass_stats = df.groupby(['passer_player_id', 'passer_player_name', 'season']).agg({
                'passing_yards': 'sum',
                'pass_touchdown': 'sum',  # Explicit Passing TDs
                'interception': 'sum',
                'sack': 'sum'
            }).reset_index().rename(columns={
                'passer_player_id': 'gsis_id',
                'passer_player_name': 'name',
                'pass_touchdown': 'passing_tds',
                'sack': 'sacks_taken',
                'interception': 'interceptions'
            })

            # --- 2. RUSHING STATS ---
            # Group by Rusher ID. Sum 'rush_touchdown' for TDs.
            rush_stats = df.groupby(['rusher_player_id', 'rusher_player_name', 'season']).agg({
                'rushing_yards': 'sum',
                'rush_touchdown': 'sum',  # Explicit Rushing TDs
                'fumble_lost': 'sum'
            }).reset_index().rename(columns={
                'rusher_player_id': 'gsis_id',
                'rusher_player_name': 'name',
                'rush_touchdown': 'rushing_tds',
                'fumble_lost': 'fumbles_lost'
            })

            # --- 3. RECEIVING STATS ---
            # Group by Receiver ID. Sum 'pass_touchdown' (caught TDs) for TDs.
            rec_stats = df.groupby(['receiver_player_id', 'receiver_player_name', 'season']).agg({
                'receiving_yards': 'sum',
                'pass_touchdown': 'sum',  # Receiving TD is a caught pass_touchdown
                'complete_pass': 'sum'
            }).reset_index().rename(columns={
                'receiver_player_id': 'gsis_id',
                'receiver_player_name': 'name',
                'pass_touchdown': 'receiving_tds',
                'complete_pass': 'receptions'
            })

            # --- 4. MERGE (The "Grand Unification") ---
            # Merge Passing & Rushing
            merged = pd.merge(pass_stats, rush_stats, on=['gsis_id', 'season'], how='outer', suffixes=('_p', '_r'))
            merged['name'] = merged['name_p'].combine_first(merged['name_r'])
            merged = merged.drop(columns=['name_p', 'name_r'])
            
            # Merge Result & Receiving
            merged = pd.merge(merged, rec_stats, on=['gsis_id', 'season'], how='outer', suffixes=('', '_rec'))
            merged['name'] = merged['name'].combine_first(merged['name_rec']) # Fix name
            merged = merged.drop(columns=['name_rec'])

            merged = merged.fillna(0)

            # --- 5. CALCULATE FANTASY ---
            merged['fantasy_points'] = merged.apply(calculate_fantasy_points, axis=1)
            merged = merged[merged['fantasy_points'] != 0] # Clean garbage

            # --- 🕵️‍♂️ SPY MODE: Verify Christian McCaffrey ---
            cmc = merged[merged['name'] == 'C.McCaffrey']
            if not cmc.empty:
                print(f"   🕵️‍♂️ SPY REPORT (C.McCaffrey {year}): {cmc[['rushing_tds', 'receiving_tds', 'fantasy_points']].to_dict(orient='records')}")
            
            all_stats.append(merged)
            print(f"   ✅ Processed {len(merged)} players for {year}.")

        except Exception as e:
            print(f"   ⚠️ Error processing {year}: {e}")

    # 6. UPLOAD
    if all_stats:
        final_df = pd.concat(all_stats, ignore_index=True)
        
        final_cols = [
            'gsis_id', 'season', 'passing_yards', 'passing_tds', 'interceptions',
            'rushing_yards', 'rushing_tds', 'receiving_yards', 'receiving_tds', 
            'fantasy_points', 'receptions', 'fumbles_lost', 'sacks_taken'
        ]
        
        # Ensure all columns exist
        for col in final_cols:
            if col not in final_df.columns: final_df[col] = 0
                
        final_df = final_df[final_cols]
        
        print(f"\n💾 Overwriting database with {len(final_df)} clean rows...")
        final_df.to_sql('season_stats', engine, if_exists='replace', index=False)
        print("✅ DATABASE REPAIR COMPLETE.")

if __name__ == "__main__":
    run_fix()