# Bot de Swing Trade US Equities: Framework V1

## 1. Objetivo

Criar um bot de swing trade para ações americanas com foco em operações de curto a médio prazo, geralmente com duração de alguns dias a algumas semanas.

O objetivo principal é capturar movimentos direcionais relevantes em ações com boa qualidade técnica, fundamentos aceitáveis, liquidez adequada, catalisadores potenciais e relação risco/retorno favorável.

Este framework foi desenhado para ser usado inicialmente como:

1. Scanner de oportunidades
2. Sistema de ranking de ativos
3. Motor de geração de sinais
4. Simulador de paper trading
5. Base para backtesting
6. Futuro sistema semi-automatizado

A primeira versão não deve executar ordens reais.

A prioridade da V1 é construir um sistema disciplinado, auditável, testável e validado estatisticamente.

## 2. Conceito de Swing Trading

Swing trading busca capturar movimentos de curto a médio prazo, normalmente por alguns dias ou semanas.

Segundo a Investopedia, swing traders procuram identificar zonas de suporte e resistência, movimentos de pullback, rompimentos, reversões e retomadas de tendência. Ferramentas comuns incluem médias móveis, RSI, MACD, suporte, resistência, padrões gráficos e análise de volume.

A diferença central para day trade é que o swing trade carrega posições durante a noite. Isso cria risco de gap, risco de earnings, risco macro e risco de notícias fora do horário de mercado.

Referência conceitual: [Investopedia, What Is Swing Trading?](https://www.investopedia.com/terms/s/swingtrading.asp?utm_source=chatgpt.com)

## 3. Princípio Geral

O bot não deve comprar uma ação apenas porque ela caiu muito.

O bot não deve comprar uma ação apenas porque está barata.

O bot não deve comprar uma ação apenas porque existe notícia positiva.

O bot deve comprar apenas quando houver confluência entre:

1. Tendência favorável
2. Força relativa positiva
3. Liquidez adequada
4. Setup técnico claro
5. Risco/retorno assimétrico
6. Ausência de evento binário perigoso
7. Confirmação de volume
8. Contexto de mercado favorável

Lógica central:

```text
Preço mostra direção.
Volume confirma interesse.
Tendência define probabilidade.
Risco define se a operação vale a pena.
```

## 4. Estratégia Recomendada para V1

Estratégia inicial:

```text
Trend Pullback + Breakout Confirmation + Relative Strength vs SPY
```

Em português:

```text
Comprar ações em tendência de alta, que corrigiram para uma zona técnica relevante, seguraram suporte e voltaram a romper com confirmação de volume e força relativa.
```

A V1 deve evitar estratégias excessivamente complexas. O setup principal deve ser simples, objetivo e testável.

## 5. Arquitetura Conceitual

```text
Universo de Ações
   ↓
Data Quality Check
   ↓
Filtro de Liquidez
   ↓
Filtro Fundamental Básico
   ↓
Market Regime Gate
   ↓
Filtro de Tendência
   ↓
Filtro de Força Relativa vs SPY
   ↓
Filtro de Força Relativa Setorial
   ↓
Filtro de Volatilidade
   ↓
Filtro de Catalisadores e Eventos
   ↓
Scanner de Setups Técnicos
   ↓
Risk/Reward Validator
   ↓
Ranking de Oportunidades
   ↓
Geração de Sinal
   ↓
Revisão Humana
   ↓
Paper Trading
   ↓
Gestão de Risco
   ↓
Gestão da Posição
   ↓
Registro de Trades
   ↓
Métricas e Validação
```

## 6. Fases de Implementação

### 6.1 Fase 1: Scanner e Ranking

Objetivo: identificar ações com boa configuração para swing trade.

Características:

- Sem execução automática
- Geração de watchlist
- Ranking por score
- Identificação de setups técnicos
- Identificação de riscos próximos, como earnings
- Decisão humana final

Resultado esperado:

```text
O sistema entrega uma lista priorizada de oportunidades, com entrada sugerida, stop, alvo e racional.
```

### 6.2 Fase 2: Paper Trading

Objetivo: validar a estratégia em ambiente simulado.

Características:

- Simulação de entrada
- Simulação de stop
- Simulação de take profit
- Simulação de trailing stop
- Registro de trades
- Cálculo de métricas
- Comparação com SPY e QQQ

Resultado esperado:

```text
O sistema prova se a estratégia tem vantagem estatística antes de usar dinheiro real.
```

### 6.3 Fase 3: Backtesting

Objetivo: testar a estratégia em histórico mais longo.

Características:

- Backtest de pelo menos 3 a 5 anos
- Teste em mercado de alta
- Teste em mercado de baixa
- Teste em mercado lateral
- Teste durante alta volatilidade
- Teste por setor
- Teste por market cap

Resultado esperado:

```text
Entender em quais regimes a estratégia funciona e em quais regimes ela deve ser reduzida ou pausada.
```

### 6.4 Fase 4: Execução Real Pequena

Objetivo: validar execução real com tamanho reduzido.

Características:

- Operações reais pequenas
- Risco por trade reduzido
- Sem alavancagem inicialmente
- Controle de perda semanal
- Kill switch
- Logs completos

### 6.5 Fase 5: Semi-Automação

Objetivo: permitir execução assistida.

Características:

- Bot gera sinal
- Humano aprova entrada
- Bot monitora stop e alvo
- Bot sugere ajuste de stop
- Bot alerta sobre earnings e eventos
- Bot registra tudo automaticamente

## 7. Universo Inicial de Ativos

O bot deve operar apenas ações americanas com liquidez adequada.

### 7.1 Filtros Mínimos

| Critério | Regra Sugerida |
|---|---:|
| Preço mínimo | > US$ 10 |
| Volume médio diário | > 1 milhão de ações |
| Market cap | > US$ 2 bilhões |
| Spread médio | Baixo |
| Listagem | NYSE ou Nasdaq |
| Histórico mínimo | 2 anos de dados, quando possível |
| Evitar | Penny stocks, microcaps, ações manipuláveis |

### 7.2 Filtros Preferenciais

| Critério | Regra Preferencial |
|---|---:|
| Volume médio diário | > 2 milhões de ações |
| Market cap | > US$ 10 bilhões |
| Beta | Entre 0.8 e 2.0 |
| Institucional ownership | Alto |
| Cobertura de analistas | Sim |
| Opções líquidas | Preferencial, mas não obrigatório |

### 7.3 Tipos de Ativos Elegíveis

O bot pode operar:

- Large caps
- Mid caps líquidas
- ETFs setoriais
- Ações de tecnologia
- Ações de saúde
- Ações financeiras
- Ações industriais
- Ações de consumo
- Ações de energia
- Ações de semicondutores
- Ações com forte momentum setorial

O bot deve evitar inicialmente:

- Penny stocks
- Biotechs binárias sem aprovação relevante
- SPACs ilíquidas
- Empresas em risco de falência
- Ações com volume muito baixo
- Ações com spreads largos
- Ações próximas de eventos binários muito incertos

## 8. Filtro Fundamental Básico

Swing trade não é investimento de longo prazo, mas fundamentos ruins podem aumentar o risco da operação.

O bot deve evitar empresas com deterioração fundamental severa, exceto se a estratégia for explicitamente de turnaround ou short squeeze, o que não faz parte da V1.

### 8.1 Critérios Fundamentais

| Fator | Regra Sugerida |
|---|---|
| Receita | Crescimento positivo ou estável |
| Margem bruta | Estável ou melhorando |
| Margem operacional | Evitar deterioração forte |
| Caixa | Preferir empresas com boa liquidez |
| Dívida | Evitar alavancagem excessiva |
| Guidance | Evitar empresas com guidance muito negativo |
| Revisões de lucro | Preferir revisões positivas |
| EPS trend | Preferir melhora ou estabilidade |

### 8.2 Classificação Fundamental

| Score | Interpretação |
|---|---|
| 0 a 2 | Fraco |
| 3 a 5 | Neutro |
| 6 a 8 | Bom |
| 9 a 10 | Excelente |

Regra:

```text
Evitar operações long em ações com score fundamental abaixo de 4, salvo exceções explícitas.
Priorizar ações com score fundamental acima de 6.
```

## 9. Filtro de Tendência

A tendência é o principal filtro do swing trade.

### 9.1 Médias Móveis

| Média | Função |
|---|---|
| EMA 8 | Momentum curto |
| EMA 21 | Tendência curta |
| SMA 50 | Tendência intermediária |
| SMA 200 | Tendência primária |

### 9.2 Regra para Long

```text
Entrada long preferencial apenas se:
1. Preço acima da SMA 50
2. Preço acima da SMA 200
3. EMA 21 inclinada para cima
4. SMA 50 acima da SMA 200
5. Ação em tendência igual ou melhor que o SPY
```

### 9.3 Exceção: Pullback em Tendência

O bot pode aceitar preço temporariamente abaixo da EMA 21 se:

```text
1. Preço ainda estiver acima da SMA 50
2. SMA 50 estiver acima da SMA 200
3. Pullback ocorrer com volume menor
4. Preço mostrar reversão em suporte
5. RSI recuperar acima de 50
```

## 10. Força Relativa vs SPY

A força relativa é um dos filtros mais importantes.

### 10.1 Cálculo

```text
Relative Strength = Retorno da ação no período - Retorno do SPY no período
```

Exemplo:

```text
Ação sobe 12% em 20 dias.
SPY sobe 4% em 20 dias.
Relative Strength = 12% - 4% = +8%
```

### 10.2 Períodos

| Período | Uso |
|---|---|
| 5 dias | Momentum curto |
| 20 dias | Swing principal |
| 50 dias | Tendência intermediária |
| 100 dias | Confirmação maior |

### 10.3 Regra

```text
Para entrada long:
- Relative Strength 20 dias > 0
- Relative Strength 50 dias preferencialmente > 0
- Ação deve estar entre as líderes do setor ou acima do SPY
```

## 11. Força Relativa Setorial

Além de comparar com SPY, o bot deve comparar a ação com seu ETF setorial.

| Setor | ETF de Referência |
|---|---|
| Tecnologia | XLK |
| Semicondutores | SMH ou SOXX |
| Saúde | XLV |
| Biotecnologia | XBI |
| Financeiro | XLF |
| Energia | XLE |
| Industrial | XLI |
| Consumo discricionário | XLY |
| Utilities | XLU |
| Real Estate | XLRE |

Regra:

```text
Priorizar ações que estejam mais fortes que:
1. SPY
2. QQQ, se for growth/tech
3. ETF setorial correspondente
```

## 12. Momentum

| Indicador | Uso |
|---|---|
| RSI 14 | Força e sobrecompra/sobrevenda |
| MACD | Mudança de momentum |
| Rate of Change | Velocidade do movimento |
| Volume | Confirmação |
| Highs/Lows | Estrutura de tendência |

### 12.1 RSI

| RSI | Leitura |
|---|---|
| < 30 | Sobrevendido |
| 30 a 45 | Fraqueza |
| 45 a 55 | Neutro |
| 55 a 70 | Momentum positivo |
| > 70 | Forte, mas pode estar esticado |

Regra:

```text
Preferir entradas quando:
1. RSI recupera acima de 50
2. RSI está entre 50 e 65
3. RSI não está extremamente esticado
4. RSI confirma reversão após pullback
```

Evitar:

```text
Comprar quando RSI > 75 após alta vertical sem consolidação.
```

### 12.2 MACD

O MACD pode ser usado como confirmação secundária.

Regra sugerida:

```text
Preferir entrada quando:
1. MACD cruza para cima
2. Histograma melhora
3. Cruzamento ocorre próximo a suporte ou após pullback
```

O MACD não deve ser usado isoladamente.

## 13. Volume

| Situação | Leitura |
|---|---|
| Alta com volume acima da média | Confirmação positiva |
| Alta com volume baixo | Movimento frágil |
| Pullback com volume baixo | Correção saudável |
| Queda com volume alto | Distribuição |
| Rompimento com volume alto | Setup mais confiável |

Regra:

```text
Para entrada long:
1. Rompimento deve ocorrer com volume acima da média de 20 dias
2. Pullback anterior deve preferencialmente ter volume menor
3. Evitar entrada após queda recente com volume muito alto
```

## 14. Volatilidade

Usar ATR de 14 períodos no gráfico diário.

| ATR % do preço | Leitura |
|---|---|
| < 2% | Baixa volatilidade |
| 2% a 5% | Boa zona para swing |
| 5% a 8% | Alta volatilidade |
| > 8% | Risco elevado |

Regra:

```text
Preferir ações com ATR entre 2% e 6% do preço.
Evitar ações com ATR acima de 8% na V1.
```

## 15. Setups Principais

### 15.1 Setup 1: Trend Pullback

Ideia: comprar uma ação em tendência de alta após correção saudável para uma zona de suporte.

Condições:

```text
1. Preço acima da SMA 50
2. Preço acima da SMA 200
3. SMA 50 acima da SMA 200
4. Pullback para EMA 21 ou SMA 50
5. Volume do pullback menor que o volume da alta anterior
6. RSI recuperando acima de 50
7. Força relativa vs SPY positiva
8. Candle de reversão ou rompimento da máxima do dia anterior
```

Entrada:

```text
Comprar quando o preço romper a máxima do candle de reversão.
```

Stop:

```text
Stop abaixo da mínima do pullback ou abaixo da SMA 50.
```

Alvo:

```text
Primeiro alvo: 2R.
Segundo alvo: máxima anterior ou resistência diária/semanal.
```

### 15.2 Setup 2: Breakout de Consolidação

Ideia: comprar uma ação que passou dias ou semanas consolidando e rompe uma resistência com volume.

Condições:

```text
1. Consolidação mínima de 5 a 15 dias
2. Resistência bem definida
3. Volume seco durante consolidação
4. Rompimento com volume acima da média
5. Preço acima da SMA 50 e SMA 200
6. Relative Strength vs SPY positiva
7. Setor favorável
```

### 15.3 Setup 3: Earnings Breakout Pós-Resultado

Ideia: comprar ações que divulgaram resultado forte e romperam resistência relevante com volume.

Condições:

```text
1. Resultado acima do esperado
2. Guidance positivo ou melhor que o esperado
3. Gap de alta controlado
4. Volume muito acima da média
5. Preço fecha perto da máxima do dia
6. Não perde VWAP diário ou suporte relevante
7. Força relativa muito positiva
```

Observação:

```text
Evitar comprar antes do resultado na V1.
```

### 15.4 Setup 4: Reclaim da SMA 50

Ideia: comprar uma ação de qualidade que perdeu temporariamente a SMA 50, mas recuperou a média com força.

Condições:

```text
1. Ação estava em tendência de alta anterior
2. Perdeu SMA 50 temporariamente
3. Recuperou SMA 50 com volume
4. RSI voltou acima de 50
5. Relative Strength melhorando
6. Mercado geral está favorável
```

## 16. Setups Evitados na V1

```text
1. Short squeeze puro
2. Biotech antes de FDA binary event
3. Compra antes de earnings
4. Compra de ação abaixo da SMA 200
5. Compra contra tendência forte do mercado
6. Compra após candle vertical muito esticado
7. Compra apenas por RSI sobrevendido
8. Compra apenas porque caiu muito
9. Compra baseada somente em notícia
10. Compra sem stop técnico claro
```

## 17. Gestão de Risco

### 17.1 Risco por Trade

| Perfil | Risco por Trade |
|---|---:|
| Conservador | 0,25% da conta |
| Moderado | 0,50% da conta |
| Agressivo | 0,75% da conta |
| Máximo recomendado V1 | 1,00% da conta |

Recomendação V1:

```text
Usar 0,25% a 0,50% por trade.
```

### 17.2 Tamanho da Posição

```text
Position Size = Valor em risco por trade / Risco por ação
```

Exemplo:

```text
Conta: US$ 100.000
Risco por trade: 0,5%
Valor em risco: US$ 500

Entrada: US$ 100
Stop: US$ 95
Risco por ação: US$ 5

Position Size = 500 / 5 = 100 ações
```

### 17.3 Exposição Máxima

| Tipo de Exposição | Limite Sugerido |
|---|---:|
| Risco por trade | 0,25% a 0,50% |
| Risco total aberto | 3% a 5% da conta |
| Exposição bruta | 50% a 100% da conta |
| Exposição por setor | 20% a 30% |
| Exposição por ativo | 5% a 10% |
| Perda semanal máxima | 3% |
| Perda mensal máxima | 6% |

### 17.4 Correlação

O bot deve evitar abrir várias posições altamente correlacionadas.

Exemplo:

```text
Comprar NVDA, AMD, AVGO, SMH e TSM ao mesmo tempo pode parecer diversificado,
mas é essencialmente uma grande aposta em semicondutores.
```

Regra:

```text
Não abrir mais de 2 ou 3 posições altamente correlacionadas no mesmo setor.
```

## 18. Stop Loss

| Tipo | Uso |
|---|---|
| Stop abaixo da mínima do pullback | Trend pullback |
| Stop abaixo da SMA 50 | Tendência intermediária |
| Stop abaixo da zona de breakout | Breakout |
| Stop por ATR | Ações mais voláteis |
| Stop de tempo | Trade não evolui |

Regra ATR:

```text
Stop = Entrada - 1.5x ATR diário
```

O stop deve ficar em um ponto onde a tese é invalidada. O tamanho da posição se ajusta ao stop, e não o contrário.

## 19. Take Profit e Saídas

### 19.1 Saída Parcial

```text
Realizar 30% a 50% da posição em 2R.
Mover stop para breakeven ou abaixo da EMA 21 após parcial.
```

### 19.2 Saída Final

Opções:

```text
1. Alvo técnico em resistência
2. Alvo por múltiplo de risco
3. Perda da EMA 21
4. Fechamento abaixo da SMA 50
5. Trailing stop por ATR
6. Sinal de reversão com volume
```

### 19.3 Trailing Stop

Regra V1:

```text
Usar EMA 21 como trailing stop principal.
```

## 20. Gestão de Tempo

Regra sugerida:

```text
Se após 5 a 10 pregões a operação não avançar ao menos 1R, encerrar ou reduzir posição.
```

| Tipo de Setup | Duração Esperada |
|---|---:|
| Trend Pullback | 5 a 20 pregões |
| Breakout | 3 a 15 pregões |
| Earnings Breakout | 5 a 25 pregões |
| Reclaim SMA 50 | 5 a 20 pregões |

## 21. Earnings e Eventos

Regra principal:

```text
Não abrir nova posição long faltando menos de 5 pregões para earnings.
```

Se a posição já estiver aberta:

```text
1. Reduzir posição
2. Mover stop
3. Encerrar antes do evento
4. Manter apenas se houver ganho suficiente e tese forte
```

## 22. Filtro de Mercado

| Indicador | Uso |
|---|---|
| SPY | Mercado amplo |
| QQQ | Growth/tecnologia |
| IWM | Small caps |
| VIX | Volatilidade |
| DXY | Dólar |
| US10Y | Juros longos |
| HYG | Crédito high yield |
| TLT | Bonds longos |

### 22.1 Classificação

| Regime | Condição | Ação do Bot |
|---|---|---|
| Bull trend | SPY acima da SMA 50 e 200 | Permitir longs |
| Pullback saudável | SPY acima da SMA 200, corrigindo até SMA 50 | Reduzir tamanho |
| Bear trend | SPY abaixo da SMA 200 | Evitar longs |
| Alta volatilidade | VIX acima de zona crítica | Reduzir risco |
| Mercado lateral | SPY sem direção | Operar menos |

Regra principal:

```text
Operar comprado com tamanho normal apenas se SPY estiver acima da SMA 200.
Reduzir tamanho se SPY estiver abaixo da SMA 50.
Evitar novas compras se SPY estiver abaixo da SMA 200.
```

## 23. Regras Bloqueantes da V1

O bot nunca gera sinal long se:

```text
1. SPY abaixo da SMA 200
2. Ativo abaixo da SMA 200
3. Earnings em até 5 pregões
4. Risco/retorno abaixo de 2:1
5. Volume médio abaixo do mínimo
6. Stop técnico indefinido
7. Score abaixo de 75
8. Exposição setorial acima do limite
9. Perda semanal máxima atingida
10. Dados insuficientes para calcular médias principais
```

## 24. Ranking de Oportunidades

| Critério | Peso |
|---|---:|
| Tendência | 20% |
| Força relativa vs SPY | 20% |
| Força relativa setorial | 10% |
| Volume | 10% |
| Setup técnico | 20% |
| Risco/retorno | 10% |
| Fundamento básico | 5% |
| Ausência de eventos perigosos | 5% |

Interpretação:

| Score | Decisão |
|---|---|
| 0 a 49 | Ignorar |
| 50 a 64 | Monitorar |
| 65 a 79 | Watchlist |
| 80 a 89 | Setup forte |
| 90 a 100 | Setup prioritário |

Regra:

```text
Gerar sinal apenas para ativos com score acima de 75.
Priorizar operações acima de 80.
```

## 25. Critérios de Entrada Long

Checklist:

```text
1. Preço acima da SMA 50
2. Preço acima da SMA 200
3. SMA 50 acima da SMA 200
4. EMA 21 inclinada para cima
5. Relative Strength vs SPY positiva
6. Relative Strength vs setor positiva
7. Setup técnico válido
8. Volume confirma movimento
9. RSI entre 50 e 70
10. Risco/retorno mínimo de 2:1
11. Sem earnings nos próximos 5 pregões
12. Mercado geral não está em bear trend
13. Exposição setorial dentro do limite
14. Stop técnico claro
15. Tamanho da posição calculado pelo risco
```

## 26. Gestão da Posição

Depois da entrada, monitorar:

```text
1. Preço vs entrada
2. Preço vs stop
3. Preço vs EMA 21
4. Volume
5. RSI
6. Relative Strength vs SPY
7. Notícias novas
8. Proximidade de earnings
9. Exposição total da carteira
```

Regras de stop:

```text
1. Não alargar stop após entrada
2. Mover stop para breakeven após ganho parcial
3. Subir stop conforme novas mínimas ascendentes
4. Usar EMA 21 como referência
5. Reduzir posição se perder momentum
```

## 27. Gestão de Carteira

Recomendação V1:

```text
Máximo de 5 a 10 posições abertas.
```

Exposição por setor:

```text
Não concentrar mais de 30% da exposição em um único setor.
```

| Regime de Mercado | Exposição Máxima |
|---|---:|
| Bull trend forte | 80% a 100% |
| Bull trend normal | 50% a 80% |
| Mercado lateral | 30% a 50% |
| Mercado fraco | 0% a 30% |
| Bear trend | 0% a 20% |

## 28. Métricas de Performance

| Métrica | Objetivo |
|---|---|
| Total de trades | Quantidade de operações |
| Win rate | Taxa de acerto |
| Average win | Ganho médio |
| Average loss | Perda média |
| Profit factor | Ganho bruto / perda bruta |
| Expectancy | Retorno esperado por trade |
| Max drawdown | Maior queda |
| Average holding period | Tempo médio por trade |
| R múltiplo médio | Qualidade do retorno |
| Exposure-adjusted return | Retorno ajustado à exposição |
| Hit rate por setup | Qual setup funciona melhor |
| Performance vs SPY | Geração de alpha |
| Performance por setor | Onde o bot funciona melhor |

### 28.1 Expectancy

```text
Expectancy = (Win Rate × Average Win) - (Loss Rate × Average Loss)
```

### 28.2 Profit Factor

```text
Profit Factor = Lucro Bruto / Perda Bruta
```

| Profit Factor | Leitura |
|---|---|
| < 1.0 | Estratégia perdedora |
| 1.0 a 1.2 | Fraca |
| 1.2 a 1.5 | Aceitável |
| 1.5 a 2.0 | Boa |
| > 2.0 | Excelente, mas verificar overfitting |

## 29. Critérios de Validação

Antes de operar dinheiro real:

```text
1. Backtest mínimo de 3 anos
2. Paper trading por 60 a 90 dias
3. Pelo menos 50 a 100 trades simulados
4. Profit factor acima de 1.3
5. Expectancy positiva
6. Max drawdown aceitável
7. Performance melhor que SPY ajustada ao risco
8. Funcionamento em diferentes regimes
9. Logs completos
10. Sem dependência de parâmetros excessivamente otimizados
```

## 30. Parâmetros Iniciais

| Parâmetro | Valor Inicial |
|---|---:|
| Timeframe principal | Diário |
| Timeframe secundário | Semanal |
| EMA curta | 8 |
| EMA principal | 21 |
| Média intermediária | SMA 50 |
| Média primária | SMA 200 |
| RSI | 14 períodos |
| ATR | 14 períodos |
| Risco por trade | 0,25% a 0,50% |
| Risco/retorno mínimo | 2:1 |
| Máximo posições abertas | 5 a 10 |
| Exposição máxima por setor | 30% |
| Stop principal | Técnico ou 1.5x ATR |
| Saída parcial | 2R |
| Trailing stop | EMA 21 |
| Evitar earnings | 5 pregões antes |
| Score mínimo para sinal | 75 |
| Score ideal | > 80 |

## 31. Estrutura Técnica Recomendada

```text
swing-trade-us-equities-bot/
│
├── README.md
├── requirements.txt
├── .env.example
├── config/
│   ├── settings.yaml
│   ├── risk.yaml
│   └── universe.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── backtests/
│   └── trades/
│
├── src/
│   ├── main.py
│   ├── market_data/
│   ├── indicators/
│   ├── filters/
│   ├── setups/
│   ├── scoring/
│   ├── risk/
│   ├── execution/
│   ├── backtesting/
│   ├── portfolio/
│   └── utils/
│
└── tests/
    ├── test_indicators.py
    ├── test_filters.py
    ├── test_setups.py
    ├── test_risk.py
    ├── test_scoring.py
    └── test_backtest.py
```

## 32. Configuração YAML Sugerida

```yaml
market:
  benchmark: "SPY"
  growth_benchmark: "QQQ"
  volatility_index: "^VIX"
  primary_timeframe: "1d"
  secondary_timeframe: "1wk"

universe:
  min_price: 10
  min_market_cap: 2000000000
  min_avg_daily_volume: 1000000
  avoid_penny_stocks: true
  avoid_low_liquidity: true

indicators:
  ema_short: 8
  ema_main: 21
  sma_intermediate: 50
  sma_primary: 200
  rsi_period: 14
  atr_period: 14
  volume_average_period: 20
  relative_strength_periods:
    - 20
    - 50

trend:
  require_price_above_sma50: true
  require_price_above_sma200: true
  require_sma50_above_sma200: true
  require_ema21_slope_positive: true

relative_strength:
  require_vs_spy_positive_20d: true
  require_vs_spy_positive_50d: true
  require_sector_confirmation: true

risk:
  account_size: 100000
  risk_per_trade_percent: 0.5
  max_total_open_risk_percent: 5
  max_sector_exposure_percent: 30
  max_positions: 10
  max_weekly_loss_percent: 3
  max_monthly_loss_percent: 6

setup:
  min_reward_risk: 2.0
  min_score_for_watchlist: 65
  min_score_for_signal: 75
  preferred_score: 80
  avoid_entries_days_before_earnings: 5

exits:
  partial_take_profit_r: 2.0
  partial_position_percent: 50
  trailing_stop: "EMA_21"
  time_stop_days_min: 5
  time_stop_days_max: 10

market_regime:
  allow_longs_if_spy_above_sma200: true
  reduce_size_if_spy_below_sma50: true
  avoid_longs_if_spy_below_sma200: true
```

## 33. Exemplos de Código

### 33.1 Indicadores Básicos

```python
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(period).mean()
```

### 33.2 Força Relativa vs SPY

```python
def period_return(close: pd.Series, period: int) -> pd.Series:
    return close.pct_change(period)


def relative_strength(stock_close: pd.Series, benchmark_close: pd.Series, period: int) -> pd.Series:
    stock_ret = period_return(stock_close, period)
    benchmark_ret = period_return(benchmark_close, period)
    return stock_ret - benchmark_ret
```

### 33.3 Filtro de Tendência

```python
def trend_filter(df: pd.DataFrame) -> bool:
    last = df.iloc[-1]

    return all([
        last["close"] > last["sma_50"],
        last["close"] > last["sma_200"],
        last["sma_50"] > last["sma_200"],
        last["ema_21"] > df["ema_21"].iloc[-5],
    ])
```

### 33.4 Detector de Trend Pullback

```python
def detect_trend_pullback(df: pd.DataFrame) -> dict | None:
    last = df.iloc[-1]
    previous = df.iloc[-2]

    trend_ok = all([
        last["close"] > last["sma_50"],
        last["close"] > last["sma_200"],
        last["sma_50"] > last["sma_200"],
    ])

    pullback_zone = (
        last["low"] <= last["ema_21"] * 1.01
        or last["low"] <= last["sma_50"] * 1.01
    )

    reversal = last["close"] > previous["high"]
    rsi_ok = 50 <= last["rsi_14"] <= 70
    volume_ok = last["volume"] > last["volume_avg_20"]

    if trend_ok and pullback_zone and reversal and rsi_ok and volume_ok:
        entry = last["high"]
        stop = min(last["low"], last["sma_50"])
        risk = entry - stop
        target = entry + (risk * 2)

        return {
            "setup": "trend_pullback",
            "entry": round(entry, 2),
            "stop": round(stop, 2),
            "target": round(target, 2),
            "reward_risk": 2.0,
            "invalidation": "Perda da mínima do pullback ou SMA 50",
        }

    return None
```

### 33.5 Position Sizing

```python
def calculate_position_size(
    account_size: float,
    risk_per_trade_percent: float,
    entry: float,
    stop: float,
) -> int:
    risk_budget = account_size * (risk_per_trade_percent / 100)
    risk_per_share = entry - stop

    if risk_per_share <= 0:
        return 0

    return int(risk_budget // risk_per_share)
```

### 33.6 Score de Oportunidade

```python
def opportunity_score(features: dict) -> int:
    score = 0

    if features["trend_ok"]:
        score += 20
    if features["rs_20d"] > 0:
        score += 12
    if features["rs_50d"] > 0:
        score += 8
    if features["sector_rs"] > 0:
        score += 10
    if features["volume_confirmation"]:
        score += 10
    if features["setup_valid"]:
        score += 20
    if features["reward_risk"] >= 2:
        score += 10
    if features["fundamental_score"] >= 6:
        score += 5
    if not features["dangerous_event"]:
        score += 5

    return min(score, 100)
```

### 33.7 Risk Gate

```python
def risk_gate(candidate: dict, portfolio: dict, config: dict) -> tuple[bool, str]:
    if candidate["reward_risk"] < config["setup"]["min_reward_risk"]:
        return False, "Risco/retorno abaixo do mínimo"

    if candidate["days_until_earnings"] <= config["setup"]["avoid_entries_days_before_earnings"]:
        return False, "Earnings muito próximo"

    if portfolio["open_risk_percent"] >= config["risk"]["max_total_open_risk_percent"]:
        return False, "Risco aberto total atingido"

    if portfolio["sector_exposure_percent"].get(candidate["sector"], 0) >= config["risk"]["max_sector_exposure_percent"]:
        return False, "Exposição setorial acima do limite"

    return True, "Aprovado"
```

### 33.8 Paper Broker

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PaperTrade:
    symbol: str
    side: str
    quantity: int
    entry: float
    stop: float
    target: float
    opened_at: datetime
    status: str = "open"


class PaperBroker:
    def __init__(self):
        self.trades: list[PaperTrade] = []

    def place_order(self, symbol: str, side: str, quantity: int, entry: float, stop: float, target: float):
        trade = PaperTrade(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry=entry,
            stop=stop,
            target=target,
            opened_at=datetime.utcnow(),
        )
        self.trades.append(trade)
        return trade
```

### 33.9 Scanner Simplificado

```python
def scan_universe(universe, price_data, benchmark_data, config):
    watchlist = []

    for symbol in universe:
        df = price_data[symbol].copy()

        if len(df) < 220:
            continue

        df["ema_8"] = ema(df["close"], 8)
        df["ema_21"] = ema(df["close"], 21)
        df["sma_50"] = sma(df["close"], 50)
        df["sma_200"] = sma(df["close"], 200)
        df["rsi_14"] = rsi(df["close"], 14)
        df["atr_14"] = atr(df, 14)
        df["volume_avg_20"] = df["volume"].rolling(20).mean()
        df["rs_20d"] = relative_strength(df["close"], benchmark_data["SPY"]["close"], 20)
        df["rs_50d"] = relative_strength(df["close"], benchmark_data["SPY"]["close"], 50)

        if not trend_filter(df):
            continue

        setup = detect_trend_pullback(df)

        if setup is None:
            continue

        features = {
            "trend_ok": True,
            "rs_20d": df["rs_20d"].iloc[-1],
            "rs_50d": df["rs_50d"].iloc[-1],
            "sector_rs": 0.01,
            "volume_confirmation": df["volume"].iloc[-1] > df["volume_avg_20"].iloc[-1],
            "setup_valid": True,
            "reward_risk": setup["reward_risk"],
            "fundamental_score": 6,
            "dangerous_event": False,
        }

        score = opportunity_score(features)

        if score >= config["setup"]["min_score_for_watchlist"]:
            watchlist.append({
                "symbol": symbol,
                "score": score,
                **setup,
            })

    return sorted(watchlist, key=lambda item: item["score"], reverse=True)
```

## 34. Prompt para Codex

```text
Você é um engenheiro sênior de software quantitativo especializado em trading systems, Python, APIs de mercado, backtesting, análise técnica e gestão de risco.

Quero construir um bot de swing trade para ações americanas baseado no seguinte framework:

Trend Pullback + Breakout Confirmation + Relative Strength vs SPY.

O objetivo da V1 não é operar dinheiro real.

O objetivo da V1 é criar um sistema de scanner, ranking de oportunidades, paper trading, backtesting inicial e validação estatística.

Crie um projeto completo em Python com arquitetura limpa, modular, testável e extensível.

Requisitos da V1:

1. Carregar universo de ações americanas
2. Filtrar liquidez
3. Filtrar market cap
4. Filtrar preço mínimo
5. Calcular médias móveis EMA 8, EMA 21, SMA 50 e SMA 200
6. Calcular RSI 14
7. Calcular ATR 14
8. Calcular volume médio de 20 dias
9. Calcular relative strength vs SPY em 20 e 50 dias
10. Calcular relative strength vs ETF setorial quando disponível
11. Identificar tendência principal
12. Identificar pullback em tendência
13. Identificar breakout de consolidação
14. Identificar reclaim da SMA 50
15. Evitar novas entradas antes de earnings
16. Calcular score de oportunidade
17. Gerar watchlist priorizada
18. Calcular entrada, stop e alvo
19. Validar risco/retorno mínimo de 2:1
20. Calcular tamanho da posição com base no risco
21. Controlar risco total aberto
22. Controlar exposição por setor
23. Simular paper trading
24. Registrar trades
25. Calcular métricas de performance
26. Gerar logs auditáveis
27. Criar README.md
28. Criar testes básicos

Não conecte execução real em corretora na V1.

A prioridade é robustez, clareza, segurança, gestão de risco e validação estatística.
```

## 35. Roadmap Técnico

### V1: Scanner + Paper Trading

- Scanner
- Indicadores
- Setups
- Scoring
- Paper trading
- Logs
- Métricas
- README
- Testes básicos

### V2: Backtesting Robusto

- Backtest de 3 a 5 anos
- Teste por regime de mercado
- Teste por setor
- Teste por setup
- Simulação de slippage
- Walk-forward analysis

### V3: Dashboard

- Dashboard Streamlit ou React
- Watchlist
- Ranking de oportunidades
- Posições abertas
- Risco da carteira
- Métricas de performance
- Alertas

### V4: Integração com Broker

- Integração com corretora
- Execução assistida
- Ordem limit
- Ordem stop
- Ordem bracket
- Kill switch reforçado

### V5: Produção

- Banco de dados
- Monitoramento
- Alertas por email, Telegram ou Slack
- Deploy cloud
- Observabilidade
- Logs persistentes
- Controle de falhas

## 36. Nota de Segurança

Este projeto deve começar obrigatoriamente em modo de simulação.

Não executar ordens reais na V1.

Swing trade envolve risco de mercado, risco overnight, risco de gap, risco de liquidez, risco de earnings, risco macroeconômico e risco de execução.

A meta da V1 não é maximizar retorno.

A meta da V1 é evitar perdas desnecessárias, criar disciplina operacional e medir se a estratégia possui vantagem real.
