import requests

# backend/etl/fetch_stats.py
import pandas as pd
from pathlib import Path

BASE_URL = "https://www.pro-football-reference.com/years/{season}/week_{week}.htm"
RAW_DIR = Path("data/raw")

RAW_DIR.mkdir(parents=True, exist_ok=True)

def fetch_week(season: int, week: int) -> dict:
    url = BASE_URL.format(season=season, week=week)

    tables = pd.read_html(url)
    return {
        "passing": tables[0],
        "rushing": tables[1],
        "receiving": tables[2],
        "defense": tables[3],
    }

def save_week(season: int, week: int):
    data = fetch_week(season, week)
    for name, df in data.items():
        path = RAW_DIR / f"{season}_week{week}_{name}.csv"
        df.to_csv(path, index=False)
        print(f"Saved {path}")

if __name__ == "__main__":
    save_week(2024, 1)
