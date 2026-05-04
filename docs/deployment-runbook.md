# Deployment Runbook — Investment Monitor

Date: 2026-05-03
Phase: 1 (Private Remote Access)
Owner: Luiz Cesar Antunes

## Prerequisites

- Python 3.9+
- Node.js 18+
- A hosting account (Render recommended for Phase 1)
- Secrets already rotated (never commit `.env` files)

---

## Local development

### Backend

```bash
cd /Users/macbook/Documents/Projects/Invest/src
cp .env.example .env          # fill in real values
python3 -m uvicorn api:app --port 8000 --host 127.0.0.1
```

### Frontend

```bash
cd /Users/macbook/Documents/Projects/Invest/frontend
cp .env.example .env          # fill in real values
node server.js
```

Open: `http://127.0.0.1:3001`

### Validation harness

```bash
cd /Users/macbook/Documents/Projects/Invest
bash scripts/validate.sh
```

Expected: `26 passed · 0 failed` before every deploy.

---

## Environment variables

### Backend (`src/.env`)

| Variable | Required | Description |
|---|---|---|
| `INTERNAL_API_TOKEN` | Yes (prod) | Random secret. Must match frontend. |
| `ALLOWED_ORIGINS` | Yes (prod) | Comma-separated frontend URLs |
| `TELEGRAM_TOKEN` | Scheduler only | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Scheduler only | Telegram chat ID |
| `FINNHUB_KEY` | Yes | Market data |
| `ALPHAVANTAGE_KEY` | Yes | News sentiment, sector performance |
| `MASSIVE_KEY` | Yes | Polygon/Massive financials |
| `ALPACA_KEY` / `ALPACA_SECRET` | Intraday only | Paper account |
| `MACRO_SHILLER_PE` | No | Manual override (default 38.0) |
| `MACRO_BUFFETT_IND` | No | Manual override (default 198.0) |

### Frontend (`frontend/.env`)

| Variable | Required | Description |
|---|---|---|
| `APP_PASSWORD` | Yes (prod) | Dashboard access password |
| `INTERNAL_API_TOKEN` | Yes (prod) | Must match backend |
| `PYTHON_API_URL` | Yes | Backend URL (e.g. `https://your-backend.onrender.com`) |
| `NODE_ENV` | Yes (prod) | Set to `production` |
| `ALLOWED_ORIGINS` | No | Not used by frontend; set on backend only |
| `PORT` | No | Default 3001 |

---

## Phase 1 — Render deployment

### Step 1: Create two services on Render

**Backend (Python)**
- Environment: Python
- Build command: `pip install -r requirements.txt`
- Start command: `cd src && python3 -m uvicorn api:app --port $PORT --host 0.0.0.0`
- Root directory: `/` (project root)
- Health check path: `/health`

**Frontend (Node.js)**
- Environment: Node
- Build command: (none)
- Start command: `cd frontend && node server.js`
- Root directory: `/`
- Health check path: `/health`

### Step 2: Configure environment variables

On the backend service, set all variables from `src/.env.example`.

Key values for production:
```
INTERNAL_API_TOKEN=<generate with: openssl rand -hex 32>
ALLOWED_ORIGINS=https://your-frontend.onrender.com
NODE_ENV=production
```

On the frontend service:
```
APP_PASSWORD=<strong password>
INTERNAL_API_TOKEN=<same as backend>
PYTHON_API_URL=https://your-backend.onrender.com
NODE_ENV=production
```

### Step 3: Deploy

Push to the connected git branch. Render will build and deploy automatically.

Or trigger manually from the Render dashboard.

### Step 4: Validate remote access

```bash
# Health check (must be public)
curl https://your-backend.onrender.com/health
# Expected: {"status":"ok"}

# Direct backend without token (must be blocked)
curl https://your-backend.onrender.com/portfolio
# Expected: 401 Unauthorized

# Frontend
open https://your-frontend.onrender.com
# Expected: login form
```

---

## Scheduler

### Option A: Render cron job

Add a third service on Render:
- Environment: Python
- Build command: `pip install -r requirements.txt`
- Start command: `cd src && python3 scheduler.py`
- Type: Background worker (not a web service)

Uses the same environment variables as the backend service.

### Option B: GitHub Actions cron (future)

Create `.github/workflows/scheduler.yml` to call protected endpoints.
Requires backend endpoints for triggering jobs — add in Phase 1.5.

---

## Data files

In Phase 1, these files are bundled at deploy time and are ephemeral:

```
src/data/portfolio_us.csv
src/data/portfolio_br.csv
src/data/policy.json
src/data/thesis.json
```

**Limitation:** changes made via the UI (policy, thesis) will be lost on redeploy.

**Mitigation (Phase 2):** move durable state to Postgres (Supabase or Neon).

Until Phase 2, export policy.json and thesis.json before redeploying and re-upload if needed.

---

## Generating secrets

```bash
# INTERNAL_API_TOKEN
openssl rand -hex 32

# APP_PASSWORD (readable)
openssl rand -base64 16
```

Never commit generated secrets. Store only in `.env` (local) or Render environment variables (production).

---

## Rollback

Render keeps previous deploys. To rollback:
1. Open the service on Render dashboard
2. Go to Deploys
3. Click "Rollback to this deploy" on the last stable version

---

## Phase 1 Definition of Done

- [ ] Private frontend URL loads over HTTPS
- [ ] Login form appears without `APP_PASSWORD` bypass
- [ ] `GET /health` returns 200
- [ ] `GET /portfolio` without token returns 401
- [ ] All main tabs load (Portfolio, Brasil, Macro, Risk Book, Weekly Committee)
- [ ] No secrets in browser source or responses
- [ ] `bash scripts/validate.sh` passes locally
- [ ] Scheduler path documented and operational

---

## Next phase

After Phase 1 is stable, proceed with:
- **Phase 1.5:** Schwab read-only API (`src/core/schwab.py`)
- **Phase 2:** Postgres for durable state (policy, thesis, decisions, snapshots)

See `docs/software-design-document.md` and `docs/developer-recommendations-from-sdd.md` for full roadmap.
