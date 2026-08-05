# Deploy: Frontend on Vercel + Backend on Render + MongoDB Atlas

This splits the app across three managed services:

| Piece | Host | Why |
|---|---|---|
| Frontend (static HTML/JS) | **Vercel** | perfect for static sites, free |
| Backend (FastAPI) | **Render** (Docker web service) | runs a persistent server; Vercel serverless can't (no disk, timeouts) |
| MongoDB | **MongoDB Atlas** (free M0) | neither Vercel nor Render hosts MongoDB |

> 📁 **File storage.** Render's disk is ephemeral (files vanish on restart),
> so uploaded PDFs + avatars go to **Firebase Storage** instead
> (`STORAGE_BACKEND=firebase`). Do the Firebase setup in Step 1b below.
> (Locally / on a VPS, `STORAGE_BACKEND=local` keeps using disk — no Firebase
> needed there.)

---

## Step 1 — MongoDB Atlas (free)

1. Create an account at <https://www.mongodb.com/atlas>, create a **free M0 cluster**.
2. **Database Access** → add a user (username + password).
3. **Network Access** → add IP `0.0.0.0/0` (allow from anywhere — Render's IPs are dynamic).
4. **Connect** → "Drivers" → copy the connection string, e.g.
   `mongodb+srv://USER:PASS@cluster0.xxxx.mongodb.net/lexassist?retryWrites=true&w=majority`
   (add `/lexassist` as the db name before the `?`).

---

## Step 1b — Firebase Storage (for uploaded files)

1. <https://console.firebase.google.com> → **Add project** (can reuse your Gemini project).
2. Left menu → **Storage** → **Get started** → accept defaults. Note the bucket
   name shown, e.g. `your-project-id.appspot.com`.
3. ⚙️ **Project settings** → **Service accounts** → **Generate new private key**.
   A JSON file downloads. You'll paste its **entire contents** into the Render
   env var `FIREBASE_CREDENTIALS_JSON` (never commit this file).

> Newer Firebase projects may prompt to enable the **Blaze** (pay-as-you-go)
> plan for Storage; you stay within the free usage limits for a small app, but
> a card may be required. Cloudflare R2 is an alternative if you prefer.

---

## Step 2 — Backend on Render

1. Push this repo to GitHub.
2. Render dashboard → **New +** → **Blueprint** → select the repo. Render reads
   `render.yaml` and creates the `lexassist-api` Docker web service.
   - Free plan: open `render.yaml` and **delete the `disk:` block** first
     (disks need a paid plan), and set `plan: free`.
3. When prompted, fill the `sync: false` env vars:
   ```
   ENVIRONMENT        = production
   JWT_SECRET         = <python3 -c "import secrets;print(secrets.token_urlsafe(48))">
   MONGO_URI          = <your Atlas connection string, incl. /lexassist>
   GEMINI_API_KEY     = <your key>
   GEMINI_MODEL       = gemini-3.5-flash
   FRONTEND_BASE_URL  = https://YOUR-APP.vercel.app     (fill after Step 3, then redeploy)
   CORS_ORIGINS       = ["https://YOUR-APP.vercel.app"] (JSON array; fill after Step 3)
   EMAIL_MODE         = smtp
   SMTP_HOST          = smtp.gmail.com
   SMTP_PORT          = 587
   SMTP_USER          = you@gmail.com
   SMTP_PASSWORD      = <Gmail App Password>
   SMTP_FROM          = you@gmail.com
   STORAGE_BACKEND    = firebase
   FIREBASE_BUCKET    = your-project-id.appspot.com
   FIREBASE_CREDENTIALS_JSON = <paste the whole service-account JSON as one value>
   ```
   > Render injects `PORT`; the container already listens on it.
4. Deploy. Note the service URL, e.g. `https://lexassist-api.onrender.com`.
   Test: open `https://lexassist-api.onrender.com/health` → `{"status":"ok"}`.

> `ENVIRONMENT=production` makes the backend refuse to start on a weak
> `JWT_SECRET`, a non-HTTPS `FRONTEND_BASE_URL`, or `CORS_ORIGINS=*`. Read the
> Render logs if it won't boot — it names the exact problem.

---

## Step 3 — Frontend on Vercel

1. **Point the frontend at your Render backend.** Edit `frontend/js/config/env.js`:
   ```js
   const API_ORIGIN = 'https://lexassist-api.onrender.com';
   ```
   Commit + push.
2. Vercel dashboard → **Add New** → **Project** → import the repo.
   - **Root Directory** → `frontend`
   - **Framework Preset** → `Other`
   - No build command (static). Deploy.
3. Note your Vercel URL, e.g. `https://lexassist.vercel.app`.

---

## Step 4 — Wire the two origins together (CORS)

Because frontend (Vercel) and backend (Render) are different origins, the
backend must allow the Vercel origin. Back in **Render → Environment**:

```
FRONTEND_BASE_URL = https://lexassist.vercel.app
CORS_ORIGINS      = ["https://lexassist.vercel.app"]
```

Save → Render redeploys. Done.

---

## Step 5 — Verify

Open your Vercel URL → register → upload a PDF → run an AI summary.
- Login/register failing with a CORS error → `CORS_ORIGINS` doesn't exactly
  match the Vercel URL (scheme + host, no trailing slash).
- AI 503 → `GEMINI_API_KEY` missing; 429 → quota.
- First request slow → Render free instances cold-start after sleeping.

---

## Updating

- **Frontend**: push to the repo → Vercel auto-deploys.
- **Backend**: push to the repo → Render auto-deploys (`autoDeploy: true`).
- Changing `env.js`'s `API_ORIGIN` requires a frontend redeploy.

## Rollback
- Vercel: dashboard → Deployments → promote a previous deployment.
- Render: dashboard → Events → "Rollback" to a previous deploy.
- Data: Atlas → Backups (paid tiers) or restore from your own `mongodump`.
