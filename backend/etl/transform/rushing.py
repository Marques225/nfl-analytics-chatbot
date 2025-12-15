# backend/etl/transform/rushing.py
import pandas as pd

def normalize_rushing(df, season, week):
    # 1. Rename columns to match Database Schema
    rename_map = {
        "player": "player_name",
        
        # Rushing Stats
        "rush_att": "carries",
        "rush_yds": "rushing_yards",
        "rush_td": "rushing_tds",
        "rush_long": "longest_rush", # <--- Standard name
        "long": "longest_rush",      # <--- ADD THIS (The PFR Weekly alias)
        
        "tm": "team",
        "opp": "opponent"
    }
    
    df = df.rename(columns=rename_map)

    # 2. Normalize remaining column names
    df.columns = (
        df.columns
        .map(str)
        .str.lower()
        .str.replace("%", "_pct")
        .str.replace(" ", "_")
        .str.replace("+", "")
    )

    # 3. Filter Garbage Rows
    if "pfr_player_id" in df.columns:
        df = df.dropna(subset=["pfr_player_id"])

    # 4. Filter duplicate columns
    df = df.loc[:, ~df.columns.duplicated()]

    # 5. Add Metadata
    df["season"] = season
    df["week"] = week

    return df