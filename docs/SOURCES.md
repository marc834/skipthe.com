# Sources

All sources live in `app/config/sources.yaml`. Goal: pull from **every available hyperlocal channel**. The AI moderator is the quality filter, so the bar for *adding* a source is lower than the bar for *publishing* an item from it.

## Source types

### `rss`

Anything with a real RSS or Atom feed. Handled by `feedparser`. Cheap and reliable — prefer this whenever a source offers it.

```yaml
- name: "St. Johns County News"
  url: "https://example.com/feed.xml"
  type: "rss"
  credibility: "official"
```

### `webpage`

Generic HTML page. The collector pulls every `<a href>` with link text ≥ 12 characters and lets the AI moderator decide what's news. Crude on purpose — works for "list of recent stories" pages without bespoke parsing.

```yaml
- name: "St. Johns County News"
  url: "https://www.sjcfl.us/news/"
  type: "webpage"
  credibility: "official"
```

The webpage collector caps output at 30 items per run and dedupes by URL.

### `reddit`

Public-subreddit posts via Reddit's `/.json` endpoint. No auth required for reads. Requires a descriptive `User-Agent` (Reddit blocks generic ones). Implemented in `app/collectors/reddit_collector.py`.

```yaml
- name: "Reddit r/Nocatee"
  url: "https://www.reddit.com/r/Nocatee/"
  type: "reddit"
  credibility: "unverified"
```

The collector takes the top 25 posts, skips stickied (mod) posts, and uses the post's reddit permalink as the item URL.

### Future: per-channel collectors

These need their own modules in `app/collectors/` and a new `type:` value:

- **`mastodon` / `bluesky`** — public timelines via their respective APIs. Federated channels are the most scrape-friendly social option.
- **`nextdoor`** — no public API, login-walled. Hard to do well; skip until someone makes a real case.
- **`facebook` groups/pages** — Meta has aggressively closed scraping paths. Realistically out of reach without API access (which requires app review).
- **`youtube`** — channel RSS exists at `https://www.youtube.com/feeds/videos.xml?channel_id=…`. Use the `rss` collector — no new module needed.
- **`govdelivery` / civic mailing lists** — many county/city alerts are mailing-list only. A `mailbox` collector that reads an IMAP inbox is plausible.
- **`meetings`** — county/town meeting agendas (PDFs). A dedicated parser pays off only once a few sources need it.

When implementing one, add it to `app/collectors/`, register it in `main.py`'s dispatch (today: `if source.get("type") == "rss"` else webpage), and document the new `type:` value.

## Channels we want, in priority order

1. **Government** — county, city, sheriff, fire, schools, utilities, water management. Almost always RSS or a news page.
2. **Local media** — newspapers, broadcast TV/radio stations, established community blogs. Most have RSS.
3. **Public records** — court filings, permits, meeting agendas. Often parseable.
4. **YouTube** — local government channels, school board meetings, community channels. Use channel RSS.
5. **Federated social** — Mastodon and Bluesky public timelines for local accounts.
6. **Reddit** — relevant subreddits via JSON.
7. **Newsletters and mailing lists** — bring them into an inbox and let a `mailbox` collector scrape.
8. **Closed social (Nextdoor, Facebook groups)** — last priority. Hard to access, hostile ToS, lower verification quality.

The AI moderator handles the verification gradient — `unverified` items still publish but are visibly tagged.

## Credibility tiers

Pick one when adding a source. The AI may override per-item, but this sets the default.

| Tier | Use for |
|---|---|
| `official` | County, city, school district, sheriff, fire, official utility |
| `local-media` | Recognized local newspaper, broadcaster, or established blog |
| `public-record` | Court filings, permits, meeting agendas, ordinance trackers |
| `reported` | Secondhand sources, aggregators with editorial process |
| `unverified` | Social posts, forums, anonymous tips |

Items labeled `unverified` are still publishable, but the credibility tag is visible in the RSS description and on the website so readers can weight it.

## Adding a source

1. Find the page. Prefer the RSS feed if one exists (look for `/feed`, `/rss`, `/atom`, or the orange icon).
2. Open `app/config/sources.yaml`.
3. Append under `feeds:` with `name`, `url`, `type`, `credibility`.
4. Run `python main.py` once locally and check `data/items.sqlite3` to confirm items are landing and the AI is classifying them sensibly.

```bash
sqlite3 data/items.sqlite3 \
  "SELECT title, category, include, reason FROM items WHERE source_name='Your Source' ORDER BY created_at DESC LIMIT 20;"
```

## Vetting checklist

Before adding a source, sanity-check:

- [ ] Is it actually about this neighborhood, or close enough that the keyword prefilter will scope it?
- [ ] Does `robots.txt` allow scraping? (`curl https://site.example/robots.txt`)
- [ ] What's the update cadence? (Drives whether 30-minute polling is wasteful — daily sources can be polled hourly or less.)
- [ ] Does it deduplicate well by URL, or does it re-stamp the same story under new URLs?
- [ ] Is there a Terms of Service that explicitly forbids automated access?

The bar isn't "this source is perfect." The bar is "the AI moderator can extract signal from this source more often than not." Re-evaluate weekly: if a source produces zero `include=1` items in a week, drop it.

## When to write a custom collector

If a source needs JS rendering, login, or a non-trivial parser, **don't** add special cases to `webpage_collector.py`. Create a new module under `app/collectors/`, register it in `main.py`'s dispatch, and add a new `type:` value in `sources.yaml`.