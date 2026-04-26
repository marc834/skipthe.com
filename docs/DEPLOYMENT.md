# Deployment — Google Cloud VM

Target: a single Compute Engine VM running Debian or Ubuntu, with nginx out front and cron driving the pipeline.

## Provisioning

- **Machine type**: `e2-small` (2 vCPU burst, 2 GB RAM) is plenty. The pipeline is I/O bound and the OpenAI calls are network-bound.
- **OS**: Debian 12 or Ubuntu 22.04 LTS.
- **Disk**: 20 GB standard persistent disk. The SQLite DB will stay tiny (megabytes per neighborhood per year).
- **Firewall**: allow `tcp:80,443` from `0.0.0.0/0`. SSH on `:22` from your IP only (or via IAP).
- **Static external IP**: reserve one and point `skipthe.com` A record at it.

## One-time host setup

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip nginx git certbot python3-certbot-nginx
sudo mkdir -p /var/www/skipthe
sudo chown $USER:$USER /var/www/skipthe
git clone <repo> /var/www/skipthe
cd /var/www/skipthe
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# edit .env: OPENAI_API_KEY, SITE_BASE_URL=https://skipthe.com, NEIGHBORHOOD=nocatee
```

## nginx

`/etc/nginx/sites-available/skipthe`:

```nginx
server {
    listen 80;
    server_name skipthe.com www.skipthe.com;

    root /var/www/skipthe/app/site;
    index index.html;

    # Static + generated HTML
    location / {
        try_files $uri $uri/ $uri.html =404;
        add_header Cache-Control "public, max-age=300";
    }

    # Generated RSS feeds
    location /feeds/ {
        alias /var/www/skipthe/data/feeds/;
        types { application/rss+xml xml; }
        default_type application/rss+xml;
        add_header Cache-Control "public, max-age=300";
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/skipthe /etc/nginx/sites-enabled/skipthe
sudo nginx -t && sudo systemctl reload nginx
```

## TLS

```bash
sudo certbot --nginx -d skipthe.com -d www.skipthe.com
```

Certbot will rewrite the nginx config to add the `:443` server block and auto-renew via systemd timer.

## Cron

Run every 30 minutes. As the deploy user (not root):

```cron
*/30 * * * * cd /var/www/skipthe && /var/www/skipthe/.venv/bin/python main.py >> /var/log/skipthe/pipeline.log 2>&1
```

Create the log dir once:

```bash
sudo mkdir -p /var/log/skipthe
sudo chown $USER:$USER /var/log/skipthe
```

## Log rotation

`/etc/logrotate.d/skipthe`:

```
/var/log/skipthe/*.log {
    weekly
    rotate 8
    compress
    missingok
    notifempty
    copytruncate
}
```

## Secrets

- `.env` lives at the repo root, mode `600`, owned by the deploy user.
- The `OPENAI_API_KEY` is the only sensitive value today.
- Do **not** commit `.env`. (`.gitignore` excludes it.)
- Long-term, consider Google Secret Manager + a wrapper that exports env at cron time. Skip until there's a real reason.

## Backups

```bash
# Daily DB snapshot, retain 14 days
0 4 * * * sqlite3 /var/www/skipthe/data/items.sqlite3 ".backup /var/backups/skipthe/items-$(date +\%F).sqlite3" && find /var/backups/skipthe -name 'items-*.sqlite3' -mtime +14 -delete
```

## Verifying a deploy

```bash
curl -I https://skipthe.com/                            # 200, text/html
curl -I https://skipthe.com/nocatee/                    # 200, text/html (once site generator ships)
curl -I https://skipthe.com/feeds/nocatee/all.xml       # 200, application/rss+xml
tail -n 50 /var/log/skipthe/pipeline.log                # last cron run output
```