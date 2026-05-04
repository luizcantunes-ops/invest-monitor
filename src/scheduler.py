import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron       import CronTrigger
import pandas as pd

from core.fetcher    import get_asset_data, get_macro_data, get_br_asset_data
from core.indicators import calc_rsi, calc_macd, interpret_rsi, interpret_macd
from core.screener   import screen_swing_candidates
from core.brasil     import get_brasil_summary
from alerts.telegram import (alert_technical, alert_screener,
                              alert_crypto_drift, weekly_report)
from data.config     import CRYPTO_TARGET_PCT

scheduler = BlockingScheduler(timezone="America/Sao_Paulo")
portfolio_df = pd.read_csv(os.path.join(os.path.dirname(__file__), "data/portfolio_us.csv"))


def job_technical_alerts():
    print("⚡ Rodando alertas técnicos...")
    for _, row in portfolio_df.iterrows():
        try:
            d    = get_asset_data(row["symbol"])
            hist = d["hist"]
            rsi  = interpret_rsi(calc_rsi(hist))
            macd = interpret_macd(calc_macd(hist))

            rsi_val = calc_rsi(hist)
            macd_raw = calc_macd(hist)

            # Dispara alerta apenas em condições relevantes
            should_alert = (
                (rsi_val is not None and (rsi_val < 35 or rsi_val > 70)) or
                (macd_raw is not None and abs(macd_raw["histogram"]) > 0 and
                 (macd_raw["prev_hist"] < 0) != (macd_raw["histogram"] < 0))
            )

            if should_alert:
                alert_technical(d, rsi, macd, row["horizon"])
                print(f"  📩 Alerta enviado: {row['symbol']}")
        except Exception as e:
            print(f"  Erro em {row['symbol']}: {e}")


def job_screener():
    print("🔍 Rodando screener...")
    portfolio_syms = portfolio_df["symbol"].tolist()
    candidates = screen_swing_candidates(max_results=5, portfolio_symbols=portfolio_syms)
    if candidates:
        alert_screener(candidates)
        print(f"  📩 Screener: {len(candidates)} oportunidades enviadas")


def job_crypto_monitor():
    print("₿ Checando cripto Brasil...")
    try:
        br           = get_brasil_summary()
        crypto_pct   = br["crypto_pct"]
        crypto_total = br["crypto_total"]
        if not br["on_target"]:
            alert_crypto_drift(crypto_pct, CRYPTO_TARGET_PCT * 100, crypto_total)
            print(f"  ⚠️ Alerta cripto: {crypto_pct:.1f}%")
        else:
            print(f"  ✓ Cripto OK: {crypto_pct:.1f}%")
    except Exception as e:
        print(f"  Erro cripto: {e}")


def job_weekly_report():
    print("📊 Gerando relatório semanal...")
    try:
        rows = []
        for _, row in portfolio_df.iterrows():
            d = get_asset_data(row["symbol"])
            mkt = d["price"] * row["qty"]
            rows.append({
                "symbol":     row["symbol"],
                "mkt_val":    mkt,
                "cost_basis": row["cost_basis"],
                "gain_usd":   mkt - row["cost_basis"],
                "gain_pct":   (mkt - row["cost_basis"]) / row["cost_basis"] * 100,
            })
        snap = pd.DataFrame(rows)
        macro      = get_macro_data()
        br         = get_brasil_summary()
        weekly_report(snap, macro, br["crypto_pct"])
        print("  📩 Relatório semanal enviado")
    except Exception as e:
        print(f"  Erro relatório: {e}")


# ── Agenda ────────────────────────────────────────────────────────────────────
# Alertas técnicos: dias úteis às 10h e 15h (horário de SP / mercado NY aberto)
scheduler.add_job(job_technical_alerts, CronTrigger(day_of_week="mon-fri", hour="10,15"), id="technical")

# Screener: dias úteis às 10h30
scheduler.add_job(job_screener, CronTrigger(day_of_week="mon-fri", hour=10, minute=30), id="screener")

# Monitor cripto: diário às 9h
scheduler.add_job(job_crypto_monitor, CronTrigger(hour=9), id="crypto")

# Relatório semanal: segunda-feira às 8h
scheduler.add_job(job_weekly_report, CronTrigger(day_of_week="mon", hour=8), id="weekly")


if __name__ == "__main__":
    print("🚀 Investment Monitor scheduler iniciado")
    print("   Alertas técnicos: seg-sex 10h e 15h")
    print("   Screener:         seg-sex 10h30")
    print("   Monitor cripto:   diário 9h")
    print("   Relatório:        segunda-feira 8h")
    print("   Pressione Ctrl+C para parar\n")
    scheduler.start()
