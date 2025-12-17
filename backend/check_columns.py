from database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
# Check a WEEKLY table this time
columns = inspector.get_columns('weekly_passing_stats')

print("\n--- COLUMNS IN 'WEEKLY_PASSING_STATS' ---")
for column in columns:
    print(f"👉 {column['name']}")
print("-----------------------------------------\n")