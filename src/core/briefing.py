"""Daily briefing — aggregates portfolio state into action/watch/ok buckets."""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import yfinance as yf
from datetime import datetime, date


def _earnings_days(ticker_obj) -> int | None:
    try:
        cal = ticker_obj.calendar
        if not cal:
            return None
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date")
            if isinstance(ed, list):
                ed = ed[0]
            if ed:
                if hasattr(ed, "date"):
                    ed = ed.date()
                return max((ed - date.today()).days, 0)
    except Exception:
        pass
    return None


def get_briefing(portfolio_csv: str) -> dict:
    df = pd.read_csv(portfolio_csv)
    symbols = df["symbol"].tolist()

    # ── Batch price download ──────────────────────────────────────────────────
    raw = yf.download(symbols + ["SPY"], period="5d", progress=False,
                      auto_adjust=True)
    closes = raw["Close"]

    prices: dict[str, float]   = {}
    day_chg: dict[str, float]  = {}
    spy_chg = 0.0

    for sym in closes.columns:
        series = closes[sym].dropna()
        if len(series) >= 2:
            prev  = float(series.iloc[-2])
            today = float(series.iloc[-1])
            chg   = (today - prev) / prev * 100 if prev else 0
            if sym == "SPY":
                spy_chg = round(chg, 2)
            else:
                prices[sym]  = round(today, 2)
                day_chg[sym] = round(chg, 2)
        elif len(series) == 1:
            prices[sym]  = round(float(series.iloc[-1]), 2)
            day_chg[sym] = 0.0

    # ── Per-position analysis ─────────────────────────────────────────────────
    needs_action: list[dict] = []
    watch:        list[dict] = []
    ok:           list[dict] = []

    for _, row in df.iterrows():
        sym         = row["symbol"]
        horizon     = row.get("horizon", "swing")
        sector      = row.get("sector", "")
        qty         = float(row.get("qty", 0))
        cost        = float(row.get("cost_basis", 0))
        price       = prices.get(sym, 0.0)
        chg         = day_chg.get(sym, 0.0)
        mkt_val     = price * qty
        gain_pct    = (mkt_val - cost) / cost * 100 if cost else 0
        gain_usd    = mkt_val - cost

        # Earnings check
        try:
            t = yf.Ticker(sym)
            earn_days = _earnings_days(t)
        except Exception:
            earn_days = None

        alerts: list[str] = []
        category = "ok"

        # ── Blockers that force action ────────────────────────────────────────
        if earn_days is not None and earn_days <= 3:
            alerts.append(f"Earnings em {earn_days}d — decidir antes")
            category = "needs_action"

        if horizon == "swing" and gain_pct < -25:
            alerts.append(f"Posição {gain_pct:.0f}% — tese enfraquecida")
            category = "needs_action"

        if horizon == "long" and gain_pct < -20:
            alerts.append(f"Posição {gain_pct:.0f}% desde entrada")
            if category != "needs_action":
                category = "watch"

        # ── Watch conditions ──────────────────────────────────────────────────
        if category == "ok":
            if abs(chg) >= 3.5:
                alerts.append(f"Movimento de {chg:+.1f}% hoje")
                category = "watch"
            elif earn_days is not None and earn_days <= 10:
                alerts.append(f"Earnings em {earn_days}d")
                category = "watch"
            elif horizon == "swing" and gain_pct < -15:
                alerts.append(f"Posição {gain_pct:.0f}% — monitorar")
                category = "watch"

        entry = {
            "symbol":    sym,
            "horizon":   horizon,
            "sector":    sector,
            "price":     price,
            "day_chg":   chg,
            "gain_pct":  round(gain_pct, 1),
            "gain_usd":  round(gain_usd, 0),
            "mkt_val":   round(mkt_val, 0),
            "earn_days": earn_days,
            "alerts":    alerts,
        }

        if category == "needs_action":
            needs_action.append(entry)
        elif category == "watch":
            watch.append(entry)
        else:
            ok.append(entry)

    # Sort by severity
    needs_action.sort(key=lambda x: (x["earn_days"] if x["earn_days"] is not None else 999,
                                      x["gain_pct"]))
    watch.sort(key=lambda x: abs(x["day_chg"]), reverse=True)

    # ── Portfolio totals ──────────────────────────────────────────────────────
    all_pos = needs_action + watch + ok
    total_cost  = sum(float(r.get("cost_basis", 0)) for _, r in df.iterrows())
    total_mkt   = sum(p["mkt_val"] for p in all_pos)
    total_gain  = total_mkt - total_cost
    total_gain_pct = total_gain / total_cost * 100 if total_cost else 0

    # Sector concentration
    sectors: dict[str, float] = {}
    for p in all_pos:
        s = p["sector"] or "Outros"
        sectors[s] = sectors.get(s, 0) + p["mkt_val"]
    sector_pct = {s: round(v / total_mkt * 100, 1) for s, v in sectors.items() if total_mkt}

    return {
        "date":        date.today().isoformat(),
        "spy_chg":     spy_chg,
        "needs_action": needs_action,
        "watch":        watch,
        "ok":           ok,
        "totals": {
            "cost":      round(total_cost, 0),
            "mkt_val":   round(total_mkt, 0),
            "gain_usd":  round(total_gain, 0),
            "gain_pct":  round(total_gain_pct, 1),
        },
        "sector_concentration": sector_pct,
        "generated_at": datetime.now().isoformat(),
    }
