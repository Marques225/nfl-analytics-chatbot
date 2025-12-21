import pandas as pd
from database import engine
from sqlalchemy import text

def fix_team_stats_only():
    print("🚑 STARTING SURGICAL FIX: season_team_stats...")

    # We use the verified PBP URL pattern
    PBP_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{}.csv.gz"
    YEARS = [2023, 2024, 2025]
    
    all_team_stats = []

    for year in YEARS:
        print(f"\nProcessing {year}...")
        try:
            print(f"   -> Downloading PBP (this may take 10-20s)...")
            # We only need specific columns to keep it fast
            pbp = pd.read_csv(
                PBP_URL.format(year), 
                compression='gzip', 
                low_memory=False, 
                usecols=['season', 'defteam', 'posteam', 'sack', 'fumble_lost', 'interception']
            )
            
            # 1. CALCULATE DEFENSE STATS (Sacks Made, Ints Caught, Fumbles Recovered)
            # Group by 'defteam' (The team playing defense)
            def_stats = pbp.groupby(['defteam', 'season']).agg({
                'sack': 'sum', 
                'interception': 'sum',
                'fumble_lost': 'sum' # Fumbles lost by the offense = Recovered by Defense
            }).reset_index().rename(columns={
                'defteam': 'team_id',
                'sack': 'def_sacks_made',
                'interception': 'def_interceptions',
                'fumble_lost': 'def_fumbles_recovered'
            })
            
            # 2. CALCULATE OFFENSE STATS (Sacks Allowed, Fumbles Lost)
            # Group by 'posteam' (The team playing offense)
            off_stats = pbp.groupby(['posteam', 'season']).agg({
                'sack': 'sum',
                'fumble_lost': 'sum',
                'interception': 'sum'
            }).reset_index().rename(columns={
                'posteam': 'team_id',
                'sack': 'off_sacks_allowed',
                'fumble_lost': 'off_fumbles_lost',
                'interception': 'off_interceptions'
            })
            
            # 3. MERGE THEM
            # We merge on team_id and season to get a complete picture
            team_stats = pd.merge(def_stats, off_stats, on=['team_id', 'season'], how='outer')
            
            # Fill NaNs (e.g. if a team somehow had 0 sacks)
            team_stats = team_stats.fillna(0)
            
            all_team_stats.append(team_stats)
            print(f"   ✅ Calculated stats for {len(team_stats)} teams.")
            
        except Exception as e:
            print(f"   ⚠️ Critical Error for {year}: {e}")

    # 3. UPLOAD (Replace ONLY this table)
    if all_team_stats:
        full_df = pd.concat(all_team_stats)
        
        # Ensure 'team_id' is clean (remove 'nan' or empty strings if any)
        full_df = full_df[full_df['team_id'].notna()]
        
        print(f"\n💾 Uploading {len(full_df)} rows to season_team_stats...")
        
        # We replace ONLY the 'season_team_stats' table
        full_df.to_sql('season_team_stats', engine, if_exists='replace', index=False)
        print("✅ DONE. season_team_stats has been fixed with calculated data.")
    else:
        print("❌ No data found.")

if __name__ == "__main__":
    fix_team_stats_only()