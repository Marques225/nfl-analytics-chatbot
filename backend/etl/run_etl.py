# etl/run_etl.py

from etl.state import get_state, update_state
from etl.config import MIN_SEASON, CURRENT_SEASON, CURRENT_WEEK, engine
from etl.fetch.pfr_weekly import fetch_week
from etl.fetch.validators import validate_week

from etl.transform.passing import normalize_passing
from etl.load.passing import load_weekly_passing
# aggregation intentionally optional for now
# from etl.aggregate.player_weekly import aggregate_player_weekly


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

    for season in range(last_season, CURRENT_SEASON + 1):
        weeks = determine_weeks(season, last_season, last_week)

        for week in weeks:
            print(f"Fetching season {season}, week {week} ...")
            try:
                # 1️⃣ FETCH
                df = fetch_week(season, week)

                # 2️⃣ VALIDATE
                validate_week(df, season, week)

                # 3️⃣ RAW SNAPSHOT (unchanged)
                df.to_csv(
                    f"data/raw/{season}_week{week}_passing.csv",
                    index=False
                )

                # 4️⃣ TRANSFORM (NEW)
                df = normalize_passing(df, season=season, week=week)

                # 5️⃣ LOAD (NEW)
                load_weekly_passing(df, engine)

                # 6️⃣ STATE UPDATE
                update_state(season, week)

                # 7️⃣ (OPTIONAL, LATER)
                # aggregate_player_weekly(engine, season, week)

                print(f" ✅ Done: season {season}, week {week}")

            except Exception as e:
                print(f" ❌ Error fetching season {season}, week {week}: {e}")
                raise  # fail fast so state is not corrupted


if __name__ == "__main__":
    main(full_refresh=True)
