# Roadmap

Phased plan and the open product questions that shape it. Phases are loose — what matters is the order.

## Decisions locked in

These were open questions; they're settled now and shape the rest of the plan.

- **Primary product is the website** (HTML pages), with RSS as a secondary surface.
- **Path-based URLs**: `skipthe.com/nocatee/`, never subdomains.
- **Start with Nocatee, expand later** — broader ambition, deliberate single-neighborhood start.
- **All available hyperlocal sources** are in scope, including federated social, Reddit, mailing lists. ToS-hostile closed networks (Nextdoor, Facebook groups) deferred.
- **Fully AI-moderated** with a visible disclaimer on every page. No human review queue.
- **Free for users.** Donations next, ads only as last resort if traffic gets large.
- **Take-down via contact form** that emails `m@skipthe.com`. No long policy on the site.
- **Repo layout flattened** — engine code lives at repo root, not in a subfolder.

## Phase 0 — MVP (current)

Status: ✅ pipeline works end-to-end for one neighborhood.

- Collect → prefilter → classify → publish RSS
- One static homepage linking to the per-category XMLs
- Manual deploy, manual cron, manual everything

## Phase 1 — Stabilize Nocatee + ship the website

The core deliverable. The goal: *one neighborhood that's actually good, with a real browsable site*.

- [ ] Deploy to the GCP VM, get the cron running, watch it for a week
- [ ] **Build the browsable site generator** ([`WEBSITE.md`](WEBSITE.md))
  - [ ] Add `jinja2` to requirements
  - [ ] `app/site/templates/` with `base.html`, `neighborhood.html`, `about.html`, `contact.html`, `legal.html`
  - [ ] `app/site/generate_site.py`, called from `main.py`
  - [ ] Replace the existing `app/site/index.html` with generated output
  - [ ] AI disclaimer visible in footer + masthead
- [ ] Pick and wire the contact form provider (Web3Forms / Formspree / Formsubmit) → `m@skipthe.com`
- [ ] Write the static `about.html` and `legal.html` content
- [ ] Prune sources that produce noise; add sources that produce signal
- [ ] Tune the keyword list against a week of real items
- [ ] Tune the AI prompt against false positives / false negatives
- [ ] Add a `/health.json` for an external uptime checker
- [ ] Decide: does anyone actually subscribe to / read the feeds and visit the site? If not, *fix the product*, don't add features.

## Phase 2 — Expand sources

- [x] Reddit collector (JSON API, public subreddits) — shipped, see `app/collectors/reddit_collector.py`
- [x] **User-submitted tips form** — shipped at `/tip`. Submissions email to `m@skipthe.com` via the same Web3Forms key as the contact form (different `subject` to filter in the inbox). Triage is manual today; a CLI helper to insert approved tips into the items DB is in tech debt below.
- [ ] Mastodon / Bluesky collector for federated public timelines
- [ ] Mailbox collector for civic alert mailing lists (IMAP) — Code Red, Nixle, county alerts
- [ ] YouTube channel feeds via the existing `rss` collector (no new code, just `sources.yaml` entries with `https://www.youtube.com/feeds/videos.xml?channel_id=<ID>`)
- [ ] Per-source quality review at one-month mark — drop sources with no `include=1` items in 30 days

### Why we won't build automated Facebook / Nextdoor scraping

Even with a willing volunteer's account: ToS violation, account-ban risk (which kills the volunteer's personal account too), credential-storage liability, and privacy violation against original posters whose content was shared with a smaller audience. The user-submitted tips form above is the right architecture for this signal.

## Phase 3 — Multi-neighborhood

Only after Phase 1 is paying off and Phase 2 has filled out Nocatee well.

- [ ] Lift the hardcoded `nocatee` path in `generate_feeds.py` (and `generate_site.py`)
- [ ] `main.py` iterates all neighborhoods in `sources.yaml`
- [ ] Top-level `skipthe.com/` becomes a real landing page listing neighborhoods
- [ ] Onboarding doc: "how to launch neighborhood N" — keyword research, source list, sanity checks

## Phase 4 — Distribution beyond the website

- [ ] Email digest (daily or weekly), one neighborhood per subscriber. Provider TBD (Buttondown, Listmonk self-hosted, AWS SES).
- [ ] Optional: post to a Mastodon / Bluesky account per neighborhood for items above a freshness/credibility bar.

## Phase 5 — Sustainability

Free for users; covering server + OpenAI costs.

- [ ] Add a donate link in the site footer once there's something worth donating to
  - Buy Me a Coffee / Ko-fi (simplest, no Stripe account needed)
  - Open Collective (transparent, fiscal-host option)
  - Stripe Payment Link / GitHub Sponsors if comfortable with Stripe/GH
- [ ] Optional later: local sponsorship slots (one named local business per neighborhood, hand-curated, never programmatic ads)
- [ ] Track running cost per neighborhood per month; aim to cover with donations + sponsorships before considering ads

## Phase 6 — Editorial review (if needed)

Only if AI-only moderation proves insufficient.

- [ ] Pending queue: classifier marks items `include=NULL` (not 0/1) and a human approves into `include=1`
- [ ] Minimal review UI (basic auth, list of pending items, approve/reject)
- [ ] Audit log of editorial decisions

## Open questions remaining

Most big questions are settled. These are still live:

- **Templating**: Jinja2 (recommended) or plain f-strings? Jinja2 adds one dependency but makes the contact / about / legal pages much easier to maintain.
- **Contact form provider**: Web3Forms (250/mo free), Formspree (50/mo free), or Formsubmit (free, recipient-confirmed). Pick one when implementing the contact page.
- **Donate link mechanism**: pick when there's a real reason to ask for money. Not before.
- **Named editorial owner per neighborhood**: who's the human to escalate to? For Nocatee it's presumably you — the about page should say so.
- **Item images**: deliberately out of scope for v1. Revisit if it becomes a real readership ask.

## Tech debt to track

- `CATEGORIES` is duplicated in `app/ai/classifier.py` and `app/rss/generate_feeds.py` — single source of truth would be cleaner. Likely belongs in `app/config/`.
- `OUT_DIR` in `generate_feeds.py` is hardcoded to `nocatee` — blocks Phase 3.
- `webpage_collector.py` harvests every link ≥ 12 chars; a smarter heuristic would cut classifier load.
- `main.py`'s `LIMIT 50` per run is a fixed cap — fine now, will need to scale (or batch into the classifier) once there are multiple neighborhoods.
- `tools/insert_tip.py` — small CLI to insert approved tip submissions into `items` as `unverified` rows so they flow through the same publish pipeline. Today operators do this via raw SQL.