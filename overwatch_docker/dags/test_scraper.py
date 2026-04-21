# test_scraper.py
import requests
from bs4 import BeautifulSoup

url = "https://overwatch.blizzard.com/en-us/rates/"
params = {
    "input":  "PC",
    "region": "Americas",
    "rq":     "0",   # Quick Play
    "tier":   "All",
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

resp = requests.get(url, params=params, headers=headers, timeout=15)
soup = BeautifulSoup(resp.text, "html.parser")

for tag in soup.find_all(attrs={"slot": lambda v: v and v.startswith("cell-") and v.endswith("-winrate")}):
    slug = tag["slot"][5:-8]
    wr   = tag.get_text(strip=True)
    pr_tag = soup.find(attrs={"slot": f"cell-{slug}-pickrate"})
    pr   = pr_tag.get_text(strip=True) if pr_tag else "N/A"
    print(f"{slug:<20} win={wr:<8} pick={pr}")