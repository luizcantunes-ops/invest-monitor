from __future__ import annotations
import ta
import pandas as pd


# ── Macro descriptions ────────────────────────────────────────────────────────

def describe_shiller_pe(value: float) -> dict:
    if value < 15:
        sentiment, emoji, color = "Mercado barato", "🟢", "#3a7d52"
        reading = "Abaixo da média histórica de 17. Historicamente associado a retornos futuros acima da média."
    elif value < 20:
        sentiment, emoji, color = "Precificação neutra", "⚪", "#64748b"
        reading = "Próximo da média histórica de 17. Sem sinal claro de super ou subavaliação."
    elif value < 28:
        sentiment, emoji, color = "Mercado caro", "🟡", "#b45309"
        reading = "Acima da média. Retornos futuros esperados tendem a ser abaixo da média histórica."
    elif value < 36:
        sentiment, emoji, color = "Mercado muito caro", "🟠", "#c2410c"
        reading = f"Nível de euforia. Em {value:.0f}, está acima do pico de 1929 (30). Cautela elevada."
    else:
        sentiment, emoji, color = "Território de bolha", "🔴", "#b84040"
        reading = (f"Em {value:.0f}, só perde para o pico da bolha das .com em 2000 (44). "
                   "O mercado está pagando muito caro por cada dólar de lucro real.")

    return {
        "name":        "Shiller P/E (CAPE Ratio)",
        "what":        ("Mede o preço das ações do S&P500 em relação à média dos lucros reais "
                        "dos últimos 10 anos, ajustados pela inflação. Remove distorções de "
                        "ciclos econômicos para revelar o verdadeiro nível de valorização."),
        "value":       value,
        "avg":         17.0,
        "dotcom_peak": 44.0,
        "1929_peak":   30.0,
        "sentiment":   sentiment,
        "emoji":       emoji,
        "color":       color,
        "reading":     reading,
        "implication": ("Para sua carteira: NVDA, GOOG, META e MSFT negociam acima dos múltiplos "
                        "de mercado. Um P/E agregado tão alto comprime a margem de segurança. "
                        "Seu cash de 35% é a proteção natural."),
    }


def describe_buffett_indicator(value: float) -> dict:
    if value < 80:
        sentiment, emoji, color = "Mercado subavaliado", "🟢", "#3a7d52"
        reading = "Abaixo de 80%: valor de mercado das empresas menor que o PIB. Historicamente raro e ótimo para comprar."
    elif value < 100:
        sentiment, emoji, color = "Precificação razoável", "⚪", "#64748b"
        reading = "Entre 80-100%: mercado próximo do tamanho real da economia."
    elif value < 140:
        sentiment, emoji, color = "Mercado esticado", "🟡", "#b45309"
        reading = "Acima de 100%: capitalização de mercado supera o PIB. Sinal de otimismo excessivo."
    elif value < 180:
        sentiment, emoji, color = "Mercado muito caro", "🟠", "#c2410c"
        reading = "Nível associado a períodos de bolha. O mercado vale muito mais do que a economia produz."
    else:
        sentiment, emoji, color = "Nível histórico extremo", "🔴", "#b84040"
        reading = (f"Em {value:.0f}%, é o 2º maior nível em 100 anos. Parte dessa valorização "
                   "vem de alavancagem — empresas tomando empréstimos para recomprar próprias ações, "
                   "não de crescimento real da economia.")

    return {
        "name":    "Indicador Buffett (Market Cap / PIB)",
        "what":    ("Compara o valor total de mercado de todas as empresas americanas com o PIB dos EUA. "
                    "O próprio Buffett chamou de 'o melhor indicador de valorização do mercado'. "
                    "Quando a distância é extrema, as expectativas de lucro estão descoladas da "
                    "produção real da economia."),
        "value":   value,
        "sentiment": sentiment,
        "emoji":   emoji,
        "color":   color,
        "reading": reading,
        "implication": ("O mercado americano vale quase o dobro do que a economia produz em um ano. "
                        "Isso não significa crash iminente — mas significa que o preço de entrada "
                        "já embute crescimento muito otimista. Margem de erro é baixa."),
    }


def describe_vix_full(value: float) -> dict:
    if value < 15:
        sentiment, emoji, color = "Calmaria — confiança elevada", "😴", "#64748b"
        reading = ("Mercado tranquilo. Opções de proteção (puts) estão baratas. "
                   "Bom momento para comprar hedge, não quando o VIX já explodiu.")
    elif value < 20:
        sentiment, emoji, color = "Volatilidade normal", "😐", "#64748b"
        reading = "Sem sinal de estresse sistêmico. Condições normais de mercado."
    elif value < 30:
        sentiment, emoji, color = "Tensão crescente", "😟", "#b45309"
        reading = ("Investidores ficando nervosos. Reduzir posições especulativas "
                   "e monitorar os swings com atenção.")
    elif value < 40:
        sentiment, emoji, color = "Medo no mercado", "😱", "#c2410c"
        reading = ("Alta volatilidade. Quedas bruscas são comuns. "
                   "Não tome decisões no calor do momento. Evite alavancagem.")
    else:
        sentiment, emoji, color = "Pânico — possível oportunidade histórica", "🔥", "#b84040"
        reading = ("Nível extremo de medo. Historicamente, VIX acima de 40 marca pontos de "
                   "entrada de longo prazo — mas requer liquidez e estômago forte.")

    return {
        "name":      "VIX — Índice de Volatilidade (Fear Index)",
        "what":      ("Mede a volatilidade esperada do S&P500 nos próximos 30 dias, calculada "
                      "a partir do preço das opções. Sobe quando o mercado tem medo, cai quando "
                      "há confiança. Abaixo de 15: calmaria. Acima de 30: estresse. "
                      "Acima de 40: pânico."),
        "value":     value,
        "sentiment": sentiment,
        "emoji":     emoji,
        "color":     color,
        "reading":   reading,
        "implication": ("Se o VIX ultrapassar 30, considere reduzir posições swing para preservar "
                        "capital. Acima de 40, seu cash de 35% no Schwab vira uma vantagem enorme."),
    }


def describe_yield_curve_full(spread: float | None, y10: float, y3m: float) -> dict:
    if spread is None:
        return {
            "name": "Yield Curve (10y – 3m)", "what": "", "value": None,
            "sentiment": "Sem dados", "emoji": "❓", "color": "#64748b",
            "reading": "", "implication": "",
        }

    if spread < -0.5:
        sentiment, emoji, color = "Curva invertida — sinal de recessão", "🔴", "#b84040"
        reading = ("Curva fortemente invertida: títulos curtos rendem mais que os longos. "
                   "O mercado aposta que o Fed vai cortar juros no futuro — sinal de recessão "
                   "esperada. Inversões precederam todas as recessões dos últimos 50 anos, "
                   "com 12-18 meses de antecedência.")
    elif spread < 0:
        sentiment, emoji, color = "Curva levemente invertida", "🟠", "#c2410c"
        reading = ("O mercado precifica desaceleração econômica e espera cortes de juros. "
                   "Atenção, mas não é sinal de alarme imediato.")
    elif spread < 0.5:
        sentiment, emoji, color = "Curva plana — transição", "🟡", "#b45309"
        reading = "Sem sinal claro de expansão ou recessão. Período de transição entre ciclos."
    else:
        sentiment, emoji, color = "Curva normal — expansão econômica", "🟢", "#3a7d52"
        reading = ("Curva saudável: juros longos maiores que curtos. Indica expectativa de "
                   "crescimento econômico e ambiente favorável para risco.")

    return {
        "name":      "Yield Curve (Treasuries 10 anos – 3 meses)",
        "what":      ("Compara o rendimento dos títulos do governo americano de 10 anos com o "
                      "de 3 meses. Quando os títulos curtos rendem mais (curva invertida), o "
                      "mercado está apostando em recessão e cortes de juros futuros. É o "
                      "indicador de recessão mais confiável da história moderna."),
        "value":     spread,
        "y10":       y10,
        "y3m":       y3m,
        "sentiment": sentiment,
        "emoji":     emoji,
        "color":     color,
        "reading":   reading,
        "implication": ("Em recessão, ativos cíclicos e de crescimento (grande parte da carteira "
                        "swing) sofrem mais. MSFT, GOOG e AAPL tendem a se recuperar mais rápido "
                        "por balanços sólidos e forte geração de caixa."),
    }


# ── RSI ──────────────────────────────────────────────────────────────────────

def calc_rsi(hist: pd.DataFrame, period: int = 14) -> float | None:
    if hist is None or len(hist) < period + 1:
        return None
    return round(ta.momentum.RSIIndicator(hist["Close"], window=period).rsi().iloc[-1], 1)


def interpret_rsi(rsi: float | None) -> dict:
    if rsi is None:
        return {"value": None, "emoji": "❓", "label": "Dados insuficientes", "action": "Sem dados para análise."}

    if rsi < 20:
        return {
            "value":  rsi,
            "emoji":  "🔥",
            "label":  "Pânico no mercado",
            "action": "Venda massiva — pode ser oportunidade histórica. Verifique se há motivo estrutural antes de comprar.",
        }
    if rsi < 30:
        return {
            "value":  rsi,
            "emoji":  "🟢",
            "label":  "Sobrevendido — oportunidade potencial",
            "action": "Pressão vendedora excessiva. Bom ponto de entrada se os fundamentos continuam sólidos.",
        }
    if rsi < 40:
        return {
            "value":  rsi,
            "emoji":  "🟡",
            "label":  "Pessimismo — cheque os fundamentos",
            "action": "Mercado desanimado com o ativo. Pode ser oportunidade, mas confirme que a tese não mudou.",
        }
    if rsi < 55:
        return {
            "value":  rsi,
            "emoji":  "⚪",
            "label":  "Neutro",
            "action": "Sem sinal claro de entrada ou saída. Aguarde um extremo para agir.",
        }
    if rsi < 65:
        return {
            "value":  rsi,
            "emoji":  "🔵",
            "label":  "Momentum positivo",
            "action": "Tendência de alta em curso. Posição existente pode ser mantida.",
        }
    if rsi < 75:
        return {
            "value":  rsi,
            "emoji":  "🟠",
            "label":  "Sobrecomprado — cuidado com entrada",
            "action": "Ativo aquecido. Evite comprar agora. Se já tem posição, considere proteger parte do ganho.",
        }
    if rsi < 85:
        return {
            "value":  rsi,
            "emoji":  "🔴",
            "label":  "Euforia — evite comprar",
            "action": "Compradores pagando caro por medo de perder o movimento. Risco de correção elevado.",
        }
    return {
        "value":  rsi,
        "emoji":  "💥",
        "label":  "Euforia extrema",
        "action": "Nível raramente sustentável. Se tem posição grande, é hora de reduzir.",
    }


# ── MACD ─────────────────────────────────────────────────────────────────────

def calc_macd(hist: pd.DataFrame) -> dict | None:
    if hist is None or len(hist) < 35:
        return None
    macd_ind  = ta.trend.MACD(hist["Close"])
    macd_line = macd_ind.macd().iloc[-1]
    signal    = macd_ind.macd_signal().iloc[-1]
    hist_val  = macd_ind.macd_diff().iloc[-1]
    prev_hist = macd_ind.macd_diff().iloc[-2]
    return {
        "macd":      round(macd_line, 4),
        "signal":    round(signal, 4),
        "histogram": round(hist_val, 4),
        "prev_hist": round(prev_hist, 4),
    }


def interpret_macd(macd_data: dict | None) -> dict:
    if macd_data is None:
        return {"emoji": "❓", "label": "Dados insuficientes", "action": "Sem dados para análise."}

    m = macd_data["macd"]
    s = macd_data["signal"]
    h = macd_data["histogram"]
    p = macd_data["prev_hist"]

    # Cruzamentos
    crossed_up   = p < 0 and h >= 0
    crossed_down = p > 0 and h <= 0
    above_zero   = m > 0
    hist_growing = abs(h) > abs(p)

    if crossed_up:
        return {
            "emoji":  "🚀",
            "label":  "A maré está virando para cima",
            "action": "Sinal de compra: a força compradora acabou de superar a vendedora. Momento de atenção.",
        }
    if crossed_down:
        return {
            "emoji":  "📉",
            "label":  "A força está saindo do ativo",
            "action": "Sinal de venda: vendedores assumiram o controle. Considere reduzir ou proteger posição.",
        }
    if above_zero and hist_growing:
        return {
            "emoji":  "💪",
            "label":  "Tendência de alta confirmada e acelerando",
            "action": "Compra ainda tem força. Posição existente pode ser mantida ou reforçada com cautela.",
        }
    if above_zero and not hist_growing:
        return {
            "emoji":  "⚠️",
            "label":  "Alta perdendo força",
            "action": "O movimento ainda é positivo, mas está desacelerando. Fique atento a uma reversão.",
        }
    if not above_zero and hist_growing:
        return {
            "emoji":  "🔻",
            "label":  "Queda acelerando",
            "action": "Vendedores no comando e ganhando força. Não entre contra a tendência agora.",
        }
    return {
        "emoji":  "😴",
        "label":  "Tendência de baixa perdendo força",
        "action": "A queda está esgotando. Pode estar se formando uma base. Aguarde confirmação antes de entrar.",
    }


# ── MÉDIAS MÓVEIS ─────────────────────────────────────────────────────────────

def calc_moving_averages(hist: pd.DataFrame) -> dict:
    result = {}
    close = hist["Close"] if hist is not None and not hist.empty else None
    if close is None:
        return result
    for period in [20, 50, 200]:
        if len(close) >= period:
            result[f"ma{period}"] = round(close.rolling(period).mean().iloc[-1], 2)
    return result


def interpret_moving_averages(price: float, mas: dict) -> str:
    msgs = []
    if "ma20" in mas:
        rel = "acima" if price > mas["ma20"] else "abaixo"
        msgs.append(f"MA20 ${mas['ma20']} ({rel})")
    if "ma50" in mas:
        rel = "acima" if price > mas["ma50"] else "abaixo"
        msgs.append(f"MA50 ${mas['ma50']} ({rel})")
    if "ma200" in mas:
        rel = "acima" if price > mas["ma200"] else "abaixo"
        msgs.append(f"MA200 ${mas['ma200']} ({rel})")
    if "ma50" in mas and "ma200" in mas:
        if mas["ma50"] > mas["ma200"]:
            msgs.append("Golden Cross ativo ✅")
        else:
            msgs.append("Death Cross ativo ⚠️")
    return " | ".join(msgs)


# ── VIX ───────────────────────────────────────────────────────────────────────

def interpret_vix(vix: float) -> dict:
    if vix < 15:
        return {"emoji": "😴", "label": "Calmaria", "action": "Mercado confiante. Opções de proteção baratas — bom momento para hedge."}
    if vix < 20:
        return {"emoji": "😐", "label": "Normal", "action": "Volatilidade saudável. Sem sinal de estresse."}
    if vix < 30:
        return {"emoji": "😟", "label": "Tensão crescente", "action": "Investidores ficando nervosos. Reduza posições especulativas."}
    if vix < 40:
        return {"emoji": "😱", "label": "Medo no mercado", "action": "Alta volatilidade. Correções bruscas são comuns. Cuidado com alavancagem."}
    return {"emoji": "🔥", "label": "Pânico — oportunidade histórica?", "action": "Níveis extremos de medo. Historicamente bom momento para acumular LT com disciplina."}


# ── YIELD CURVE ───────────────────────────────────────────────────────────────

def interpret_yield_curve(spread: float | None) -> dict:
    if spread is None:
        return {"emoji": "❓", "label": "Sem dados", "action": ""}
    if spread < -0.5:
        return {"emoji": "🔴", "label": "Curva invertida — sinal de recessão", "action": "Juros curtos > longos. Historicamente precede recessão em 12-18 meses."}
    if spread < 0:
        return {"emoji": "🟠", "label": "Curva levemente invertida", "action": "Atenção. Mercado esperando queda de juros ou desaceleração."}
    if spread < 1:
        return {"emoji": "🟡", "label": "Curva plana", "action": "Transição. Sem sinal claro de expansão ou recessão."}
    return {"emoji": "🟢", "label": "Curva normal — expansão econômica", "action": "Juros longos > curtos. Ambiente favorável para crescimento."}
