import supabase
# backend/etl/load_stats.py
import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
CLEAN_DIR = Path("data/clean")

def sync_players(df):
    if "pfr_player_id" not in df.columns or "player_name" not in df.columns:
        return

    players_to_sync = df[["pfr_player_id", "player_name"]].drop_duplicates().dropna()
    
    with engine.begin() as conn:
        for _, row in players_to_sync.iterrows():
            name = row["player_name"]
            exists = conn.execute(
                text("SELECT player_id FROM players WHERE name = :name"), 
                {"name": name}
            ).fetchone()
            
            if not exists:
                print(f"Creating new player: {name}")
                conn.execute(
                    text("INSERT INTO players (name, position, team_id) VALUES (:name, 'QB', NULL)"),
                    {"name": name}
                )

def load_csv(path: Path, table_name: str):
    df = pd.read_csv(path)
    if df.empty: return

    sync_players(df)

    # 1. Prepare Schema (The Target List)
    valid_cols = [
        "season", "week", "pfr_player_id", "player_name", "team",
        "passing_yards", "passing_tds", "interceptions", 
        "completions", "attempts", "passer_rating",
        "sacks", "sack_yards", "longest_pass", "qbr",
        "first_downs", "fourth_qtr_comebacks", "game_winning_drives"
    ]

    # 2. SCHEMA ENFORCEMENT (The Fix)
    # If a column is missing in the CSV, add it as None (NULL)
    # This ensures the Database Table is always created with ALL columns.
    for col in valid_cols:
        if col not in df.columns:
            df[col] = None

    # 3. Cleanup Old Data
    season = int(df["season"].iloc[0])
    week = int(df["week"].iloc[0])
    print(f"🧹 Clearing existing data for Season {season} Week {week} in {table_name}...")
    
    try:
        with engine.begin() as conn:
            conn.execute(
                text(f"DELETE FROM {table_name} WHERE season = :s AND week = :w"),
                {"s": season, "w": week}
            )
    except ProgrammingError as e:
        if "does not exist" in str(e):
            print(f"⚠️ Table '{table_name}' not found. It will be created now.")
        else:
            raise e

    # 4. Load Data
    # Now df_clean is GUARANTEED to have 'sacks', 'longest_pass', etc.
    df_clean = df[valid_cols]
    
    df_clean.to_sql(table_name, engine, if_exists="append", index=False, method="multi")
    print(f"✅ Loaded {path} ({len(df_clean)} rows)")

if __name__ == "__main__":
    for file in CLEAN_DIR.glob("*passing*.csv"):
        load_csv(file, "weekly_passing_stats")