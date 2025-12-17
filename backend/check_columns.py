# backend/check_columns.py
from database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
# Change 'players' to 'season_passing_stats'
columns = inspector.get_columns('season_passing_stats')

print("\n--- COLUMNS IN 'SEASON_PASSING_STATS' ---")
for column in columns:
    print(f"👉 {column['name']}")
print("-----------------------------------------\n") 