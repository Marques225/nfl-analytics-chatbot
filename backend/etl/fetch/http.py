import time
import requests

HEADERS = {
    "User-Agent": "NFL Analytics Research Bot (educational, non-commercial)"
}

REQUEST_DELAY = 3  # seconds (PFR-safe)

def get(url: str) -> str:
    time.sleep(REQUEST_DELAY)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text
