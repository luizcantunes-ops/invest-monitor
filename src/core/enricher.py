from __future__ import annotations
import requests
import yfinance as yf
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.config import ALPHAVANTAGE_KEY, FINNHUB_KEY

FH  = f"https://finnhub.io/api/v1"
AV  = "https://www.alphavantage.co/query"
HDR = {"X-Finnhub-Token": FINNHUB_KEY}


# ── Finnhub ───────────────────────────────────────────────────────────────────

def get_news_sentiment(symbol: str) -> dict:
    try:
        r = requests.get(f"{FH}/news-sentiment",
                         params={"symbol": symbol}, headers=HDR, timeout=10)
        d = r.json()
        bull = d.get("sentiment", {}).get("bullishPercent", 0)
        bear = d.get("sentiment", {}).get("bearishPercent", 0)
        score = d.get("companyNewsScore", 0)
        articles = d.get("buzz", {}).get("articlesInLastWeek", 0)

        if score > 0.75:
            label, color = "Muito positivo", "#3a7d52"
        elif score > 0.6:
            label, color = "Positivo", "#3a7d52"
        elif score > 0.4:
            label, color = "Neutro", "#64748b"
        elif score > 0.25:
            label, color = "Levemente negativo", "#b45309"
        else:
            label, color = "Negativo", "#b84040"

        return {
            "score":    round(score, 2),
            "bullish":  round(bull * 100, 1),
            "bearish":  round(bear * 100, 1),
            "articles": articles,
            "label":    label,
            "color":    color,
            "error":    None,
        }
    except Exception as e:
        return {"error": str(e)}


def get_insider_transactions(symbol: str) -> dict:
    try:
        since = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        r = requests.get(f"{FH}/stock/insider-transactions",
                         params={"symbol": symbol, "from": since},
                         headers=HDR, timeout=10)
        data = r.json().get("data", [])

        buys  = [t for t in data if t.get("transactionCode") in ("P", "A") and t.get("change", 0) > 0]
        sells = [t for t in data if t.get("transactionCode") == "S" and t.get("change", 0) < 0]

        buy_val  = sum(abs(t.get("change", 0)) * (t.get("transactionPrice") or 0) for t in buys)
        sell_val = sum(abs(t.get("change", 0)) * (t.get("transactionPrice") or 0) for t in sells)

        if not buys and not sells:
            signal, color = "Sem movimentação recente", "#64748b"
        elif buy_val > sell_val * 1.5:
            signal, color = "Insiders comprando", "#3a7d52"
        elif sell_val > buy_val * 1.5:
            signal, color = "Insiders vendendo", "#b84040"
        else:
            signal, color = "Misto — compras e vendas", "#b45309"

        latest = sorted(data, key=lambda x: x.get("transactionDate",""), reverse=True)[:3]
        summary = []
        for t in latest:
            name  = t.get("name", "Insider")
            chg   = t.get("change", 0)
            code  = t.get("transactionCode", "")
            price = t.get("transactionPrice") or 0
            date  = t.get("transactionDate", "")
            action = "comprou" if chg > 0 else "vendeu"
            summary.append(f"{name} {action} {abs(chg):,} ações @ ${price:.2f} ({date})")

        return {
            "signal":  signal,
            "color":   color,
            "buy_val":  buy_val,
            "sell_val": sell_val,
            "summary":  summary,
            "error":    None,
        }
    except Exception as e:
        return {"error": str(e)}


def get_earnings_surprises(symbol: str) -> dict:
    try:
        r = requests.get(f"{FH}/stock/earnings",
                         params={"symbol": symbol, "limit": 4},
                         headers=HDR, timeout=10)
        data = r.json()
        if not data:
            return {"error": "Sem dados"}

        quarters = []
        for q in data[:4]:
            actual   = q.get("actual")
            estimate = q.get("estimate")
            surprise = q.get("surprisePercent", 0) or 0
            period   = q.get("period", "")
            if actual is None:
                continue
            beat = actual >= (estimate or 0)
            quarters.append({
                "period":   period,
                "actual":   actual,
                "estimate": estimate,
                "surprise": round(surprise, 1),
                "beat":     beat,
            })

        beats = sum(1 for q in quarters if q["beat"])
        if beats == 4:
            trend, color = "Bateu as estimativas nos 4 últimos trimestres", "#3a7d52"
        elif beats >= 3:
            trend, color = f"Bateu em {beats}/4 trimestres", "#3a7d52"
        elif beats >= 2:
            trend, color = f"Bateu em {beats}/4 trimestres", "#b45309"
        else:
            trend, color = f"Perdeu estimativas em {4-beats}/4 trimestres", "#b84040"

        return {
            "quarters": quarters,
            "trend":    trend,
            "color":    color,
            "error":    None,
        }
    except Exception as e:
        return {"error": str(e)}


def get_recommendation_trend(symbol: str) -> dict:
    try:
        r = requests.get(f"{FH}/stock/recommendation",
                         params={"symbol": symbol},
                         headers=HDR, timeout=10)
        data = r.json()
        if not data:
            return {"error": "Sem dados"}

        latest = data[0]
        strong_buy  = latest.get("strongBuy", 0)
        buy         = latest.get("buy", 0)
        hold        = latest.get("hold", 0)
        sell        = latest.get("sell", 0)
        strong_sell = latest.get("strongSell", 0)
        period      = latest.get("period", "")

        total  = strong_buy + buy + hold + sell + strong_sell
        bull_p = (strong_buy + buy) / total * 100 if total else 0
        bear_p = (sell + strong_sell) / total * 100 if total else 0

        if bull_p > 70:
            consensus, color = "Consenso de compra forte", "#3a7d52"
        elif bull_p > 55:
            consensus, color = "Maioria recomenda compra", "#3a7d52"
        elif bear_p > 40:
            consensus, color = "Pressão de venda crescente", "#b84040"
        else:
            consensus, color = "Consenso neutro", "#64748b"

        return {
            "strong_buy":  strong_buy,
            "buy":         buy,
            "hold":        hold,
            "sell":        sell,
            "strong_sell": strong_sell,
            "bull_pct":    round(bull_p, 1),
            "bear_pct":    round(bear_p, 1),
            "consensus":   consensus,
            "color":       color,
            "period":      period,
            "error":       None,
        }
    except Exception as e:
        return {"error": str(e)}


def get_ebitda_metrics(symbol: str) -> dict:
    try:
        t    = yf.Ticker(symbol)
        info = t.info or {}

        ebitda    = info.get("ebitda")
        margin    = info.get("ebitdaMargins")
        ev_ebitda = info.get("enterpriseToEbitda")

        # YoY EBITDA growth via annual financials
        growth = None
        try:
            fin = t.financials
            if fin is not None and not fin.empty:
                ebitda_rows = [r for r in fin.index if "ebitda" in str(r).lower()]
                if ebitda_rows and len(fin.columns) >= 2:
                    curr = float(fin.loc[ebitda_rows[0]].iloc[0])
                    prev = float(fin.loc[ebitda_rows[0]].iloc[1])
                    if prev and prev != 0:
                        growth = (curr - prev) / abs(prev) * 100
        except Exception:
            pass

        def _fmt_ebitda(v):
            if v is None:
                return "—"
            if abs(v) >= 1e9:
                return f"${v/1e9:.1f}B"
            if abs(v) >= 1e6:
                return f"${v/1e6:.0f}M"
            return f"${v:,.0f}"

        def _interpret_margin(m):
            if m is None:
                return "Sem dados", "#64748b"
            if m > 0.40:
                return "Excelente  >40%", "#3a7d52"
            if m > 0.25:
                return "Sólida", "#3a7d52"
            if m > 0.15:
                return "Razoável", "#b45309"
            if m > 0:
                return "Comprimida", "#c2410c"
            return "Negativa — alerta", "#b84040"

        def _interpret_ev(ev):
            if ev is None or ev < 0:
                return "Sem dados", "#64748b"
            if ev < 8:
                return "Barato — cheque por que", "#3a7d52"
            if ev < 15:
                return "Razoável", "#3a7d52"
            if ev < 25:
                return "Premium", "#b45309"
            if ev < 40:
                return "Caro", "#c2410c"
            return "Múltiplo extremo", "#b84040"

        def _interpret_growth(g):
            if g is None:
                return "Sem dados", "#64748b"
            if g > 50:
                return "Explosivo  >50%", "#3a7d52"
            if g > 20:
                return "Forte", "#3a7d52"
            if g > 5:
                return "Positivo", "#b45309"
            if g >= 0:
                return "Estagnado", "#b45309"
            return "Encolhendo — alerta", "#b84040"

        m_label, m_color = _interpret_margin(margin)
        e_label, e_color = _interpret_ev(ev_ebitda)
        g_label, g_color = _interpret_growth(growth)

        return {
            "ebitda":       ebitda,
            "ebitda_fmt":   _fmt_ebitda(ebitda),
            "margin":       margin,
            "margin_pct":   f"{margin*100:.1f}%" if margin is not None else "—",
            "ev_ebitda":    ev_ebitda,
            "ev_fmt":       f"{ev_ebitda:.1f}x" if ev_ebitda and ev_ebitda > 0 else "—",
            "growth":       growth,
            "growth_fmt":   f"{growth:+.1f}%" if growth is not None else "—",
            "margin_label": m_label, "margin_color": m_color,
            "ev_label":     e_label, "ev_color":     e_color,
            "growth_label": g_label, "growth_color": g_color,
            "error":        None,
        }
    except Exception as e:
        return {"error": str(e)}


def get_upcoming_earnings(symbols: list[str]) -> list[dict]:
    try:
        since = datetime.now().strftime("%Y-%m-%d")
        until = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        r = requests.get(f"{FH}/calendar/earnings",
                         params={"from": since, "to": until},
                         headers=HDR, timeout=10)
        data = r.json().get("earningsCalendar", [])
        syms = {s.upper() for s in symbols}
        return [e for e in data if e.get("symbol", "").upper() in syms]
    except Exception:
        return []


def get_economic_calendar() -> list[dict]:
    try:
        since = datetime.now().strftime("%Y-%m-%d")
        until = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        r = requests.get(f"{FH}/calendar/economic",
                         params={"from": since, "to": until},
                         headers=HDR, timeout=10)
        events = r.json().get("economicCalendar", [])
        important = [e for e in events
                     if e.get("impact", "").lower() in ("high", "medium")]
        return sorted(important, key=lambda x: x.get("time", ""))[:15]
    except Exception:
        return []


def get_ticker_enrichment(symbol: str) -> dict:
    return {
        "news":    get_news_sentiment(symbol),
        "insider": get_insider_transactions(symbol),
        "earnings": get_earnings_surprises(symbol),
        "reco":    get_recommendation_trend(symbol),
    }


def get_analyst_full(symbol: str) -> dict:
    """Analyst data: price targets from yfinance + recommendation trend from Finnhub.
    Replaces Yahoo Finance v10 which blocks server-side requests."""
    # Price targets via yfinance (different internal endpoint, not blocked)
    targets = {}
    try:
        t    = yf.Ticker(symbol)
        info = t.info or {}
        targets = {
            "targetMean":   info.get("targetMeanPrice"),
            "targetHigh":   info.get("targetHighPrice"),
            "targetLow":    info.get("targetLowPrice"),
            "targetMedian": info.get("targetMedianPrice"),
            "nAnalysts":    info.get("numberOfAnalystOpinions", 0),
            "recKey":       (info.get("recommendationKey") or "").lower(),
            "recMean":      info.get("recommendationMean"),
        }
    except Exception as e:
        targets = {"error": str(e)}

    # Recommendation trend via Finnhub (free tier, works)
    trend = []
    try:
        r = requests.get(f"{FH}/stock/recommendation",
                         params={"symbol": symbol}, headers=HDR, timeout=10)
        raw = r.json()
        if isinstance(raw, list):
            trend = [
                {
                    "period":    item.get("period", ""),
                    "strongBuy": item.get("strongBuy", 0),
                    "buy":       item.get("buy", 0),
                    "hold":      item.get("hold", 0),
                    "sell":      item.get("sell", 0),
                    "strongSell": item.get("strongSell", 0),
                }
                for item in raw[:4]
            ]
    except Exception:
        pass

    return {
        "symbol":  symbol,
        "source":  "finnhub+yfinance",
        **targets,
        "trend":   trend,
        "upgrades": [],       # Finnhub paid only — omit cleanly
    }


# ── Alpha Vantage ─────────────────────────────────────────────────────────────

def get_sector_performance() -> dict:
    try:
        r = requests.get(AV, params={
            "function": "SECTOR",
            "apikey":   ALPHAVANTAGE_KEY,
        }, timeout=15)
        d = r.json()
        if "Note" in d or "Information" in d:
            return {"error": "Limite diário Alpha Vantage atingido", "sectors": {}}

        today  = d.get("Rank A: Real-Time Performance", {})
        ytd    = d.get("Rank E: Year-to-Date (YTD) Performance", {})
        month  = d.get("Rank C: 1 Month Performance", {})

        sectors = {}
        for name in today:
            sectors[name] = {
                "today": today.get(name, ""),
                "month": month.get(name, ""),
                "ytd":   ytd.get(name, ""),
            }
        return {"sectors": sectors, "error": None}
    except Exception as e:
        return {"sectors": {}, "error": str(e)}


def get_economic_indicator(function: str, interval: str = "monthly") -> list[dict]:
    try:
        r = requests.get(AV, params={
            "function": function,
            "interval": interval,
            "apikey":   ALPHAVANTAGE_KEY,
        }, timeout=15)
        d = r.json()
        if "Note" in d or "Information" in d:
            return []
        data = d.get("data", [])
        return data[:6]
    except Exception:
        return []
