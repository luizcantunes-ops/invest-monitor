import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def _send(text: str) -> bool:
    url  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       text,
        "parse_mode": "HTML",
    }, timeout=10)
    return resp.status_code == 200


# ── Templates ─────────────────────────────────────────────────────────────────

def alert_technical(asset: dict, rsi: dict, macd: dict, horizon: str) -> bool:
    tag   = "📈 SWING" if horizon == "swing" else "🏛 LONG TERM"
    price = asset.get("price", 0)
    sym   = asset.get("symbol", "")
    up    = asset.get("upside_pct", 0)
    tgt   = asset.get("target_mean", 0)
    h52   = asset.get("week52_high", 0)
    l52   = asset.get("week52_low", 0)

    msg = (
        f"{tag} — <b>{sym}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💲 Preço: <b>${price:.2f}</b>\n"
        f"🎯 Fair Price (consenso): ${tgt:.2f}  "
        f"{'▲' if up > 0 else '▼'} {abs(up):.1f}% {'upside' if up > 0 else 'downside'}\n"
        f"📅 52 semanas: ${l52:.2f} ↔ ${h52:.2f}\n"
        f"\n"
        f"{rsi['emoji']} <b>Sentimento:</b> {rsi['label']}\n"
        f"↳ {rsi['action']}\n"
        f"\n"
        f"{macd['emoji']} <b>Força do movimento:</b> {macd['label']}\n"
        f"↳ {macd['action']}\n"
    )
    return _send(msg)


def alert_screener(candidates: list[dict]) -> bool:
    if not candidates:
        return True
    lines = ["🔍 <b>SWING RADAR — Oportunidades externas</b>\n━━━━━━━━━━━━━━━━━━━━"]
    for c in candidates:
        up = ""
        if c.get("target_mean") and c.get("price"):
            pct = (c["target_mean"] - c["price"]) / c["price"] * 100
            up  = f"  🎯 Upside: {pct:.1f}%"
        lines.append(
            f"\n{c['score_label']} <b>{c['symbol']}</b> — {c['name']}\n"
            f"  💲 ${c['price']:.2f}{up}\n"
            f"  {c['rsi']['emoji']} {c['rsi']['label']}\n"
            f"  {c['macd']['emoji']} {c['macd']['label']}\n"
            f"  📊 Analistas: {c['rec']}"
        )
    return _send("\n".join(lines))


def alert_crypto_drift(current_pct: float, target_pct: float, value: float) -> bool:
    direction = "abaixo" if current_pct < target_pct else "acima"
    emoji     = "📉" if current_pct < target_pct else "📈"
    msg = (
        f"{emoji} <b>ALERTA CRIPTO — Brasil</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Posição atual: <b>{current_pct:.1f}%</b> do portfólio\n"
        f"Meta: {target_pct:.0f}%  |  Faixa: 8–12%\n"
        f"Valor: R$ {value:,.0f}\n"
        f"\n"
        f"Portfólio {direction} da faixa alvo.\n"
        f"Considere rebalancear via HASH11."
    )
    return _send(msg)


def weekly_report(snapshot_df, macro: dict, crypto_pct: float) -> bool:
    total_val  = snapshot_df["mkt_val"].sum()
    total_gain = snapshot_df["gain_usd"].sum()
    gain_pct   = total_gain / snapshot_df["cost_basis"].sum() * 100

    winners = snapshot_df.nlargest(3, "gain_pct")[["symbol", "gain_pct"]]
    losers  = snapshot_df.nsmallest(3, "gain_pct")[["symbol", "gain_pct"]]

    win_txt  = "  ".join([f"{r.symbol} {r.gain_pct:+.1f}%" for _, r in winners.iterrows()])
    lose_txt = "  ".join([f"{r.symbol} {r.gain_pct:+.1f}%" for _, r in losers.iterrows()])

    vix_status = "🟢 Calmo" if macro["vix"] < 20 else ("🟡 Tenso" if macro["vix"] < 30 else "🔴 Medo")

    msg = (
        f"📊 <b>RELATÓRIO SEMANAL — Investment Monitor</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"🇺🇸 <b>Carteira EUA (Schwab)</b>\n"
        f"  Valor total: ${total_val:,.0f}\n"
        f"  Ganho acumulado: ${total_gain:,.0f} ({gain_pct:+.1f}%)\n"
        f"  🏆 Melhores: {win_txt}\n"
        f"  ⚠️ Piores: {lose_txt}\n"
        f"\n"
        f"🇧🇷 <b>Carteira Brasil (Itaú)</b>\n"
        f"  Cripto: {crypto_pct:.1f}% do portfólio  "
        f"{'✅' if 8 <= crypto_pct <= 12 else '⚠️ Fora da faixa 8-12%'}\n"
        f"\n"
        f"🌍 <b>Macro</b>\n"
        f"  VIX: {macro['vix']} — {vix_status}\n"
        f"  S&P500: {macro['sp500']:,.0f}\n"
        f"  Yield Curve (10y–3m): {macro['yield_spread']:+.2f}%\n"
        f"  Shiller P/E: 38  ⚠️  |  Buffett Ind: 198%  ⚠️\n"
        f"\n"
        f"<i>Gerado automaticamente — Investment Monitor</i>"
    )
    return _send(msg)


def send_test_message() -> bool:
    return _send(
        "✅ <b>Investment Monitor conectado!</b>\n"
        "Alertas técnicos, screener e relatório semanal estão configurados."
    )
