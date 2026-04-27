import requests

HEADERS = {
    "User-Agent": "SkipThe Hyperlocal News Aggregator/0.1 (+https://skipthe.com; contact: m@skipthe.com)"
}


def collect_reddit(source: dict):
    """Pull recent posts from a public subreddit via Reddit's JSON endpoint.

    `source["url"]` should be either:
      - https://www.reddit.com/r/<sub>/        (we'll append .json)
      - https://www.reddit.com/r/<sub>/.json   (already correct)
      - https://www.reddit.com/r/<sub>/new/    (we'll append .json)
    """
    url = source["url"].rstrip("/")
    if not url.endswith(".json"):
        url = url + "/.json"

    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    items = []
    for child in data.get("data", {}).get("children", [])[:25]:
        post = child.get("data", {})
        if post.get("stickied"):
            continue
        permalink = post.get("permalink") or ""
        items.append({
            "source_name": source["name"],
            "source_url": source["url"],
            "title": (post.get("title") or "")[:240],
            "url": "https://www.reddit.com" + permalink if permalink else post.get("url", ""),
            "raw_summary": (post.get("selftext") or "")[:600],
            "published_at": "",
            "credibility": source.get("credibility", "unverified"),
        })
    return [x for x in items if x.get("url") and x.get("title")]