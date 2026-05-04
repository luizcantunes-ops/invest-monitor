# Investment Monitor — Setup

## 1. Instalar dependências
```bash
pip3 install yfinance pandas ta streamlit python-telegram-bot \
             apscheduler plotly requests beautifulsoup4
```

## 2. Criar bot no Telegram
1. Abra o Telegram e busque @BotFather
2. Digite /newbot e siga as instruções
3. Copie o TOKEN gerado
4. Inicie uma conversa com o bot
5. Acesse: https://api.telegram.org/bot<TOKEN>/getUpdates
6. Copie o "chat_id" do resultado

## 3. Configurar credenciais
Edite `data/config.py`:
```python
TELEGRAM_TOKEN   = "seu_token_aqui"
TELEGRAM_CHAT_ID = "seu_chat_id_aqui"
```

## 4. Testar conexão Telegram
```bash
cd ~/invest_monitor
python3 -c "from alerts.telegram import send_test_message; send_test_message()"
```

## 5. Rodar o dashboard
```bash
cd ~/invest_monitor
streamlit run dashboard/app.py
```

## 6. Rodar o scheduler (alertas automáticos)
```bash
cd ~/invest_monitor
python3 scheduler.py
```

## Estrutura
```
invest_monitor/
├── data/
│   ├── config.py           ← tokens e configurações
│   ├── portfolio_us.csv    ← carteira Schwab
│   └── portfolio_br.csv    ← carteira Itaú (FIIs + HASH11)
├── core/
│   ├── fetcher.py          ← dados de mercado (yfinance)
│   ├── indicators.py       ← RSI, MACD com linguagem humana
│   └── screener.py         ← swing candidates externos
├── alerts/
│   └── telegram.py         ← bot de alertas
├── dashboard/
│   └── app.py              ← interface Streamlit
└── scheduler.py            ← jobs automáticos
```
