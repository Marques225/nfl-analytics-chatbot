# backend/etl/transform/receiving.py
import pandas as pd

def normalize_receiving(df, season, week):
    # 1. Rename columns to match Database Schema
    rename_map = {
        "player": "player_name",
        
        # Receiving Stats
        "rec_tgt": "targets",        # <--- Standard name
        "tgt": "targets",            # <--- ADD THIS
        
        "rec": "receptions",
        "rec_yds": "receiving_yards",
        "rec_td": "receiving_tds",
        
        "rec_long": "longest_reception", # <--- Standard name
        "long": "longest_reception",     # <--- ADD THIS
        
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