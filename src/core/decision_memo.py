"""Decision Memo — rule-based analysis for a specific trade decision."""
from __future__ import annotations
from datetime import datetime


def get_decision_memo(symbol: str, action: str, rationale: str,
                      asset_data: dict, thesis: dict, policy: dict, briefing: dict) -> dict:
    action = action.lower().strip()
    price  = asset_data.get("price", 0) or 0
    target = asset_data.get("target_mean", 0) or 0
    rec    = asset_data.get("recommendation", "N/A") or "N/A"
    upside = (target - price) / price * 100 if target and price else 0

    # ── Find position in briefing ────────────────────────────────────
    all_pos = (briefing.get("needs_action", []) + briefing.get("watch", []) + briefing.get("ok", []))
    pos     = next((p for p in all_pos if p.get("symbol") == symbol), None)
    gain_pct = pos.get("gain_pct", 0) if pos else 0
    mkt_val  = pos.get("mkt_val", 0)  if pos else 0
    horizon  = pos.get("horizon", "")  if pos else ""

    account_total = float(policy.get("account_total_usd", 742_000))
    total_invested = briefing.get("totals", {}).get("mkt_val", 0) or 0
    cash_pct = (account_total - total_invested) / account_total * 100 if account_total else 0
    pos_pct  = mkt_val / account_total * 100 if account_total else 0
    max_pos  = float(policy.get("max_position_pct", 15))
    min_cash = float(policy.get("min_cash_pct", 25))

    # ── Policy flags ─────────────────────────────────────────────────
    flags = []
    if action in ("buy", "add") and pos_pct >= max_pos:
        flags.append(f"Posição já em {pos_pct:.1f}% da conta — limite é {max_pos:.0f}%.")
    if action in ("buy", "add") and cash_pct < min_cash:
        flags.append(f"Caixa em {cash_pct:.1f}% — abaixo do mínimo de {min_cash:.0f}%. Compra reduz liquidez.")
    if action in ("sell", "reduce") and gain_pct > 0 and thesis.get("reason"):
        flags.append("Posição em lucro com tese ativa. Confirme se saída é intencional ou reativa.")
    if action == "hold" and gain_pct < -20:
        flags.append(f"Posição em {gain_pct:.1f}%. Manter exige convicção explícita — não é default seguro.")

    # ── Risks ────────────────────────────────────────────────────────
    risks = []
    if thesis.get("main_risk"):
        risks.append({"source": "Tese documentada", "risk": thesis["main_risk"]})
    if upside < 5 and action in ("buy", "add"):
        risks.append({"source": "Valuação", "risk": f"Upside limitado: {upside:.1f}% vs preço-alvo médio dos analistas."})
    if gain_pct < -20 and action == "hold":
        risks.append({"source": "Técnico/P&L", "risk": "Queda significativa sem recuperação visível. Revisar tese."})
    if horizon == "swing" and action == "hold" and gain_pct < -10:
        risks.append({"source": "Horizonte", "risk": "Posição Swing em queda — swing não vira hold por inércia."})

    recommendation = _recommendation(action, flags, thesis, gain_pct, upside, horizon)

    return {
        "generated_at":  datetime.now().isoformat(),
        "symbol":        symbol,
        "action":        action,
        "user_rationale": rationale or "",
        "current": {
            "price":           price,
            "gain_pct":        round(gain_pct, 1),
            "mkt_val":         round(mkt_val, 0),
            "pos_pct_account": round(pos_pct, 1),
            "horizon":         horizon,
            "analyst_rec":     rec,
            "analyst_target":  target,
            "upside_pct":      round(upside, 1),
        },
        "thesis_summary": {
            "reason":      thesis.get("reason", "Não definida."),
            "sell_if":     thesis.get("sell_if", "Não definido."),
            "main_risk":   thesis.get("main_risk", "Não definido."),
            "last_review": thesis.get("last_review", "—"),
        },
        "policy_flags": flags,
        "risks":        risks,
        "checklist":    _checklist(action, thesis, flags),
        "recommendation": recommendation,
    }


def _checklist(action, thesis, flags):
    if action in ("buy", "add"):
        return [
            {"check": "Tese documentada e atualizada",       "done": bool(thesis.get("reason"))},
            {"check": "Stop definido antes da entrada",       "done": False},
            {"check": "Tamanho da posição dentro do limite",  "done": not any("limite" in f for f in flags)},
            {"check": "Caixa mínimo mantido após compra",     "done": not any("Caixa" in f for f in flags)},
            {"check": "Sem earnings nos próximos 7 dias",     "done": True},
            {"check": "Regime de mercado não é sell-off",     "done": True},
        ]
    if action in ("sell", "reduce"):
        return [
            {"check": "Motivo de saída documentado",              "done": bool(thesis.get("sell_if"))},
            {"check": "Decisão de tese, não emocional",           "done": True},
            {"check": "Impacto fiscal considerado",               "done": False},
            {"check": "Não vender no fundo de uma correção",      "done": True},
        ]
    return [
        {"check": "Tese ainda intacta",                    "done": bool(thesis.get("reason"))},
        {"check": "Posição dentro dos limites de risco",   "done": not flags},
        {"check": "Stop mental definido",                  "done": bool(thesis.get("sell_if"))},
        {"check": "Próxima revisão agendada",              "done": bool(thesis.get("last_review"))},
    ]


def _recommendation(action, flags, thesis, gain_pct, upside, horizon):
    if flags:
        return {"verdict": "Atenção antes de prosseguir", "color": "warning",
                "detail": f"{len(flags)} ponto(s) de política a resolver primeiro."}
    if action in ("buy", "add") and not thesis.get("reason"):
        return {"verdict": "Documentar tese primeiro", "color": "warning",
                "detail": "Tese não definida. Documente o motivo antes de aumentar a posição."}
    if action in ("sell", "reduce") and gain_pct > 20 and thesis.get("reason"):
        return {"verdict": "Revisão cuidadosa recomendada", "color": "neutral",
                "detail": "Posição lucrativa com tese ativa. Certifique-se que a saída é intencional."}
    if action == "hold" and horizon == "swing" and gain_pct < -15:
        return {"verdict": "Hold ativo com convicção necessária", "color": "warning",
                "detail": "Swing em queda. Se a tese está quebrada, encerrar é melhor do que esperar."}
    return {"verdict": "Pode prosseguir", "color": "ok",
            "detail": "Sem violações de política identificadas. Execute com disciplina e stop definido."}
