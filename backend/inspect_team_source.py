import pandas as pd

def inspect_team_source():
    print("🕵️ INSPECTING TEAM DATA SOURCE...")
    
    # Check 2024 Team Stats File
    URL = "https://github.com/nflverse/nflverse-data/releases/download/team_stats/team_stats_2024.parquet"
    
    try:
        df = pd.read_parquet(URL)
        print(f"✅ Downloaded 2024 Team Stats ({len(df)} rows)")
        
        # Print all columns containing 'sack' or 'fumble'
        sack_cols = [c for c in df.columns if 'sack' in c]
        fumble_cols = [c for c in df.columns if 'fumble' in c]
        
        print("\n--- SACK COLUMNS FOUND ---")
        print(sack_cols)
        print("Sample Values:")
        print(df[['team'] + sack_cols].head(3))
        
        print("\n--- FUMBLE COLUMNS FOUND ---")
        print(fumble_cols)
        print("Sample Values:")
        print(df[['team'] + fumble_cols].head(3))
        
    except Exception as e:
        print(f"❌ Failed to load source: {e}")

if __name__ == "__main__":
    inspect_team_source()