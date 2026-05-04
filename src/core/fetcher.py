from __future__ import annotations
import yfinance as yf
import pandas as pd
from datetime import datetime


def get_asset_data(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    info   = ticker.info or {}

    price       = info.get("currentPrice") or info.get("regularMarketPrice", 0)
    prev_close  = info.get("previousClose", 0)
    day_chg_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0

    week52_high = info.get("fiftyTwoWeekHigh", 0)
    week52_low  = info.get("fiftyTwoWeekLow", 0)
    pct_from_high = ((price - week52_high) / week52_high * 100) if week52_high else 0
    pct_from_low  = ((price - week52_low)  / week52_low  * 100) if week52_low  else 0

    # Fair price: consenso de analistas
    target_mean = info.get("targetMeanPrice", 0)
    target_high = info.get("targetHighPrice", 0)
    target_low  = info.get("targetLowPrice", 0)
    upside = ((target_mean - price) / price * 100) if (target_mean and price) else 0

    # Analistas
    rec = info.get("recommendationKey", "n/a").upper()
    n_analysts = info.get("numberOfAnalystOpinions", 0)

    # Fundamentals
    pe_forward  = info.get("forwardPE", None)
    pe_trailing = info.get("trailingPE", None)
    market_cap  = info.get("marketCap", 0)
    beta        = info.get("beta", None)

    # Stock-based compensation proxy (SBC/Revenue)
    sbc_ratio = _calc_sbc_ratio(ticker)

    hist = ticker.history(period="6mo")

    return {
        "symbol":        symbol,
        "name":          info.get("shortName", symbol),
        "price":         price,
        "prev_close":    prev_close,
        "day_chg_pct":   round(day_chg_pct, 2),
        "week52_high":   week52_high,
        "week52_low":    week52_low,
        "pct_from_high": round(pct_from_high, 1),
        "pct_from_low":  round(pct_from_low, 1),
        "target_mean":   target_mean,
        "target_high":   target_high,
        "target_low":    target_low,
        "upside_pct":    round(upside, 1),
        "recommendation": rec,
        "n_analysts":    n_analysts,
        "pe_forward":    pe_forward,
        "pe_trailing":   pe_trailing,
        "market_cap":    market_cap,
        "beta":          beta,
        "sbc_ratio":     sbc_ratio,
        "hist":          hist,
        "fetched_at":    datetime.now().isoformat(),
    }


def get_portfolio_snapshot(portfolio_csv: str) -> pd.DataFrame:
    df = pd.read_csv(portfolio_csv)
    rows = []
    for _, row in df.iterrows():
        try:
            data = get_asset_data(row["symbol"])
            data["qty"]        = row["qty"]
            data["cost_basis"] = row["cost_basis"]
            data["horizon"]    = row["horizon"]
            data["sector"]     = row["sector"]
            mkt_val            = data["price"] * data["qty"]
            data["mkt_val"]    = round(mkt_val, 2)
            data["gain_usd"]   = round(mkt_val - data["cost_basis"], 2)
            data["gain_pct"]   = round((mkt_val - data["cost_basis"]) / data["cost_basis"] * 100, 2)
            rows.append(data)
        except Exception as e:
            print(f"Erro ao buscar {row['symbol']}: {e}")
    return pd.DataFrame(rows)


def get_macro_data() -> dict:
    vix   = yf.Ticker("^VIX").info.get("regularMarketPrice", 0)
    sp500 = yf.Ticker("^GSPC").info.get("regularMarketPrice", 0)
    tnx   = yf.Ticker("^TNX").info.get("regularMarketPrice", 0)   # 10y yield
    irx   = yf.Ticker("^IRX").info.get("regularMarketPrice", 0)   # 3mo yield
    yield_spread = round(tnx - irx, 2) if (tnx and irx) else None

    return {
        "vix":          round(vix, 2),
        "sp500":        round(sp500, 2),
        "yield_10y":    round(tnx, 2),
        "yield_3m":     round(irx, 2),
        "yield_spread": yield_spread,
        "fetched_at":   datetime.now().isoformat(),
    }


def get_br_asset_data(ticker_sa: str) -> dict:
    symbol = ticker_sa if ticker_sa.endswith(".SA") else f"{ticker_sa}.SA"
    t    = yf.Ticker(symbol)
    info = t.info or {}
    price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
    hist  = t.history(period="6mo")
    return {
        "symbol":  ticker_sa,
        "price":   price,
        "hist":    hist,
        "fetched_at": datetime.now().isoformat(),
    }


def _calc_sbc_ratio(ticker) -> float | None:
    try:
        cf  = ticker.cashflow
        inc = ticker.income_stmt
        if cf is None or inc is None or cf.empty or inc.empty:
            return None
        sbc_row = [r for r in cf.index if "stock" in r.lower() and "compensation" in r.lower()]
        rev_row = [r for r in inc.index if "total" in r.lower() and "revenue" in r.lower()]
        if not sbc_row or not rev_row:
            return None
        sbc = abs(float(cf.loc[sbc_row[0]].iloc[0]))
        rev = abs(float(inc.loc[rev_row[0]].iloc[0]))
        return round(sbc / rev * 100, 2) if rev else None
    except Exception:
        return None
