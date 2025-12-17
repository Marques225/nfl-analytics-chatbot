import os
from datetime import datetime
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)

# ---------------------------------------------------------
# DYNAMIC SEASON & WEEK CALCULATOR (2025 COMPATIBLE)
# ---------------------------------------------------------
def get_nfl_season_and_week():
    today = datetime.now()
    
    # 1. Determine Current Season Year
    # If we are in Jan/Feb 2026, it's still the 2025 season.
    # If we are in Sept-Dec 2025, it's the 2025 season.
    if today.month < 3: # Jan or Feb
        current_season = today.year - 1
    else:
        current_season = today.year

    # 2. Define Start Date for THIS Season (First Thursday of Sept)
    # Simple logic: Start roughly Sept 5th.
    season_start = datetime(current_season, 9, 5) 
    
    # 3. Calculate Week
    delta = today - season_start
    if delta.days < 0:
        return current_season, 1 # Pre-season
        
    week_num = int(delta.days // 7) + 1
    
    # Cap at Week 18 for Regular Season
    current_week = min(week_num, 18)
    
    return current_season, current_week

# Dynamic Constants
CURRENT_SEASON, CURRENT_WEEK = get_nfl_season_and_week()
MIN_SEASON = 2024 

print(f"⚙️ Config Loaded: Season {CURRENT_SEASON}, Week {CURRENT_WEEK}")