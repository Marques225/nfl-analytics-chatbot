# backend/etl/transform/passing.py
import pandas as pd

def normalize_passing(df, season, week):
    # 1. Rename columns to match Database Schema
    # We map BOTH the "old" PFR names and the "new" data-stat names to be safe.
    rename_map = {
        "player": "player_name",
        
        # Passing Stats
        "yds": "passing_yards",
        "pass_yds": "passing_yards",
        "td": "passing_tds",
        "pass_td": "passing_tds",
        "att": "attempts",
        "pass_att": "attempts",
        "cmp": "completions",
        "pass_cmp": "completions",
        "int": "interceptions",
        "pass_int": "interceptions",
        "rate": "passer_rating",
        "pass_rating": "passer_rating",
        
        # Advanced Stats (The missing pieces)
        "sk": "sacks",
        "pass_sacked": "sacks",
        "yds.1": "sack_yards",       # PFR sometimes duplicates 'yds' header
        "pass_sacked_yds": "sack_yards",
        "lng": "longest_pass",
        "pass_long": "longest_pass",
        "qbr": "qbr",
        "1st": "first_downs",
        "pass_first_down": "first_downs",
        "4qc": "fourth_qtr_comebacks",
        "comebacks": "fourth_qtr_comebacks",
        "gwd": "game_winning_drives",
        
        # Metadata
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