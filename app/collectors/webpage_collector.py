import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

HEADERS = {"User-Agent": "SkipThe Local Signal Bot/0.1; contact: m@skipthe.com"}

# Article URLs have descriptive slugs (multiple hyphens) or date paths.
# Nav URLs are short and use single words (/news/, /about/, /departments/).
_DATE_IN_PATH = re.compile(r"/\d{4}/\d{1,2}/|/\d{4}-\d{1,2}-\d{1,2}")


def _looks_like_article_url(url: str, base_url: str) -> bool:
    parsed = urlparse(url)
    base = urlparse(base_url)
    if parsed.netloc and parsed.netloc != base.netloc:
        return False
    last_segment = parsed.path.strip("/").split("/")[-1] if parsed.path.strip("/") else ""
    if not last_segment:
        return False
    if last_segment.count("-") >= 3:
        return True
    if len(last_segment) >= 30:
        return True
    if _DATE_IN_PATH.search(parsed.path):
        return True
    return False


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
        if not _looks_like_article_url(url, source["url"]):
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
    seen, unique = set(), []
    for item in items:
        if item["url"] not in seen:
            unique.append(item)
            seen.add(item["url"])
    return unique[:30]
