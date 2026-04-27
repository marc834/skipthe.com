# Website spec

The website is the primary product. RSS is a secondary surface for power users.

This doc is the spec for the browsable site. **Not yet implemented** — today `app/site/index.html` is a hand-written page linking to the RSS XMLs. The plan below replaces that.

## Principles

- **Statically generated.** The pipeline writes HTML files alongside the RSS XML. nginx serves them. No app server, no DB on the request path.
- **No JavaScript framework.** Plain HTML and minimal CSS. Page must be readable on a slow phone.
- **Mobile-first.** Most readers will arrive from a text message or shared link.
- **Click-through to source.** We never republish article bodies. Each item is a card with title, one-sentence AI summary, source name, credibility tag, and a link to the original.
- **AI disclaimer visible on every page.** Footer at minimum, ideally a small tag near the masthead too.

## URL structure (path-based, decided)

```
skipthe.com/                              top-level landing — list of neighborhoods
skipthe.com/nocatee/                      neighborhood home — latest items, all categories
skipthe.com/nocatee/crime-safety          category page
skipthe.com/nocatee/development
skipthe.com/nocatee/schools
skipthe.com/nocatee/business
skipthe.com/nocatee/events
skipthe.com/nocatee/community-chatter
skipthe.com/nocatee/politics
skipthe.com/nocatee/feeds                 RSS index (links to the XML files)

skipthe.com/about                         what this is, who runs it, AI disclaimer
skipthe.com/contact                       take-down + general inbound (form → m@skipthe.com)
skipthe.com/tip                           submit a tip (Nextdoor/Facebook signal we can't scrape)
skipthe.com/legal                         terms, privacy, attribution
```

nginx serves these from disk. `try_files $uri $uri/ $uri.html =404;` handles the trailing-slash and `.html`-optional cases.

## Page anatomy

### Item card

```
┌────────────────────────────────────────────────────────────┐
│ [development] [official]                                    │
│                                                             │
│ Headline pulled from the source                             │
│                                                             │
│ One neutral sentence written by the AI moderator describing │
│ what happened.                                              │
│                                                             │
│ Source: St. Johns County · 2 hours ago · Read original →   │
└────────────────────────────────────────────────────────────┘
```

The "Read original →" link is the primary action. Whole card can be the link target on mobile.

### Neighborhood landing (`/nocatee/`)

- Masthead: "Nocatee Signal · skipthe.com" + tagline
- Disclaimer banner: "This page is curated by an AI moderator. Mistakes happen — see the [contact page](#)."
- Latest 30 items, mixed categories, newest first
- Sidebar (or footer on mobile): category links, RSS links, donate link (when added)

### Category page (`/nocatee/crime-safety`)

Same as the landing page but filtered to one category. Top 50 items.

### About page

- What skipthe.com is
- Who runs it (named editorial owner — TBD)
- The AI moderation disclaimer in full
- How sources are chosen
- How to add a neighborhood (contact form)

### Contact page

A simple HTML form. Fields:

- Your name
- Your website (optional, used to verify identity for take-down requests)
- Your email (so we can reply)
- The URL of the item this is about (optional)
- Message

Form posts to a third-party form-to-email service that delivers to `m@skipthe.com`. Recommended providers (free tier, no backend needed):

- **Web3Forms** — free up to 250 submissions/month, no account required for the recipient
- **Formspree** — free up to 50/month
- **Formsubmit** — free, recipient-confirmed

Pick one when implementing. Keep the form action URL in `app/config/sources.yaml` or a small `app/config/site.yaml` so it's not buried in the template.

### Tip page

A second form, separate page (`/tip`), same Web3Forms credentials as `/contact` but a different `subject` so submissions are filterable in the inbox. Captures the high-value Nextdoor / Facebook / group-text signal we can't scrape. Fields:

- What happened (textarea, required)
- When (text, optional)
- Where (text, optional)
- Source URL (URL, optional — Nextdoor link, screenshot, etc.)
- Your name (optional)
- Your email (optional, for follow-up)

Linked from a `.notice` banner on every neighborhood page ("Saw something we missed? Submit a tip.") and from the footer.

Triage workflow today: tips email to `m@skipthe.com`, the operator manually decides whether to surface them, and inserts via SQL on the VM. A small CLI helper (`tools/insert_tip.py`) is on the roadmap to make that one-line.

## Templating

Add `jinja2` to `requirements.txt`. Templates live in `app/site/templates/`:

```
app/site/templates/
├── base.html            shared header/footer, disclaimer, nav
├── neighborhood.html    landing + category pages (same template, different filter)
├── landing.html         top-level / lists neighborhoods
├── about.html
├── contact.html
├── tip.html             user-submitted tip form
└── legal.html
```

Static pages (`about`, `contact`, `legal`) render once at deploy time. Dynamic pages (`neighborhood`, category pages) render every cron run.

## Generator module

Create `app/site/generate_site.py`. Called from `main.py` after `generate_feeds.generate()`.

Sketch:

```python
def generate(neighborhood_key: str):
    # 1. read items WHERE include=1 AND neighborhood=? ORDER BY created_at DESC
    # 2. render <neighborhood>/index.html with all items
    # 3. for each category: render <neighborhood>/<category>.html with filtered items
    # 4. render top-level index if not already (lists neighborhoods)
```

Static pages are not regenerated — they're checked in under `app/site/`.

## Caching

- nginx: `Cache-Control: public, max-age=300` on HTML and XML. Five minutes is enough; the pipeline runs every 30.
- No CDN needed at this scale. Add Cloudflare in front later if traffic justifies it.

## Open implementation questions

- Item permalinks on skipthe.com? **No** for v1 — every card links straight to the source. Adding our own permalinks would imply we're hosting content, which is a different legal posture.
- Search across past items? **No** for v1 — premature.
- Pagination? **No** for v1 — show top 50 per category, the rest stays in the DB.
- Images? **No** for v1 — text-only cards. Adds bandwidth, copyright questions, and complexity.