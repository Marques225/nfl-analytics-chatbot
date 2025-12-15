from etl.fetch.http import get
from bs4 import BeautifulSoup, Comment

# We use Week 1 of 2024 as our test subject
url = "https://www.pro-football-reference.com/years/2024/week_1.htm"
print(f"🔍 X-Raying: {url} ...")

html = get(url)
soup = BeautifulSoup(html, "html.parser")

def scan_headers(soup, table_id, category_name):
    # 1. Find the table (checking main DOM and comments)
    table = soup.find("table", id=table_id)
    if not table:
        comments = soup.find_all(string=lambda t: isinstance(t, Comment))
        for c in comments:
            c_soup = BeautifulSoup(c, "html.parser")
            table = c_soup.find("table", id=table_id)
            if table: break
    
    if not table:
        print(f"\n❌ Could not find table '{table_id}' ({category_name})")
        return

    print(f"\n✅ FOUND {category_name.upper()} TABLE ('{table_id}')")
    print("-" * 50)
    print(f"{'Visible Header':<20} | {'Hidden data-stat Key (Use this!)'}")
    print("-" * 50)

    # 2. Extract Headers and Keys
    # We look at the <thead> section to see the mapping
    thead = table.find("thead")
    if thead:
        for row in thead.find_all("tr"):
            for cell in row.find_all(["th", "td"]):
                text = cell.get_text().strip()
                key = cell.get("data-stat", "NO_KEY")
                if key != "NO_KEY":
                    print(f"{text:<20} | {key}")

# Scan Rushing and Receiving
scan_headers(soup, "rush_stats", "Rushing")
scan_headers(soup, "rec_stats", "Receiving")