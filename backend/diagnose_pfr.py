# diagnose_pfr.py
import os
from bs4 import BeautifulSoup, Comment
import requests

# 1. CONSTANTS
URL = "https://www.pro-football-reference.com/years/2024/week_1.htm"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def diagnose():
    print(f"🕵️  Connecting to: {URL}")
    
    # 2. FETCH
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Network Error: {e}")
        return

    html = resp.text
    size_kb = len(html) / 1024
    print(f"✅ Downloaded {size_kb:.2f} KB of HTML")

    # 3. SAVE FOR HUMAN EYES (Crucial)
    with open("last_debug.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("📄 Saved HTML to 'last_debug.html'.")

    # 4. CHECK FOR BLOCKS
    if "429 Too Many Requests" in html or "spam" in html.lower():
        print("🚨 CRITICAL: You are likely rate-limited or blocked.")
        return

    # 5. SCAN FOR TABLES (Visible & Hidden)
    soup = BeautifulSoup(html, "html.parser")
    
    visible_tables = [t.get("id") for t in soup.find_all("table") if t.get("id")]
    print(f"👀 Visible Tables found: {visible_tables}")

    # Check Comments
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    print(f"🔍 Found {len(comments)} HTML comments to scan...")
    
    hidden_tables = []
    for c in comments:
        c_soup = BeautifulSoup(c, "html.parser")
        tables = c_soup.find_all("table")
        for t in tables:
            tid = t.get("id")
            if tid:
                hidden_tables.append(tid)

    print(f"👻 Hidden Tables found: {hidden_tables}")

    # 6. VERDICT
    if "passing" in visible_tables or "passing" in hidden_tables:
        print("✅ GOOD NEWS: The 'passing' table is there! The parser logic just needs a tweak.")
    else:
        print("❌ BAD NEWS: The 'passing' table is completely missing.")

if __name__ == "__main__":
    diagnose()