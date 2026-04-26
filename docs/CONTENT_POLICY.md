# Content policy

This is the editorial contract — what we publish, what we don't, and how we present what we do.

The AI moderator enforces most of this. **There is no human review queue.** A visible disclaimer on every page and in every RSS description makes that clear to readers.

## The disclaimer

Every page footer (and every RSS feed `<description>`) carries:

> Curated by an AI moderator from public sources. Mistakes happen — links go straight to the original publisher. Concerns? [Contact us](https://skipthe.com/contact).

Wording can evolve, but the three load-bearing claims are: (1) it's AI-curated, (2) we link to the original, (3) there's a clear contact path.

## What's in

- Government and quasi-government announcements affecting the neighborhood
- Public-safety incidents reported by the sheriff, fire, or recognized local media
- Development and zoning activity (permits, hearings, road work, new construction)
- School district news that touches schools serving the neighborhood
- Local business openings, closings, and material changes
- Events open to the community
- Election news and ballot items affecting the area
- Community chatter from federated/public social channels — surfaced with the `unverified` tag

## What's out

- Ads, sponsored placements, classifieds
- Navigation links, "about us" pages, generic landing pages the scraper picked up
- Items that don't actually concern the neighborhood (national news that happens to mention the state, etc.)
- Personal attacks, doxxing, content targeting private individuals
- Real-estate listings (separate use case; not what we're building)
- Anything behind a paywall (we'd be republishing paid summaries)

## Allegations and unverified claims

- **Never present allegations as fact.** Suspect ≠ guilty. "Reports of" ≠ "happened."
- Items tagged `unverified` are still publishable, but the credibility label renders on the card and in the RSS description so readers see the weight.
- Names of suspects accused of non-violent crimes: prefer not to surface unless a charging decision has been made by an official source.
- Names of victims, minors, or witnesses: not surfaced.

## Attribution

Every item links back to its original source. We do not republish full article bodies. The card and the RSS `<description>` carry the AI's one-sentence neutral summary plus `Source: <name>. Credibility: <tier>.` so readers always know where to click through.

## Take-down requests

We don't publish a long take-down policy on the site — just a contact form that emails `m@skipthe.com`. The form fields:

- Name
- Website (optional, used for identity verification)
- Email (so we can reply)
- URL of the item in question
- Message

The form is a static HTML page wired to a third-party form-to-email provider (Web3Forms, Formspree, or similar — see [`WEBSITE.md`](WEBSITE.md)).

When a valid request arrives:

1. Mark the offending row `include = 0` in `data/items.sqlite3`.
2. Re-run the publisher to regenerate feeds and HTML pages without it.
3. Append a line to a tiny audit log (`data/removals.log`) — date, URL, requester, reason. Append-only.
4. Reply to the requester confirming the action.

Target turnaround: 48 hours.

## AI mistakes

The classifier will occasionally include junk or exclude something good. Mitigations, in order of cost:

1. Tighten the prompt (cheapest, fast feedback loop)
2. Tighten keyword prefilter
3. Drop noisy sources
4. Long-term: human review queue (deferred — see [`ROADMAP.md`](ROADMAP.md))

If a specific source consistently produces noise, drop it from `sources.yaml`. The bar is "does this regularly produce items worth publishing." Sources that don't clear it should go.