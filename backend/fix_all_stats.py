import pandas as pd
import numpy as np
from database import engine
from sqlalchemy import text

def calculate_fantasy_points(row):
    """Standard PPR Fantasy Calculation"""
    # Passing: 1pt/25yds, 4pt/TD, -2pt/INT
    pass_pts = (row.get('passing_yards', 0) / 25) + (row.get('passing_tds', 0) * 4) - (row.get('interceptions', 0) * 2)
    
    # Rushing: 1pt/10yds, 6pt/TD
    rush_pts = (row.get('rushing_yards', 0) / 10) + (row.get('rushing_tds', 0) * 6)
    
    # Receiving: 1pt/10yds, 6pt/TD, 1pt/Reception (PPR)
    rec_pts = (row.get('receiving_yards', 0) / 10) + (row.get('receiving_tds', 0) * 6) + (row.get('receptions', 0) * 1)
    
    # Fumbles: -2pt
    fum_pts = (row.get('fumbles_lost', 0) * -2)
    
    return round(pass_pts + rush_pts + rec_pts + fum_pts, 2)

def run_fix():
    print("🚑 STARTING GRAND UNIFICATION STATS FIX (2023-2025)...")
    
    YEARS = [2023, 2024, 2025]
    BASE_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{}.csv.gz"
    
    all_stats = []

    for year in YEARS:
        print(f"\n📥 Downloading {year} Data... (This may take a moment)")
        try:
            df = pd.read_csv(BASE_URL.format(year), compression='gzip', low_memory=False)
            
            # 1. AGGREGATE PASSING
            pass_stats = df.groupby(['passer_player_id', 'passer_player_name', 'season']).agg({
                'passing_yards': 'sum',
                'touchdown': 'sum',
                'interception': 'sum',
                'sack': 'sum'
            }).reset_index().rename(columns={
                'passer_player_id': 'gsis_id',
                'passer_player_name': 'name',
                'touchdown': 'passing_tds',
                'sack': 'sacks_taken'
            })

            # 2. AGGREGATE RUSHING
            rush_stats = df.groupby(['rusher_player_id', 'rusher_player_name', 'season']).agg({
                'rushing_yards': 'sum',
                'touchdown': 'sum',
                'fumble_lost': 'sum'
            }).reset_index().rename(columns={
                'rusher_player_id': 'gsis_id',
                'rusher_player_name': 'name',
                'touchdown': 'rushing_tds',
                'fumble_lost': 'fumbles_lost'
            })

            # 3. AGGREGATE RECEIVING
            rec_stats = df.groupby(['receiver_player_id', 'receiver_player_name', 'season']).agg({
                'receiving_yards': 'sum',
                'touchdown': 'sum',
                'complete_pass': 'sum'
            }).reset_index().rename(columns={
                'receiver_player_id': 'gsis_id',
                'receiver_player_name': 'name',
                'touchdown': 'receiving_tds',
                'complete_pass': 'receptions'
            })

            # 4. MERGE EVERYTHING (Carefully handling Name Collisions)
            
            # Merge Passing & Rushing
            merged = pd.merge(pass_stats, rush_stats, on=['gsis_id', 'season'], how='outer', suffixes=('_p', '_r'))
            
            # Combine Names: If 'name_p' exists use it, otherwise 'name_r'
            merged['name'] = merged['name_p'].combine_first(merged['name_r'])
            merged = merged.drop(columns=['name_p', 'name_r'])
            
            # Merge Result & Receiving
            # We use suffix '_rec' for receiving. The left table keeps 'name'.
            merged = pd.merge(merged, rec_stats, on=['gsis_id', 'season'], how='outer', suffixes=('', '_rec'))
            
            # Combine Names Again
            merged['name'] = merged['name'].combine_first(merged['name_rec'])
            merged = merged.drop(columns=['name_rec'])

            # Fill NaNs with 0
            merged = merged.fillna(0)
            
            # Rename 'interception' if needed
            if 'interception' in merged.columns:
                merged = merged.rename(columns={'interception': 'interceptions'})

            # 5. CALCULATE FANTASY POINTS
            merged['fantasy_points'] = merged.apply(calculate_fantasy_points, axis=1)
            
            # Filter out players with zero fantasy points (irrelevant backups)
            merged = merged[merged['fantasy_points'] != 0]

            print(f"   ✅ Processed {len(merged)} players for {year}.")
            all_stats.append(merged)
            
        except Exception as e:
            print(f"   ⚠️ Error processing {year}: {e}")

    # 6. COMBINE AND UPLOAD
    if all_stats:
        final_df = pd.concat(all_stats, ignore_index=True)
        
        # Ensure correct columns for DB
        final_cols = [
            'gsis_id', 'season', 'passing_yards', 'passing_tds', 'interceptions',
            'rushing_yards', 'rushing_tds', 'receiving_yards', 'receiving_tds', 
            'fantasy_points', 'receptions', 'fumbles_lost', 'sacks_taken'
        ]
        
        # Select only valid columns (and fill any missing ones with 0 just in case)
        for col in final_cols:
            if col not in final_df.columns:
                final_df[col] = 0
                
        final_df = final_df[final_cols]
        
        print(f"\n💾 Uploading {len(final_df)} rows to season_stats...")
        
        # THIS COMMAND REPLACES THE OLD TABLE ENTIRELY
        final_df.to_sql('season_stats', engine, if_exists='replace', index=False)
        print("✅ DONE. Database Refueled Successfully!")

if __name__ == "__main__":
    run_fix()