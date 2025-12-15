# backend/etl/fetch/pfr_urls.py

# 1. Define base_url so it can be imported by other files
base_url = "https://www.pro-football-reference.com"

def weekly_passing_url(season: int, week: int) -> str:
    """
    Returns the URL for the weekly stats page.
    Note: PFR puts all stats (passing, rushing, receiving) on the same page.
    """
    return f"{base_url}/years/{season}/week_{week}.htm"