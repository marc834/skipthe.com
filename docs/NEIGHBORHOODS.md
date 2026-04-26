# Neighborhoods

A neighborhood is the unit of curation. One neighborhood = one set of keywords, one set of source feeds, one set of generated pages and RSS files.

The first (and currently only) neighborhood is **Nocatee, FL**. Architecture should support adding more without rewrites — but the immediate priority is making Nocatee good, not racing to neighborhood #2.

## URL scheme — decided

Path-based: `skipthe.com/nocatee/`, `skipthe.com/<other-neighborhood>/`. Not subdomains. One TLS cert, simpler nginx, easier analytics.

## What defines a neighborhood

In `app/config/sources.yaml`:

```yaml
neighborhoods:
  nocatee:
    display_name: "Nocatee, FL"
    keywords:
      - nocatee
      - ponte vedra
      - st. johns county
      - 32081
      - 32082
      - nocatee parkway
      - crosswater
      - town center
```

The `keywords` list does double duty:

1. **Prefilter** — items whose title + raw summary contain none of these keywords are dropped before the AI classifier sees them. Saves tokens.
2. **Anchor for the AI** — the keyword list is sent to the model as part of the neighborhood context, so it knows what "in scope" means.

## Choosing keywords

Aim for 8–15 terms covering:

- The neighborhood name and any common alternate spellings
- ZIP codes
- Major landmarks, subdivisions, or roads only locals would cite
- The parent city and county (so county-wide stories that mention the area still land)

Avoid:

- Single common English words (`park`, `school`) — they will match everything
- Person names — too noisy and they change over time

## Adding a new neighborhood

Today this is a config + sources + nginx exercise. There is no admin UI.

1. **Pick the keyword set** (see above).
2. **Add it to `sources.yaml`** under `neighborhoods:`.
3. **Add neighborhood-specific feeds** under `feeds:`. Some sources (county, school district) will be shared across neighborhoods in the same county; that's fine — the prefilter handles scoping.
4. **Lift the publisher hardcode**: `app/rss/generate_feeds.py` currently writes only to `data/feeds/nocatee/`. Change it to take the neighborhood key as an argument and iterate over `cfg["neighborhoods"]` from `main.py`. (Same change is needed in `app/site/generate_site.py` once it exists.)
5. **Run the pipeline** with `NEIGHBORHOOD=<key> python main.py` (or have `main.py` loop all neighborhoods) and verify XML lands in `data/feeds/<key>/` and HTML lands in `app/site/<key>/`.
6. **nginx already routes** by path — `try_files $uri $uri/ $uri.html =404;` will pick up the new directory automatically. Add a link to the new neighborhood from the top-level landing page.

## Top-level landing page

Once there's more than one neighborhood, `skipthe.com/` shows a list. For now it can redirect to `/nocatee/` (or be the same as `/nocatee/` until #2 ships).

## Expansion playbook

Order of operations when scaling beyond Nocatee:

1. **Multi-neighborhood publisher** — lift the hardcoded `nocatee` paths in `generate_feeds.py` and the (yet-to-build) `generate_site.py`.
2. **Per-neighborhood iteration** — `main.py` loops over `cfg["neighborhoods"]` instead of reading one from env.
3. **Source library** — as more neighborhoods come online, the same county / state sources will recur. Either tag sources with the neighborhoods they're relevant to, or just rely on keyword prefilter (cheaper, less DRY, fine at this scale).
4. **Onboarding** — a new neighborhood needs a real human to pick keywords and find the right 5–10 sources. This is the bottleneck, not the code.

## Long-term: many neighborhoods

If skipthe.com grows to dozens or hundreds of neighborhoods, two things change:

- **Source onboarding becomes the work**. Per-neighborhood research is irreducible — there's no way to auto-discover the right local government feeds.
- **Cost scales with item volume**. The AI classifier is the dominant cost. At 50 items × every 30 minutes × N neighborhoods, costs grow linearly. Cap and budget.

Don't pre-build for this. Build for Nocatee, ship Nocatee, then learn what neighborhood #2 actually requires.