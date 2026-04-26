import html
import os
from datetime import datetime, timezone
from pathlib import Path
from app.db.database import get_conn

BASE_URL = os.getenv("SITE_BASE_URL", "https://skipthe.com").rstrip("/")
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "feeds" / "nocatee"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = ["all", "crime-safety", "development", "schools", "business", "events", "community-chatter", "politics"]

def rss_item(row):
    title = html.escape(row["title"] or "Local update")
    link = html.escape(row["url"])
    desc = html.escape(row["ai_summary"] or row["raw_summary"] or "")
    source = html.escape(row["source_name"] or "")
    pub = row["published_at"] or datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    return f"""
    <item>
      <title>{title}</title>
      <link>{link}</link>
      <guid>{link}</guid>
      <description>{desc} Source: {source}. Credibility: {html.escape(row['credibility'] or '')}.</description>
      <pubDate>{html.escape(pub)}</pubDate>
    </item>"""

def generate():
    with get_conn() as conn:
        for category in CATEGORIES:
            if category == "all":
                rows = conn.execute("SELECT * FROM items WHERE include=1 ORDER BY created_at DESC LIMIT 100").fetchall()
            else:
                rows = conn.execute("SELECT * FROM items WHERE include=1 AND category=? ORDER BY created_at DESC LIMIT 100", (category,)).fetchall()
            title = f"SkipThe Nocatee - {category}"
            items_xml = "\n".join(rss_item(r) for r in rows)
            xml = f'''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>{html.escape(title)}</title>
    <link>{BASE_URL}/nocatee/</link>
    <description>Useful hyperlocal updates for Nocatee, FL. No noise.</description>
    <lastBuildDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")}</lastBuildDate>
    {items_xml}
  </channel>
</rss>'''
            (OUT_DIR / f"{category}.xml").write_text(xml, encoding="utf-8")
