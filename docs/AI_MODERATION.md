# AI moderation

OpenAI is the gatekeeper between "we scraped a link" and "we publish it." Everything that ships to readers has been judged by the model.

## Why AI moderates

Hyperlocal sources mix real news (a school board vote, a road closure) with navigation links, ads, classifieds, and pages that have nothing to do with the neighborhood. Hand-tuned regex filters fall over fast. The model is cheap enough per-item that it's a reasonable replacement for a human triage pass.

The AI does **not** write articles. It decides include/exclude, picks a category, assigns a credibility label, and writes one neutral sentence of summary. The headline and link from the source are preserved.

## Model

- Default: `gpt-4o-mini` (configurable via `OPENAI_MODEL` env var).
- Temperature: `0.1` — we want consistent classification, not creativity.
- `response_format: {"type": "json_object"}` — we parse the response with `json.loads` and trust the schema.

## The prompt contract

System prompt (in `engine/app/ai/classifier.py`):

> You classify hyperlocal news items for a free neighborhood RSS feed.
> Return only valid JSON. Be conservative. Exclude ads, generic pages, navigation links, classifieds, low-information social posts, and anything not relevant to the neighborhood.
> Never present allegations as fact. Label unverified claims clearly.
> Categories: crime-safety, development, schools, business, events, community-chatter, politics, other.
> Credibility: official, local-media, public-record, reported, unverified.

The user message is a JSON blob with the neighborhood config (name, keywords) and the item being classified. The model returns JSON matching:

```json
{
  "include": true,
  "neighborhood": "nocatee",
  "category": "development",
  "credibility": "official",
  "summary": "One neutral sentence describing what happened.",
  "reason": "Brief reason for include/exclude."
}
```

## Categories

Defined in two places — keep them in sync:

- `classifier.py` SYSTEM prompt (the model's allowed values)
- `generate_feeds.py` `CATEGORIES` list (drives which XML files get written)

Current set: `crime-safety`, `development`, `schools`, `business`, `events`, `community-chatter`, `politics`, `other`. The publisher also generates an `all` feed that aggregates everything.

## Credibility labels

- `official` — government source (county, school district, sheriff)
- `local-media` — a recognized local outlet
- `public-record` — court filings, permits, meeting minutes
- `reported` — secondhand but plausible
- `unverified` — claim not yet corroborated; surfaced with the label visible in the RSS description

## Cost shape

- ~50 items per cron run (hard cap in `main.py`).
- Each call sends ~500–1500 tokens of input and gets ~150 tokens back.
- At `gpt-4o-mini` pricing this is fractions of a cent per run. A 30-minute cadence is well under $5/month per neighborhood at current volumes.

If cost becomes an issue, knobs to turn:
1. Tighten the keyword prefilter so fewer items reach the model.
2. Shrink the `LIMIT 50` cap.
3. Send the model a slimmer item payload (drop `raw_summary` if it's noisy).
4. Batch multiple items into a single call (changes the JSON contract — non-trivial).

## Tuning the prompt

- Edit `SYSTEM` in `classifier.py`.
- Test against a sample of past items by querying the SQLite DB and re-running classification by hand.
- The prompt's JSON schema is load-bearing: `generate_feeds.py` reads `include`, `category`, `summary`, `credibility` directly. Don't rename these fields without updating the publisher.
- "Be conservative" and the allegations clause are the editorial guardrails — keep them.

## Failure modes

- **Malformed JSON** — `json.loads` raises, `main.py` catches and logs. The item stays unclassified and will be retried next run.
- **OpenAI 429 / 5xx** — same path; the item stays unclassified.
- **Model says `include: true` for junk** — tighten the prompt or add a post-classification rule. There is no human review queue today (see [`ROADMAP.md`](ROADMAP.md)).