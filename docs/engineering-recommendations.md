# Investment Advisor - Recomendacoes de Implementacao

## Objetivo

Transformar o Investment Monitor em um advisor pessoal privado para consolidar carteira US/BR, explicar riscos, sugerir proximas acoes e alertar apenas mudancas relevantes.

O produto deve funcionar como copiloto de decisao, nao como executor automatico de ordens.

## Prioridade Imediata

### P0 - Seguranca antes de publicar

1. Remover segredos de `src/data/config.py`.
2. Ler chaves por variaveis de ambiente.
3. Criar `.env.example` sem valores reais.
4. Rotacionar todas as chaves ja expostas.
5. Adicionar autenticacao simples antes de publicar na web.

Variaveis esperadas:

```env
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
ALPHAVANTAGE_KEY=
FINNHUB_KEY=
MASSIVE_KEY=
MASSIVE_BASE=https://api.massive.com
ALPACA_KEY=
ALPACA_SECRET=
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

### P1 - Corrigir bugs de confianca

1. Corrigir `/brasil` para calcular exposicao cripto pelo CSV.
2. Corrigir frontend para classificar `HASH11` como `Cripto`, usando `categoria` antes de `tipo`.
3. Criar endpoint `/macro/full`.
4. Atualizar frontend para consumir os cards macro ricos vindos do backend.

## Correcoes Especificas

### `/brasil`

Arquivo: `src/api.py`

Hoje:

```python
crypto_total = 241_770.0
```

Recomendado:

```python
crypto_total = sum(
    float(row.get("valor_investido") or 0)
    for row in rows
    if str(row.get("categoria", "")).lower() == "crypto"
)
```

Manter:

```python
crypto_pct = crypto_total / PORTFOLIO_TOTAL_BR * 100
```

### Carteira Brasil no frontend

Arquivo: `frontend/public/app.js`

Recomendado:

```js
const categoria = p.categoria || p.category || "";
const tipo = categoria || p.tipo || p.type || "";
```

Motivo: `HASH11` tem `tipo=acao`, mas `categoria=crypto`.

### `/macro/full`

Arquivo: `src/api.py`

Importar:

```python
from core.indicators import (
    describe_shiller_pe,
    describe_buffett_indicator,
    describe_vix_full,
    describe_yield_curve_full,
)
from data.config import MACRO_SHILLER_PE, MACRO_BUFFETT_IND
```

Criar:

```python
@app.get("/macro/full")
def macro_full():
    try:
        macro = _cached("macro", 900, get_macro_data)
        return {
            "raw": macro,
            "shiller_pe": describe_shiller_pe(MACRO_SHILLER_PE),
            "buffett_indicator": describe_buffett_indicator(MACRO_BUFFETT_IND),
            "vix": describe_vix_full(macro.get("vix")),
            "yield_curve": describe_yield_curve_full(
                macro.get("yield_spread"),
                macro.get("yield_10y"),
                macro.get("yield_3m"),
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
```

## Roadmap de Produto

### Fase 1 - Publicavel e seguro

- Corrigir os 4 findings de review.
- Adicionar autenticacao.
- Separar configuracao sensivel por ambiente.
- Publicar backend em Render ou Koyeb.
- Publicar frontend em Vercel ou Cloudflare Pages.
- Mover scheduler para GitHub Actions cron ou endpoints protegidos.

### Fase 2 - Advisor util

- Criar `Investment Policy` do Luiz:
  - classificacao Long Term vs Swing;
  - limite por ativo;
  - limite por setor;
  - alvo cripto BR 8%-12%;
  - caixa minimo;
  - regras de venda;
  - regras de aumento/reducao de posicao.
- Criar tese por ativo:
  - motivo da posicao;
  - horizonte;
  - gatilho de compra;
  - gatilho de venda;
  - risco principal;
  - ultima revisao.
- Criar dashboard orientado a decisao:
  - o que mudou;
  - o que exige acao;
  - o que e ruido;
  - riscos concentrados;
  - proximas decisoes provaveis.

### Fase 3 - Advisor inteligente

- Criar score proprietario por ativo:
  - qualidade;
  - momentum;
  - valuation;
  - risco macro;
  - sentimento;
  - confirmacao institucional;
  - adequacao a carteira.
- Criar log de decisoes em `decisions.csv` ou banco simples:
  - data;
  - ativo;
  - decisao;
  - motivo;
  - preco;
  - regime macro;
  - resultado posterior.
- Adicionar resumos por IA para:
  - earnings;
  - noticias;
  - filings;
  - mudancas na tese;
  - briefing semanal.

### Fase 4 - Sofisticacao

- Integrar FRED para macro confiavel.
- Melhorar dados de FIIs/Brasil.
- Criar simulador de rebalanceamento.
- Criar analise tax-aware.
- Evoluir alertas Telegram para WhatsApp via Twilio.

## Novas Fontes de Dados

Nao adicionar novas fontes antes de corrigir seguranca, Brasil e macro.

Depois disso, priorizar:

1. FRED - juros, inflacao, desemprego, spreads e liquidez.
2. SEC EDGAR - 10-K, 10-Q, 8-K e earnings context.
3. Fonte especializada para FIIs/Brasil - dividend yield, P/VP, vacancia e rendimentos.

## Regras de Produto

- Menos alertas, mais qualidade.
- Toda recomendacao deve explicar o motivo.
- Toda sugestao deve separar decisao de dado bruto.
- O sistema nao deve executar ordens.
- O sistema deve indicar incerteza quando dados forem incompletos.
- O advisor deve dizer "nao fazer nada" quando esta for a melhor decisao.

## Criterios de Aceite

### Seguranca

- Nenhuma chave real aparece no codigo.
- App roda localmente com variaveis de ambiente.
- Deploy aceita variaveis pelo painel da plataforma.
- Frontend nao recebe segredos.

### Brasil

- `/brasil` calcula `crypto_total` a partir de `portfolio_br.csv`.
- `HASH11` aparece como `Cripto`.
- Percentual cripto bate com o CSV.
- Faixa 8%-12% continua funcionando.

### Macro

- `/macro/full` responde com `raw`, `shiller_pe`, `buffett_indicator`, `vix` e `yield_curve`.
- Cards macro do frontend usam descricoes do backend.
- Textos hardcoded de Shiller/Buffett deixam de ser fonte principal.

### Publicacao

- Backend responde em `/health` ou endpoint equivalente.
- Frontend carrega sem erro de console relevante.
- Rotas `/api/py/brasil` e `/api/py/macro/full` funcionam em producao.
- Endpoints sensiveis de alertas exigem token.

## Testes Manuais

Backend:

```bash
cd /Users/macbook/Documents/Projects/Invest/src
python3 -m uvicorn api:app --port 8000 --host 127.0.0.1
curl http://127.0.0.1:8000/brasil
curl http://127.0.0.1:8000/macro/full
```

Frontend:

```bash
cd /Users/macbook/Documents/Projects/Invest/frontend
node server.js
```

Validar no navegador:

- Aba Brasil mostra `HASH11` como `Cripto`.
- Exposicao cripto bate com o CSV.
- Aba Investidores & Macro mostra cards com descricoes vindas do backend.
- Nenhuma chave aparece no bundle/frontend.

## Referencias

- SEC/Investor.gov - Robo-advisers: https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-45
- Schwab Intelligent Portfolios: https://www.schwab.com/intelligent-portfolios
- Wealthfront Tax-Loss Harvesting: https://support.wealthfront.com/hc/en-us/articles/209348486-Tax-Loss-Harvesting
- OpenAI API Key Safety: https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety
- CFPB Personal Financial Data Rights: https://www.consumerfinance.gov/compliance/compliance-resources/other-applicable-requirements/personal-financial-data-rights/
