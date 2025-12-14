# backend/etl/fetch/pfr_weekly.py
import pandas as pd
from bs4 import BeautifulSoup, Comment
from .http import get
from .pfr_urls import weekly_passing_url

def fetch_week(season: int, week: int) -> pd.DataFrame:
    """
    Fetch weekly passing stats.
    Robustly extracts Player Name and PFR ID using data-stat attributes.
    """
    url = weekly_passing_url(season, week)
    html = get(url)
    soup = BeautifulSoup(html, "html.parser")

    # 1. FIND THE TABLE (qb_stats or passing)
    target_ids = ["qb_stats", "passing"]
    table_soup = None
    
    # Helper to find table in a soup
    def find_table(s):
        for tid in target_ids:
            t = s.find("table", id=tid)
            if t: return t
        return None

    # Check Main DOM
    table_soup = find_table(soup)
    
    # Check Comments if not found
    if not table_soup:
        comments = soup.find_all(string=lambda t: isinstance(t, Comment))
        for c in comments:
            c_soup = BeautifulSoup(c, "html.parser")
            table_soup = find_table(c_soup)
            if table_soup: break

    if not table_soup:
        print(f"WARNING: No passing table for {season} week {week}")
        return pd.DataFrame()

    # 2. PARSE ROWS USING 'data-stat'
    # This is safer than counting columns because PFR changes column order.
    rows = []
    tbody = table_soup.find("tbody")
    if not tbody:
        return pd.DataFrame()

    for tr in tbody.find_all("tr"):
        if "thead" in tr.get("class", []):
            continue

        row_data = {}
        
        # Iterate over ALL cells (th and td)
        for cell in tr.find_all(["th", "td"]):
            stat_name = cell.get("data-stat")
            if not stat_name:
                continue
            
            # Clean text
            text_val = cell.get_text().strip()
            row_data[stat_name] = text_val

            # SPECIAL EXTRACTION: Player ID
            if stat_name == "player":
                # Try data-append-csv
                pfr_id = cell.get("data-append-csv")
                # Fallback to href
                if not pfr_id and cell.find("a"):
                    href = cell.find("a")["href"]
                    pfr_id = href.split("/")[-1].replace(".htm", "")
                
                row_data["pfr_player_id"] = pfr_id

        if row_data:
            rows.append(row_data)

    df = pd.DataFrame(rows)
    
    if df.empty:
        return df

    # 3. NORMALIZE COLUMNS
    # Ensure we have the standard columns expected by the transformer
    df["season"] = season
    df["week"] = week
    
    return df