# Developer Recommendations from SDD

Date: 2026-05-03
Source: `docs/software-design-document.md`
Audience: developer/implementation agent
Goal: evolve Investment Monitor into a private, remotely accessible personal investments platform.

## Executive Direction

Do not rebuild the product. Preserve the current FastAPI + Node.js architecture and make the smallest safe changes needed to support private remote access.

The next milestone is not Databricks, AI, or new market data features. The next milestone is secure remote availability.

Priority order:

1. Make production configuration explicit and safe.
2. Package backend and frontend for deployment.
3. Keep private portfolio data behind authentication.
4. Add a repeatable validation harness.
5. Deploy privately.
6. Then add Schwab read-only sync.
7. Then move durable state to Postgres.

## P0 - Production Safety

### Recommendation

Confirm the app fails closed in production.

Required behavior:

- Frontend must not start in production without `APP_PASSWORD`.
- Backend must reject all non-health routes without `X-Internal-Token`.
- CORS must be restricted by `ALLOWED_ORIGINS`.
- Secrets must come from environment variables.
- No real secrets should exist in committed files.

Relevant files:

```text
frontend/server.js
src/api.py
src/data/config.py
requirements.txt
```

Acceptance criteria:

```bash
NODE_ENV=production node frontend/server.js
# Expected: fails if APP_PASSWORD is missing
```

```bash
curl http://127.0.0.1:8000/portfolio
# Expected: 401 if INTERNAL_API_TOKEN is configured and header is absent
```

## P1 - Deployment Readiness

### Recommendation

Add deployment-specific documentation and manifests without changing runtime behavior.

Create or update:

```text
.env.example
docs/deployment-runbook.md
```

Optional platform files depending on chosen host:

```text
render.yaml
Dockerfile.backend
Dockerfile.frontend
```

Prefer two services for Phase 1:

```text
backend: FastAPI / uvicorn
frontend: Node.js server/proxy
```

Reason:

- The existing frontend already acts as a private gateway.
- The backend can remain internal-token protected.
- This keeps changes smaller than merging everything into one runtime.

Acceptance criteria:

- A new environment can be configured from `.env.example`.
- Backend starts with one documented command.
- Frontend starts with one documented command.
- `PYTHON_API_URL` points frontend to backend.

## P2 - Local Validation Harness

### Recommendation

Yes, create a local validation harness.

In this project, a harness should mean a repeatable set of scripts that runs the same checks before every deploy. This is more useful immediately than adopting a full CI/CD platform.

Recommended file:

```text
scripts/validate.sh
```

It should run:

```bash
python3 -m py_compile src/api.py src/scheduler.py src/alerts/telegram.py src/core/brasil.py
node --check frontend/server.js
node --check frontend/public/app.js
curl backend /health when server is running
curl protected backend endpoint without token and expect 401
curl protected backend endpoint with token and expect 200
```

Optional later:

```text
scripts/smoke_backend.sh
scripts/smoke_frontend.sh
scripts/check_secrets.sh
```

Acceptance criteria:

- One command gives confidence that the app is deployable.
- The harness does not print secrets.
- The harness can run locally and later in CI.

## P3 - Hosting Choice

### Recommendation

Start with Render unless there is a strong preference for another host.

Why Render fits Phase 1:

- Native Python web service.
- Native Node web service.
- Cron jobs are straightforward.
- Environment variables are easy to configure.
- Good enough for private personal access.

Alternative:

- Railway is developer-friendly, but the free/low-cost model is credit-based.
- Fly.io is powerful, but has more operational surface.
- Koyeb is viable, but less common than Render for this stack.
- Vercel is excellent for frontend, but the current Node server/proxy plus FastAPI backend makes Render simpler at first.

Acceptance criteria:

- Private frontend URL works over HTTPS.
- Backend health endpoint works.
- Backend direct access is protected.
- Main tabs load remotely.

## P4 - Schwab Read-Only Sync

### Recommendation

Implement Schwab only after Phase 1 remote access is stable.

Do not add order execution.

Add:

```text
src/core/schwab.py
```

Suggested endpoints:

```text
GET /schwab/status
GET /schwab/accounts
GET /schwab/positions
GET /schwab/transactions
POST /schwab/sync
```

Required environment variables:

```env
SCHWAB_CLIENT_ID=
SCHWAB_CLIENT_SECRET=
SCHWAB_REDIRECT_URI=
SCHWAB_TRADING_ENABLED=false
```

Implementation policy:

- Read-only first.
- Keep CSV fallback.
- Normalize Schwab positions into the same shape expected by existing portfolio code.
- Show data source and last sync timestamp in the UI.
- Never expose Schwab tokens to frontend code.

Acceptance criteria:

- Portfolio can load from CSV when Schwab is not configured.
- Portfolio can load from Schwab when configured.
- No order route exists.
- `SCHWAB_TRADING_ENABLED=false` is the default and documented.

## P5 - Portfolio Provider Abstraction

### Recommendation

Add a small provider boundary before changing the portfolio source.

Suggested design:

```python
class PortfolioProvider:
    def get_positions(self) -> list[dict]:
        ...

class CsvPortfolioProvider(PortfolioProvider):
    ...

class SchwabPortfolioProvider(PortfolioProvider):
    ...
```

Avoid broad refactors. Start by moving only the portfolio-loading logic behind a function or simple class.

Provider order:

```text
Phase 1: CSV
Phase 1.5: Schwab with CSV fallback
Phase 2: Database with Schwab sync
```

Acceptance criteria:

- Existing `/portfolio` response shape remains stable.
- Existing frontend does not require major changes.
- Provider choice can be controlled by environment variable.

## P6 - Durable State

### Recommendation

Move durable data to Postgres only after remote access and Schwab sync are working.

Target:

```text
Supabase Postgres or Neon Postgres
```

Move these first:

```text
policy.json
thesis.json
portfolio snapshots
decision memos
alert history
```

Keep CSV files as import/export and fallback, not the source of truth.

Acceptance criteria:

- Policy updates survive redeploy.
- Thesis updates survive redeploy.
- Decision memos are retained historically.
- Alert history enables deduplication.

## P7 - Public Reference Mode

### Recommendation

Do not build the public reference version yet.

When ready, add:

```env
APP_MODE=private|demo
```

Demo mode must:

- Use fake/anonymized data.
- Disable write endpoints.
- Hide account values.
- Avoid real holdings, quantities, cost basis, thesis notes, and account metadata.

Acceptance criteria:

- Public URL contains no real personal financial data.
- Private app remains separate and authenticated.

## Harness Recommendation

### If "Harness" means the Harness CI/CD platform

Not yet.

Harness is a capable DevOps platform with CI, CD/GitOps, secrets, RBAC, connectors, policy-as-code, and pipeline automation. Its official docs describe the account/organization/project model, RBAC, connectors, delegates, secrets, and pipelines. The pricing page also lists a Free Plan and DevOps modules.

However, for this project right now, Harness is likely overkill.

Reasons:

- Single-developer personal project.
- Small deployment topology: one frontend, one backend, one scheduler.
- Main risk is privacy/security, not deployment complexity.
- Render/GitHub Actions can cover the near-term workflow with less operational overhead.
- More tooling now would slow down the Schwab and persistence work.

Use Harness later if:

- The project becomes multi-environment with staging/production.
- Deployments need approvals, rollbacks, audit trails, and policy gates.
- Infrastructure becomes Kubernetes or multi-cloud.
- More developers or agents work on the platform.
- You want governed CI/CD as a product capability.

Near-term recommendation:

```text
Use GitHub Actions or Render native deploys first.
Reconsider Harness after Phase 2.
```

### If "harness" means a test/deployment harness

Yes, absolutely.

This project should have a lightweight local harness before deployment. It will reduce risk, document operational expectations, and give every future agent/developer one reliable command to run.

Recommended first implementation:

```text
scripts/validate.sh
```

The harness should check:

- Python syntax.
- Node syntax.
- Required env variables in production mode.
- Backend auth behavior.
- Core endpoints.
- Secret leakage patterns.

This is the highest-leverage "harness" for the current stage.

## Recommended Implementation Sequence

1. Create `.env.example`.
2. Create `docs/deployment-runbook.md`.
3. Create `scripts/validate.sh`.
4. Add deployment manifests for the selected host.
5. Deploy backend privately.
6. Deploy frontend privately.
7. Validate remote access.
8. Implement Schwab read-only sync.
9. Add portfolio provider abstraction if not already introduced during Schwab work.
10. Move durable state to Postgres.

## Do Not Do Yet

- Do not migrate to Databricks Apps as the app host.
- Do not add order execution.
- Do not expose the real portfolio publicly.
- Do not rewrite the frontend framework.
- Do not replace the existing Node proxy until the deployment is stable.
- Do not add new data vendors before remote access and Schwab sync are stable.

## Definition of Done for Phase 1

- Private remote URL works.
- Login is required.
- Backend is protected by internal token.
- Main tabs load remotely.
- Scheduler path is documented.
- Secrets are environment-based.
- Local validation harness passes.
- Deployment runbook exists.
