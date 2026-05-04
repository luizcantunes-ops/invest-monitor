from __future__ import annotations
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, time
import pytz

NY = pytz.timezone("America/New_York")
MARKET_OPEN  = time(9, 30)
OR_END       = time(9, 45)   # Opening Range = first 15 min


# ── Data helpers ──────────────────────────────────────────────────────────────

def _get_today_bars(symbol: str) -> pd.DataFrame:
    df = yf.Ticker(symbol).history(period="1d", interval="1m")
    if df.empty:
        return df
    df.index = df.index.tz_convert(NY)
    return df[["Open", "High", "Low", "Close", "Volume"]]


def _get_hist_bars(symbol: str) -> pd.DataFrame:
    """5 days of 5-min bars for RVOL reference."""
    df = yf.Ticker(symbol).history(period="5d", interval="5m")
    if df.empty:
        return df
    df.index = df.index.tz_convert(NY)
    return df[["Open", "High", "Low", "Close", "Volume"]]


# ── Indicators ────────────────────────────────────────────────────────────────

def calc_vwap(bars: pd.DataFrame) -> float | None:
    if bars.empty:
        return None
    tp  = (bars["High"] + bars["Low"] + bars["Close"]) / 3
    cum = (tp * bars["Volume"]).cumsum()
    vol = bars["Volume"].cumsum()
    vwap_series = cum / vol.replace(0, np.nan)
    last = vwap_series.dropna()
    return float(last.iloc[-1]) if not last.empty else None


def calc_rvol(today_bars: pd.DataFrame, hist_bars: pd.DataFrame) -> float | None:
    if today_bars.empty or hist_bars.empty:
        return None

    # Current session volume (from open to now)
    session = today_bars[today_bars.index.time >= MARKET_OPEN]
    current_vol = float(session["Volume"].sum()) if not session.empty else 0.0
    if current_vol == 0:
        return None

    # Minutes elapsed since open
    now_ny = datetime.now(NY)
    open_dt = now_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    elapsed_min = max(1, (now_ny - open_dt).seconds // 60)

    # Historical average volume at the same elapsed minutes (past 5 days, 5m bars)
    hist_past = hist_bars[hist_bars.index.date < now_ny.date()]
    if hist_past.empty:
        return None

    daily_vols = []
    for date in set(hist_past.index.date):
        day_bars = hist_past[hist_past.index.date == date]
        session_bars = day_bars[day_bars.index.time >= MARKET_OPEN]
        # Slice to same number of 5-min bars as elapsed minutes
        n_bars = max(1, elapsed_min // 5)
        daily_vols.append(float(session_bars["Volume"].iloc[:n_bars].sum()))

    avg_vol = np.mean(daily_vols) if daily_vols else 0
    if avg_vol == 0:
        return None

    return round(current_vol / avg_vol, 2)


def calc_opening_range(bars: pd.DataFrame) -> dict:
    if bars.empty:
        return {"high": None, "low": None, "formed": False}
    or_bars = bars[
        (bars.index.time >= MARKET_OPEN) &
        (bars.index.time < OR_END)
    ]
    if or_bars.empty:
        return {"high": None, "low": None, "formed": False}
    return {
        "high":   float(or_bars["High"].max()),
        "low":    float(or_bars["Low"].min()),
        "formed": datetime.now(NY).time() >= OR_END,
    }


def calc_atr(bars: pd.DataFrame, period: int = 14) -> float | None:
    if len(bars) < period + 1:
        return None
    high  = bars["High"]
    low   = bars["Low"]
    close = bars["Close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - close).abs(),
        (low  - close).abs()
    ], axis=1).max(axis=1)
    return float(tr.iloc[-period:].mean())


def calc_relative_strength(today_bars: pd.DataFrame, spy_bars: pd.DataFrame) -> float | None:
    if today_bars.empty or spy_bars.empty:
        return None
    def _ret(df):
        session = df[df.index.time >= MARKET_OPEN]
        if len(session) < 2:
            return None
        return (float(session["Close"].iloc[-1]) - float(session["Close"].iloc[0])) / float(session["Close"].iloc[0]) * 100
    stock_ret = _ret(today_bars)
    spy_ret   = _ret(spy_bars)
    if stock_ret is None or spy_ret is None:
        return None
    return round(stock_ret - spy_ret, 2)


def calc_gap(today_bars: pd.DataFrame, prev_close: float) -> float | None:
    if today_bars.empty or not prev_close:
        return None
    open_bar = today_bars[today_bars.index.time >= MARKET_OPEN]
    if open_bar.empty:
        return None
    open_price = float(open_bar["Open"].iloc[0])
    return round((open_price - prev_close) / prev_close * 100, 2)


# ── Scoring ───────────────────────────────────────────────────────────────────

def _score_signal(data: dict) -> dict:
    checks = []
    score  = 0

    rvol = data.get("rvol") or 0
    gap  = data.get("gap_pct") or 0
    rs   = data.get("relative_strength") or 0
    vwap = data.get("vwap")
    price = data.get("price") or 0
    or_high = (data.get("opening_range") or {}).get("high")
    or_formed = (data.get("opening_range") or {}).get("formed", False)

    checks.append({"label": "RVOL > 2.0",               "ok": rvol >= 2.0,  "value": f"{rvol:.1f}×" if rvol else "—"})
    checks.append({"label": "Gap 2%–8%",                 "ok": 2 <= gap <= 8, "value": f"{gap:+.1f}%"})
    checks.append({"label": "Preço acima do VWAP",       "ok": bool(vwap and price > vwap), "value": f"${vwap:.2f}" if vwap else "—"})
    checks.append({"label": "Força relativa vs SPY > 0", "ok": rs > 0,       "value": f"{rs:+.2f}%"})
    checks.append({"label": "OR formado (09:45)",         "ok": or_formed,    "value": "Sim" if or_formed else "Aguardando"})

    if or_formed and or_high:
        broke_out = price > or_high
        checks.append({"label": "Rompeu OR High",         "ok": broke_out,    "value": f"${or_high:.2f}"})
        if broke_out: score += 2
    else:
        checks.append({"label": "Rompeu OR High",         "ok": False,        "value": "OR não formado"})

    score += sum(1 for c in checks if c["ok"])
    total  = len(checks)

    if score >= total - 1:
        rating, color = "SETUP",  "#059669"
    elif score >= total // 2:
        rating, color = "WATCH",  "#D97706"
    else:
        rating, color = "EVITAR", "#DC2626"

    return {"rating": rating, "color": color, "score": score, "total": total, "checks": checks}


# ── Serialization helper ──────────────────────────────────────────────────────

def _to_python(obj):
    """Recursively convert numpy types to native Python."""
    if isinstance(obj, dict):
        return {k: _to_python(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_python(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


# ── Main snapshot ─────────────────────────────────────────────────────────────

_SPY_CACHE: dict = {}

def _get_spy_bars() -> pd.DataFrame:
    import time as _time
    now = _time.time()
    if "bars" in _SPY_CACHE and now - _SPY_CACHE.get("ts", 0) < 300:
        return _SPY_CACHE["bars"]
    bars = _get_today_bars("SPY")
    _SPY_CACHE["bars"] = bars
    _SPY_CACHE["ts"]   = now
    return bars


def get_intraday_snapshot(symbol: str, prev_close: float | None = None) -> dict:
    try:
        today   = _get_today_bars(symbol)
        hist    = _get_hist_bars(symbol)
        spy     = _get_spy_bars()

        if today.empty:
            return {"symbol": symbol, "error": "Sem dados intraday"}

        price = float(today["Close"].iloc[-1])

        if not prev_close:
            info = yf.Ticker(symbol).info
            prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")

        vwap    = calc_vwap(today)
        rvol    = calc_rvol(today, hist)
        or_data = calc_opening_range(today)
        atr     = calc_atr(today)
        rs      = calc_relative_strength(today, spy)
        gap     = calc_gap(today, prev_close) if prev_close else None

        spy_price = float(spy["Close"].iloc[-1]) if not spy.empty else None
        spy_vwap  = calc_vwap(spy)
        spy_above_vwap = bool(spy_price and spy_vwap and spy_price > spy_vwap)

        data = {
            "symbol":          symbol,
            "price":           round(price, 2),
            "prev_close":      round(prev_close, 2) if prev_close else None,
            "vwap":            round(vwap, 2) if vwap else None,
            "above_vwap":      bool(vwap and price > vwap),
            "rvol":            rvol,
            "gap_pct":         gap,
            "atr":             round(atr, 2) if atr else None,
            "relative_strength": rs,
            "opening_range":   or_data,
            "spy_above_vwap":  spy_above_vwap,
            "market_regime":   "risk-on" if spy_above_vwap else "risk-off",
            "timestamp":       datetime.now(NY).strftime("%H:%M:%S"),
            "error":           None,
        }

        # Stop and target if OR is formed
        if or_data["formed"] and or_data["high"] and or_data["low"] and vwap and atr:
            stop = min(or_data["low"], vwap, price - atr * 0.8)
            risk = price - stop
            data["trade"] = {
                "entry":   round(or_data["high"], 2),
                "stop":    round(stop, 2),
                "risk":    round(risk, 2),
                "target1": round(or_data["high"] + risk * 1.5, 2),
                "target2": round(or_data["high"] + risk * 2.0, 2),
                "rr":      round(risk * 2 / risk, 1) if risk > 0 else None,
            }

        data["signal"] = _score_signal(data)
        return _to_python(data)

    except Exception as e:
        return {"symbol": symbol, "error": str(e)}
