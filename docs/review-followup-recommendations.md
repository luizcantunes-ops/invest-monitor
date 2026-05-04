# Review Follow-up - Recomendacoes de Implementacao

## Objetivo

Fechar os achados da revisao recente antes de avancar em novas features. O foco e reduzir divergencia entre UI, alertas, documentacao e deploy.

## Prioridades

1. Unificar calculo da carteira Brasil/cripto.
2. Tornar falha do Telegram explicita quando variaveis de ambiente estiverem ausentes.
3. Atualizar `AGENTS.md` e `CLAUDE.md` para refletirem o estado real.
4. Declarar dependencias Python para deploy limpo.

---

## 1. Unificar calculo de cripto BR

### Problema

`/brasil` ja calcula `crypto_total` a partir de `portfolio_br.csv`, mas `src/scheduler.py` ainda usa:

```python
crypto_total = 241_770.0
```

Isso pode gerar alerta Telegram incorreto mesmo com a interface web correta.

### Recomendacao

Criar uma funcao unica reutilizavel, por exemplo:

Arquivo sugerido:

```text
src/core/brasil.py
```

Funcao sugerida:

```python
def get_brasil_summary() -> dict:
    ...
```

Retorno esperado:

```python
{
    "total": PORTFOLIO_TOTAL_BR,
    "crypto_total": 174545.00,
    "crypto_pct": 6.77,
    "crypto_band": {"low": 8.0, "high": 12.0},
    "on_target": False,
    "positions": [...]
}
```

### Usar em

- `src/api.py` em `/brasil`
- `src/api.py` em `/risk-book`
- `src/api.py` em `/weekly-committee`
- `src/scheduler.py` em `job_crypto_monitor`

### Criterios de aceite

- Nao existe mais `crypto_total = 241_770.0` em codigo ativo.
- `/brasil` continua retornando `crypto_total` baseado no CSV.
- Scheduler usa o mesmo calculo do endpoint.
- Mudanca no CSV altera UI e alerta automaticamente.

---

## 2. Validar configuracao do Telegram

### Problema

Depois da migracao para env vars, `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID` podem estar vazios. Hoje `_send()` ainda tenta chamar:

```python
https://api.telegram.org/bot/sendMessage
```

Isso falha de forma opaca.

### Recomendacao

Em `src/alerts/telegram.py`, validar antes do POST:

```python
def _send(text: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram nao configurado: TELEGRAM_TOKEN/TELEGRAM_CHAT_ID ausentes")
        return False
    ...
```

Opcional:

- capturar `requests.RequestException`
- logar status code e trecho curto da resposta
- nunca imprimir token

### Criterios de aceite

- Sem env vars, scheduler nao quebra.
- Log informa claramente que Telegram nao esta configurado.
- Token nunca aparece em logs.
- Com env vars validas, envio continua funcionando.

---

## 3. Atualizar documentacao operacional

### Problema

`AGENTS.md` e `CLAUDE.md` ainda dizem que:

- existem IDs duplicados no HTML;
- `/macro/full` nao existe;
- Brasil ainda usa colunas erradas.

Esses pontos ja foram corrigidos total ou parcialmente.

### Recomendacao

Atualizar a secao de problemas conhecidos:

```md
### Problemas corrigidos

- IDs duplicados removidos do HTML.
- `/macro/full` criado.
- Frontend Brasil usa `categoria` antes de `tipo`.
- `/brasil` calcula cripto pelo CSV.

### Pendencias atuais

- Centralizar calculo Brasil/cripto em helper unico.
- Scheduler ainda deve usar helper comum.
- Telegram precisa validar env vars ausentes.
- Dependencias Python precisam ser declaradas.
```

### Criterios de aceite

- `AGENTS.md` nao lista como pendente algo ja implementado.
- `CLAUDE.md` fica consistente com `AGENTS.md`.
- Proximo agente nao sera induzido a desfazer/corrigir algo que ja esta correto.

---

## 4. Declarar dependencias Python

### Problema

`src/data/config.py` agora usa:

```python
from dotenv import load_dotenv
```

Mas nao existe `requirements.txt` nem `pyproject.toml`. Em deploy limpo, o backend pode falhar no import.

### Recomendacao

Criar `src/requirements.txt` ou `requirements.txt` na raiz.

Dependencias minimas provaveis:

```txt
fastapi
uvicorn
pandas
yfinance
requests
python-dotenv
pydantic
apscheduler
```

Validar se tambem sao usadas:

```txt
numpy
beautifulsoup4
lxml
```

### Criterios de aceite

- Ambiente limpo consegue instalar dependencias com um comando.
- README/setup indica o comando correto.
- `python3 -m uvicorn api:app --port 8000 --host 127.0.0.1` sobe apos instalacao.

---

## Ordem recomendada para Claude/engenheiro

1. Criar helper `src/core/brasil.py`.
2. Substituir calculos duplicados em API e scheduler.
3. Adicionar validacao de Telegram.
4. Criar manifesto de dependencias Python.
5. Atualizar `AGENTS.md` e `CLAUDE.md`.
6. Rodar validacoes manuais.

## Validacoes manuais

Backend:

```bash
cd /Users/macbook/Documents/Projects/Invest/src
python3 -m uvicorn api:app --port 8000 --host 127.0.0.1
curl http://127.0.0.1:8000/brasil
curl http://127.0.0.1:8000/macro/full
curl http://127.0.0.1:8000/risk-book
curl http://127.0.0.1:8000/weekly-committee
```

Compilacao:

```bash
cd /Users/macbook/Documents/Projects/Invest
PYTHONPYCACHEPREFIX=/private/tmp/invest-pycache python3 -m py_compile \
  src/api.py \
  src/scheduler.py \
  src/alerts/telegram.py \
  src/core/brasil.py
```

Frontend:

```bash
cd /Users/macbook/Documents/Projects/Invest/frontend
node --check server.js
node --check public/app.js
node server.js
```

Validar no navegador:

- Aba Brasil mostra `HASH11` como `Cripto`.
- Percentual cripto bate com `portfolio_br.csv`.
- Risk Book mostra a mesma exposicao cripto da aba Brasil.
- Weekly Committee mostra a mesma exposicao cripto.
- Sem variaveis Telegram, scheduler loga erro claro e nao quebra.

