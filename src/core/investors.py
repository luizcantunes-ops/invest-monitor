from __future__ import annotations
import requests
import pandas as pd
from core.dataroma import get_dataroma_holdings

INVESTORS = {
    "Berkshire Hathaway": {
        "dataroma": "BRK",
        "manager":  "Warren Buffett",
        "style":    "Value / Longo prazo",
        "known_for": "Concentra em poucas empresas excepcionais com vantagem competitiva duradoura. "
                     "Nunca venda o que você não compraria hoje.",
        "emoji": "🏦",
    },
    "Scion Asset Mgmt": {
        "dataroma": "SAM",
        "manager":  "Michael Burry",
        "style":    "Contrarian / Deep value",
        "known_for": "Apostas contrárias ao consenso. Ficou famoso pelo short do mercado "
                     "imobiliário antes de 2008. Usar como alerta de risco narrativo.",
        "emoji": "🔍",
    },
    "Pershing Square": {
        "dataroma": "psc",
        "manager":  "Bill Ackman",
        "style":    "Activist / Concentrado",
        "known_for": "Posições altamente concentradas com influência ativa nas empresas. "
                     "Opera hedge macro com opções em momentos de crise.",
        "emoji": "⚔️",
    },
    "Tiger Global": {
        "dataroma": "TGM",
        "manager":  "Chase Coleman",
        "style":    "Tech / Growth",
        "known_for": "Um dos maiores fundos de tech e growth do mundo. Posições em "
                     "empresas de alto crescimento em tecnologia, software e internet.",
        "emoji": "🐯",
    },
    "Lone Pine Capital": {
        "dataroma": "LPC",
        "manager":  "Stephen Mandel",
        "style":    "Growth equity / Qualidade",
        "known_for": "Foco em empresas de crescimento de alta qualidade. Heavy em tech "
                     "e consumer. Um dos melhores track records de longo prazo em growth.",
        "emoji": "🌲",
    },
    "Viking Global": {
        "dataroma": "vg",
        "manager":  "Andreas Halvorsen",
        "style":    "Long/Short equity / Growth",
        "known_for": "Estilo disciplinado de growth com rigorosa análise fundamental. "
                     "Posições long/short com foco em qualidade e momentum.",
        "emoji": "⚓",
    },
    "Appaloosa Management": {
        "dataroma": "AM",
        "manager":  "David Tepper",
        "style":    "Macro / Distressed / Tech",
        "known_for": "Macro trader com visão de ciclo. Fez fortunas em ativos distressed "
                     "e tem se tornado cada vez mais tech. Bom termômetro de risco sistêmico.",
        "emoji": "🐎",
    },
}

ARK_ETFS = {
    "ARKK": {
        "name":      "ARK Innovation ETF",
        "manager":   "Cathie Wood",
        "known_for": "ETF de inovação disruptiva. Alta concentração em tech, biotech e cripto. "
                     "Alta volatilidade, horizonte longo.",
        "emoji":     "🚀",
        "csv_url":   "https://ark-funds.com/wp-content/uploads/funds-etf-csv/ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv",
    },
}

CHANGE_LABELS = {
    "new":       ("🆕", "Nova posição", "#059669"),
    "increased": ("⬆️",  "Aumentou",    "#059669"),
    "held":      ("→",   "Manteve",     "#6B7280"),
    "reduced":   ("⬇️",  "Reduziu",     "#DC2626"),
    "closed":    ("❌",  "Encerrou",    "#DC2626"),
}


def get_investor_holdings(inv_name: str) -> dict:
    inv = INVESTORS.get(inv_name)
    if not inv:
        return {"error": "Investidor não encontrado"}

    code   = inv.get("dataroma", "")
    result = get_dataroma_holdings(code)
    return {**inv, **result}


def find_overlaps(holdings: pd.DataFrame, user_symbols: list[str]) -> list[str]:
    if holdings is None or holdings.empty:
        return []

    if "ticker" in holdings.columns:
        return [s for s in user_symbols if s in holdings["ticker"].values]

    name_col = "name" if "name" in holdings.columns else None
    if not name_col:
        return []

    overlaps = []
    for sym in user_symbols:
        for hname in holdings[name_col].dropna():
            if sym.lower() in str(hname).lower():
                overlaps.append(sym)
                break
    return list(set(overlaps))


# ── ARK ──────────────────────────────────────────────────────────────────────

def get_ark_holdings(etf: str = "ARKK") -> dict:
    ark = ARK_ETFS.get(etf, ARK_ETFS["ARKK"])
    try:
        url  = f"https://arkfunds.io/api/v2/etf/holdings?symbol={etf}"
        resp = requests.get(url, headers={"User-Agent": "InvestmentMonitor/1.0"}, timeout=20)
        resp.raise_for_status()

        data     = resp.json()
        holdings = data.get("holdings", [])
        date     = data.get("date_to", "N/A")

        if not holdings:
            return {**ark, "error": "Sem holdings retornados", "holdings": pd.DataFrame()}

        df = pd.DataFrame(holdings)[
            ["ticker", "company", "weight", "market_value", "shares", "share_price"]
        ].head(30)
        df = df[df["ticker"].notna() & (df["ticker"].astype(str).str.strip() != "")]

        return {**ark, "as_of": date, "holdings": df, "error": None}
    except Exception as e:
        return {**ark, "error": str(e), "holdings": pd.DataFrame()}
