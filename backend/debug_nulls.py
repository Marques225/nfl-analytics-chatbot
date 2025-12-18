from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("\n--- 🔍 INSPECTING SEASON_TEAM_STATS ---")
    
    # Check for rows with NULL sacks in 2024
    sql = text("""
        SELECT t.name, s.def_sacks_made 
        FROM season_team_stats s
        JOIN teams t ON t.id = s.team_id
        WHERE s.season = 2024
        LIMIT 5
    """)
    
    rows = conn.execute(sql).fetchall()
    
    for row in rows:
        print(f"Team: {row.name} | Sacks: {row.def_sacks_made}")
        
    print("---------------------------------------")