"""Risk Book — portfolio risk metrics and policy compliance snapshot."""
from __future__ import annotations
from datetime import datetime


def get_risk_book(briefing: dict, policy: dict, br_data: dict | None = None) -> dict:
    all_pos = (
        briefing.get("needs_action", []) +
        briefing.get("watch", []) +
        briefing.get("ok", [])
    )

    account_total  = float(policy.get("account_total_usd", 742_000))
    total_invested = briefing.get("totals", {}).get("mkt_val", 0) or 0
    cash_usd       = account_total - total_invested
    cash_pct       = cash_usd / account_total * 100 if account_total else 0

    # ── Exposure by horizon ──────────────────────────────────────────
    long_val  = sum(p["mkt_val"] for p in all_pos if p.get("horizon") == "long")
    swing_val = sum(p["mkt_val"] for p in all_pos if p.get("horizon") == "swing")
    long_pct  = long_val  / account_total * 100 if account_total else 0
    swing_pct = swing_val / account_total * 100 if account_total else 0

    # ── Top 5 positions ──────────────────────────────────────────────
    sorted_pos = sorted(all_pos, key=lambda p: p["mkt_val"], reverse=True)
    top5       = sorted_pos[:5]
    top5_val   = sum(p["mkt_val"] for p in top5)
    top5_pct   = top5_val / total_invested * 100 if total_invested else 0

    # ── US vs BR ─────────────────────────────────────────────────────
    br_total       = float((br_data or {}).get("total", 0))
    total_portfolio = total_invested + br_total
    us_pct = total_invested / total_portfolio * 100 if total_portfolio else 0
    br_pct = br_total       / total_portfolio * 100 if total_portfolio else 0

    # ── Crypto BR ───────────────────────────────────────────────────
    crypto_pct_br = float((br_data or {}).get("crypto_pct", 0))
    crypto_band   = (br_data or {}).get("crypto_band", {"low": 8, "high": 12})

    # ── Policy check ────────────────────────────────────────────────
    from core.policy import check_policy
    policy_check = check_policy(briefing, policy)

    # ── Positions at risk / near target ─────────────────────────────
    swing_at_risk = [p for p in all_pos if p.get("horizon") == "swing" and p.get("gain_pct", 0) < -15]
    near_target   = [p for p in all_pos if p.get("gain_pct", 0) > 20]

    alerts = _build_alerts(policy, briefing.get("sector_concentration", {}), cash_pct, crypto_pct_br, crypto_band, top5_pct)

    return {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "account_total":  account_total,
            "total_invested": round(total_invested, 0),
            "cash_usd":       round(cash_usd, 0),
            "cash_pct":       round(cash_pct, 1),
            "positions":      len(all_pos),
        },
        "exposure": {
            "long_usd":  round(long_val, 0),
            "long_pct":  round(long_pct, 1),
            "swing_usd": round(swing_val, 0),
            "swing_pct": round(swing_pct, 1),
            "us_pct":    round(us_pct, 1),
            "br_pct":    round(br_pct, 1),
        },
        "sectors": briefing.get("sector_concentration", {}),
        "top5": [
            {
                "symbol":      p["symbol"],
                "mkt_val":     round(p["mkt_val"], 0),
                "pct_account": round(p["mkt_val"] / account_total * 100, 1),
                "gain_pct":    round(p.get("gain_pct", 0), 1),
                "horizon":     p.get("horizon", ""),
            }
            for p in top5
        ],
        "top5_concentration": round(top5_pct, 1),
        "crypto_br": {
            "pct":       crypto_pct_br,
            "band":      crypto_band,
            "on_target": crypto_band["low"] <= crypto_pct_br <= crypto_band["high"] if crypto_pct_br else None,
        },
        "swing_at_risk": [{"symbol": p["symbol"], "gain_pct": round(p["gain_pct"], 1)} for p in swing_at_risk],
        "near_target":   [{"symbol": p["symbol"], "gain_pct": round(p["gain_pct"], 1)} for p in near_target],
        "alerts":           alerts,
        "policy_status":     policy_check["status"],
        "policy_violations": policy_check["violations"],
        "recommendations":   _recommendations(alerts, policy_check["violations"], swing_at_risk, near_target, cash_pct),
    }


def _build_alerts(policy, sectors, cash_pct, crypto_pct_br, crypto_band, top5_pct):
    alerts = []
    max_sec  = float(policy.get("max_sector_pct", 40))
    min_cash = float(policy.get("min_cash_pct", 25))

    for sec, pct in sectors.items():
        if pct > max_sec:
            alerts.append({"level": "high", "area": "Setor", "message": f"{sec}: {pct:.1f}% do investido — limite {max_sec:.0f}%"})

    if cash_pct < min_cash:
        alerts.append({"level": "medium", "area": "Caixa", "message": f"Caixa em {cash_pct:.1f}% da conta — mínimo {min_cash:.0f}%"})

    if crypto_pct_br and not (crypto_band["low"] <= crypto_pct_br <= crypto_band["high"]):
        direction = "acima" if crypto_pct_br > crypto_band["high"] else "abaixo"
        alerts.append({"level": "medium", "area": "Cripto BR",
                        "message": f"Cripto BR em {crypto_pct_br:.1f}% — {direction} da faixa {crypto_band['low']:.0f}%–{crypto_band['high']:.0f}%"})

    if top5_pct > 60:
        alerts.append({"level": "medium", "area": "Concentração", "message": f"Top 5 posições = {top5_pct:.1f}% do portfólio investido"})

    return alerts


def _recommendations(alerts, violations, swing_at_risk, near_target, cash_pct):
    recs = []

    if not alerts and not violations and not swing_at_risk:
        return [{"priority": "low", "action": "Manter posições",
                 "rationale": "Carteira dentro dos limites. Nenhuma ação necessária agora."}]

    for v in violations:
        if v.get("severity") == "high":
            recs.append({"priority": "high", "action": v.get("title", "Revisar"), "rationale": v.get("action", "")})

    for p in swing_at_risk:
        recs.append({"priority": "high", "action": f"Revisar tese de {p['symbol']}",
                     "rationale": f"Swing em {p['gain_pct']:.1f}%. Verificar se tese ainda é válida ou encerrar."})

    for p in near_target[:3]:
        recs.append({"priority": "medium", "action": f"Avaliar realização parcial em {p['symbol']}",
                     "rationale": f"+{p['gain_pct']:.1f}% — proteger lucro ou aguardar confirmação de continuidade."})

    if cash_pct < 20:
        recs.append({"priority": "medium", "action": "Aumentar liquidez",
                     "rationale": f"Caixa em {cash_pct:.1f}%. Reduzir exposição tática para manter flexibilidade."})

    return recs
