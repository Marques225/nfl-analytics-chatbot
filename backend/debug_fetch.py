# debug_fetch.py
from etl.fetch.pfr_weekly import fetch_week

# Fetch just one week to see if the new logic works
print("Fetching 2024 Week 1...")
df = fetch_week(2024, 1)

if df.empty:
    print("❌ FAIL: DataFrame is empty.")
else:
    # Check if our new column exists
    if "pfr_player_id" in df.columns:
        print("✅ SUCCESS: Found 'pfr_player_id' column!")
        
        # PRINT ALL COLUMNS so we can see the real names
        print("\n--- ACTUAL COLUMNS FOUND ---")
        print(list(df.columns)) 
        
        # Print the first row to verify data quality
        print("\n--- FIRST ROW SAMPLE ---")
        print(df.iloc[0].to_dict())
    else:
        print("❌ FAIL: DataFrame exists, but 'pfr_player_id' is MISSING.")