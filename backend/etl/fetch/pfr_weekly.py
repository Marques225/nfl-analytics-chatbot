import pandas as pd
from bs4 import BeautifulSoup, Comment
from .http import get
from .pfr_urls import weekly_passing_url


def fetch_week(season: int, week: int) -> pd.DataFrame:
    """
    Fetch weekly passing stats from Pro-Football-Reference.
    Returns a DataFrame with season and week columns added.
    """

    # Fetch HTML
    html = get(weekly_passing_url(season, week))

    # TEMP DEBUG: save HTML locally for inspection
    with open(f"debug_week_{season}_week{week}.html", "w", encoding="utf-8") as f:
        f.write(html)

    soup = BeautifulSoup(html, "html.parser")

    # PFR hides tables inside HTML comments
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))

    # Try multiple possible table IDs
    table_ids = ["passing", "qb_stats", "player_stats"]  # add more if needed
    passing_table = None

    for comment in comments:
        comment_soup = BeautifulSoup(comment, "html.parser")
        for tid in table_ids:
            table = comment_soup.find("table", {"id": tid})
            if table is not None:
                passing_table = table
                break
        if passing_table:
            break

    if passing_table is None:
        # Option 1: log missing table and continue (ETL continues)
        print(f"WARNING: No passing table for {season} week {week}. HTML saved to debug_week_{season}_week{week}.html")
        return pd.DataFrame()  # empty DF to avoid stopping ETL

        # Option 2: strict mode — raise error instead
        # raise ValueError(f"No passing table for {season} week {week}")

    # Convert table to DataFrame
    df = pd.read_html(str(passing_table))[0]

    # Clean column names
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    # Add season and week columns
    df["season"] = season
    df["week"] = week

    return df
