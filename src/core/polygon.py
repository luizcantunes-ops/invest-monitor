from __future__ import annotations
import requests
import pandas as pd
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.config import MASSIVE_KEY, MASSIVE_BASE

BASE = MASSIVE_BASE
KEY  = MASSIVE_KEY


def _get(path: str, params: dict | None = None) -> dict:
    p = {"apiKey": KEY, **(params or {})}
    r = requests.get(f"{BASE}{path}", params=p, timeout=12)
    r.raise_for_status()
    return r.json()


# ── Preços ────────────────────────────────────────────────────────────────────

def get_prev_close(symbol: str) -> dict:
    try:
        d = _get(f"/v2/aggs/ticker/{symbol}/prev")
        results = d.get("results", [])
        if not results:
            return {}
        r = results[0]
        return {
            "symbol": symbol,
            "open":   r.get("o"),
            "high":   r.get("h"),
            "low":    r.get("l"),
            "close":  r.get("c"),
            "volume": r.get("v"),
            "vwap":   r.get("vw"),
            "date":   datetime.fromtimestamp(r["t"] / 1000).strftime("%Y-%m-%d") if r.get("t") else "",
        }
    except Exception:
        return {}


def get_history(symbol: str, days: int = 180) -> pd.DataFrame:
    try:
        end   = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        d = _get(
            f"/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}",
            {"adjusted": "true", "sort": "asc", "limit": 500},
        )
        results = d.get("results", [])
        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)
        df["date"] = pd.to_datetime(df["t"], unit="ms")
        df = df.rename(columns={
            "o": "Open", "h": "High", "l": "Low",
            "c": "Close", "v": "Volume", "vw": "VWAP",
        })
        df = df.set_index("date")[["Open","High","Low","Close","Volume","VWAP"]]
        return df
    except Exception:
        return pd.DataFrame()


# ── Fundamentais ──────────────────────────────────────────────────────────────

def get_financials(symbol: str, timeframe: str = "annual") -> list[dict]:
    try:
        d = _get("/vX/reference/financials", {
            "ticker": symbol,
            "timeframe": timeframe,
            "limit": 4,
            "sort": "period_of_report_date",
            "order": "desc",
        })
        return d.get("results", [])
    except Exception:
        return []


def get_income_statement(symbol: str) -> dict:
    results = get_financials(symbol, "annual")
    if not results:
        return {}

    latest = results[0]
    inc = latest.get("financials", {}).get("income_statement", {})
    prev_inc = results[1].get("financials", {}).get("income_statement", {}) if len(results) > 1 else {}

    def val(d: dict, key: str) -> float | None:
        v = d.get(key, {}).get("value")
        return float(v) if v is not None else None

    rev       = val(inc, "revenues")
    prev_rev  = val(prev_inc, "revenues")
    net       = val(inc, "net_income_loss")
    op_income = val(inc, "operating_income_loss")
    eps       = val(inc, "basic_earnings_per_share")

    rev_growth = ((rev - prev_rev) / abs(prev_rev) * 100) if (rev and prev_rev and prev_rev != 0) else None

    return {
        "period":       latest.get("fiscal_period", ""),
        "end_date":     latest.get("end_date", ""),
        "revenues":     rev,
        "net_income":   net,
        "op_income":    op_income,
        "eps":          eps,
        "rev_growth":   round(rev_growth, 1) if rev_growth is not None else None,
        "net_margin":   round(net / rev * 100, 1) if (net and rev and rev != 0) else None,
        "op_margin":    round(op_income / rev * 100, 1) if (op_income and rev and rev != 0) else None,
    }


def get_balance_sheet(symbol: str) -> dict:
    results = get_financials(symbol, "annual")
    if not results:
        return {}

    latest = results[0]
    bs = latest.get("financials", {}).get("balance_sheet", {})

    def val(key: str) -> float | None:
        v = bs.get(key, {}).get("value")
        return float(v) if v is not None else None

    assets   = val("assets")
    equity   = val("equity")
    liab     = val("liabilities")
    cash     = val("cash")
    debt     = val("long_term_debt") or val("current_portion_of_long_term_debt")

    return {
        "total_assets":   assets,
        "total_equity":   equity,
        "total_liab":     liab,
        "cash":           cash,
        "long_term_debt": debt,
        "debt_to_equity": round(liab / equity, 2) if (liab and equity and equity != 0) else None,
    }


# ── Dividendos ────────────────────────────────────────────────────────────────

def get_dividends(symbol: str, limit: int = 8) -> list[dict]:
    try:
        d = _get("/v3/reference/dividends", {
            "ticker": symbol,
            "limit":  limit,
            "order":  "desc",
            "sort":   "ex_dividend_date",
        })
        return [
            {
                "ex_date":   r.get("ex_dividend_date"),
                "pay_date":  r.get("pay_date"),
                "amount":    r.get("cash_amount"),
                "frequency": r.get("frequency"),
                "type":      r.get("dividend_type"),
            }
            for r in d.get("results", [])
        ]
    except Exception:
        return []


def get_dividend_yield(symbol: str, price: float) -> float | None:
    divs = get_dividends(symbol, 4)
    if not divs or not price:
        return None
    annual = sum(d["amount"] or 0 for d in divs[:4])
    return round(annual / price * 100, 2) if price > 0 else None


# ── Detalhes do ticker ────────────────────────────────────────────────────────

def get_ticker_details(symbol: str) -> dict:
    try:
        d = _get(f"/v3/reference/tickers/{symbol}")
        r = d.get("results", {})
        return {
            "name":         r.get("name"),
            "description":  r.get("description", "")[:300],
            "sector":       r.get("sic_description"),
            "employees":    r.get("total_employees"),
            "list_date":    r.get("list_date"),
            "market_cap":   r.get("market_cap"),
            "homepage":     r.get("homepage_url"),
        }
    except Exception:
        return {}


# ── News ──────────────────────────────────────────────────────────────────────

def get_news(symbol: str, limit: int = 5) -> list[dict]:
    try:
        d = _get("/v2/reference/news", {"ticker": symbol, "limit": limit, "sort": "published_utc", "order": "desc"})
        return [
            {
                "title":     r.get("title"),
                "published": r.get("published_utc", "")[:10],
                "source":    r.get("publisher", {}).get("name"),
                "url":       r.get("article_url"),
                "sentiment": r.get("insights", [{}])[0].get("sentiment") if r.get("insights") else None,
            }
            for r in d.get("results", [])
        ]
    except Exception:
        return []


# ── Market status ─────────────────────────────────────────────────────────────

def get_market_status() -> dict:
    try:
        d = _get("/v1/marketstatus/now")
        return {
            "market":    d.get("market"),
            "exchanges": d.get("exchanges", {}),
            "after_hrs": d.get("afterHours"),
            "early_hrs": d.get("earlyHours"),
        }
    except Exception:
        return {}


# ── Enriquecimento completo por ativo ─────────────────────────────────────────

def get_full_enrichment(symbol: str) -> dict:
    income  = get_income_statement(symbol)
    balance = get_balance_sheet(symbol)
    price_d = get_prev_close(symbol)
    details = get_ticker_details(symbol)
    divs    = get_dividends(symbol, 4)
    news    = get_news(symbol, 3)

    price = price_d.get("close") or 0
    div_yield = get_dividend_yield(symbol, price) if divs else None

    return {
        "income":    income,
        "balance":   balance,
        "price":     price_d,
        "details":   details,
        "dividends": divs,
        "div_yield": div_yield,
        "news":      news,
    }
