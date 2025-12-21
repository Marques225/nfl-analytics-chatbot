import pandas as pd
import io
import requests

def check_2025_status():
    print("🕵️ CHECKING FOR LIVE 2025 DATA...")
    
    # 1. LIVE ROSTERS (Official nflverse data)
    print("\n--- 1. CHECKING 2025 ROSTERS ---")
    try:
        # We look at the 'nflverse-data' repository directly
        roster_url = "https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_2025.csv"
        rosters = pd.read_csv(roster_url)
        print(f"✅ FOUND 2025 ROSTERS! ({len(rosters)} players)")
        print(rosters[['full_name', 'team', 'position', 'gsis_id']].head(3))
    except Exception as e:
        print(f"❌ Failed to find Rosters: {e}")

    # 2. LIVE PLAY-BY-PLAY (The source of all stats)
    print("\n--- 2. CHECKING 2025 GAME STATS ---")
    try:
        # This file contains EVERY play from the 2025 season so far
        pbp_url = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2025.csv.gz"
        print("   (Downloading ~50MB of 2025 play-by-play data, please wait...)")
        pbp = pd.read_csv(pbp_url, compression='gzip', low_memory=False)
        
        print(f"✅ FOUND 2025 PLAY DATA! ({len(pbp)} plays processed)")
        
        # Prove it's recent by showing the latest games
        recent_games = pbp[['game_id', 'home_team', 'away_team', 'week']].drop_duplicates().tail(5)
        print("   Latest 5 Games in Database:")
        print(recent_games)
        
        # Check for Advanced Stats availability
        print("\n   Checking for Advanced Columns in 2025:")
        cols = pbp.columns
        print(f"   - EPA (Expected Points Added)? {'epa' in cols}")
        print(f"   - CPOE (Completion % Over Expected)? {'cpoe' in cols}")
        print(f"   - WPA (Win Probability Added)? {'wpa' in cols}")
        
    except Exception as e:
        print(f"❌ Failed to find 2025 Stats: {e}")

if __name__ == "__main__":
    check_2025_status()