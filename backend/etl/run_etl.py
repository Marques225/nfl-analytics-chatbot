# backend/etl/run_etl.py
from pathlib import Path
from etl.state import get_state, update_state
from etl.config import MIN_SEASON, CURRENT_SEASON, CURRENT_WEEK, engine
from etl.fetch.pfr_weekly import fetch_week
from etl.fetch.validators import validate_week
from etl.transform.passing import normalize_passing

# FIX: Import from the correct file (load_stats.py), not etl.load.passing
from etl.load_stats import load_csv 

def determine_weeks(season, last_season, last_week):
    if season < CURRENT_SEASON:
        start_week = 1 if season != last_season else last_week + 1
        return range(start_week, 19)
    else:
        start_week = 1 if season != last_season else last_week + 1
        return range(start_week, CURRENT_WEEK + 1)

def main(full_refresh=False):
    if full_refresh:
        last_season, last_week = MIN_SEASON, 0
    else:
        last_season, last_week = get_state()

    print(f"🚀 Starting ETL. Last processed: {last_season} Week {last_week}")

    for season in range(last_season, CURRENT_SEASON + 1):
        weeks = determine_weeks(season, last_season, last_week)

        for week in weeks:
            print(f"Fetching season {season}, week {week} ...")
            try:
                # 1️⃣ FETCH
                df = fetch_week(season, week)
                
                # Check for empty DF before validation
                if df.empty:
                    print(f"⚠️  No data found for {season} Week {week}. Skipping.")
                    continue

                # 2️⃣ VALIDATE
                # (Simple check to ensure we have player column)
                if "player" not in df.columns:
                    print(f"❌ Validation Failed: 'player' column missing. Columns: {list(df.columns)}")
                    continue

                # 3️⃣ RAW SNAPSHOT
                raw_path = Path(f"data/raw/{season}_week{week}_passing.csv")
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(raw_path, index=False)

                # 4️⃣ TRANSFORM
                df_clean = normalize_passing(df, season=season, week=week)
                
                # Save Clean Snapshot (Important for the Loader)
                clean_path = Path(f"data/clean/{season}_week{week}_passing.csv")
                clean_path.parent.mkdir(parents=True, exist_ok=True)
                df_clean.to_csv(clean_path, index=False)

                # 5️⃣ LOAD
                # Use the load_csv function from load_stats.py
                load_csv(clean_path, "weekly_passing_stats")

                # 6️⃣ STATE UPDATE
                update_state(season, week)

                print(f" ✅ Done: season {season}, week {week}")

            except Exception as e:
                print(f" ❌ Error fetching season {season}, week {week}: {e}")
                # We raise to stop the pipeline so you don't mark failed weeks as 'done'
                raise 

if __name__ == "__main__":
    # Set full_refresh=True to re-process Week 1 with the new fixes
    main(full_refresh=True)