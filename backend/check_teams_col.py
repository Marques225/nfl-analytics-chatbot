from database import engine
from sqlalchemy import inspect

columns = inspect(engine).get_columns('teams')
print("\n--- COLUMNS IN 'TEAMS' TABLE ---")
for c in columns:
    print(f"👉 {c['name']}")
print("--------------------------------\n")