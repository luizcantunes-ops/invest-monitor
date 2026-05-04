"""Swing trade decision support — score, setup detection, entry/stop/target."""
from __future__ import annotations
import yfinance as yf
import pandas as pd
from datetime import datetime, date


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()

def _sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()

def _rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(n).mean()
    loss  = (-delta.clip(upper=0)).rolling(n).mean()
    rs    = gain / loss
    return 100 - (100 / (1 + rs))

def _atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    hl  = df["High"] - df["Low"]
    hc  = (df["High"] - df["Close"].shift()).abs()
    lc  = (df["Low"]  - df["Close"].shift()).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def _days_to_earnings(ticker_obj) -> int | None:
    try:
        cal = ticker_obj.calendar
        if cal is None:
            return None
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date")
            if isinstance(ed, list):
                ed = ed[0]
            if ed:
                if hasattr(ed, "date"):
                    ed = ed.date()
                return max((ed - date.today()).days, 0)
        return None
    except Exception:
        return None


# ── Main analysis ──────────────────────────────────────────────────────────────

def get_swing_analysis(symbol: str, account_size: float = 742_000) -> dict:
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="14mo", interval="1d")
        if len(df) < 60:
            return {"symbol": symbol, "error": "Dados históricos insuficientes"}

        spy_df = yf.Ticker("SPY").history(period="14mo", interval="1d")

        close  = df["Close"]
        volume = df["Volume"]

        df["ema8"]      = _ema(close, 8)
        df["ema21"]     = _ema(close, 21)
        df["sma50"]     = _sma(close, 50)
        df["sma200"]    = _sma(close, 200)
        df["rsi14"]     = _rsi(close, 14)
        df["atr14"]     = _atr(df, 14)
        df["vol_avg20"] = volume.rolling(20).mean()

        df = df.dropna(subset=["sma200"])
        if len(df) < 5:
            return {"symbol": symbol, "error": "Dados insuficientes para calcular SMA200"}

        last  = df.iloc[-1]
        prev  = df.iloc[-2]
        price = float(last["Close"])

        sma50  = float(last["sma50"])
        sma200 = float(last["sma200"])
        ema21  = float(last["ema21"])
        rsi_val   = round(float(last["rsi14"]), 1)
        atr_val   = float(last["atr14"])
        atr_pct   = round(atr_val / price * 100, 2) if price else 0
        vol_ratio = round(float(last["Volume"]) / float(last["vol_avg20"]), 2) if last["vol_avg20"] else 1.0
        ema21_5d  = float(df["ema21"].iloc[-5]) if len(df) >= 5 else ema21

        # Relative strength vs SPY
        def _rs(n: int) -> float | None:
            try:
                if len(df) < n or len(spy_df) < n:
                    return None
                s_ret = (df["Close"].iloc[-1] / df["Close"].iloc[-n] - 1) * 100
                m_ret = (spy_df["Close"].iloc[-1] / spy_df["Close"].iloc[-n] - 1) * 100
                return round(s_ret - m_ret, 2)
            except Exception:
                return None

        rs_20 = _rs(20)
        rs_50 = _rs(50)

        # SPY regime
        spy_close  = spy_df["Close"].dropna()
        spy_price  = float(spy_close.iloc[-1])
        spy_sma50  = float(spy_close.rolling(50).mean().iloc[-1])
        spy_sma200 = float(spy_close.rolling(200).mean().iloc[-1])
        spy_bull   = spy_price > spy_sma200 and spy_price > spy_sma50
        spy_above_200 = spy_price > spy_sma200

        # Earnings
        days_earn = _days_to_earnings(ticker)
        near_earn = days_earn is not None and days_earn <= 5

        # Trend flags
        above_sma50     = price > sma50
        above_sma200    = price > sma200
        golden_cross    = sma50 > sma200
        ema21_rising    = ema21 > ema21_5d

        # ── Setup detection ────────────────────────────────────────
        setup = entry = stop = target = rr = None

        if above_sma50 and above_sma200 and golden_cross:
            near_support = (last["Low"] <= ema21 * 1.02) or (last["Low"] <= sma50 * 1.02)
            if near_support and 45 <= rsi_val <= 72 and (rs_20 or 0) > -3:
                setup = "Trend Pullback"
                entry = round(price * 1.001, 2)
                stop_a = float(df["Low"].iloc[-3:].min()) * 0.99
                stop_b = sma50 * 0.99
                stop   = round(min(stop_a, stop_b) if last["Low"] <= sma50 * 1.02 else stop_a, 2)
                risk   = entry - stop
                if risk > 0:
                    target = round(entry + risk * 2, 2)
                    rr = 2.0

            elif not setup:
                recent_high = float(df["High"].iloc[-15:].max())
                r15_range   = recent_high - float(df["Low"].iloc[-15:].min())
                tight = r15_range / price < 0.08
                breakout = price >= recent_high * 0.99 and vol_ratio > 1.5
                if tight and breakout and (rs_20 or 0) > 0:
                    setup = "Breakout de Consolidação"
                    entry = round(recent_high * 1.001, 2)
                    stop  = round(float(df["Low"].iloc[-5:].min()) * 0.99, 2)
                    risk  = entry - stop
                    if risk > 0:
                        target = round(entry + risk * 2, 2)
                        rr = 2.0

        elif not above_sma50 and golden_cross:
            recently_above = any(df["Close"].iloc[-10:-1] > df["sma50"].iloc[-10:-1])
            recovering = price > sma50 * 0.98
            if recently_above and recovering and rsi_val > 45 and (rs_20 or 0) > -5:
                setup = "Reclaim SMA50"
                entry = round(sma50 * 1.005, 2)
                stop  = round(sma50 * 0.97, 2)
                risk  = entry - stop
                if risk > 0:
                    target = round(entry + risk * 2, 2)
                    rr = 2.0

        # ── Scoring ────────────────────────────────────────────────
        score = 0
        checklist = []

        # Tendência (20 pts)
        if above_sma50 and above_sma200 and golden_cross and ema21_rising:
            score += 20
            checklist.append({"ok": True, "item": "Tendência — preço > SMA50 > SMA200, EMA21 subindo"})
        elif above_sma200 and golden_cross:
            score += 10
            checklist.append({"ok": "partial", "item": "Tendência — acima SMA200, abaixo SMA50"})
        else:
            checklist.append({"ok": False, "item": "Tendência — estrutura de alta quebrada"})

        # RS 20d (12 pts)
        if rs_20 is not None and rs_20 > 2:
            score += 12
            checklist.append({"ok": True, "item": f"RS vs SPY 20d: {rs_20:+.1f}% — líder de mercado"})
        elif rs_20 is not None and rs_20 > 0:
            score += 6
            checklist.append({"ok": "partial", "item": f"RS vs SPY 20d: {rs_20:+.1f}% — levemente positivo"})
        else:
            checklist.append({"ok": False, "item": f"RS vs SPY 20d: {rs_20:+.1f}%" if rs_20 is not None else "RS 20d: indisponível"})

        # RS 50d (8 pts)
        if rs_50 is not None and rs_50 > 0:
            score += 8
            checklist.append({"ok": True, "item": f"RS vs SPY 50d: {rs_50:+.1f}%"})
        else:
            checklist.append({"ok": False, "item": f"RS vs SPY 50d: {rs_50:+.1f}%" if rs_50 is not None else "RS 50d: indisponível"})

        # Volume (10 pts)
        if vol_ratio >= 1.3:
            score += 10
            checklist.append({"ok": True, "item": f"Volume {vol_ratio:.1f}× média — confirmação forte"})
        elif vol_ratio >= 0.7:
            score += 5
            checklist.append({"ok": "partial", "item": f"Volume {vol_ratio:.1f}× média — neutro"})
        else:
            checklist.append({"ok": False, "item": f"Volume {vol_ratio:.1f}× média — muito fraco"})

        # Setup (20 pts)
        if setup:
            score += 20
            checklist.append({"ok": True, "item": f"Setup: {setup}"})
        else:
            checklist.append({"ok": False, "item": "Nenhum setup técnico identificado"})

        # R:R (10 pts)
        if rr and rr >= 2.0:
            score += 10
            checklist.append({"ok": True, "item": f"Risco/Retorno {rr:.1f}:1"})
        else:
            checklist.append({"ok": False, "item": "R:R < 2:1 — não calculável ou insuficiente"})

        # RSI (10 pts)
        if 50 <= rsi_val <= 65:
            score += 10
            checklist.append({"ok": True, "item": f"RSI {rsi_val} — zona ideal (50–65)"})
        elif 40 <= rsi_val < 72:
            score += 5
            checklist.append({"ok": "partial", "item": f"RSI {rsi_val} — aceitável"})
        else:
            checklist.append({"ok": False, "item": f"RSI {rsi_val} — {'esticado' if rsi_val >= 72 else 'fraco'}"})

        # Earnings (5 pts / -15 penalty)
        if near_earn:
            score -= 15
            checklist.append({"ok": False, "item": f"Earnings em {days_earn} pregões — risco binário"})
        elif days_earn is not None and days_earn <= 15:
            score -= 3
            checklist.append({"ok": "partial", "item": f"Earnings em {days_earn} pregões — atenção"})
        else:
            score += 5
            d_str = f"em {days_earn}d" if days_earn else "não identificado"
            checklist.append({"ok": True, "item": f"Earnings {d_str} — sem risco imediato"})

        # Regime SPY (5 pts / -10 penalty)
        if spy_bull:
            score += 5
            checklist.append({"ok": True, "item": "SPY em bull trend — contexto favorável"})
        elif spy_above_200:
            score += 2
            checklist.append({"ok": "partial", "item": "SPY acima SMA200, mas abaixo SMA50 — cautela"})
        else:
            score -= 10
            checklist.append({"ok": False, "item": "SPY abaixo da SMA200 — bear market, reduzir risco"})

        score = max(0, min(100, score))

        # ── Blockers e decisão ─────────────────────────────────────
        blockers = []
        if not spy_above_200:
            blockers.append("SPY abaixo da SMA200 — bear market")
        if not above_sma200:
            blockers.append(f"{symbol} abaixo da SMA200")
        if near_earn:
            blockers.append(f"Earnings em {days_earn} pregões")
        if not setup:
            blockers.append("Nenhum setup técnico válido")
        if not rr or rr < 2.0:
            blockers.append("R:R abaixo de 2:1")

        if score >= 80 and not blockers:
            decision, decision_color = "SETUP FORTE", "good"
        elif score >= 65 and len(blockers) <= 1:
            decision, decision_color = "MONITORAR", "watch"
        else:
            decision, decision_color = "EVITAR", "bad"

        # ── Position sizing ────────────────────────────────────────
        risk_budget = account_size * 0.005  # 0.5% da conta
        pos_shares = pos_value = None
        if entry and stop and (entry - stop) > 0:
            pos_shares = int(risk_budget / (entry - stop))
            pos_value  = round(pos_shares * entry, 0)

        return {
            "symbol":       symbol,
            "price":        round(price, 2),
            "score":        score,
            "decision":     decision,
            "decision_color": decision_color,
            "setup":        setup,
            "entry":        entry,
            "stop":         stop,
            "target":       target,
            "rr":           rr,
            "rsi":          rsi_val,
            "atr_pct":      atr_pct,
            "vol_ratio":    vol_ratio,
            "rs_20d":       rs_20,
            "rs_50d":       rs_50,
            "above_sma50":  bool(above_sma50),
            "above_sma200": bool(above_sma200),
            "ema21_rising": bool(ema21_rising),
            "days_to_earnings": days_earn,
            "blockers":     blockers,
            "checklist":    checklist,
            "spy_regime":   "bull" if spy_bull else ("pullback" if spy_above_200 else "bear"),
            "position_shares": pos_shares,
            "position_value":  pos_value,
            "risk_per_trade":  round(risk_budget, 0),
            "fetched_at":   datetime.now().isoformat(),
        }

    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


# ── Market sentiment (standalone) ─────────────────────────────────────────────

def get_market_sentiment() -> dict:
    try:
        spy_df = yf.Ticker("SPY").history(period="1y", interval="1d")
        spy_c  = spy_df["Close"].dropna()
        spy_px = float(spy_c.iloc[-1])
        sma50  = float(spy_c.rolling(50).mean().iloc[-1])
        sma200 = float(spy_c.rolling(200).mean().iloc[-1])

        vix = float(yf.Ticker("^VIX").info.get("regularMarketPrice", 0))

        if spy_px > sma200 and spy_px > sma50:
            regime, r_label, r_color = "bull",     "Bull Trend",        "good"
        elif spy_px > sma200:
            regime, r_label, r_color = "pullback", "Pullback — cautela", "watch"
        else:
            regime, r_label, r_color = "bear",     "Bear Trend",        "bad"

        if vix < 15:
            v_label, v_color = "Complacência", "watch"
        elif vix < 20:
            v_label, v_color = "Calmo",        "good"
        elif vix < 30:
            v_label, v_color = "Elevado",      "watch"
        else:
            v_label, v_color = "Estresse",     "bad"

        swing_ok = regime != "bear"

        return {
            "spy_price":  round(spy_px, 2),
            "spy_sma50":  round(sma50, 2),
            "spy_sma200": round(sma200, 2),
            "regime":       regime,
            "regime_label": r_label,
            "regime_color": r_color,
            "vix":        round(vix, 2),
            "vix_label":  v_label,
            "vix_color":  v_color,
            "swing_ok":   swing_ok,
            "swing_note": "Swing trade permitido" if swing_ok else "SPY abaixo SMA200 — evitar novas compras",
            "fetched_at": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}
