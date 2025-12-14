import supabase
# backend/etl/load_stats.py
import os
import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

CLEAN_DIR = Path("data/clean")

def load_csv(path: Path, table_name: str):
    df = pd.read_csv(path)

    # ---- SAFETY FIXES (minimal but critical) ----
    df.columns = df.columns.map(str)
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    df = df.loc[:, ~df.columns.duplicated()]

    # Ensure season/week exist (derived from filename)
    # Example filename: 2024_week5_passing.csv
    parts = path.stem.split("_")
    df["season"] = int(parts[0])
    df["week"] = int(parts[1].replace("week", ""))
    # --------------------------------------------

    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False,
        method="multi"
    )

    print(f"Loaded {path} into {table_name}")


if __name__ == "__main__":
    for file in CLEAN_DIR.glob("*passing*.csv"):
        load_csv(file, "weekly_passing_stats")
