# LexAssist AI — Production Readiness Checklist

_Last audited: 2026-07-24. Stack: FastAPI + MongoDB + Docker + nginx + Gemini._

## Readiness matrix

| Target | Ready? | Notes |
|---|---|---|
| Local development | ✅ Yes | `docker compose up -d` |
| Docker deployment | ✅ Yes | dev + `docker-compose.prod.yml` |
| Ubuntu VPS deployment | ✅ Yes | see `deployment-ubuntu.md` |
| Public internet exposure | ✅ Yes | HTTPS, security headers, rate limiting, non-root, fail-fast config |
| Real users (non-paying) | ✅ Yes | all core features backend-connected |
| Real users (paying) | ⚠️ Blocked on ONE thing | no real payment gateway — billing is an intentional mock (`POST /billing/upgrade` flips the plan in DB). Integrate Stripe/iyzico before charging. |

---

## ✅ Done & verified

**Security**
- JWT secret validated at startup (length + placeholder + fail-fast in production); tokens carry `iss`/`aud`/`iat`, validated on decode; only HMAC algs allowed.
- Security-headers middleware (CSP, X-Frame-Options DENY, nosniff, HSTS in prod).
- CORS restricted (production rejects `*`).
- Rate limiting (`slowapi`): 5–10/min on auth endpoints, 20/min on AI endpoints.
- Request body size cap (30MB) + per-endpoint upload cap (25MB).
- Password policy (length + complexity + common-password blocklist), reuse rejected on change.
- Centralized exception handlers — no stack traces leak to clients; unhandled errors logged server-side only.
- Anti-enumeration on forgot-password / resend-verification (always 204).
- Non-root container user; storage volumes chowned by entrypoint.

**Data**
- MongoDB indexes on startup: unique `users.email` (fixes the register race), token-hash lookups, all `owner_id`/`case_id`, unique `ai_results` and `preferences` and `folders(owner_id,slug)`.
- Account-delete cascade removes every collection + files + avatar (verified all-zero).

**Features (all backend-connected — no demo except billing)**
- AI chat/summary/risks/draft on real Gemini (`gemini-3.5-flash`), per-case persistence + result cache.
- Case-scoped dashboard (PDF, chat history, summary/risks/draft, activity) persisted across refresh/session.
- Real SMTP email (dev console fallback + prod SMTP), tokenized reset/verify with expiry, HTML templates.
- Uploads: content-type + **magic-byte (`%PDF`)** signature check, size limit, uuid storage (no path traversal), filename sanitized, owner-scoped download.
- Real avatar upload, custom folders, notifications, preferences, activity history.

**Ops**
- `/health` endpoint; healthchecks on all 3 containers; backend gated on `mongo: service_healthy`.
- Structured logging; backup/restore scripts.
- Same-origin nginx reverse proxy (no CORS in the browser path); gzip; static caching; HTTP→HTTPS redirect; Let's Encrypt-ready.

---

## ⚠️ Remaining risks / optional improvements

| Item | Severity | Recommendation |
|---|---|---|
| **Real payment gateway** | Blocker *for paid users only* | Integrate Stripe/iyzico; replace the mock `/billing/upgrade`. |
| JWT logout is client-side only (stateless) | Low | Fine for MVP. For forced server-side revocation, add a token denylist / short-lived access + refresh tokens. |
| Rate-limit store is in-process | Low | Fine for single instance. Move `slowapi` to Redis if you run multiple backend replicas. |
| AI result cache is in-process | Low | Same — move to Redis for multi-replica. |
| No automated tests / CI | Medium | Add pytest + a GitHub Actions pipeline before a larger team iterates. |
| Secrets in `.env` on disk | Medium | Acceptable for a single VPS; use a secrets manager (Vault/SSM) at scale. |
| Frontend features left intentionally UI-only | Low | Dark theme, English i18n, active-sessions list — not backend concerns; not blockers. |

---

## Deployment blockers: **none** (for non-paying launch)
## Security blockers: **none**
## Performance blockers: **none** at expected small-to-medium load

---

## Scaling notes (when you outgrow one VPS)
1. Move rate-limit + AI cache to **Redis** (both are currently in-process).
2. Run **multiple backend replicas** behind nginx (`upstream`); backend is stateless apart from those two caches.
3. Use **MongoDB Atlas** or a replica set instead of the single-container Mongo.
4. Put uploads/avatars on **object storage (S3-compatible)** instead of local volumes so replicas share files.
5. Add a real **monitoring/alerting** stack (Prometheus + Grafana, or a hosted APM) and centralized log shipping.

## Backup recommendations
- Nightly `scripts/backup-mongo.sh` via cron (14-day retention built in).
- Include the `backend_uploads` + `backend_avatars` volumes in VPS snapshots.
- Test a restore (`scripts/restore-mongo.sh`) into a staging environment periodically.
