# backend/etl/run_etl.py
from pathlib import Path
from etl.state import get_state, update_state
from etl.config import MIN_SEASON, CURRENT_SEASON, CURRENT_WEEK, engine

# Fetchers
from etl.fetch.pfr_weekly import fetch_week as fetch_passing
from etl.fetch.pfr_rushing import fetch_rushing_week
from etl.fetch.pfr_receiving import fetch_receiving_week # <--- NEW

# Transformers
from etl.transform.passing import normalize_passing
from etl.transform.rushing import normalize_rushing
from etl.transform.receiving import normalize_receiving # <--- NEW

# Loader
from etl.load_stats import load_csv 

def determine_weeks(season, last_season, last_week):
    if season < CURRENT_SEASON:
        start_week = 1 if season != last_season else last_week + 1
        return range(start_week, 19)
    else:
        start_week = 1 if season != last_season else last_week + 1
        return range(start_week, CURRENT_WEEK + 1)

def process_category(season, week, category_name, fetch_func, transform_func, table_name):
    print(f"   > Processing {category_name}...")
    try:
        # 1. Fetch
        df = fetch_func(season, week)
        if df.empty:
            print(f"     ⚠️ No {category_name} data found.")
            return

        # 2. Transform
        df_clean = transform_func(df, season=season, week=week)
        
        # 3. Save to CSV
        clean_path = Path(f"data/clean/{season}_week{week}_{category_name}.csv")
        clean_path.parent.mkdir(parents=True, exist_ok=True)
        df_clean.to_csv(clean_path, index=False)

        # 4. Load to DB
        load_csv(clean_path, table_name)
        
    except Exception as e:
        print(f"     ❌ Error processing {category_name}: {e}")
        pass

def main(full_refresh=False):
    if full_refresh:
        last_season, last_week = MIN_SEASON, 0
    else:
        last_season, last_week = get_state()

    print(f"🚀 Starting ETL. Last processed: {last_season} Week {last_week}")

    for season in range(last_season, CURRENT_SEASON + 1):
        weeks = determine_weeks(season, last_season, last_week)

        for week in weeks:
            print(f"\n--- Season {season}, Week {week} ---")
            
            # 1. Passing
            process_category(
                season, week, "passing", 
                fetch_passing, normalize_passing, "weekly_passing_stats"
            )

            # 2. Rushing
            process_category(
                season, week, "rushing", 
                fetch_rushing_week, normalize_rushing, "weekly_rushing_stats"
            )

            # 3. Receiving (NEW)
            process_category(
                season, week, "receiving", 
                fetch_receiving_week, normalize_receiving, "weekly_receiving_stats"
            )

            # 4. Update State
            update_state(season, week)

if __name__ == "__main__":
    # Run full refresh to get all data
    main(full_refresh=False)