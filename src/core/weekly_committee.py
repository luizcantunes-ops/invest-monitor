"""Weekly Investment Committee — executive summary of portfolio state."""
from __future__ import annotations
from datetime import datetime, date


def get_weekly_committee(briefing: dict, policy_check: dict, br_data: dict | None = None) -> dict:
    all_pos = (briefing.get("needs_action", []) + briefing.get("watch", []) + briefing.get("ok", []))
    totals  = briefing.get("totals", {})

    total_mkt    = totals.get("mkt_val", 0) or 0
    total_gain_pct = totals.get("gain_pct", 0) or 0

    # ── Biggest daily movers ─────────────────────────────────────────
    movers = sorted(all_pos, key=lambda p: abs(p.get("day_chg", 0)), reverse=True)[:5]

    # ── Best / worst by total P&L ────────────────────────────────────
    by_gain  = sorted(all_pos, key=lambda p: p.get("gain_pct", 0))
    worst3   = by_gain[:3]
    best3    = by_gain[-3:][::-1]

    # ── Decisions to review this week ───────────────────────────────
    decisions = []
    for p in all_pos:
        reasons = []
        if p.get("horizon") == "swing" and p.get("gain_pct", 0) < -20:
            reasons.append(f"Swing em {p['gain_pct']:.1f}% — tese pode estar quebrada")
        if p.get("gain_pct", 0) > 25:
            reasons.append(f"+{p['gain_pct']:.1f}% — avaliar realização parcial")
        if p.get("alerts"):
            reasons.extend(p["alerts"][:1])
        if reasons:
            decisions.append({"symbol": p["symbol"], "horizon": p.get("horizon", ""), "reasons": reasons[:2]})

    # ── Policy snapshot ──────────────────────────────────────────────
    violations     = policy_check.get("violations", [])
    high_v         = [v for v in violations if v.get("severity") == "high"]
    policy_status  = policy_check.get("status", "ok")

    # ── Suggested actions ────────────────────────────────────────────
    suggested = []
    for v in high_v:
        suggested.append({"priority": "alta", "action": v.get("title", ""), "detail": v.get("action", "")})
    for d in decisions[:3]:
        suggested.append({"priority": "média", "action": f"Revisar {d['symbol']}", "detail": d["reasons"][0]})
    if not suggested:
        suggested.append({"priority": "baixa", "action": "Manter posições",
                           "detail": "Carteira OK esta semana. Próxima revisão agendada."})

    # ── Posture ──────────────────────────────────────────────────────
    spy_chg = briefing.get("spy_chg", 0) or 0
    if high_v:
        posture = f"{len(high_v)} violação(ões) crítica(s) — priorizar gestão de risco."
        posture_level = "critical"
    elif decisions:
        posture = f"{len(decisions)} posição(ões) a revisar — restante da carteira OK."
        posture_level = "watch"
    else:
        posture = "Carteira dentro da política. Nenhuma ação necessária."
        posture_level = "ok"

    return {
        "generated_at": datetime.now().isoformat(),
        "week_of":      date.today().isoformat(),
        "posture":      posture,
        "posture_level": posture_level,
        "market": {
            "spy_chg": spy_chg,
            "context": ("Alta" if spy_chg > 1 else "Baixa" if spy_chg < -1 else "Lateral"),
        },
        "portfolio": {
            "total_mkt":        round(total_mkt, 0),
            "total_gain_pct":   round(total_gain_pct, 1),
            "positions":        len(all_pos),
            "needs_action":     len(briefing.get("needs_action", [])),
        },
        "best3":  [{"symbol": p["symbol"], "gain_pct": round(p.get("gain_pct", 0), 1)} for p in best3],
        "worst3": [{"symbol": p["symbol"], "gain_pct": round(p.get("gain_pct", 0), 1)} for p in worst3],
        "movers": [{"symbol": p["symbol"], "day_chg": round(p.get("day_chg", 0), 2), "up": p.get("day_chg", 0) >= 0} for p in movers],
        "decisions_to_review": decisions,
        "suggested_actions":   suggested,
        "policy": {
            "status":     policy_status,
            "violations": len(violations),
            "high":       len(high_v),
        },
        "br": {
            "total":       br_data.get("total", 0),
            "crypto_pct":  br_data.get("crypto_pct", 0),
            "on_target":   br_data.get("on_target"),
        } if br_data else None,
    }
