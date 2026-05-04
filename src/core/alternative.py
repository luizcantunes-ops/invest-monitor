from __future__ import annotations
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

HEADERS_BROWSER = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
HEADERS_BOT = {"User-Agent": "InvestmentMonitor/1.0 contact@personal.com"}

C_SUITE = {"ceo", "cfo", "coo", "cto", "president", "chairman", "dir", "evp", "svp", "vp"}


# ── OpenInsider ───────────────────────────────────────────────────────────────

def get_openinsider_trades(symbol: str) -> dict:
    url = f"http://openinsider.com/{symbol.upper()}"
    try:
        r = requests.get(url, headers=HEADERS_BROWSER, timeout=12)
        r.raise_for_status()
        soup  = BeautifulSoup(r.text, "html.parser")
        table = _find_trade_table(soup)
        if table is None:
            return {"error": "Tabela não encontrada", "trades": [], "signal": "Sem dados", "color": "#64748b"}

        rows   = table.find_all("tr")[1:]
        trades = []
        for row in rows[:60]:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) < 10:
                continue
            trades.append({
                "filing_date": cells[1][:10] if len(cells) > 1 else "",
                "trade_date":  cells[2][:10] if len(cells) > 2 else "",
                "insider":     cells[4]       if len(cells) > 4 else "",
                "title":       cells[5]       if len(cells) > 5 else "",
                "trade_type":  cells[6]       if len(cells) > 6 else "",
                "price":       cells[7]       if len(cells) > 7 else "",
                "qty":         cells[8]       if len(cells) > 8 else "",
                "value":       cells[10]      if len(cells) > 10 else "",
            })

        purchases = [t for t in trades if "P -" in t["trade_type"] or "Purchase" in t["trade_type"]]
        sales     = [t for t in trades if "S -" in t["trade_type"] and "Iss" not in t["trade_type"]]

        # Filter C-suite
        exec_buys = [t for t in purchases if _is_csuite(t["title"])]

        signal, color, emoji = _insider_signal(exec_buys, purchases, sales)

        return {
            "trades":     trades[:10],
            "purchases":  purchases[:6],
            "exec_buys":  exec_buys[:4],
            "sales":      sales[:6],
            "signal":     signal,
            "color":      color,
            "emoji":      emoji,
            "buy_count":  len(purchases),
            "sell_count": len(sales),
            "exec_count": len(exec_buys),
            "error":      None,
        }
    except Exception as e:
        return {"error": str(e), "trades": [], "signal": "Erro", "color": "#64748b", "emoji": "❓"}


def _find_trade_table(soup: BeautifulSoup):
    for t in soup.find_all("table"):
        rows = t.find_all("tr")
        if not rows:
            continue
        header_text = " ".join(td.get_text() for td in rows[0].find_all(["th", "td"]))
        if "Trade" in header_text and "Insider" in header_text and "Price" in header_text:
            return t
    return None


def _is_csuite(title: str) -> bool:
    t = title.lower()
    return any(role in t for role in C_SUITE)


def _insider_signal(exec_buys: list, purchases: list, sales: list) -> tuple:
    nb = len(purchases)
    ns = len(sales)
    ne = len(exec_buys)

    if ne >= 2:
        return "C-suite comprando — sinal forte", "#3a7d52", "🔥"
    if ne == 1:
        return f"Executivo comprou: {exec_buys[0]['title']}", "#3a7d52", "✅"
    if nb > 0 and ns == 0:
        return f"{nb} insider(s) comprando, sem vendas", "#3a7d52", "🟢"
    if nb > ns * 1.5:
        return f"Mais compras ({nb}) que vendas ({ns})", "#3a7d52", "🟡"
    if ns > nb * 2 and ns >= 3:
        return f"Insiders vendendo ({ns} vendas)", "#b84040", "🔴"
    if nb == 0 and ns == 0:
        return "Sem movimentações recentes de insiders", "#64748b", "⚪"
    return f"{nb} compras · {ns} vendas — misto", "#b45309", "🟡"


# ── Reddit / WallStreetBets ───────────────────────────────────────────────────

def get_wsb_sentiment(symbol: str) -> dict:
    try:
        url = (f"https://www.reddit.com/r/wallstreetbets/search.json"
               f"?q={symbol}&sort=relevance&t=week&limit=25&restrict_sr=1")
        r     = requests.get(url, headers=HEADERS_BOT, timeout=10)
        r.raise_for_status()
        posts = r.json().get("data", {}).get("children", [])

        if not posts:
            return {
                "count": 0, "total_score": 0, "avg_ratio": 0,
                "signal": "Sem menções no WSB esta semana",
                "color": "#64748b", "emoji": "⚪", "top_posts": [], "error": None,
            }

        count       = len(posts)
        total_score = sum(p["data"].get("score", 0) for p in posts)
        avg_ratio   = sum(p["data"].get("upvote_ratio", 0.5) for p in posts) / count
        top_posts   = [
            {
                "title": p["data"].get("title", "")[:90],
                "score": p["data"].get("score", 0),
                "url":   f"https://reddit.com{p['data'].get('permalink', '')}",
            }
            for p in sorted(posts, key=lambda x: x["data"].get("score", 0), reverse=True)[:3]
        ]

        signal, color, emoji = _wsb_signal(count, avg_ratio, total_score)

        return {
            "count":       count,
            "total_score": total_score,
            "avg_ratio":   round(avg_ratio, 2),
            "signal":      signal,
            "color":       color,
            "emoji":       emoji,
            "top_posts":   top_posts,
            "error":       None,
        }
    except Exception as e:
        return {"error": str(e), "count": 0, "signal": "Erro", "color": "#64748b", "emoji": "❓"}


def _wsb_signal(count: int, avg_ratio: float, total_score: int) -> tuple:
    if count >= 15 and avg_ratio >= 0.75 and total_score >= 2000:
        return "Euforia no WSB — muito barulho, cuidado com FOMO", "#c2410c", "🔥"
    if count >= 10 and avg_ratio >= 0.7:
        return "Alta tração no WSB — sentimento otimista", "#3a7d52", "📈"
    if count >= 5 and avg_ratio >= 0.65:
        return "Menções positivas no WSB", "#3a7d52", "🟢"
    if count >= 5 and avg_ratio < 0.45:
        return "Sentimento negativo no WSB", "#b84040", "🔴"
    if count >= 3:
        return f"{count} menções neutras no WSB esta semana", "#64748b", "⚪"
    if count > 0:
        return f"{count} menção(ões) pontuais no WSB", "#64748b", "⚪"
    return "Sem menções no WSB esta semana", "#64748b", "⚪"


# ── Combinado ─────────────────────────────────────────────────────────────────

def get_alternative_signals(symbol: str) -> dict:
    return {
        "insider": get_openinsider_trades(symbol),
        "wsb":     get_wsb_sentiment(symbol),
    }
