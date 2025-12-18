from database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
all_tables = inspector.get_table_names()

print("\n--- 📊 DATABASE TABLES ---")
print(all_tables)

print("\n--- 🛡️ DEFENSIVE PLAYER COLUMNS (If exists) ---")
if 'season_defense_stats' in all_tables:
    columns = inspector.get_columns('season_defense_stats')
    for c in columns:
        print(f"👉 {c['name']}")
else:
    print("❌ Table 'season_defense_stats' NOT FOUND")

print("\n--- 🏈 TEAM STATS COLUMNS (If exists) ---")
if 'season_team_stats' in all_tables:
    columns = inspector.get_columns('season_team_stats')
    for c in columns:
        print(f"👉 {c['name']}")
else:
    print("❌ Table 'season_team_stats' NOT FOUND")
print("----------------------------------\n")