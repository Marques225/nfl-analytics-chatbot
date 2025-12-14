# etl/fetch/pfr_weekly_passing.py
from bs4 import BeautifulSoup, Comment
import pandas as pd
from etl.http import get
from etl.pfr_urls import weekly_passing_url

def fetch_weekly_passing(season: int, week: int) -> pd.DataFrame:
    html = get(weekly_passing_url(season, week))
    soup = BeautifulSoup(html, "html.parser")

    comments = soup.find_all(string=lambda t: isinstance(t, Comment))

    for c in comments:
        table = BeautifulSoup(c, "html.parser").find("table", id="passing")
        if table:
            df = pd.read_html(str(table))[0]
            df["season"] = season
            df["week"] = week
            return df

    raise ValueError(f"No passing table for {season} week {week}")
