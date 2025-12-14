# etl/fetch/pfr_season_passing.py
import pandas as pd
from bs4 import BeautifulSoup, Comment
from etl.http import get
from etl.pfr_urls import season_passing_url

def fetch_season_passing(season: int) -> pd.DataFrame:
    html = get(season_passing_url(season))
    soup = BeautifulSoup(html, "html.parser")

    comments = soup.find_all(string=lambda t: isinstance(t, Comment))

    for c in comments:
        table = BeautifulSoup(c, "html.parser").find("table", id="passing")
        if table:
            df = pd.read_html(str(table))[0]
            df["season"] = season
            return df

    raise ValueError(f"No season passing table for {season}")
