import pandas as pd

print("🔍 INSPECTING NFLVERSE CSV COLUMNS...")
url = "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv"
try:
    # Read just the first row to get headers
    df = pd.read_csv(url, nrows=1)
    print("\n✅ AVAILABLE COLUMNS:")
    print(df.columns.tolist())
except Exception as e:
    print(f"❌ Error downloading CSV: {e}")



# from database import engine
# from sqlalchemy import inspect

# inspector = inspect(engine)
# # Check a WEEKLY table this time
# columns = inspector.get_columns('weekly_passing_stats')

# print("\n--- COLUMNS IN 'WEEKLY_PASSING_STATS' ---")
# for column in columns:
#     print(f"👉 {column['name']}")
# print("-----------------------------------------\n")