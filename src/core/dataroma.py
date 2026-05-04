from __future__ import annotations
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}
_BASE = "https://www.dataroma.com/m"


def get_dataroma_holdings(code: str) -> dict:
    url = f"{_BASE}/holdings.php?m={code}"
    try:
        r = requests.get(url, headers=_HEADERS, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        as_of = _extract_date(soup)
        table = soup.find("table", {"id": "holdings"}) or soup.find("table")
        if not table:
            return {"error": "Tabela não encontrada no Dataroma", "holdings": pd.DataFrame(), "as_of": as_of}

        rows = table.find_all("tr")[1:]
        holdings = []
        for row in rows:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) < 3:
                continue

            stock_cell = cells[1] if len(cells) > 1 else ""
            m = re.match(r"^([A-Z.\-]+?)-\s*(.+)$", stock_cell)
            if not m:
                continue

            ticker   = m.group(1).strip()
            name     = m.group(2).strip()
            pct      = _parse_float(cells[2]) if len(cells) > 2 else 0.0
            activity = cells[3].strip() if len(cells) > 3 else ""
            shares   = cells[4].strip() if len(cells) > 4 else ""
            change   = _classify_activity(activity)

            holdings.append({
                "ticker":   ticker,
                "name":     name,
                "pct":      pct,
                "activity": activity,
                "change":   change,
                "shares":   shares,
            })

        df = pd.DataFrame(holdings) if holdings else pd.DataFrame()
        return {"as_of": as_of, "holdings": df, "error": None}

    except Exception as e:
        return {"error": str(e), "holdings": pd.DataFrame(), "as_of": ""}


def _extract_date(soup) -> str:
    text = soup.get_text(" ")
    m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text)
    return m.group(1) if m else ""


def _parse_float(s: str) -> float:
    try:
        return float(re.sub(r"[^\d.]", "", s))
    except Exception:
        return 0.0


def _classify_activity(activity: str) -> str:
    a = activity.lower()
    if not a or a in ("-", ""):
        return "held"
    if any(k in a for k in ("add", "buy", "new")):
        return "new"
    if "incr" in a or "increase" in a:
        return "increased"
    if any(k in a for k in ("reduc", "sell", "trim")):
        return "reduced"
    return "held"
