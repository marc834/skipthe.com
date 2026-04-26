# Operations runbook

Day-to-day operation of the pipeline on the production VM.

## Where things are (production)

- App: `/var/www/skipthe/`
- venv: `/var/www/skipthe/.venv/`
- DB: `/var/www/skipthe/data/items.sqlite3`
- Generated feeds: `/var/www/skipthe/data/feeds/<neighborhood>/*.xml`
- Generated HTML: `/var/www/skipthe/app/site/<neighborhood>/*.html` (once site generator ships)
- Static pages (about, contact, legal): `/var/www/skipthe/app/site/*.html`
- Logs: `/var/log/skipthe/pipeline.log`
- Backups: `/var/backups/skipthe/`

## Health checks

```bash
# Did the last cron run succeed?
tail -n 100 /var/log/skipthe/pipeline.log

# When was the all-updates feed last regenerated?
stat -c '%y' /var/www/skipthe/data/feeds/nocatee/all.xml

# Are feeds being served?
curl -I https://skipthe.com/feeds/nocatee/all.xml

# Is the homepage being served?
curl -I https://skipthe.com/nocatee/
```

A healthy run logs lines like `Classified: <title> -> True / development` and ends with `RSS feeds generated.`

## Common failures

### `ModuleNotFoundError` after a deploy

Forgot to install new requirements after a pull.

```bash
cd /var/www/skipthe
.venv/bin/pip install -r requirements.txt
```

### `OPENAI_API_KEY` missing

`load_dotenv()` couldn't find `.env` (probably wrong CWD). Cron command must `cd` into the repo root first — check the crontab line.

### Collector failed for `<source>`

A source changed shape, returned 4xx/5xx, or rate-limited us. The pipeline logs `Collector failed for X: <error>` and continues with other sources. Dig in only if it persists across runs.

### AI classification failed for `<url>`

Usually a transient OpenAI 429/5xx, or malformed JSON from the model. The item stays in the DB with `ai_summary IS NULL` and gets retried next run. If a single URL keeps failing, inspect it:

```bash
sqlite3 /var/www/skipthe/data/items.sqlite3 \
  "SELECT title, raw_summary FROM items WHERE url='<url>';"
```

### Feeds aren't updating on the site

Pipeline succeeded but XML didn't change → check `include=1` row counts:

```bash
sqlite3 /var/www/skipthe/data/items.sqlite3 \
  "SELECT category, COUNT(*) FROM items WHERE include=1 GROUP BY category;"
```

If counts are zero or stale, the issue is upstream (no new items collected, or AI excluded everything).

If counts look right but the served XML is stale → nginx is serving from disk, no caching layer, so it's almost always a permissions issue. Check `ls -la data/feeds/nocatee/`.

## Manual operations

### Trigger a one-off run

```bash
cd /var/www/skipthe
.venv/bin/python main.py
```

### Re-classify a specific item

Clear its `ai_summary` and let the next cron run pick it up:

```bash
sqlite3 /var/www/skipthe/data/items.sqlite3 \
  "UPDATE items SET ai_summary=NULL WHERE url='<url>';"
```

### Hide an item from feeds (manual take-down)

```bash
sqlite3 /var/www/skipthe/data/items.sqlite3 \
  "UPDATE items SET include=0 WHERE url='<url>';"

# Append to the removal audit log
echo "$(date -Iseconds)|<url>|<requester>|<reason>" >> /var/www/skipthe/data/removals.log

# Regenerate feeds (and HTML, once that exists)
cd /var/www/skipthe && .venv/bin/python -c "from app.rss.generate_feeds import generate; generate()"
```

### Roll back to yesterday's DB

```bash
sudo systemctl stop cron   # avoid a run mid-restore
cp /var/backups/skipthe/items-$(date -d yesterday +%F).sqlite3 \
   /var/www/skipthe/data/items.sqlite3
sudo systemctl start cron
```

## Monitoring (current state)

Today: `tail` the log and trust cron. That's it.

Worth adding when there's bandwidth (see [`ROADMAP.md`](ROADMAP.md)):

- Email-on-failure for cron (`MAILTO=` in crontab if mail is configured, or pipe to a webhook)
- A `/health.json` static file the pipeline writes with last run time + counts, so an external uptime checker (UptimeRobot etc.) can alert on staleness
- OpenAI usage tracking — pull the dashboard once a week until automated