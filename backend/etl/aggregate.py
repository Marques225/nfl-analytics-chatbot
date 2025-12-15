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
        # 1. AGGREGATE PASSING
        # ---------------------------------------------------------
        print("   > Updating Passing Totals...")
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
                p.player_id,
                t.id,
                w.season,
                COUNT(DISTINCT w.week) as games_played,
                
                SUM(w.completions),
                SUM(w.attempts),
                ROUND(SUM(w.completions)::numeric / NULLIF(SUM(w.attempts), 0), 4),
                
                SUM(w.passing_yards),
                SUM(w.passing_tds),
                SUM(w.interceptions),
                
                SUM(w.sacks),
                SUM(w.sack_yards),
                
                ROUND(AVG(w.passer_rating)::numeric, 2),
                ROUND(AVG(w.qbr)::numeric, 2),
                
                MAX(w.longest_pass), -- Takes the longest pass of the season
                SUM(w.first_downs),
                SUM(w.fourth_qtr_comebacks),
                SUM(w.game_winning_drives)
                
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
        # 2. AGGREGATE RUSHING
        # ---------------------------------------------------------
        print("   > Updating Rushing Totals...")
        conn.execute(text("""
            INSERT INTO season_rushing_stats (
                player_id, team_id, season, games_played,
                carries, rushing_yards, rushing_tds,
                yards_per_carry, rushing_yards_per_game,
                longest_rush
            )
            SELECT
                p.player_id,
                t.id,
                w.season,
                COUNT(DISTINCT w.week),
                
                SUM(w.carries),
                SUM(w.rushing_yards),
                SUM(w.rushing_tds),
                
                ROUND(SUM(w.rushing_yards)::numeric / NULLIF(SUM(w.carries), 0), 2),
                ROUND(SUM(w.rushing_yards)::numeric / COUNT(DISTINCT w.week), 1),
                
                MAX(w.longest_rush) -- Will be NULL, but that's okay for now
                
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
        # 3. AGGREGATE RECEIVING
        # ---------------------------------------------------------
        print("   > Updating Receiving Totals...")
        conn.execute(text("""
            INSERT INTO season_receiving_stats (
                player_id, team_id, season, games_played,
                targets, receptions, receiving_yards, receiving_tds,
                yards_per_reception, receptions_per_game, receiving_yards_per_game,
                longest_reception
            )
            SELECT
                p.player_id,
                t.id,
                w.season,
                COUNT(DISTINCT w.week),
                
                SUM(w.targets), -- Will be NULL
                SUM(w.receptions),
                SUM(w.receiving_yards),
                SUM(w.receiving_tds),
                
                ROUND(SUM(w.receiving_yards)::numeric / NULLIF(SUM(w.receptions), 0), 2),
                ROUND(SUM(w.receptions)::numeric / COUNT(DISTINCT w.week), 1),
                ROUND(SUM(w.receiving_yards)::numeric / COUNT(DISTINCT w.week), 1),
                
                MAX(w.longest_reception) -- Will be NULL
                
            FROM weekly_receiving_stats w
            JOIN players p ON p.name = w.player_name
            JOIN teams t ON t.name = w.team
            GROUP BY p.player_id, t.id, w.season
            
            ON CONFLICT (player_id, season) DO UPDATE SET
                receptions = EXCLUDED.receptions,
                receiving_yards = EXCLUDED.receiving_yards,
                receiving_tds = EXCLUDED.receiving_tds;
        """))

    print("✅ Season Aggregation Complete!")

if __name__ == "__main__":
    run_aggregation()