from etl.fetch.http import get
from bs4 import BeautifulSoup, Comment

# URL for 2024 Week 1
url = "https://www.pro-football-reference.com/years/2024/week_1.htm"
print(f"🔍 Scanning: {url} ...")

html = get(url)
soup = BeautifulSoup(html, "html.parser")

def scan_tables(s, source_name):
    tables = s.find_all("table")
    if tables:
        print(f"\n--- Tables found in {source_name} ---")
        for t in tables:
            t_id = t.get("id", "NO_ID")
            # Print the first few headers to help identify it
            headers = [th.get_text().strip() for th in t.find_all("th", limit=5)]
            print(f"ID: '{t_id}' | Headers: {headers}")

# 1. Scan Main Page
scan_tables(soup, "MAIN HTML")

# 2. Scan Comments (Hidden Tables)
comments = soup.find_all(string=lambda t: isinstance(t, Comment))
for i, c in enumerate(comments):
    c_soup = BeautifulSoup(c, "html.parser")
    # Only print if it actually contains a table
    if c_soup.find("table"):
        scan_tables(c_soup, f"COMMENT #{i+1}")