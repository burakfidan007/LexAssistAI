# LexAssist AI — Ubuntu 22.04 VPS Deployment Guide

Deploys the full stack (nginx + FastAPI backend + MongoDB) with Docker
Compose, HTTPS via Let's Encrypt. Everything runs behind one nginx that
serves the frontend and reverse-proxies `/api` to the backend, so the app
is a single HTTPS origin.

> Stack note: the backend is **FastAPI (Python) + uvicorn**, not Node/Express.
> There is no PM2 or npm — the process manager is Docker (`restart: always`
> + healthchecks). Nodemailer/Winston equivalents are Python `smtplib` /
> `logging`, already implemented.

---

## 1. Prerequisites

- Ubuntu 22.04 VPS, a domain name pointed at the server's IP (A record for
  `your-domain.com` and `www`).
- Ports 80 and 443 open.

```bash
# Install Docker Engine + compose plugin
sudo apt update && sudo apt install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Firewall
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 2. Get the code

```bash
sudo mkdir -p /opt/lexassist-ai && sudo chown $USER /opt/lexassist-ai
git clone <your-repo-url> /opt/lexassist-ai
cd /opt/lexassist-ai
```

---

## 3. Configure `.env` (production)

```bash
cp .env.example .env
nano .env
```

Set at minimum:

```ini
ENVIRONMENT=production

# Generate: python3 -c "import secrets; print(secrets.token_urlsafe(48))"
JWT_SECRET=<long-random-value>

MONGO_INITDB_ROOT_USERNAME=lexassist_prod
MONGO_INITDB_ROOT_PASSWORD=<strong-password>
MONGO_URI=mongodb://lexassist_prod:<strong-password>@mongo:27017/lexassist?authSource=admin

GEMINI_API_KEY=<your-key>
GEMINI_MODEL=gemini-3.5-flash

# HTTPS origin used inside password-reset / verification email links
FRONTEND_BASE_URL=https://your-domain.com
CORS_ORIGINS=["https://your-domain.com"]

# Real email (see .env.example for the Gmail App Password steps)
EMAIL_MODE=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=<app-password>
SMTP_FROM=you@gmail.com
```

> In `production`, the backend **refuses to start** if `JWT_SECRET` is a
> placeholder/too short, `CORS_ORIGINS` is `*`, `FRONTEND_BASE_URL` isn't
> HTTPS, or email would only log to console. This is intentional fail-fast.

Point nginx at your domain:

```bash
sed -i 's/YOUR_DOMAIN/your-domain.com/g' nginx.prod.conf
```

---

## 4. Issue the TLS certificate (Let's Encrypt)

The prod nginx serves `/.well-known/acme-challenge/` from `./certbot/www`
and reads certs from `./certbot/conf`.

```bash
mkdir -p certbot/www certbot/conf

# Start ONLY nginx+backend+mongo on HTTP first so the ACME challenge works.
# (nginx will warn about missing certs until issued — that's expected.)
docker compose -f docker-compose.prod.yml up -d

# Obtain the certificate via the webroot method
docker run --rm \
  -v "$PWD/certbot/conf:/etc/letsencrypt" \
  -v "$PWD/certbot/www:/var/www/certbot" \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  -d your-domain.com -d www.your-domain.com \
  --email you@example.com --agree-tos --no-eff-email

# Reload nginx to pick up the certs
docker compose -f docker-compose.prod.yml restart frontend
```

**Auto-renewal** (cron, twice daily):

```bash
( crontab -l 2>/dev/null; echo '0 3,15 * * * cd /opt/lexassist-ai && docker run --rm -v "$PWD/certbot/conf:/etc/letsencrypt" -v "$PWD/certbot/www:/var/www/certbot" certbot/certbot renew --quiet && docker compose -f docker-compose.prod.yml restart frontend' ) | crontab -
```

---

## 5. Launch

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps        # all should be healthy
docker compose -f docker-compose.prod.yml logs -f    # tail logs
```

Visit `https://your-domain.com` → the login page. Register, upload a PDF,
run an AI summary to confirm end-to-end.

---

## 6. Backups (recommended: nightly cron)

```bash
chmod +x scripts/*.sh
( crontab -l 2>/dev/null; echo '0 2 * * * cd /opt/lexassist-ai && ./scripts/backup-mongo.sh >> /var/log/lexassist-backup.log 2>&1' ) | crontab -

# Restore a specific backup:
./scripts/restore-mongo.sh ./backups/lexassist-YYYYmmdd-HHMMSS.archive.gz
```

Uploaded PDFs and avatars live in the `backend_uploads` / `backend_avatars`
Docker volumes — include them in your VPS-level backup, or snapshot the
whole `/var/lib/docker/volumes`.

---

## 7. Updating a running deployment

```bash
cd /opt/lexassist-ai
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Frontend-only changes take effect immediately (static files are mounted
read-only). Backend changes rebuild the image.

---

## 8. Rollback

```bash
# Code rollback
cd /opt/lexassist-ai
git log --oneline -n 10
git checkout <previous-good-commit>
docker compose -f docker-compose.prod.yml up -d --build

# Data rollback (restore last good DB backup)
./scripts/restore-mongo.sh ./backups/<good-backup>.archive.gz

# Full stop (keeps data volumes)
docker compose -f docker-compose.prod.yml down

# Full stop + WIPE data (destructive — only for a clean reinstall)
docker compose -f docker-compose.prod.yml down -v
```

---

## Common issues

- **Backend won't start in production** → read `docker compose -f docker-compose.prod.yml logs backend`; it prints exactly which env var failed the fail-fast validation.
- **Emails not arriving** → Gmail needs an **App Password** (not your login password) with 2FA enabled; check `EMAIL_MODE=smtp`.
- **502 from nginx** → backend not healthy yet; `docker compose -f docker-compose.prod.yml ps` and check the backend logs.
- **AI returns 503** → `GEMINI_API_KEY` missing/invalid; 429 = quota.
