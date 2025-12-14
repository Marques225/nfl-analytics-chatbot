# backend/etl/transform_stats.py
import pandas as pd
import re
from pathlib import Path

RAW_DIR = Path("data/raw")
CLEAN_DIR = Path("data/clean")

CLEAN_DIR.mkdir(parents=True, exist_ok=True)

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def transform_file(path: Path):
    df = pd.read_csv(path)

    if "Player" in df.columns:
        df["player_id"] = df["Player"].apply(slugify)

    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    out = CLEAN_DIR / path.name
    df.to_csv(out, index=False)
    print(f"Cleaned {out}")

if __name__ == "__main__":
    for file in RAW_DIR.glob("*.csv"):
        transform_file(file)
