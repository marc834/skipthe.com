import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {"User-Agent": "SkipThe Local Signal Bot/0.1; contact: admin@skipthe.com"}

def collect_webpage(source: dict):
    resp = requests.get(source["url"], headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    items = []
    for a in soup.find_all("a", href=True):
        title = " ".join(a.get_text(" ").split())
        if len(title) < 12:
            continue
        url = urljoin(source["url"], a["href"])
        if url == source["url"]:
            continue
        items.append({
            "source_name": source["name"],
            "source_url": source["url"],
            "title": title[:180],
            "url": url,
            "raw_summary": "",
            "published_at": "",
            "credibility": source.get("credibility", "reported"),
        })
    # basic de-dupe by URL
    seen, unique = set(), []
    for item in items:
        if item["url"] not in seen:
            unique.append(item)
            seen.add(item["url"])
    return unique[:30]
