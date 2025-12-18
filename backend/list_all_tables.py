from database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()

print("\n--- 🗄️ ALL TABLES ---")
for t in tables:
    print(f"👉 {t}")
print("---------------------\n")