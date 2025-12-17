from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("\n--- 🔍 DIAGNOSTICS REPORT ---")
    
    # 1. Check if the table has ANY data
    count = conn.execute(text("SELECT COUNT(*) FROM weekly_rushing_stats")).scalar()
    print(f"Total Rows in Weekly Rushing: {count}")
    
    if count > 0:
        # 2. Check which Seasons and Weeks exist
        print("\nAvailable Seasons & Weeks:")
        weeks = conn.execute(text("SELECT DISTINCT season, week FROM weekly_rushing_stats ORDER BY season DESC, week ASC")).fetchall()
        for row in weeks:
            print(f"  -> Season {row.season} | Week {row.week}")

        # 3. Check what the IDs look like (to verify our Join works)
        sample = conn.execute(text("SELECT pfr_player_id, player_name FROM weekly_rushing_stats LIMIT 3")).fetchall()
        print("\nSample Data (IDs):")
        for row in sample:
            print(f"  -> Name: {row.player_name} | ID: '{row.pfr_player_id}'")
            
    print("-----------------------------\n")