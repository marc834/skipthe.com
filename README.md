# skipthe.com

Hyperlocal news, with the noise stripped out.

skipthe.com collects updates from every available hyperlocal source — official sites, local media, public records, community forums — runs each item through an AI moderator (OpenAI), and publishes the survivors as a browsable website plus per-category RSS feeds.

The first neighborhood is **Nocatee, FL**. The architecture is built so additional neighborhoods can be added by editing one config file.

The site is **free** to use and intended to stay that way. Donations and lightweight local-business sponsorships may follow once the product is real; ads are last resort.

## Status

Working MVP pipeline. Single-neighborhood end-to-end:

`collect → keyword prefilter → AI classify → store → publish RSS`

The browsable HTML site (the actual product surface) is the next build. Today the site is just a static page linking to the RSS files.

Open decisions live in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # then edit OPENAI_API_KEY
python main.py
```

Generated feeds land in `data/feeds/<neighborhood>/`.

## Layout

```
skipthe.com/
├── main.py                 Pipeline entrypoint (run from cron)
├── requirements.txt
├── .env.example
├── app/
│   ├── ai/                 OpenAI classifier
│   ├── collectors/         RSS + webpage scrapers
│   ├── config/             sources.yaml — neighborhoods + feeds
│   ├── db/                 SQLite schema + helpers
│   ├── rss/                Feed XML generator
│   └── site/               Static homepage (gets richer — see WEBSITE.md)
├── data/                   SQLite DB + generated feed XML (gitignored)
└── docs/                   Project documentation
```

## Documentation

| File | What it covers |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Components, data flow, schema |
| [`docs/WEBSITE.md`](docs/WEBSITE.md) | Browsable site spec (the next build) |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Google Cloud VM, nginx, cron, TLS |
| [`docs/AI_MODERATION.md`](docs/AI_MODERATION.md) | Classifier prompt, categories, costs, tuning |
| [`docs/SOURCES.md`](docs/SOURCES.md) | Adding sources from any hyperlocal channel |
| [`docs/NEIGHBORHOODS.md`](docs/NEIGHBORHOODS.md) | Adding a new neighborhood |
| [`docs/CONTENT_POLICY.md`](docs/CONTENT_POLICY.md) | What's in, what's out, AI disclaimer, take-down |
| [`docs/OPERATIONS.md`](docs/OPERATIONS.md) | Runbook, monitoring, common failures |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Phases and remaining open decisions |
| [`CLAUDE.md`](CLAUDE.md) | Notes for AI assistants working in this repo |