from sqlalchemy import text
from etl.config import engine

def get_state(source="pfr", full_refresh=False):
    """
    Returns the last processed season and week.
    If full_refresh=True, returns the earliest season/week in the database
    so that the ETL will fetch all past weeks.
    """
    with engine.begin() as conn:
        if full_refresh:
            # Earliest season we care about
            row = conn.execute(
                text("SELECT MIN(last_season) AS last_season, 0 AS last_week FROM etl_state WHERE source=:s"),
                {"s": source}
            ).fetchone()
        else:
            row = conn.execute(
                text("SELECT last_season, last_week FROM etl_state WHERE source=:s"),
                {"s": source}
            ).fetchone()

    if not row:
        raise RuntimeError("ETL state missing")

    return row.last_season, row.last_week


def update_state(season, week, source="pfr"):
    """
    Updates the ETL state table after a week has been fetched/processed.
    Prints output so you know ETL is progressing.
    """
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE etl_state
                SET last_season=:season,
                    last_week=:week,
                    updated_at=now()
                WHERE source=:s
            """),
            {"season": season, "week": week, "s": source}
        )
    print(f"ETL state updated: season {season}, week {week}")
