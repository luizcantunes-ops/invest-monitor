"""Policy checker — validates portfolio state against defined investment rules."""
from __future__ import annotations
from datetime import datetime


def check_policy(briefing: dict, policy: dict) -> dict:
    account_total  = float(policy.get("account_total_usd", 742_000))
    max_pos_pct    = float(policy.get("max_position_pct",  15))
    max_sec_pct    = float(policy.get("max_sector_pct",    40))
    min_cash_pct   = float(policy.get("min_cash_pct",      25))
    swing_loss_lim = float(policy.get("swing_max_loss_pct", -25))

    all_pos = (
        briefing.get("needs_action", []) +
        briefing.get("watch",        []) +
        briefing.get("ok",           [])
    )
    total_invested = briefing.get("totals", {}).get("mkt_val", 0) or 1
    sectors        = briefing.get("sector_concentration", {})
    cash_usd       = account_total - total_invested
    cash_pct       = cash_usd / account_total * 100

    violations: list[dict] = []

    # ── Sector concentration ──────────────────────────────────────────────────
    for sector, pct in sectors.items():
        if pct > max_sec_pct:
            delta = pct - max_sec_pct
            violations.append({
                "severity": "high",
                "rule":     "max_sector_pct",
                "title":    f"Concentração em {sector}",
                "detail":   f"{pct:.1f}% da carteira investida — limite é {max_sec_pct:.0f}%.",
                "action":   f"Rebalancear: reduzir {delta:.1f}pp em {sector} ou aumentar exposição em outros setores.",
                "current":  round(pct, 1),
                "limit":    max_sec_pct,
            })

    # ── Individual position size ──────────────────────────────────────────────
    for p in all_pos:
        pos_pct_account  = p["mkt_val"] / account_total * 100
        pos_pct_invested = p["mkt_val"] / total_invested * 100
        if pos_pct_account > max_pos_pct:
            violations.append({
                "severity": "medium",
                "rule":     "max_position_pct",
                "title":    f"{p['symbol']} acima do limite",
                "detail":   f"{pos_pct_account:.1f}% da conta total — limite é {max_pos_pct:.0f}%.",
                "action":   f"Considerar redução parcial em {p['symbol']}.",
                "current":  round(pos_pct_account, 1),
                "limit":    max_pos_pct,
            })

    # ── Swing positions with severe loss ─────────────────────────────────────
    swing_losses = [p for p in all_pos
                    if p.get("horizon") == "swing" and p["gain_pct"] < swing_loss_lim]
    if swing_losses:
        names = ", ".join(p["symbol"] for p in swing_losses)
        worst = min(swing_losses, key=lambda x: x["gain_pct"])
        violations.append({
            "severity": "high",
            "rule":     "swing_max_loss",
            "title":    f"Swing em perda severa ({len(swing_losses)} {'posições' if len(swing_losses) > 1 else 'posição'})",
            "detail":   f"{names} — abaixo de {swing_loss_lim:.0f}%. Pior: {worst['symbol']} em {worst['gain_pct']:.1f}%.",
            "action":   "Revisar tese de cada posição. Se a tese está quebrada, encerrar. Se não, documentar por que mantém.",
            "symbols":  [p["symbol"] for p in swing_losses],
            "current":  round(worst["gain_pct"], 1),
            "limit":    swing_loss_lim,
        })

    # ── Cash below minimum ────────────────────────────────────────────────────
    if cash_pct < min_cash_pct:
        violations.append({
            "severity": "medium",
            "rule":     "min_cash",
            "title":    "Caixa abaixo do mínimo",
            "detail":   f"Caixa estimado em {cash_pct:.1f}% da conta — mínimo é {min_cash_pct:.0f}%.",
            "action":   "Considerar redução de posições táticas ou aguardar liquidez natural.",
            "current":  round(cash_pct, 1),
            "limit":    min_cash_pct,
        })

    # ── OK if no violations ───────────────────────────────────────────────────
    summary = "ok" if not violations else (
        "critical" if any(v["severity"] == "high" for v in violations) else "warning"
    )

    return {
        "status":     summary,
        "violations": violations,
        "stats": {
            "cash_usd":   round(cash_usd, 0),
            "cash_pct":   round(cash_pct, 1),
            "invested":   round(total_invested, 0),
            "account":    account_total,
        },
        "checked_at": datetime.now().isoformat(),
    }
