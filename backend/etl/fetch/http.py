# backend/etl/fetch/http.py
import requests
import time
import random

# 1. Define "Disguise" Headers
# This tells the website: "I am a Windows 10 PC using Chrome, not a python script."
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# 2. Add delays to be polite
REQUEST_DELAY = 4  # Seconds to wait between requests (PFR asks for at least 3s)

def get(url: str) -> str:
    """
    Fetches the HTML content of a URL with a browser-like User-Agent.
    """
    print(f"    ☁️ Fetching: {url} ...")
    time.sleep(REQUEST_DELAY + random.random()) # Sleep 4-5 seconds
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status() # Raise error if 403 (Forbidden) or 404
        return response.text
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            print("    ⏳ Rate limited! Waiting 30 seconds...")
            time.sleep(30)
            return get(url) # Retry once
        else:
            raise e