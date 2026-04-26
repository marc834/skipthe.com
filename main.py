import os
import yaml
from dotenv import load_dotenv
from app.collectors.rss_collector import collect_rss
from app.collectors.webpage_collector import collect_webpage
from app.db.database import get_conn, upsert_item, update_ai_result
from app.ai.classifier import classify_item
from app.rss import generate_feeds
from app.site import generate_site

load_dotenv()

CONFIG_PATH = "app/config/sources.yaml"

def basic_keyword_prefilter(item, neighborhood):
    text = f"{item.get('title','')} {item.get('raw_summary','')}".lower()
    return any(k.lower() in text for k in neighborhood.get("keywords", []))

def run():
    cfg = yaml.safe_load(open(CONFIG_PATH, "r", encoding="utf-8"))
    neighborhood_key = os.getenv("NEIGHBORHOOD", "nocatee")
    neighborhood = cfg["neighborhoods"][neighborhood_key]

    collected = []
    for source in cfg["feeds"]:
        try:
            if source.get("type") == "rss":
                collected.extend(collect_rss(source))
            else:
                collected.extend(collect_webpage(source))
        except Exception as e:
            print(f"Collector failed for {source['name']}: {e}")

    for item in collected:
        if not basic_keyword_prefilter(item, neighborhood):
            continue
        item["neighborhood"] = neighborhood_key
        upsert_item(item)

    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM items WHERE ai_summary IS NULL LIMIT 50").fetchall()

    for row in rows:
        item = dict(row)
        try:
            result = classify_item(item, neighborhood)
            update_ai_result(item["url"], result)
            print(f"Classified: {item['title']} -> {result.get('include')} / {result.get('category')}")
        except Exception as e:
            print(f"AI classification failed for {item['url']}: {e}")

    generate_feeds.generate()
    generate_site.generate(neighborhood_key, cfg)
    print("Site and RSS feeds generated.")

if __name__ == "__main__":
    run()