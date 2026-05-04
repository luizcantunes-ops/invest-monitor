# Software Design Document - Investment Monitor Evolution

Date: 2026-05-03
Status: Draft v1
Owner: Luiz Cesar Antunes
System: Investment Monitor / Personal Investments Advisor

## 1. Purpose

This document defines the target evolution of the current Investment Monitor into a private, remotely accessible personal investments platform.

The product should remain a decision-support system, not an order-execution system. It should consolidate portfolio data, market context, policy constraints, investment theses, risk signals, and alerts into a calm, institutional-grade experience.

The immediate goal is remote access from outside the personal computer. The strategic goal is to become a reference personal investments intelligence platform while preserving privacy and safety.

## 2. Current State

The project currently runs locally under:

```text
/Users/macbook/Documents/invest
```

Current components:

```text
Browser
  -> frontend Node.js server on port 3001
       -> static UI in frontend/public
       -> direct integrations with some external APIs
       -> proxy to Python backend
  -> backend FastAPI on port 8000
       -> portfolio endpoints
       -> macro endpoints
       -> investor tracking
       -> Brasil/FII/crypto summary
       -> policy, thesis, risk book, decision memo
  -> scheduler
       -> Telegram alerts
       -> screener alerts
       -> crypto allocation drift
       -> weekly report
```

Important local state:

```text
src/data/portfolio_us.csv
src/data/portfolio_br.csv
src/data/policy.json
src/data/thesis.json
frontend/.data/
```

Important external dependencies:

```text
Yahoo Finance
Finnhub
Alpha Vantage
Massive/Polygon
Dataroma
ARK public CSVs
OpenInsider
Reddit WSB
Telegram Bot API
Alpaca paper account
```

## 3. Product Principles

The product must preserve the existing product register:

- Calm, precise, institutional.
- Private-banking feel, not a retail trading app.
- Decision support, not entertainment.
- Data density with hierarchy.
- Alerts only when action or review is justified.
- No automated trading in the initial remote-access version.

## 4. Non-Goals

The following are explicitly out of scope for the next evolution phase:

- Public access to the real personal portfolio.
- Automatic order execution.
- Social, gamified, or community features.
- Databricks Free Edition as the primary hosting runtime.
- Storing Schwab account passwords in application code.
- Exposing raw backend endpoints without internal authentication.

## 5. Target Architecture

### 5.1 Phase 1 Target: Private Remote Access

Use the existing app structure with cloud hosting and strict private access.

```text
User browser
  -> HTTPS frontend URL
       -> APP_PASSWORD session auth
       -> Node.js frontend/proxy
            -> X-Internal-Token
            -> FastAPI backend
                 -> local app data bundled at deploy time
                 -> external market/data providers
            -> Telegram alerts via scheduler/cron
```

Recommended deployment:

```text
Frontend Node.js service: Render, Railway, Fly.io, or Koyeb
Backend FastAPI service: Render, Railway, Fly.io, or Koyeb
Scheduler: Render cron job, GitHub Actions cron, or separate worker service
Secrets: platform environment variables
```

Phase 1 is acceptable for personal remote access, but not ideal for long-term persistence because CSV/JSON files remain local to the deployed runtime.

### 5.2 Phase 2 Target: Durable Private Platform

Move user-owned state into a durable database.

```text
User browser
  -> frontend
       -> backend API
            -> Postgres
                 -> accounts
                 -> positions
                 -> portfolio snapshots
                 -> policy
                 -> thesis
                 -> decisions
                 -> alerts
            -> Schwab API
            -> market/data providers
            -> Telegram/WhatsApp notification providers
```

Recommended data platform:

```text
Supabase Postgres or Neon Postgres
```

The CSV/JSON files become seed/fallback data, not the system of record.

### 5.3 Phase 3 Target: Reference Platform

Split the platform into private and public surfaces.

```text
Private app
  -> real portfolio
  -> real policy
  -> real thesis
  -> authenticated access only

Public reference app
  -> anonymized/fictitious portfolio
  -> methodology
  -> sample insights
  -> product demonstration
```

The public version should never expose:

- Real holdings and quantities.
- Real cost basis.
- Real account balances.
- Real decision notes.
- API keys, tokens, account identifiers, or refresh tokens.

## 6. Databricks Decision

Databricks should not be used as the main hosting environment for the product.

Rationale:

- Free Edition is quota-limited.
- Free Edition allows one Databricks App per account.
- Databricks Apps in Free Edition stop after up to 24 hours.
- Outbound internet access is restricted in Free Edition.
- The project depends on many external data sources.
- The product requires stable private access.

Recommended use of Databricks:

- Research notebooks.
- Historical market data lakehouse.
- Backtesting and simulations.
- Proprietary scoring experiments.
- Data enrichment pipelines.
- Internal analytical demos.

Databricks may become an analytics layer later, but not the production web runtime.

## 7. Schwab API Integration

### 7.1 Objective

Replace manual Schwab CSV imports with read-only API ingestion.

Initial scope:

- Account discovery.
- Balances.
- Positions.
- Transactions.
- Optional order history.

Out of initial scope:

- Placing orders.
- Canceling orders.
- Modifying orders.
- Options trading workflows.
- Any automated trade execution.

### 7.2 Integration Model

Add a backend module:

```text
src/core/schwab.py
```

Add backend endpoints:

```text
GET /schwab/status
GET /schwab/accounts
GET /schwab/positions
GET /schwab/transactions
POST /schwab/sync
```

The frontend should consume normalized portfolio data through existing portfolio endpoints where possible. Schwab-specific endpoints are for setup, diagnostics, and sync details.

### 7.3 OAuth and Token Storage

Required environment variables:

```env
SCHWAB_CLIENT_ID=
SCHWAB_CLIENT_SECRET=
SCHWAB_REDIRECT_URI=
SCHWAB_TRADING_ENABLED=false
```

Required stored secrets:

```text
refresh_token
access_token
access_token_expires_at
authorized_account_hashes
```

In Phase 1, tokens may be stored in encrypted server-side storage only if the hosting platform supports durable secure storage. Otherwise, Schwab API should wait until Phase 2.

In Phase 2, store tokens encrypted in Postgres or in a managed secrets store. Never expose Schwab tokens to the frontend.

### 7.4 Safety Controls

Default policy:

```env
SCHWAB_TRADING_ENABLED=false
```

The system must reject order-related functionality unless this flag is explicitly enabled. The first implementation should not include order routes at all.

All Schwab ingestion should be read-only and idempotent.

## 8. Data Model

### 8.1 Core Tables

Recommended Phase 2 schema:

```text
accounts
  id
  provider
  provider_account_id_hash
  display_name
  currency
  created_at
  updated_at

positions
  id
  account_id
  symbol
  description
  quantity
  average_cost
  market_value
  currency
  asset_type
  horizon
  sector
  source
  as_of

portfolio_snapshots
  id
  account_id
  total_market_value
  total_cost_basis
  cash
  currency
  as_of

policy
  id
  account_scope
  max_position_pct
  max_sector_pct
  min_cash_pct
  swing_max_loss_pct
  crypto_br_min_pct
  crypto_br_max_pct
  note
  updated_at

thesis
  id
  symbol
  reason
  sell_if
  main_risk
  last_review
  updated_at

decisions
  id
  symbol
  action
  rationale
  price
  market_regime
  created_at

alerts
  id
  type
  symbol
  severity
  message
  delivered_to
  delivered_at
  created_at
```

### 8.2 Data Ownership

The backend is the owner of:

- Schwab integration.
- Account data.
- Portfolio snapshots.
- Policy.
- Thesis.
- Decision records.
- Alert generation.

The frontend is the owner of:

- Navigation.
- Presentation.
- Local session handling.
- User interactions.

The frontend must not own durable investment data.

## 9. Security Requirements

### 9.1 Authentication

The frontend must require authentication in production:

```env
NODE_ENV=production
APP_PASSWORD=<strong-password>
```

The backend must require an internal token for all non-health routes:

```env
INTERNAL_API_TOKEN=<random-secret>
```

The frontend proxy must pass:

```http
X-Internal-Token: <INTERNAL_API_TOKEN>
```

### 9.2 Secrets

Secrets must live in environment variables or managed secret storage:

```env
APP_PASSWORD=
INTERNAL_API_TOKEN=
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
ALPHAVANTAGE_KEY=
FINNHUB_KEY=
MASSIVE_KEY=
ALPACA_KEY=
ALPACA_SECRET=
SCHWAB_CLIENT_ID=
SCHWAB_CLIENT_SECRET=
SCHWAB_REFRESH_TOKEN=
```

Secrets must not be committed to source control.

### 9.3 Network Exposure

Backend CORS must be restricted:

```env
ALLOWED_ORIGINS=https://private-frontend.example.com,http://127.0.0.1:3001
```

Backend direct access without `X-Internal-Token` must return `401`.

### 9.4 Privacy

The production private app contains highly sensitive financial information. It must not be indexed, shared, screenshotted publicly, or deployed without authentication.

Recommended HTTP headers:

```text
Cache-Control: no-store
X-Frame-Options: DENY
Referrer-Policy: no-referrer
```

## 10. Scheduler and Alerts

Current scheduler jobs:

```text
technical alerts
screener alerts
crypto allocation drift
weekly report
```

Target scheduler options:

```text
Option A: Render cron job
Option B: GitHub Actions cron calling protected backend endpoint
Option C: separate worker service
```

Recommended Phase 1:

```text
Separate worker service or Render cron job using the same backend codebase.
```

Requirements:

- Scheduler must read secrets from environment variables.
- Telegram failures must be explicit and non-fatal.
- Alert routes, if exposed, must require a scheduler token.
- Alerts should be deduplicated where possible.

## 11. API Evolution

### 11.1 Preserve Existing Routes

The existing frontend relies on many `/api/py/*` proxy routes. Preserve them during Phase 1.

### 11.2 Normalize Portfolio Source

Introduce a portfolio provider abstraction:

```python
class PortfolioProvider:
    def get_positions(self) -> list[dict]:
        ...

class CsvPortfolioProvider(PortfolioProvider):
    ...

class SchwabPortfolioProvider(PortfolioProvider):
    ...

class DatabasePortfolioProvider(PortfolioProvider):
    ...
```

Provider resolution:

```text
Phase 1: CSV provider
Phase 1.5: Schwab provider with CSV fallback
Phase 2: Database provider with Schwab sync
```

### 11.3 Proposed New Internal Endpoints

```text
GET /sources/status
GET /portfolio/source
POST /portfolio/sync
GET /sync/jobs
GET /sync/jobs/{id}
```

These endpoints support observability and remote operation.

## 12. Deployment Plan

### 12.1 Phase 1 - Private Remote MVP

Goal: Access the app securely from outside the personal computer.

Tasks:

1. Add `.env.example` for frontend and backend.
2. Confirm no real secrets are in code.
3. Ensure frontend fails closed in production without `APP_PASSWORD`.
4. Ensure backend rejects calls without `INTERNAL_API_TOKEN`.
5. Restrict CORS with `ALLOWED_ORIGINS`.
6. Deploy backend FastAPI.
7. Deploy frontend Node.js.
8. Configure `PYTHON_API_URL`.
9. Configure environment variables.
10. Validate all main tabs remotely.

Acceptance criteria:

- Private URL loads over HTTPS.
- Login is required.
- `/health` works.
- Backend direct calls without token return `401`.
- Portfolio, Brasil, Macro, Risk Book, and Weekly Committee load.
- No secrets appear in frontend source or browser responses.

### 12.2 Phase 1.5 - Schwab Read-Only Sync

Goal: Stop relying on manual Schwab CSV imports.

Tasks:

1. Register Schwab developer app.
2. Implement OAuth callback flow.
3. Store refresh token securely.
4. Implement read-only account and position fetch.
5. Add `SchwabPortfolioProvider`.
6. Add manual `POST /schwab/sync`.
7. Preserve CSV fallback.
8. Display data source and last sync timestamp in UI.

Acceptance criteria:

- Positions can be synced without using local Downloads.
- CSV fallback still works.
- No order endpoints exist.
- Trading is disabled by default.
- Last sync timestamp is visible.

### 12.3 Phase 2 - Durable Data Platform

Goal: Make the app reliable across deploys and devices.

Tasks:

1. Create Supabase or Neon Postgres project.
2. Create core tables.
3. Migrate CSV/JSON into database.
4. Replace policy/thesis file writes with database writes.
5. Store portfolio snapshots.
6. Add decision history table.
7. Add alert history table.
8. Add database migrations.

Acceptance criteria:

- Policy updates survive redeploy.
- Thesis updates survive redeploy.
- Portfolio snapshots are queryable.
- The app no longer depends on local files as system of record.

### 12.4 Phase 3 - Public Reference Version

Goal: Create a portfolio-safe public demonstration.

Tasks:

1. Create anonymized sample dataset.
2. Add environment flag:

```env
APP_MODE=private|demo
```

3. Hide all real account values in demo mode.
4. Disable write endpoints in demo mode.
5. Publish reference URL.

Acceptance criteria:

- Public app contains no real personal data.
- Methodology is visible.
- Product quality is demonstrable.
- Private app remains separate and authenticated.

## 13. Observability

Minimum logs:

- Backend startup configuration health, without secrets.
- External API failures by provider.
- Scheduler execution results.
- Schwab sync success/failure.
- Auth failures count, without logging passwords/tokens.

Recommended health endpoints:

```text
GET /health
GET /sources/status
```

Do not log:

- Schwab tokens.
- Account numbers.
- Full portfolio CSV content.
- APP_PASSWORD.
- INTERNAL_API_TOKEN.

## 14. Testing Strategy

### 14.1 Local Validation

```bash
cd /Users/macbook/Documents/invest/src
python3 -m uvicorn api:app --port 8000 --host 127.0.0.1
```

```bash
cd /Users/macbook/Documents/invest/frontend
node server.js
```

Validate:

- Login flow.
- Portfolio tab.
- Brasil tab.
- Investors and Macro tab.
- Risk Book.
- Weekly Committee.
- Policy and Thesis updates.

### 14.2 Security Validation

Backend:

```bash
curl https://backend.example.com/portfolio
# Expected: 401
```

Frontend:

```bash
NODE_ENV=production node server.js
# Expected: fatal error if APP_PASSWORD is missing
```

### 14.3 Deploy Validation

After each deploy:

- Open private frontend URL.
- Authenticate.
- Check browser console.
- Check backend logs.
- Verify `/api/py/brasil`.
- Verify `/api/py/macro/full`.
- Verify `/api/py/portfolio`.
- Verify scheduler dry run if available.

## 15. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---:|---|
| Real portfolio exposed publicly | Critical | Production auth, backend token, private deployment, no indexing |
| Schwab token leak | Critical | Backend-only OAuth, encrypted storage, no frontend exposure |
| Accidental trading capability | Critical | Do not implement order routes; `SCHWAB_TRADING_ENABLED=false` |
| Ephemeral disk loses policy/thesis changes | High | Move durable state to Postgres in Phase 2 |
| External provider rate limits | Medium | Caching, backoff, provider status page |
| Dataroma/scraping breaks | Medium | Soft failure and cached previous result |
| Scheduler duplicate alerts | Medium | Alert history and deduplication |
| Vendor lock-in | Low | Keep provider abstraction and standard Postgres |

## 16. Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-05-03 | Use cloud hosting for remote access instead of Databricks Apps | The current app needs stable web access and many external integrations |
| 2026-05-03 | Treat Databricks as future analytics layer | Better suited for research, backtests, and lakehouse workloads |
| 2026-05-03 | Prioritize Schwab read-only API integration | Removes manual CSV dependency and enables remote accuracy |
| 2026-05-03 | Keep trading disabled | Product is an advisor/monitor, not an execution system |
| 2026-05-03 | Move durable state to Postgres in Phase 2 | Required for reliable remote access and redeploy safety |

## 17. Open Questions

1. Preferred hosting provider for Phase 1: Render, Railway, Fly.io, Koyeb, or another platform?
2. Should Phase 1 deploy frontend and backend as two services or consolidate temporarily into one service?
3. Should the first Schwab integration use a maintained library or direct HTTP requests against the official API?
4. Should Supabase or Neon be the default Postgres target?
5. Should demo/public mode exist soon, or only after the private version is stable?

## 18. Recommended Next Step

Proceed with Phase 1:

1. Add deployment manifests.
2. Add `.env.example`.
3. Validate production auth behavior.
4. Deploy backend and frontend privately.
5. Confirm remote access.

After Phase 1 is stable, implement Schwab read-only sync before adding any new analytical features.
