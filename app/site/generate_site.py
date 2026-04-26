import os
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.db.database import get_conn

SITE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SITE_DIR / "templates"

CATEGORIES = [
    ("crime-safety", "Crime & Safety"),
    ("development", "Development"),
    ("schools", "Schools"),
    ("business", "Business"),
    ("events", "Events"),
    ("community-chatter", "Community Chatter"),
    ("politics", "Politics"),
    ("other", "Other"),
]


def time_ago(dt_str):
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return dt_str
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = datetime.now(timezone.utc) - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    if seconds < 604800:
        return f"{seconds // 86400}d ago"
    return dt.strftime("%b %d")


def _env():
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["time_ago"] = time_ago
    return env


def _load_items(neighborhood_key, category=None, limit=50):
    with get_conn() as conn:
        if category:
            rows = conn.execute(
                "SELECT * FROM items WHERE include=1 AND neighborhood=? AND category=? "
                "ORDER BY created_at DESC LIMIT ?",
                (neighborhood_key, category, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM items WHERE include=1 AND neighborhood=? "
                "ORDER BY created_at DESC LIMIT ?",
                (neighborhood_key, limit),
            ).fetchall()
    return [dict(r) for r in rows]


def _render_neighborhood(neighborhood_key, neighborhood_cfg, env):
    out_dir = SITE_DIR / neighborhood_key
    out_dir.mkdir(parents=True, exist_ok=True)
    template = env.get_template("neighborhood.html")

    landing_html = template.render(
        neighborhood_key=neighborhood_key,
        display_name=neighborhood_cfg["display_name"],
        active_category="all",
        category_label="Latest",
        categories=CATEGORIES,
        items=_load_items(neighborhood_key),
    )
    (out_dir / "index.html").write_text(landing_html, encoding="utf-8")

    for cat_key, cat_label in CATEGORIES:
        page_html = template.render(
            neighborhood_key=neighborhood_key,
            display_name=neighborhood_cfg["display_name"],
            active_category=cat_key,
            category_label=cat_label,
            categories=CATEGORIES,
            items=_load_items(neighborhood_key, category=cat_key),
        )
        (out_dir / f"{cat_key}.html").write_text(page_html, encoding="utf-8")


def _render_top_landing(cfg, env):
    template = env.get_template("landing.html")
    neighborhoods = [
        {"key": k, "display_name": v["display_name"]}
        for k, v in cfg["neighborhoods"].items()
    ]
    html = template.render(neighborhoods=neighborhoods)
    (SITE_DIR / "index.html").write_text(html, encoding="utf-8")


def _render_static_pages(env):
    contact_form_action = os.getenv("CONTACT_FORM_ACTION", "https://api.web3forms.com/submit").strip()
    contact_form_key = os.getenv("CONTACT_FORM_ACCESS_KEY", "").strip()
    contact_email = os.getenv("CONTACT_EMAIL", "m@skipthe.com").strip()

    context = {
        "contact_form_action": contact_form_action,
        "contact_form_key": contact_form_key,
        "contact_email": contact_email,
    }

    for name in ("about", "contact", "legal"):
        html = env.get_template(f"{name}.html").render(**context)
        (SITE_DIR / f"{name}.html").write_text(html, encoding="utf-8")


def generate(neighborhood_key, cfg):
    env = _env()
    nbhd = cfg["neighborhoods"][neighborhood_key]
    _render_neighborhood(neighborhood_key, nbhd, env)
    _render_top_landing(cfg, env)
    _render_static_pages(env)