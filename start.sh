#!/bin/bash
# Writes portfolio data from env vars to files before starting the server.
# Used by Render: data files are sensitive and not in the repo.
set -e

DATA_DIR="$(dirname "$0")/src/data"
mkdir -p "$DATA_DIR"

if [ -n "$DATA_PORTFOLIO_US" ] && [ ! -f "$DATA_DIR/portfolio_us.csv" ]; then
  printf '%s' "$DATA_PORTFOLIO_US" > "$DATA_DIR/portfolio_us.csv"
  echo "Wrote portfolio_us.csv"
fi

if [ -n "$DATA_PORTFOLIO_BR" ] && [ ! -f "$DATA_DIR/portfolio_br.csv" ]; then
  printf '%s' "$DATA_PORTFOLIO_BR" > "$DATA_DIR/portfolio_br.csv"
  echo "Wrote portfolio_br.csv"
fi

if [ -n "$DATA_POLICY" ] && [ ! -f "$DATA_DIR/policy.json" ]; then
  printf '%s' "$DATA_POLICY" > "$DATA_DIR/policy.json"
  echo "Wrote policy.json"
fi

if [ -n "$DATA_THESIS" ] && [ ! -f "$DATA_DIR/thesis.json" ]; then
  printf '%s' "$DATA_THESIS" > "$DATA_DIR/thesis.json"
  echo "Wrote thesis.json"
fi

cd "$(dirname "$0")/src"
exec python3 -m uvicorn api:app --port "${PORT:-9000}" --host 0.0.0.0
