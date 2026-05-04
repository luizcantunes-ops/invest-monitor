from __future__ import annotations
import yfinance as yf
import pandas as pd
import ta
from core.indicators import calc_rsi, calc_macd, interpret_rsi, interpret_macd

UNIVERSE = [
    # Mega-cap tech
    "AAPL","MSFT","GOOG","GOOGL","AMZN","NVDA","META","TSLA","AVGO","ORCL",
    # Semis
    "AMD","QCOM","MU","AMAT","LRCX","KLAC","MRVL","ARM","INTC","TXN",
    # Cloud / SaaS
    "CRM","SNOW","DDOG","MDB","HUBS","WDAY","VEEV","NOW","PAYC","PCVX",
    "ZS","CRWD","PANW","NET","OKTA","GTLB","BILL","AFRM","ADBE","INTU",
    # Consumer tech / platforms
    "TTD","APP","RBLX","U","LYFT","UBER","ABNB","BKNG","EXPE",
    # AI / data
    "PLTR","AI","BBAI","SOUN","IONQ","IBM","DELL","HPE","SMCI",
    # Healthcare
    "AMGN","GILD","REGN","VRTX","ABBV","LLY","PFE","JNJ","TMO","DHR",
    "ISRG","BSX","EW","DXCM","PODD","MRNA","BNTX",
    # Financials
    "JPM","GS","MS","V","MA","AXP","PYPL","COIN","COF","BX","KKR",
    # Energy / infra
    "XOM","CVX","COP","OXY","SLB","NEE","CEG","VST","TLN","FSLR","ENPH",
    # Consumer / retail
    "WMT","COST","TGT","HD","LOW","NKE","LULU","CELH","MNST","ELF",
    # Industrials / defense
    "HON","CAT","DE","LMT","RTX","NOC","GE","ETN","CARR","TT",
    # Communications
    "DIS","NFLX","SPOT","WBD","PARA","T","VZ","CHTR",
    # Real estate / REITs
    "PLD","AMT","EQIX","CCI","WELL","O",
]

UNIVERSE = list(dict.fromkeys(UNIVERSE))


def screen_swing_candidates(
    max_results: int = 20,
    portfolio_symbols: list[str] | None = None,
) -> list[dict]:
    exclude   = set(portfolio_symbols or [])
    candidates = []

    for symbol in UNIVERSE:
        if symbol in exclude:
            continue
        try:
            t    = yf.Ticker(symbol)
            info = t.info or {}
            hist = t.history(period="3mo")

            if hist is None or len(hist) < 30:
                continue

            rsi_val  = calc_rsi(hist)
            macd_raw = calc_macd(hist)
            score    = _score_combined(info, rsi_val, macd_raw, hist)

            if score["total"] < 4:
                continue

            price  = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            target = info.get("targetMeanPrice", 0)
            upside = ((target - price) / price * 100) if (price and target) else 0

            margin    = info.get("ebitdaMargins")
            ev_ebitda = info.get("enterpriseToEbitda")
            rev_g     = info.get("revenueGrowth")
            earn_g    = info.get("earningsGrowth")

            candidates.append({
                "symbol":      symbol,
                "name":        info.get("shortName", symbol),
                "price":       price,
                "target":      target,
                "upside":      round(upside, 1),
                "rec":         info.get("recommendationKey", "n/a").upper().replace("_"," "),
                "n_analysts":  info.get("numberOfAnalystOpinions", 0),
                "pe_forward":  info.get("forwardPE"),
                "margin":      round(margin * 100, 1) if margin else None,
                "ev_ebitda":   round(ev_ebitda, 1) if ev_ebitda and ev_ebitda > 0 else None,
                "rev_growth":  round(rev_g * 100, 1) if rev_g else None,
                "earn_growth": round(earn_g * 100, 1) if earn_g else None,
                "week52_high": info.get("fiftyTwoWeekHigh", 0),
                "week52_low":  info.get("fiftyTwoWeekLow", 0),
                "beta":        info.get("beta"),
                "rsi":         interpret_rsi(rsi_val),
                "macd":        interpret_macd(macd_raw),
                "score":       score["total"],
                "score_label": score["label"],
                "reasons":     score["reasons"],
            })
        except Exception:
            continue

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:max_results]


def _score_combined(info: dict, rsi_val, macd_raw, hist: pd.DataFrame) -> dict:
    pts     = 0
    reasons = []

    price  = info.get("currentPrice") or info.get("regularMarketPrice", 0)
    target = info.get("targetMeanPrice", 0)

    # ── Upside para preço-alvo ────────────────────────────────────────────────
    if price and target:
        upside = (target - price) / price * 100
        if upside > 35:
            pts += 5
            reasons.append(f"Upside {upside:.1f}% até preço-alvo dos analistas")
        elif upside > 25:
            pts += 4
            reasons.append(f"Upside {upside:.1f}% até preço-alvo")
        elif upside > 15:
            pts += 2
            reasons.append(f"Upside {upside:.1f}%")
        elif upside > 8:
            pts += 1

    # ── Consenso de analistas ─────────────────────────────────────────────────
    rec = info.get("recommendationKey", "").lower()
    if rec == "strong_buy":
        pts += 4
        reasons.append("Analistas: Compra Forte")
    elif rec == "buy":
        pts += 3
        reasons.append("Analistas: Compra")
    elif rec == "hold":
        pts += 0
    elif rec in ("sell", "strong_sell"):
        pts -= 2

    # ── Margem EBITDA ─────────────────────────────────────────────────────────
    margin = info.get("ebitdaMargins", 0) or 0
    if margin > 0.35:
        pts += 3
        reasons.append(f"Margem EBITDA {margin*100:.0f}% — negócio escalável")
    elif margin > 0.20:
        pts += 2
        reasons.append(f"Margem EBITDA {margin*100:.0f}%")
    elif margin > 0.10:
        pts += 1

    # ── EV/EBITDA ─────────────────────────────────────────────────────────────
    ev_eb = info.get("enterpriseToEbitda", 0) or 0
    if 0 < ev_eb < 12:
        pts += 3
        reasons.append(f"EV/EBITDA {ev_eb:.1f}x — abaixo da média de mercado")
    elif 12 <= ev_eb < 20:
        pts += 2
        reasons.append(f"EV/EBITDA {ev_eb:.1f}x — razoável")
    elif 20 <= ev_eb < 30:
        pts += 1

    # ── Crescimento de receita ────────────────────────────────────────────────
    rev_g = info.get("revenueGrowth", 0) or 0
    if rev_g > 0.30:
        pts += 3
        reasons.append(f"Receita crescendo {rev_g*100:.0f}% ao ano")
    elif rev_g > 0.15:
        pts += 2
        reasons.append(f"Crescimento de receita {rev_g*100:.0f}%")
    elif rev_g > 0.05:
        pts += 1

    # ── Crescimento de lucro ──────────────────────────────────────────────────
    earn_g = info.get("earningsGrowth", 0) or 0
    if earn_g > 0.30:
        pts += 2
        reasons.append(f"Lucro crescendo {earn_g*100:.0f}%")
    elif earn_g > 0.10:
        pts += 1

    # ── RSI ───────────────────────────────────────────────────────────────────
    if rsi_val is not None:
        if rsi_val < 35:
            pts += 3
            reasons.append("RSI sobrevendido — pressão vendedora excessiva")
        elif rsi_val < 45:
            pts += 1

    # ── MACD ──────────────────────────────────────────────────────────────────
    if macd_raw is not None:
        h, p = macd_raw["histogram"], macd_raw["prev_hist"]
        if p < 0 and h >= 0:
            pts += 3
            reasons.append("MACD cruzamento altista — força compradora retornando")
        elif h > 0 and abs(h) > abs(p):
            pts += 1

    # ── Volume ────────────────────────────────────────────────────────────────
    if len(hist) >= 20:
        avg_vol = hist["Volume"].rolling(20).mean().iloc[-1]
        if hist["Volume"].iloc[-1] > avg_vol * 1.5:
            pts += 1
            reasons.append("Volume acima da média — interesse institucional")

    # ── Proximidade de suporte (MA50) ─────────────────────────────────────────
    if len(hist) >= 50:
        ma50  = hist["Close"].rolling(50).mean().iloc[-1]
        price_now = hist["Close"].iloc[-1]
        if 0.96 <= price_now / ma50 <= 1.04:
            pts += 1
            reasons.append("Próximo da MA50 — zona de suporte")

    label = (
        "🔥 Oportunidade forte"  if pts >= 15 else
        "✅ Setup sólido"        if pts >= 10 else
        "🟡 Potencial moderado"  if pts >= 6  else
        "⚪ Setup fraco"
    )

    return {"total": pts, "label": label, "reasons": reasons}
