import feedparser

def collect_rss(source: dict):
    feed = feedparser.parse(source["url"])
    items = []
    for entry in feed.entries[:25]:
        items.append({
            "source_name": source["name"],
            "source_url": source["url"],
            "title": entry.get("title", "Untitled"),
            "url": entry.get("link"),
            "raw_summary": entry.get("summary", ""),
            "published_at": entry.get("published", ""),
            "credibility": source.get("credibility", "reported"),
        })
    return [x for x in items if x.get("url")]
