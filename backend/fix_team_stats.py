import pandas as pd
from database import engine
from sqlalchemy import text

def fix_team_stats_final():
    print("🚑 STARTING FINAL TEAM STATS FIX (Adding Yards & TDs)...")

    PBP_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{}.csv.gz"
    YEARS = [2023, 2024, 2025]
    
    all_team_stats = []

    for year in YEARS:
        print(f"\nProcessing {year}...")
        try:
            print(f"   -> Downloading PBP...")
            # Added 'yards_gained' and 'touchdown'
            pbp = pd.read_csv(
                PBP_URL.format(year), 
                compression='gzip', 
                low_memory=False, 
                usecols=['season', 'defteam', 'posteam', 'sack', 'fumble_lost', 'interception', 'yards_gained', 'touchdown']
            )
            
            # 1. DEFENSE (Sacks, INTs, Fumbles Rec)
            def_stats = pbp.groupby(['defteam', 'season']).agg({
                'sack': 'sum', 
                'interception': 'sum',
                'fumble_lost': 'sum'
            }).reset_index().rename(columns={
                'defteam': 'team_id',
                'sack': 'def_sacks_made',
                'interception': 'def_interceptions',
                'fumble_lost': 'def_fumbles_recovered'
            })
            
            # 2. OFFENSE (Yards, TDs, Sacks Allowed)
            off_stats = pbp.groupby(['posteam', 'season']).agg({
                'yards_gained': 'sum',   # TOTAL YARDS
                'touchdown': 'sum',      # TOTAL TDS
                'sack': 'sum',
                'fumble_lost': 'sum',
                'interception': 'sum'
            }).reset_index().rename(columns={
                'posteam': 'team_id',
                'yards_gained': 'off_total_yards',
                'touchdown': 'off_total_tds',
                'sack': 'off_sacks_allowed',
                'fumble_lost': 'off_fumbles_lost',
                'interception': 'off_interceptions'
            })
            
            # 3. MERGE
            team_stats = pd.merge(def_stats, off_stats, on=['team_id', 'season'], how='outer')
            team_stats = team_stats.fillna(0)
            
            all_team_stats.append(team_stats)
            print(f"   ✅ Calculated Yards/TDs/Sacks for {len(team_stats)} teams.")
            
        except Exception as e:
            print(f"   ⚠️ Error for {year}: {e}")

    # UPLOAD
    if all_team_stats:
        full_df = pd.concat(all_team_stats)
        full_df = full_df[full_df['team_id'].notna()]
        
        print(f"\n💾 Uploading {len(full_df)} rows to season_team_stats...")
        full_df.to_sql('season_team_stats', engine, if_exists='replace', index=False)
        print("✅ DONE. Team stats are now populated with OFFENSE and DEFENSE data.")

if __name__ == "__main__":
    fix_team_stats_final()