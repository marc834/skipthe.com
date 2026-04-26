import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "items.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT,
    source_url TEXT,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    raw_summary TEXT,
    ai_summary TEXT,
    neighborhood TEXT,
    category TEXT,
    credibility TEXT,
    include INTEGER DEFAULT 0,
    reason TEXT,
    published_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn

def upsert_item(item: dict):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO items
            (source_name, source_url, title, url, raw_summary, neighborhood, category, credibility, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("source_name"), item.get("source_url"), item["title"], item["url"],
                item.get("raw_summary"), item.get("neighborhood"), item.get("category"),
                item.get("credibility"), item.get("published_at")
            )
        )

def update_ai_result(url: str, result: dict):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE items SET ai_summary=?, neighborhood=?, category=?, credibility=?, include=?, reason=?
            WHERE url=?
            """,
            (
                result.get("summary"), result.get("neighborhood"), result.get("category"),
                result.get("credibility"), 1 if result.get("include") else 0,
                result.get("reason"), url
            )
        )
