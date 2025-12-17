import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

def check_data_quality():
    print("🔍 Running Data Quality Checks...")
    issues = []

    with engine.connect() as conn:
        # Check 1: Negative Yards (Anomaly Detection)
        result = conn.execute(text("SELECT COUNT(*) FROM season_rushing_stats WHERE rushing_yards < 0")).scalar()
        if result > 0:
            issues.append(f"⚠️ Found {result} players with negative rushing yards (Check for errors!)")

        # Check 2: Missing Names (Integrity Check)
        result = conn.execute(text("SELECT COUNT(*) FROM players WHERE name IS NULL")).scalar()
        if result > 0:
            issues.append(f"❌ Found {result} players with NULL names!")

        # Check 3: Zero Stats for Top Players (Stale Data Check)
        # Did we fail to load stats for active players?
        result = conn.execute(text("""
            SELECT COUNT(*) FROM season_passing_stats 
            WHERE passing_yards = 0 AND games_played > 5
        """)).scalar()
        if result > 0:
            issues.append(f"⚠️ Found {result} QBs with 0 yards despite playing 5+ games.")

    if issues:
        print("\n".join(issues))
        # In a real job, you would send a Slack/Email alert here
        exit(1) # Fail the pipeline so you notice
    else:
        print("✅ Data Quality Check Passed: Database is healthy.")
        exit(0)

if __name__ == "__main__":
    check_data_quality()