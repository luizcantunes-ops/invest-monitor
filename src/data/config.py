import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from src/ root (one level up from data/)
load_dotenv(Path(__file__).parent.parent / ".env")

# ── Portfolio constants ───────────────────────────────────────────────────────

PORTFOLIO_TOTAL_BR = 2_579_940.12
CRYPTO_TARGET_PCT  = 0.10
CRYPTO_BAND_LOW    = 0.08
CRYPTO_BAND_HIGH   = 0.12

# ── Macro (updated manually) ──────────────────────────────────────────────────

MACRO_SHILLER_PE  = float(os.getenv("MACRO_SHILLER_PE",  "38.0"))
MACRO_BUFFETT_IND = float(os.getenv("MACRO_BUFFETT_IND", "198.0"))

# ── API keys ──────────────────────────────────────────────────────────────────

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN",   "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

ALPHAVANTAGE_KEY = os.getenv("ALPHAVANTAGE_KEY", "")
FINNHUB_KEY      = os.getenv("FINNHUB_KEY",      "")
MASSIVE_KEY      = os.getenv("MASSIVE_KEY",      "")
MASSIVE_BASE     = os.getenv("MASSIVE_BASE",     "https://api.massive.com")

ALPACA_KEY       = os.getenv("ALPACA_KEY",       "")
ALPACA_SECRET    = os.getenv("ALPACA_SECRET",    "")
ALPACA_BASE_URL  = os.getenv("ALPACA_BASE_URL",  "https://paper-api.alpaca.markets")

INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "")
