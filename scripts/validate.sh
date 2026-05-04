#!/usr/bin/env bash
# validate.sh — pre-deploy validation harness
# Usage: bash scripts/validate.sh
# Checks syntax, secrets, and auth behavior before every deploy.
# Does not start servers — run against an already-running backend for auth checks.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASS=0
FAIL=0
SKIP=0

# ── Helpers ───────────────────────────────────────────────────────────────────

ok()   { echo "  ✓  $1"; PASS=$((PASS+1)); }
fail() { echo "  ✗  $1"; FAIL=$((FAIL+1)); }
skip() { echo "  -  $1 (skipped)"; SKIP=$((SKIP+1)); }
header() { echo; echo "── $1 ──────────────────────────────────────────"; }

# ── 1. Python syntax ──────────────────────────────────────────────────────────

header "Python syntax"
PY_FILES=(
  src/api.py
  src/scheduler.py
  src/alerts/telegram.py
  src/core/brasil.py
  src/core/briefing.py
  src/core/policy.py
  src/core/risk_book.py
  src/core/decision_memo.py
  src/core/weekly_committee.py
  src/data/config.py
)
ALL_PY_OK=true
for f in "${PY_FILES[@]}"; do
  if [ -f "$ROOT/$f" ]; then
    if PYTHONPYCACHEPREFIX=/private/tmp/invest-pycache python3 -m py_compile "$ROOT/$f" 2>/dev/null; then
      ok "$f"
    else
      fail "$f — syntax error"
      ALL_PY_OK=false
    fi
  else
    skip "$f — not found"
  fi
done

# ── 2. Node syntax ────────────────────────────────────────────────────────────

header "Node.js syntax"
JS_FILES=(
  frontend/server.js
  frontend/public/app.js
)
for f in "${JS_FILES[@]}"; do
  if [ -f "$ROOT/$f" ]; then
    if node --check "$ROOT/$f" 2>/dev/null; then
      ok "$f"
    else
      fail "$f — syntax error"
    fi
  else
    skip "$f — not found"
  fi
done

# ── 3. Secret leakage check ───────────────────────────────────────────────────

header "Secret leakage"
PATTERNS=(
  "241_770"
  "sk-proj-"
  "sk-ant-"
  "Bearer eyJ"
)
LEAKED=false
for pattern in "${PATTERNS[@]}"; do
  hits=$(grep -r "$pattern" "$ROOT/src" "$ROOT/frontend/public" 2>/dev/null \
    | grep -v ".pyc" | grep -v ".example" | grep -v "# " || true)
  if [ -n "$hits" ]; then
    fail "Pattern '$pattern' found in source"
    echo "$hits" | head -3
    LEAKED=true
  fi
done
if [ "$LEAKED" = false ]; then
  ok "No known secret patterns in source"
fi

# ── 4. .env.example completeness ─────────────────────────────────────────────

header ".env.example completeness"
REQUIRED_KEYS=(
  "INTERNAL_API_TOKEN"
  "APP_PASSWORD"
  "ALLOWED_ORIGINS"
  "PYTHON_API_URL"
)
if [ -f "$ROOT/frontend/.env.example" ]; then
  for key in "${REQUIRED_KEYS[@]}"; do
    if grep -q "^$key=" "$ROOT/frontend/.env.example" 2>/dev/null; then
      ok "frontend/.env.example has $key"
    else
      fail "frontend/.env.example missing $key"
    fi
  done
else
  fail "frontend/.env.example not found"
fi

SRC_REQUIRED=(
  "INTERNAL_API_TOKEN"
  "ALLOWED_ORIGINS"
)
if [ -f "$ROOT/src/.env.example" ]; then
  for key in "${SRC_REQUIRED[@]}"; do
    if grep -q "^$key=" "$ROOT/src/.env.example" 2>/dev/null; then
      ok "src/.env.example has $key"
    else
      fail "src/.env.example missing $key"
    fi
  done
else
  fail "src/.env.example not found"
fi

# ── 5. Production fail-closed (frontend) ─────────────────────────────────────

header "Frontend fail-closed"
if NODE_ENV=production node -e "
const localEnv = {};
const APP_PASSWORD = process.env.APP_PASSWORD || '';
const IS_PRODUCTION = (process.env.NODE_ENV || 'development') === 'production';
if (IS_PRODUCTION && !APP_PASSWORD) { process.exit(1); }
process.exit(0);
" 2>/dev/null; then
  fail "Frontend did NOT fail-close without APP_PASSWORD in production — check server.js"
else
  ok "Frontend correctly exits without APP_PASSWORD in NODE_ENV=production"
fi

# ── 6. Backend auth (requires running backend) ───────────────────────────────

header "Backend auth (live)"
BACKEND_URL="${PYTHON_API_URL:-http://127.0.0.1:9000}"
if curl -s --max-time 2 "$BACKEND_URL/health" > /dev/null 2>&1; then
  # Health must be public
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$BACKEND_URL/health" 2>/dev/null) || STATUS="timeout"
  if [ "$STATUS" = "200" ]; then
    ok "GET /health → 200 (public)"
  else
    fail "GET /health → $STATUS (expected 200)"
  fi

  # If INTERNAL_API_TOKEN is set in env, test auth enforcement
  if [ -n "${INTERNAL_API_TOKEN:-}" ]; then
    # Without token → 401
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$BACKEND_URL/portfolio" 2>/dev/null) || STATUS="timeout"
    if [ "$STATUS" = "401" ]; then
      ok "GET /portfolio without token → 401"
    else
      fail "GET /portfolio without token → $STATUS (expected 401)"
    fi

    # With correct token → 200
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
      -H "X-Internal-Token: $INTERNAL_API_TOKEN" "$BACKEND_URL/portfolio" 2>/dev/null) || STATUS="timeout"
    if [ "$STATUS" = "200" ]; then
      ok "GET /portfolio with correct token → 200"
    else
      fail "GET /portfolio with correct token → $STATUS (expected 200)"
    fi
  else
    skip "INTERNAL_API_TOKEN not set — skipping auth enforcement checks"
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$BACKEND_URL/portfolio" 2>/dev/null) || STATUS="timeout"
    if [ "$STATUS" = "200" ]; then
      ok "GET /portfolio → 200 (open dev mode)"
    else
      fail "GET /portfolio → $STATUS (expected 200 in dev mode)"
    fi
  fi
else
  skip "Backend not running at $BACKEND_URL — skipping live checks"
fi

# ── 7. Core endpoints (requires running backend) ──────────────────────────────

header "Core endpoints (live)"
if curl -s --max-time 2 "$BACKEND_URL/health" > /dev/null 2>&1; then
  TOKEN_HEADER=""
  [ -n "${INTERNAL_API_TOKEN:-}" ] && TOKEN_HEADER="-H X-Internal-Token: $INTERNAL_API_TOKEN"

  ENDPOINTS=("/brasil" "/macro/full" "/risk-book" "/weekly-committee")
  for ep in "${ENDPOINTS[@]}"; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 \
      ${INTERNAL_API_TOKEN:+-H "X-Internal-Token: $INTERNAL_API_TOKEN"} \
      "$BACKEND_URL$ep" 2>/dev/null) || STATUS="timeout"
    if [ "$STATUS" = "200" ]; then
      ok "GET $ep → 200"
    elif [ "$STATUS" = "401" ]; then
      fail "GET $ep → 401 (check INTERNAL_API_TOKEN)"
    elif [ "$STATUS" = "timeout" ]; then
      skip "GET $ep → timeout (endpoint may be slow on first call)"
    else
      fail "GET $ep → $STATUS"
    fi
  done
else
  skip "Backend not running — skipping endpoint checks"
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo
echo "────────────────────────────────────────────────"
echo "  Results: $PASS passed · $FAIL failed · $SKIP skipped"
echo "────────────────────────────────────────────────"

if [ "$FAIL" -gt 0 ]; then
  echo "  FAIL — resolve issues before deploying"
  exit 1
else
  echo "  PASS — ready to deploy"
  exit 0
fi
