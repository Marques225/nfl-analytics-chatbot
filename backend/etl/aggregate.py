import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def run_aggregation():
    print("🔄 Aggregating Season Stats...")
    
    with engine.begin() as conn:
        # ---------------------------------------------------------
        # 1. AGGREGATE PASSING (Player)
        # ---------------------------------------------------------
        print("   > Updating Player Passing Totals...")
        conn.execute(text("""
            INSERT INTO season_passing_stats (
                player_id, team_id, season, games_played,
                completions, attempts, completion_pct,
                passing_yards, passing_tds, interceptions,
                sacks, sack_yards,
                passer_rating, qbr,
                longest_pass, first_downs,
                fourth_qtr_comebacks, game_winning_drives
            )
            SELECT
                p.player_id, t.id, w.season, COUNT(DISTINCT w.week),
                SUM(w.completions), SUM(w.attempts),
                ROUND(SUM(w.completions)::numeric / NULLIF(SUM(w.attempts), 0), 4),
                SUM(w.passing_yards), SUM(w.passing_tds), SUM(w.interceptions),
                SUM(w.sacks), SUM(w.sack_yards),
                ROUND(AVG(w.passer_rating)::numeric, 2), ROUND(AVG(w.qbr)::numeric, 2),
                MAX(w.longest_pass), SUM(w.first_downs),
                SUM(w.fourth_qtr_comebacks), SUM(w.game_winning_drives)
            FROM weekly_passing_stats w
            JOIN players p ON p.name = w.player_name
            JOIN teams t ON t.name = w.team
            GROUP BY p.player_id, t.id, w.season
            ON CONFLICT (player_id, season) DO UPDATE SET
                games_played = EXCLUDED.games_played,
                passing_yards = EXCLUDED.passing_yards,
                passing_tds = EXCLUDED.passing_tds,
                interceptions = EXCLUDED.interceptions,
                passer_rating = EXCLUDED.passer_rating,
                qbr = EXCLUDED.qbr;
        """))

        # ---------------------------------------------------------
        # 2. AGGREGATE RUSHING (Player)
        # ---------------------------------------------------------
        print("   > Updating Player Rushing Totals...")
        conn.execute(text("""
            INSERT INTO season_rushing_stats (
                player_id, team_id, season, games_played,
                carries, rushing_yards, rushing_tds,
                yards_per_carry, rushing_yards_per_game, longest_rush
            )
            SELECT
                p.player_id, t.id, w.season, COUNT(DISTINCT w.week),
                SUM(w.carries), SUM(w.rushing_yards), SUM(w.rushing_tds),
                ROUND(SUM(w.rushing_yards)::numeric / NULLIF(SUM(w.carries), 0), 2),
                ROUND(SUM(w.rushing_yards)::numeric / COUNT(DISTINCT w.week), 1),
                MAX(w.longest_rush)
            FROM weekly_rushing_stats w
            JOIN players p ON p.name = w.player_name
            JOIN teams t ON t.name = w.team
            GROUP BY p.player_id, t.id, w.season
            ON CONFLICT (player_id, season) DO UPDATE SET
                carries = EXCLUDED.carries,
                rushing_yards = EXCLUDED.rushing_yards,
                rushing_tds = EXCLUDED.rushing_tds;
        """))

        # ---------------------------------------------------------
        # 3. AGGREGATE RECEIVING (Player)
        # ---------------------------------------------------------
        print("   > Updating Player Receiving Totals...")
        conn.execute(text("""
            INSERT INTO season_receiving_stats (
                player_id, team_id, season, games_played,
                targets, receptions, receiving_yards, receiving_tds,
                yards_per_reception, receptions_per_game, receiving_yards_per_game,
                longest_reception
            )
            SELECT
                p.player_id, t.id, w.season, COUNT(DISTINCT w.week),
                SUM(w.targets), SUM(w.receptions), SUM(w.receiving_yards), SUM(w.receiving_tds),
                ROUND(SUM(w.receiving_yards)::numeric / NULLIF(SUM(w.receptions), 0), 2),
                ROUND(SUM(w.receptions)::numeric / COUNT(DISTINCT w.week), 1),
                ROUND(SUM(w.receiving_yards)::numeric / COUNT(DISTINCT w.week), 1),
                MAX(w.longest_reception)
            FROM weekly_receiving_stats w
            JOIN players p ON p.name = w.player_name
            JOIN teams t ON t.name = w.team
            GROUP BY p.player_id, t.id, w.season
            ON CONFLICT (player_id, season) DO UPDATE SET
                receptions = EXCLUDED.receptions,
                receiving_yards = EXCLUDED.receiving_yards,
                receiving_tds = EXCLUDED.receiving_tds;
        """))

        # ---------------------------------------------------------
        # 4. AGGREGATE TEAM STATS (Offense & Defense) - NEW!
        # ---------------------------------------------------------
        print("   > Updating Team Offense & Defense Totals...")
        
        # We use a CTE (Common Table Expression) to calculate Offense and Defense separately
        # then join them together to insert into the main table.
        conn.execute(text("""
            INSERT INTO season_team_stats (
                team_id, season, 
                off_games_played, off_passing_yards, off_rushing_yards, off_total_yards, 
                off_passing_tds, off_rushing_tds, off_interceptions_thrown,
                def_passing_yards_allowed, def_rushing_yards_allowed, def_total_yards_allowed,
                def_passing_tds_allowed, def_rushing_tds_allowed, def_sacks_made
            )
            WITH team_offense AS (
                -- Sum up stats for the team's OWN players
                SELECT 
                    t.id as team_id, w.season,
                    COUNT(DISTINCT w.week) as games,
                    SUM(w.passing_yards) as pass_yds,
                    SUM(w.passing_tds) as pass_tds,
                    SUM(w.interceptions) as ints,
                    SUM(w.sacks) as sacks_allowed -- Sacks allowed BY offense
                FROM weekly_passing_stats w
                JOIN teams t ON t.name = w.team
                GROUP BY t.id, w.season
            ),
            team_rushing_offense AS (
                 SELECT 
                    t.id as team_id, w.season,
                    SUM(w.rushing_yards) as rush_yds,
                    SUM(w.rushing_tds) as rush_tds
                FROM weekly_rushing_stats w
                JOIN teams t ON t.name = w.team
                GROUP BY t.id, w.season
            ),
            team_defense_pass AS (
                -- Sum up stats where this team was the OPPONENT
                SELECT 
                    t.id as team_id, w.season,
                    SUM(w.passing_yards) as pass_yds_allowed,
                    SUM(w.passing_tds) as pass_tds_allowed,
                    SUM(w.sacks) as sacks_made -- Sacks made BY defense
                FROM weekly_passing_stats w
                JOIN teams t ON t.name = w.opponent -- JOIN ON OPPONENT
                GROUP BY t.id, w.season
            ),
            team_defense_rush AS (
                SELECT 
                    t.id as team_id, w.season,
                    SUM(w.rushing_yards) as rush_yds_allowed,
                    SUM(w.rushing_tds) as rush_tds_allowed
                FROM weekly_rushing_stats w
                JOIN teams t ON t.name = w.opponent -- JOIN ON OPPONENT
                GROUP BY t.id, w.season
            )
            SELECT 
                o.team_id, o.season,
                o.games,
                o.pass_yds,
                ro.rush_yds,
                (COALESCE(o.pass_yds,0) + COALESCE(ro.rush_yds,0)) as total_yards,
                o.pass_tds,
                ro.rush_tds,
                o.ints,
                
                dp.pass_yds_allowed,
                dr.rush_yds_allowed,
                (COALESCE(dp.pass_yds_allowed,0) + COALESCE(dr.rush_yds_allowed,0)) as total_allowed,
                dp.pass_tds_allowed,
                dr.rush_tds_allowed,
                dp.sacks_made
                
            FROM team_offense o
            LEFT JOIN team_rushing_offense ro ON o.team_id = ro.team_id AND o.season = ro.season
            LEFT JOIN team_defense_pass dp ON o.team_id = dp.team_id AND o.season = dp.season
            LEFT JOIN team_defense_rush dr ON o.team_id = dr.team_id AND o.season = dr.season
            
            ON CONFLICT (team_id, season) DO UPDATE SET
                off_total_yards = EXCLUDED.off_total_yards,
                off_passing_yards = EXCLUDED.off_passing_yards,
                off_rushing_yards = EXCLUDED.off_rushing_yards,
                def_total_yards_allowed = EXCLUDED.def_total_yards_allowed,
                def_sacks_made = EXCLUDED.def_sacks_made;
        """))

    print("✅ Season Aggregation Complete!")

if __name__ == "__main__":
    run_aggregation()