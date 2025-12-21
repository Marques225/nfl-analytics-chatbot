import pandas as pd
import io

def inspect_raw_source():
    print("🕵️ INSPECTING RAW 2025 PLAY-BY-PLAY DATA...")
    
    # 1. Download the first 1000 rows of 2025 data (Fast Check)
    PBP_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2025.csv.gz"
    
    try:
        print("   Downloading sample of 2025 data...")
        # valid columns to check
        cols_to_check = ['epa', 'cpoe', 'sack', 'defteam', 'posteam', 'air_yards', 'xyac_epa', 'wpa']
        
        df = pd.read_csv(PBP_URL, compression='gzip', nrows=1000, low_memory=False)
        
        print(f"\n✅ DOWNLOAD SUCCESSFUL (First 1000 rows)")
        
        # 2. Check for Advanced Metrics
        print("\n--- COLUMN AVAILABILITY CHECK ---")
        for col in cols_to_check:
            found = col in df.columns
            sample_val = df[col].iloc[0] if found else "N/A"
            print(f"   [{'✅' if found else '❌'}] {col.ljust(15)} Sample: {sample_val}")

        # 3. Check specific NULL rates for EPA (is it mostly empty?)
        if 'epa' in df.columns:
            null_count = df['epa'].isnull().sum()
            print(f"\n   EPA Null Rate: {null_count}/1000 rows (Expected: punts/kickoffs have no EPA)")
            
    except Exception as e:
        print(f"❌ FAILED TO DOWNLOAD: {e}")

if __name__ == "__main__":
    inspect_raw_source()