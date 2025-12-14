# etl/aggregate/player_weekly.py
from sqlalchemy import text

def aggregate_player_weekly(engine, season, week):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO player_weekly_stats (
                player_id, team_id, season, week,
                passing_yards, passing_tds, interceptions,
                total_touchdowns, total_yards
            )
            SELECT
                player_id,
                team_id,
                season,
                week,
                passing_yards,
                passing_tds,
                interceptions,
                passing_tds,
                passing_yards
            FROM weekly_passing_stats
            WHERE season=:season AND week=:week
            ON CONFLICT (player_id, season, week)
            DO UPDATE SET
                passing_yards = EXCLUDED.passing_yards,
                passing_tds = EXCLUDED.passing_tds;
        """), {"season": season, "week": week})
