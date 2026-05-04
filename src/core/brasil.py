"""Centralized Brasil/crypto helper — single source of truth for all consumers."""
from __future__ import annotations
import os
import pandas as pd
from data.config import PORTFOLIO_TOTAL_BR, CRYPTO_BAND_LOW, CRYPTO_BAND_HIGH

_DEFAULT_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "portfolio_br.csv")


def get_brasil_summary(csv_path: str | None = None) -> dict:
    path = csv_path or _DEFAULT_CSV
    df   = pd.read_csv(path)
    rows = df.to_dict(orient="records")

    crypto_total = sum(
        float(row.get("valor_investido") or 0)
        for row in rows
        if str(row.get("categoria", "")).lower() == "crypto"
    )
    crypto_pct = crypto_total / PORTFOLIO_TOTAL_BR * 100 if PORTFOLIO_TOTAL_BR else 0

    return {
        "total":        PORTFOLIO_TOTAL_BR,
        "crypto_total": round(crypto_total, 2),
        "crypto_pct":   round(crypto_pct, 2),
        "crypto_band":  {"low": CRYPTO_BAND_LOW * 100, "high": CRYPTO_BAND_HIGH * 100},
        "on_target":    CRYPTO_BAND_LOW * 100 <= crypto_pct <= CRYPTO_BAND_HIGH * 100,
        "positions":    rows,
    }
