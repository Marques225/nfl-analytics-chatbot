# backend/etl/fetch/pfr_rushing.py
import pandas as pd
from bs4 import BeautifulSoup, Comment
from .http import get
from .pfr_urls import base_url 

def get_rushing_url(season, week):
    return f"{base_url}/years/{season}/week_{week}.htm"

def fetch_rushing_week(season: int, week: int) -> pd.DataFrame:
    """
    Fetch weekly rushing stats.
    """
    url = get_rushing_url(season, week)
    html = get(url)
    soup = BeautifulSoup(html, "html.parser")

    # 1. FIND THE TABLE
    # FIX: We now know the correct ID is 'rush_stats'
    target_ids = ["rush_stats", "rushing", "rushing_and_receiving"]
    table_soup = None
    
    def find_table(s):
        for tid in target_ids:
            t = s.find("table", id=tid)
            if t: return t
        return None

    # Check Main DOM
    table_soup = find_table(soup)
    
    # Check Comments if not found (It was hidden in Comment #34!)
    if not table_soup:
        comments = soup.find_all(string=lambda t: isinstance(t, Comment))
        for c in comments:
            c_soup = BeautifulSoup(c, "html.parser")
            table_soup = find_table(c_soup)
            if table_soup: break

    if not table_soup:
        print(f"WARNING: No rushing table for {season} week {week}")
        return pd.DataFrame()

    # 2. PARSE ROWS
    rows = []
    tbody = table_soup.find("tbody")
    if not tbody:
        return pd.DataFrame()

    for tr in tbody.find_all("tr"):
        if "thead" in tr.get("class", []):
            continue

        row_data = {}
        for cell in tr.find_all(["th", "td"]):
            stat_name = cell.get("data-stat")
            if not stat_name: continue
            
            text_val = cell.get_text().strip()
            row_data[stat_name] = text_val

            # Extract PFR ID
            if stat_name == "player":
                pfr_id = cell.get("data-append-csv")
                if not pfr_id and cell.find("a"):
                    href = cell.find("a")["href"]
                    pfr_id = href.split("/")[-1].replace(".htm", "")
                row_data["pfr_player_id"] = pfr_id

        # 3. FILTER FOR RUSHERS
        # PFR Weekly 'rush_stats' table typically uses 'rush_att' for attempts.
        # We ensure the row actually has rushing data.
        if row_data.get("rush_att", "0") != "0":
            rows.append(row_data)

    df = pd.DataFrame(rows)
    if df.empty: return df

    df["season"] = season
    df["week"] = week
    
    return df