# Security and Data Consistency - Engineering Recommendations

## Objetivo

Fechar os riscos encontrados na revisao antes de publicar o Investment Monitor na web. O foco desta etapa e proteger dados sensiveis, eliminar divergencia entre UI/alertas/relatorios e reduzir risco de corrupcao dos arquivos de configuracao.

## Prioridade Executiva

1. Proteger o backend Python com token interno.
2. Fazer o frontend falhar fechado em producao se `APP_PASSWORD` estiver ausente.
3. Centralizar calculo Brasil/cripto em um helper unico.
4. Remover valores cripto hardcoded do scheduler e relatorio semanal.
5. Tornar writes de `policy.json` e `thesis.json` atomicos.

---

## 1. Backend Python exposto se publicado separadamente

### Problema

O frontend Node tem login por senha, mas o FastAPI nao tem autenticacao propria. Se o backend Python for publicado com URL publica, endpoints sensiveis podem ser chamados diretamente:

- `/portfolio`
- `/brasil`
- `/risk-book`
- `/weekly-committee`
- `/thesis`
- `/policy`
- `/decision-memo`

Hoje o backend tambem usa:

```python
allow_origins=["*"]
```

### Recomendacao

Adicionar um token interno no backend e exigir esse token em todas as rotas, exceto health check.

Variavel sugerida:

```env
INTERNAL_API_TOKEN=
```

Header sugerido:

```http
X-Internal-Token: <token>
```

No FastAPI:

```python
from fastapi import Header
from data.config import INTERNAL_API_TOKEN

def require_internal_token(x_internal_token: str | None = Header(default=None)):
    if not INTERNAL_API_TOKEN:
        raise HTTPException(status_code=500, detail="INTERNAL_API_TOKEN not configured")
    if x_internal_token != INTERNAL_API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
```

Aplicar como dependency global ou por router protegido.

No Node proxy:

```js
const internalToken = process.env.INTERNAL_API_TOKEN || localEnv.INTERNAL_API_TOKEN || "";

await fetch(`${PYTHON_API}${path}`, {
  headers: {
    "accept": "application/json",
    "X-Internal-Token": internalToken,
  },
});
```

### CORS

Restringir CORS. Para producao, evitar `*`.

Variavel sugerida:

```env
ALLOWED_ORIGINS=https://seu-frontend.vercel.app,http://127.0.0.1:3001
```

### Criterios de aceite

- Chamar backend direto sem `X-Internal-Token` retorna `401`.
- Chamar via frontend/proxy continua funcionando.
- Backend falha claramente se `INTERNAL_API_TOKEN` estiver ausente em producao.
- CORS nao fica aberto para `*` em producao.

---

## 2. Frontend deve falhar fechado em producao

### Problema

Hoje `APP_PASSWORD` vazio desativa autenticacao:

```js
if (!APP_PASSWORD) return true;
```

Isso e aceitavel para desenvolvimento local, mas perigoso em deploy. Um erro de configuracao publica a carteira.

### Recomendacao

Manter modo aberto apenas em desenvolvimento local. Em producao, exigir senha.

Exemplo:

```js
const isProduction = process.env.NODE_ENV === "production";

if (isProduction && !APP_PASSWORD) {
  throw new Error("APP_PASSWORD is required in production");
}
```

Opcionalmente aceitar:

```env
ALLOW_NO_AUTH_LOCAL=true
```

Somente para desenvolvimento.

### Criterios de aceite

- `NODE_ENV=production` sem `APP_PASSWORD` impede o servidor de subir.
- Ambiente local ainda pode rodar sem senha se explicitamente permitido.
- `.env.example` documenta `APP_PASSWORD`.

---

## 3. Centralizar calculo Brasil/cripto

### Problema

O calculo de exposicao cripto aparece duplicado em:

- `/brasil`
- `/risk-book`
- `/weekly-committee`
- `scheduler.py`

Isso cria risco de divergencia. Hoje o endpoint principal ja calcula pelo CSV, mas outros fluxos ainda podem ficar inconsistentes.

### Recomendacao

Criar helper unico:

Arquivo:

```text
src/core/brasil.py
```

Interface sugerida:

```python
from __future__ import annotations
import os
import pandas as pd
from data.config import PORTFOLIO_TOTAL_BR, CRYPTO_BAND_LOW, CRYPTO_BAND_HIGH


def get_brasil_summary(csv_path: str | None = None) -> dict:
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "portfolio_br.csv")

    df = pd.read_csv(csv_path)
    rows = df.to_dict(orient="records")

    crypto_total = sum(
        float(row.get("valor_investido") or 0)
        for row in rows
        if str(row.get("categoria", "")).lower() == "crypto"
    )
    crypto_pct = crypto_total / PORTFOLIO_TOTAL_BR * 100 if PORTFOLIO_TOTAL_BR else 0

    return {
        "total": PORTFOLIO_TOTAL_BR,
        "crypto_total": round(crypto_total, 2),
        "crypto_pct": round(crypto_pct, 2),
        "crypto_band": {"low": CRYPTO_BAND_LOW * 100, "high": CRYPTO_BAND_HIGH * 100},
        "on_target": CRYPTO_BAND_LOW * 100 <= crypto_pct <= CRYPTO_BAND_HIGH * 100,
        "positions": rows,
    }
```

Substituir os calculos duplicados por:

```python
from core.brasil import get_brasil_summary
```

### Criterios de aceite

- `rg "241_770|crypto_total =" src` nao encontra valores hardcoded antigos.
- `/brasil`, `/risk-book`, `/weekly-committee` e scheduler usam o mesmo helper.
- Alterar `portfolio_br.csv` muda todos os outputs de forma consistente.

---

## 4. Scheduler e relatorio semanal ainda usam valor antigo

### Problema

No scheduler:

```python
crypto_total = 241_770.0
crypto_pct = 241_770.0 / PORTFOLIO_TOTAL_BR * 100
```

Com o CSV atual, a exposicao correta e aproximadamente `6.77%`, abaixo da faixa 8%-12%. O valor antigo mostra cerca de `9.37%`, dentro da faixa.

### Recomendacao

Usar `get_brasil_summary()`:

```python
def job_crypto_monitor():
    print("Checando cripto Brasil...")
    try:
        br = get_brasil_summary()
        crypto_pct = br["crypto_pct"]
        crypto_total = br["crypto_total"]
        band = br["crypto_band"]

        if not br["on_target"]:
            alert_crypto_drift(crypto_pct, CRYPTO_TARGET_PCT * 100, crypto_total)
            print(f"Alerta cripto: {crypto_pct:.1f}%")
    except Exception as e:
        print(f"Erro cripto: {e}")
```

E no weekly report:

```python
br = get_brasil_summary()
weekly_report(snap, macro, br["crypto_pct"])
```

### Criterios de aceite

- O scheduler informa a mesma exposicao cripto que `/brasil`.
- O weekly report usa o percentual real do CSV.
- HASH11 abaixo da faixa gera alerta correto.

---

## 5. Writes atomicos para `policy.json` e `thesis.json`

### Problema

Hoje os arquivos sao escritos diretamente:

```python
with open(_POLICY_PATH, "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

Se o processo cair durante a escrita, o JSON pode ser corrompido. O loader captura `JSONDecodeError` e retorna `{}`, ocultando o problema.

### Recomendacao

Criar helper atomico:

```python
def _atomic_write_json(path: str, data: dict) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)
```

Usar em:

```python
def _save_policy(data: dict) -> None:
    _atomic_write_json(_POLICY_PATH, data)

def _save_thesis(data: dict) -> None:
    _atomic_write_json(_THESIS_PATH, data)
```

Tambem melhorar o loader:

```python
except json.JSONDecodeError as e:
    raise HTTPException(status_code=500, detail=f"Invalid JSON config: {path}")
```

Ou logar erro e retornar fallback apenas para arquivos realmente opcionais.

### Criterios de aceite

- Escrita usa arquivo temporario + `os.replace`.
- JSON invalido nao e engolido silenciosamente.
- Falha de leitura aparece como erro claro no endpoint.
- Update de policy/thesis continua funcionando pelo frontend.

---

## Dependencias e ambiente

Adicionar no `.env.example`:

```env
APP_PASSWORD=
INTERNAL_API_TOKEN=
ALLOWED_ORIGINS=http://127.0.0.1:3001
NODE_ENV=development
```

Criar manifesto Python:

```text
requirements.txt
```

Dependencias minimas esperadas:

```txt
fastapi
uvicorn
pandas
yfinance
requests
python-dotenv
pydantic
apscheduler
beautifulsoup4
lxml
```

---

## Ordem Recomendada de Implementacao

1. Criar `core/brasil.py` e substituir todos os calculos duplicados.
2. Corrigir scheduler e weekly report.
3. Adicionar token interno no FastAPI e no proxy Node.
4. Fazer frontend falhar fechado em producao sem `APP_PASSWORD`.
5. Implementar writes atomicos para JSON.
6. Atualizar `.env.example`, `AGENTS.md`, `CLAUDE.md` e docs.
7. Criar `requirements.txt`.

---

## Validacoes Manuais

### Backend

```bash
cd /Users/macbook/Documents/Projects/Invest/src
python3 -m uvicorn api:app --port 8000 --host 127.0.0.1
```

Sem token:

```bash
curl -i http://127.0.0.1:8000/brasil
```

Esperado:

```text
401 Unauthorized
```

Com token:

```bash
curl -H "X-Internal-Token: $INTERNAL_API_TOKEN" http://127.0.0.1:8000/brasil
```

Esperado:

- retorna JSON;
- `crypto_total` bate com `portfolio_br.csv`;
- `crypto_pct` e igual ao Risk Book e Weekly Committee.

### Frontend

```bash
cd /Users/macbook/Documents/Projects/Invest/frontend
NODE_ENV=production node server.js
```

Sem `APP_PASSWORD`, esperado:

```text
APP_PASSWORD is required in production
```

Com env vars configuradas:

```bash
node server.js
```

Esperado:

- login aparece;
- proxy chama backend com `X-Internal-Token`;
- abas Brasil, Risk Book e Weekly Committee funcionam.

### Sintaxe

```bash
cd /Users/macbook/Documents/Projects/Invest
PYTHONPYCACHEPREFIX=/private/tmp/invest-pycache python3 -m py_compile \
  src/api.py \
  src/scheduler.py \
  src/alerts/telegram.py \
  src/core/brasil.py \
  src/core/risk_book.py \
  src/core/weekly_committee.py

cd frontend
node --check server.js
node --check public/app.js
```

---

## Observacao de Produto

Essas correcoes sao pre-requisito para evoluir o produto para um padrao de private banking. Antes de adicionar stress testing, tax-aware, benchmark attribution ou whole balance sheet, a plataforma precisa garantir:

- acesso privado;
- dados consistentes;
- relatorios coerentes com a UI;
- configuracoes persistidas com seguranca;
- deploy reproduzivel.

