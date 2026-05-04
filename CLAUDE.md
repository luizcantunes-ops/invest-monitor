# Claude Code Instructions

You are a senior software engineer focused on minimal, safe, testable changes.

Rules:
- Preserve the existing architecture.
- Do not refactor broadly unless explicitly requested.
- Change the smallest number of files possible.
- Before editing, identify relevant files and state the plan in max 5 bullets.
- Prefer patches over rewriting full files.
- Do not generate long explanations.
- After changes, summarize:
  - files changed
  - what changed
  - why
  - how to test
- Do not paste large logs. Summarize only the relevant error lines.
- If requirements are ambiguous, make the safest reasonable assumption and proceed.
- For research dependencies, prefer official docs and current package documentation.

---

# Investment Monitor — Contexto Completo

> Leia este arquivo inteiro antes de qualquer edição. Ele captura todas as decisões, arquitetura e estado atual do projeto.

---

## Quem é o usuário

**Luiz Cesar Antunes** — investidor pessoa física sofisticado.

- Carteira US: ~$742K no Charles Schwab (24 posições — Long Term + Swing)
- Carteira BR: ~R$2.58M no Itaú Personnalité (fundos, previdência, FIIs, HASH11)
- Perfil: técnico + fundamentalista, horizonte misto
- **Não é day trader** — toma decisões deliberadas e pesquisadas
- Alertas: Telegram configurado; objetivo futuro WhatsApp via Twilio

### Classificação dos ativos US
**Long Term (núcleo):** AAPL, MSFT, GOOG, NVDA, META, JPM, BAC, AMZN  
**Swing (carteira ativa):** TTD, CRM, AMD, SAP, DDOG, CELH, ZS, LLY, CEG, FSLR, NET, CRWD, PANW, MDB, NOW, XYZ

---

## Estrutura do Projeto

```
/Users/macbook/Documents/Projects/Invest/        ← DIRETÓRIO ÚNICO DE TRABALHO
├── CLAUDE.md                           ← ESTE ARQUIVO — leia primeiro
├── PRODUCT.md                          ← Contexto de produto para /impeccable
├── src/                                ← Backend Python — porta 8000
│   ├── api.py                          ← FastAPI
│   ├── scheduler.py                    ← APScheduler — alertas automáticos
│   ├── core/
│   │   ├── fetcher.py                  ← Yahoo Finance (cotações, macro, histórico)
│   │   ├── indicators.py               ← RSI, MACD, Shiller PE, Buffett, VIX, Yield Curve
│   │   ├── screener.py                 ← Swing screener ~200 ativos
│   │   ├── enricher.py                 ← Finnhub + Alpha Vantage + get_analyst_full()
│   │   ├── swing.py                    ← Swing trade decision support (score, setup, entry/stop/target)
│   │   ├── investors.py                ← Dataroma 13F (7 fundos) + ARK
│   │   ├── dataroma.py                 ← Scraper Dataroma
│   │   ├── alternative.py              ← Reddit WSB
│   │   ├── polygon.py                  ← Massive/Polygon API (financials, dividendos)
│   │   └── intraday.py                 ← Day Trade advisor (RVOL, VWAP, ORB, RS vs SPY)
│   ├── alerts/
│   │   └── telegram.py                 ← Alertas técnicos, screener, cripto, relatório semanal
│   └── data/
│       ├── config.py                   ← Chaves de API (NÃO commitar)
│       ├── portfolio_us.csv            ← Carteira Schwab (symbol, qty, cost_basis, horizon, sector)
│       └── portfolio_br.csv            ← Carteira Itaú (ticker, nome, tipo, valor_investido, categoria)
└── frontend/                           ← Frontend Node.js — porta 3001
    ├── server.js                       ← Servidor HTTP Node.js
    ├── PRODUCT.md                      ← Design context (cópia — fonte em /Projects/Invest/PRODUCT.md)
    ├── DESIGN.md                       ← Design system tokens e componentes
    └── public/
        ├── index.html                  ← 6 abas de navegação
        ├── app.js                      ← Toda a lógica do frontend
        └── styles.css                  ← Design system OKLCH, Inter font
```

### Path de trabalho único
**Editar diretamente em `/Users/macbook/Documents/Projects/Invest/`**
Os diretórios antigos (`invest_monitor/` e `New project 2/`) foram deletados.

---

## Como rodar

```bash
# Backend (FastAPI) — porta 8000
cd /Users/macbook/Documents/Projects/Invest/src
python3 -m uvicorn api:app --port 8000 --host 127.0.0.1

# Frontend (Node.js) — porta 3001
cd /Users/macbook/Documents/Projects/Invest/frontend
node server.js

# Scheduler (alertas automáticos)
cd /Users/macbook/Documents/Projects/Invest/src
python3 scheduler.py
```

---

## Arquitetura — como os dois projetos se conectam

```
Browser
  └── frontend (Node.js :3001)
        ├── /api/quote                 → Yahoo Finance (server.js direto)
        ├── /api/analysis              → Yahoo Finance (server.js direto)
        ├── /api/market-regime         → Yahoo Finance (server.js direto)
        ├── /api/sentiment             → Alpha Vantage (server.js direto)
        ├── /api/alternative-signals   → OpenInsider + WSB (server.js direto)
        ├── /api/upload-portfolio      → Parse CSV Schwab (server.js direto)
        ├── /api/import-portfolio      → Lê CSV mais recente de ~/Downloads
        └── /api/py/*  ── proxy ──►  backend (Python :8000)
                                         ├── /portfolio
                                         ├── /portfolio/summary
                                         ├── /intraday, /intraday/{symbol}
                                         ├── /investors, /ark
                                         ├── /macro
                                         ├── /screener
                                         ├── /brasil
                                         ├── /sectors
                                         ├── /calendar
                                         └── /asset/{s}, /enrichment/{s}, /ebitda/{s}
                                             /alternative/{s}, /polygon/{s}
```

---

## Frontend — Abas e Estado Atual

| Tab | `data-tab` | Painel HTML | Dados | Estado |
|-----|-----------|-------------|-------|--------|
| Carteira US | `carteira` | `tab-carteira` | `/api/import-portfolio` + `/api/py/asset/{s}` | ✅ Funciona |
| Day Trade | `daytrade` | `tab-daytrade` | `/api/py/intraday` | ✅ Funciona |
| Análise de Ativo | `mercado` | `tab-mercado` | `/api/quote`, `/api/analysis`, `/api/sentiment`, `/api/alternative-signals` | ✅ Funciona |
| Investidores & Macro | `investidores` | `tab-investidores` | `/api/py/investors`, `/api/py/ark`, `/api/py/macro`, `/api/py/sectors`, `/api/py/calendar` | ⚠️ Ver problema abaixo |
| Screener | `screener` | `tab-screener` | `/api/py/screener` | ✅ Funciona (3-5 min) |
| Brasil | `brasil` | `tab-brasil` | `/api/py/brasil` | ⚠️ Ver problema abaixo |

### Problemas conhecidos a corrigir

**1. IDs duplicados no HTML** — `tab-mercado` ainda tem elementos antigos:
```html
<!-- Estes três blocos ainda estão dentro de tab-mercado e precisam ser removidos: -->
<section class="portfolio-panel"> ... </section>           <!-- lixo do Codex -->
<section class="market-regime-panel" id="macro-indicators"> ... </section>  <!-- DUPLICADO -->
<section class="investors-panel" id="investor-list"> ... </section>         <!-- DUPLICADO -->
```
O `querySelector("#macro-indicators")` retorna o elemento de `tab-mercado` (oculto), por isso a aba Investidores & Macro aparece vazia.

**2. Brasil — colunas corretas do CSV:**
- CSV usa: `ticker`, `nome`, `tipo`, `valor_investido`, `categoria`
- JS estava buscando: `type`, `value`, `return_pct` — errado

**3. `/macro/full` não existe na API:**
- `api.py` retorna só números crus em `/macro`
- As descrições ricas estão em `core/indicators.py` (`describe_shiller_pe`, `describe_buffett_indicator`, `describe_vix_full`, `describe_yield_curve_full`)
- Falta criar endpoint `/macro/full` que use essas funções

---

## Fontes de Dados

| Fonte | Módulo | O que fornece | Chave | Status |
|-------|--------|---------------|-------|--------|
| Yahoo Finance | `fetcher.py` | Cotações, histórico, macro, analistas | Nenhuma | ✅ |
| Alpaca | MCP `~/.claude/settings.json` | Dados intraday, barras, status do mercado | `config.py` | ✅ Paper account |
| Finnhub | `enricher.py` | Sentimento de notícias, insider, earnings | `FINNHUB_KEY` | ✅ Free tier |
| Alpha Vantage | `enricher.py` | Performance setorial, calendário econômico | `ALPHAVANTAGE_KEY` | ✅ 25 req/dia |
| Massive/Polygon | `polygon.py` | Histórico OHLCV, financials, dividendos | `MASSIVE_KEY` | ✅ |
| OpenInsider | `alternative.py` | Form 4 — compras/vendas executivos | Scraping | ✅ |
| Reddit WSB | `alternative.py` | Sentimento WallStreetBets | API pública | ✅ |
| Dataroma | `dataroma.py` | Holdings 13F dos 7 fundos | Scraping | ✅ |
| ARK Funds | `investors.py` | Holdings diários ARKK | CSV público | ✅ |
| SEC EDGAR | — | 13F — **removido**, substituído por Dataroma | — | ❌ |

---

## Investidores monitorados (Dataroma)

| Manager | Código | Estilo |
|---------|--------|--------|
| Warren Buffett | `BRK` | Value / Longo prazo |
| Michael Burry | `SAM` | Contrarian / Deep value |
| Bill Ackman | `psc` | Activist / Concentrado |
| Chase Coleman | `TGM` | Tech / Growth |
| Stephen Mandel | `LPC` | Growth equity / Qualidade |
| Andreas Halvorsen | `vg` | Long/Short equity |
| David Tepper | `AM` | Macro / Distressed / Tech |

Ray Dalio removido — Bridgewater não está no Dataroma.

---

## Indicadores Macro (indicators.py)

Funções que retornam dicts ricos com `sentiment`, `emoji`, `color`, `reading`, `implication`:

| Função | Parâmetro | Fonte do valor |
|--------|-----------|----------------|
| `describe_shiller_pe(38.0)` | `MACRO_SHILLER_PE` em config.py (estático) | Manual |
| `describe_buffett_indicator(198.0)` | `MACRO_BUFFETT_IND` em config.py (estático) | Manual |
| `describe_vix_full(vix)` | `get_macro_data()["vix"]` | Yahoo Finance |
| `describe_yield_curve_full(spread, y10, y3m)` | `get_macro_data()` | Yahoo Finance |

**Pendência:** criar endpoint `/macro/full` na API que chame essas funções e retorne as descrições completas.

---

## Scheduler — Jobs automáticos

| Job | Horário (SP) | O que faz |
|-----|-------------|-----------|
| `job_technical_alerts` | Seg-sex 10h e 15h | RSI < 35 ou > 70, ou cruzamento MACD → Telegram |
| `job_screener` | Seg-sex 10h30 | Top 5 swing candidates → Telegram |
| `job_crypto_monitor` | Diário 9h | Verifica se cripto BR saiu da faixa 8-12% |
| `job_weekly_report` | Segunda 8h | P&L total, top 3 melhores/piores, macro, cripto |

---

## Day Trade Advisor — Framework V1

**Estratégia:** Opening Range Breakout (15min) + VWAP + RVOL + Força relativa vs SPY

**Checklist de entrada (todos obrigatórios):**
1. RVOL > 2.0
2. Gap entre 2%–8%
3. Preço acima do VWAP
4. Força relativa vs SPY positiva
5. OR formado (após 9:45 ET)
6. Rompimento do OR High com volume

**Gestão de risco:**
- Risco por trade: 0.25%–0.50% da conta
- Perda diária máxima: 1%–2%
- Stop: OR Low / VWAP / 1× ATR
- Parcial em 1.5R, final em 2R ou trailing EMA 9

**Fase atual:** V1 — Scanner/Advisor. Sem execução automática.
**Próxima fase:** V2 — Backtesting histórico.

---

## Carteira Brasil (portfolio_br.csv)

Colunas: `ticker`, `nome`, `tipo`, `valor_investido`, `categoria`

```
HASH11  Hashdex Nasdaq Crypto Index  acao   174545.00  crypto
KNCA11  FIAGRO Kinea CI              fii     17905.86  fii
KNHY11  FII Kinea HY CI              fii     30494.31  fii
KNIP11  FII Kinea IP CI              fii     21138.75  fii
RPRI11  FII RBR PR CI                fii     16618.04  fii
RBRP11  FII RBRP PAX CI              fii     14906.62  fii
```

Monitor cripto: faixa alvo 8%–12% do portfólio BR total (R$ 2.579.940).  
Atual: 9.3% — **dentro da faixa**.

---

## Tom e UX

**Referência:** ferramenta de private banking premium.
- Informação ganha seu lugar — sem decoração
- Calma e autoridade — alertas medidos, não alarmistas
- Light theme — fundo cinza suave (#F4F5F7), cards brancos, accent indigo (#4F46E5)
- Fonte: Inter (Google Fonts)

**Anti-referências:** Binance UI, Robinhood, dark neon apps, hero metrics genéricos.

---

## Regras de trabalho (aprendidas na prática)

1. **Ler o arquivo completo antes de editar** — nunca assumir que lembra o conteúdo
2. **`curl` antes de escrever JS** — confirmar estrutura real dos dados da API
3. **Uma mudança por vez** — verificar no browser antes da próxima
4. **Checar IDs duplicados** — HTML teve bugs por IDs iguais em abas diferentes
5. **Diretório único de trabalho:** `/Users/macbook/Documents/Projects/Invest/`
6. **Backend principal:** `/Users/macbook/Documents/Projects/Invest/src/`
7. **Frontend principal:** `/Users/macbook/Documents/Projects/Invest/frontend/`
