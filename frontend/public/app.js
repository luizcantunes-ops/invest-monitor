// ═══════════════════════════════════════════════════════════════
// AUTH
// ═══════════════════════════════════════════════════════════════

const AUTH_KEY = "fc_token";

function getToken() { return localStorage.getItem(AUTH_KEY) || ""; }
function setToken(t) { localStorage.setItem(AUTH_KEY, t); }
function clearToken() { localStorage.removeItem(AUTH_KEY); }

// Wrap fetch to always send the auth token
const _origFetch = window.fetch.bind(window);
window.fetch = function(url, opts = {}) {
  const token = getToken();
  if (token && typeof url === "string" && url.startsWith("/api/")) {
    opts.headers = { ...(opts.headers || {}), "Authorization": `Bearer ${token}` };
  }
  return _origFetch(url, opts);
};

async function initAuth() {
  const gate = document.querySelector("#login-gate");
  const loginForm = document.querySelector("#login-form");
  const loginPwd  = document.querySelector("#login-password");
  const loginErr  = document.querySelector("#login-error");

  // Check existing token
  const res = await _origFetch("/api/auth/check", {
    headers: { "Authorization": `Bearer ${getToken()}` }
  });
  const { ok } = await res.json();
  if (ok) return; // already authenticated

  // Show login gate, block app
  gate.style.display = "flex";

  await new Promise(resolve => {
    loginForm.addEventListener("submit", async e => {
      e.preventDefault();
      loginErr.style.display = "none";
      const password = loginPwd.value;
      const r = await _origFetch("/api/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ password })
      });
      const data = await r.json();
      if (r.ok) {
        setToken(data.token);
        gate.style.display = "none";
        resolve();
      } else {
        loginErr.style.display = "block";
        loginPwd.value = "";
        loginPwd.focus();
      }
    });
  });
}

await initAuth();

// ═══════════════════════════════════════════════════════════════

const form = document.querySelector("#quote-form");
const input = document.querySelector("#symbol");
const statusStrip = document.querySelector("#status-strip");
const portfolioForm = document.querySelector("#portfolio-form");
const importPortfolioButton = document.querySelector("#import-portfolio");
const portfolioRows = document.querySelector("#portfolio-rows");
const portfolioTotal = document.querySelector("#portfolio-total");
const portfolioInvested = document.querySelector("#portfolio-invested");
const portfolioCurrent = document.querySelector("#portfolio-current");
const portfolioResult = document.querySelector("#portfolio-result");
const portfolioScore = document.querySelector("#portfolio-score");
const decisionRegime = document.querySelector("#decision-regime");
const decisionPortfolio = document.querySelector("#decision-portfolio");
const decisionSentiment = document.querySelector("#decision-sentiment");
const decisionPosture = document.querySelector("#decision-posture");
const marketRegimeLabel = document.querySelector("#market-regime-label");
const marketRegimeScore = document.querySelector("#market-regime-score");
const marketRegimeValuation = document.querySelector("#market-regime-valuation");
const marketRegimeLiquidity = document.querySelector("#market-regime-liquidity");
const marketRegimeSentiment = document.querySelector("#market-regime-sentiment");
const macroIndicators = document.querySelector("#macro-indicators");
const investorsCache = document.querySelector("#investors-cache");
const investorList = document.querySelector("#investor-list");
const marketState = document.querySelector("#market-state");
const quoteSymbol = document.querySelector("#quote-symbol");
const quotePrice = document.querySelector("#quote-price");
const quoteChange = document.querySelector("#quote-change");
const quoteExchange = document.querySelector("#quote-exchange");
const quoteCurrency = document.querySelector("#quote-currency");
const quotePrevious = document.querySelector("#quote-previous");
const miniChart = document.querySelector("#mini-chart");
const localChart = document.querySelector("#local-chart");
const tradingViewLink = document.querySelector("#tradingview-link");
const analysisSource = document.querySelector("#analysis-source");
const recommendationLabel = document.querySelector("#recommendation-label");
const targetMean = document.querySelector("#target-mean");
const analystCount = document.querySelector("#analyst-count");
const targetLow = document.querySelector("#target-low");
const targetMedian = document.querySelector("#target-median");
const targetHigh = document.querySelector("#target-high");
const recommendationBars = document.querySelector("#recommendation-bars");
const upgradeList = document.querySelector("#upgrade-list");
const readingBias = document.querySelector("#reading-bias");
const readingTrend = document.querySelector("#reading-trend");
const readingMomentum = document.querySelector("#reading-momentum");
const readingRsi = document.querySelector("#reading-rsi");
const readingVolume = document.querySelector("#reading-volume");
const readingAnalytical = document.querySelector("#reading-analytical");
const readingPrescriptive = document.querySelector("#reading-prescriptive");
const readingDidactic = document.querySelector("#reading-didactic");
const sentimentSource = document.querySelector("#sentiment-source");
const sentimentLabel = document.querySelector("#sentiment-label");
const sentimentScore = document.querySelector("#sentiment-score");
const sentimentRelevance = document.querySelector("#sentiment-relevance");
const sentimentCount = document.querySelector("#sentiment-count");
const newsList = document.querySelector("#news-list");
const alternativeSource = document.querySelector("#alternative-source");
const insiderSignal = document.querySelector("#insider-signal");
const insiderPurchases = document.querySelector("#insider-purchases");
const insiderOfficerPurchases = document.querySelector("#insider-officer-purchases");
const insiderTotalBought = document.querySelector("#insider-total-bought");
const insiderSales = document.querySelector("#insider-sales");
const insiderList = document.querySelector("#insider-list");
const congressSignal = document.querySelector("#congress-signal");
const congressNote = document.querySelector("#congress-note");
const congressLink = document.querySelector("#congress-link");

const exchangeMap = {
  NMS: "NASDAQ",
  NAS: "NASDAQ",
  NYQ: "NYSE",
  ASE: "AMEX",
  PCX: "AMEX",
  SAO: "BMFBOVESPA"
};

const formatterCache = new Map();
const recommendationLabels = {
  strong_buy: "Compra forte",
  buy: "Compra",
  hold: "Manter",
  sell: "Venda",
  strong_sell: "Venda forte",
  none: "Sem consenso"
};
const portfolioStorageKey = "finance-connect-portfolio";
const tacticalTypes = ["Tatico", "Tatico growth", "Tatico tematico", "Tatico/energia", "Tatico/semicondutores", "Ciclico/valor", "Revisao de qualidade"];

function currencyFormatter(currency = "USD") {
  if (!formatterCache.has(currency)) {
    formatterCache.set(currency, new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency,
      maximumFractionDigits: 2
    }));
  }
  return formatterCache.get(currency);
}

function setStatus(message, isError = false) {
  statusStrip.classList.toggle("error", isError);
  statusStrip.querySelector("span:last-child").textContent = message;
}

function sentimentClass(label) {
  if (label === "favoravel") return "good";
  if (label === "alerta") return "bad";
  return "watch";
}

function renderMarketRegime(data) {
  marketRegimeLabel.textContent = data.label || "--";
  marketRegimeScore.textContent = `${data.score ?? "--"}/100`;
  decisionRegime.textContent = data.label || "--";
  decisionPosture.textContent = data.score >= 65 ? "Construtiva" : data.score >= 45 ? "Seletiva" : "Defensiva";
  marketRegimeValuation.textContent = data.indicators?.some((item) => item.pillar === "Valuation" && item.current !== "Pendente")
    ? "Parcial"
    : "Pendente";
  marketRegimeLiquidity.textContent = data.indicators?.some((item) => item.pillar === "Macro e credito" && item.current !== "Pendente")
    ? "Parcial"
    : "Pendente";
  marketRegimeSentiment.textContent = data.indicators?.some((item) => item.pillar === "Sentimento" && item.current !== "Pendente")
    ? "Parcial"
    : "Pendente";

  macroIndicators.innerHTML = (data.indicators || []).map((item) => `
    <article class="macro-card ${sentimentClass(item.tone?.label)}">
      <div class="macro-card-head">
        <div>
          <span>${escapeHtml(item.pillar)}</span>
          <h2>${escapeHtml(item.name)}</h2>
        </div>
        <strong>${escapeHtml(item.tone?.emoji || "⚪")} ${escapeHtml(item.tone?.label || "pendente")}</strong>
      </div>
      <p>${escapeHtml(item.measures)}</p>
      <dl>
        <div>
          <dt>Leitura atual</dt>
          <dd>${escapeHtml(item.current)}</dd>
        </div>
        <div>
          <dt>Contexto histórico</dt>
          <dd>${escapeHtml(item.context)}</dd>
        </div>
        <div>
          <dt>Implicação para a carteira</dt>
          <dd>${escapeHtml(item.implication)}</dd>
        </div>
      </dl>
    </article>
  `).join("");
}

function renderInvestors(data) {
  investorsCache.textContent = data.cached ? "Cache ativo" : "13F 6h · ARK 1h";
  investorList.innerHTML = (data.investors || []).map((investor) => `
    <article class="investor-card">
      <div class="investor-card-head">
        <div>
          <h2>${escapeHtml(investor.name)}</h2>
          <span>${escapeHtml(investor.source)} · cache ${escapeHtml(investor.cacheTtl)}</span>
        </div>
        <strong>${escapeHtml(investor.status)}</strong>
      </div>
      <p>${escapeHtml(investor.focus)}</p>
      ${investor.date ? `<p class="muted-note">Base ${escapeHtml(investor.date)} · ${escapeHtml(investor.holdingCount)} holdings</p>` : ""}
      <p class="muted-note">${escapeHtml(investor.overlapHint)}</p>
      <div class="investor-changes">
        <div><span>Novas</span><strong>${investor.changes?.newPositions?.length || 0}</strong></div>
        <div><span>Aumentos</span><strong>${investor.changes?.increases?.length || 0}</strong></div>
        <div><span>Reduções</span><strong>${investor.changes?.reductions?.length || 0}</strong></div>
      </div>
      <div class="holding-list">${investor.topHoldings?.length
        ? investor.topHoldings.map((holding) => `
          <span>${holding.overlap ? "🔗 " : ""}${escapeHtml(holding.symbol)}${holding.weight ? ` · ${formatNumber(holding.weight)}%` : ""} · ${escapeHtml(holding.direction || "monitorar")}</span>
        `).join("")
        : "<span>Top 10 pendente de parser</span>"}
      </div>
    </article>
  `).join("");
}

// Legacy — replaced by loadMacro() below
async function refreshMarketRegime() { await loadMacro(); }
async function refreshInvestors()    { await loadInvestors(); }

function parseLocalNumber(value) {
  return Number(String(value || "").replace(",", "."));
}

function formatPercent(value) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatNumber(value, fallback = "--") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return fallback;
  }

  return new Intl.NumberFormat("pt-BR", {
    maximumFractionDigits: 2
  }).format(value);
}

function formatLargeMoney(value, currency = "USD") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }

  const suffix = Math.abs(value) >= 1_000_000 ? "T" : Math.abs(value) >= 1_000 ? "B" : "M";
  const divisor = suffix === "T" ? 1_000_000 : suffix === "B" ? 1_000 : 1;
  return `${currency} ${formatNumber(value / divisor)}${suffix}`;
}

function formatMetricPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }

  return `${formatNumber(value)}%`;
}

function formatDateFromEpoch(value) {
  if (!value) {
    return "";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(new Date(value * 1000));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function loadPortfolio() {
  try {
    return JSON.parse(localStorage.getItem(portfolioStorageKey)) || [];
  } catch {
    return [];
  }
}

function savePortfolio(positions) {
  localStorage.setItem(portfolioStorageKey, JSON.stringify(positions));
}

function technicalScore(reading) {
  if (!reading) {
    return 0;
  }

  let score = 50;

  if (reading.trend === "alta") score += 18;
  if (reading.trend === "baixa") score -= 18;
  if (reading.momentum === "positivo") score += 12;
  if (reading.momentum === "fraco") score -= 12;
  if (reading.momentum === "sobrecomprado") score -= 4;
  if (reading.momentum === "sobrevendido") score += 4;
  if (reading.volumeRatio >= 1.1 && reading.trend === "alta") score += 10;
  if (reading.volumeRatio < 0.75 && reading.trend === "alta") score -= 6;
  if (reading.bias === "construtivo") score += 10;
  if (reading.bias === "defensivo") score -= 10;

  return Math.max(0, Math.min(100, Math.round(score)));
}

function scoreLabel(score) {
  if (score >= 75) return "Manter forte";
  if (score >= 60) return "Manter";
  if (score >= 45) return "Monitorar";
  if (score >= 30) return "Reduzir risco";
  return "Tese fraca";
}

function buildPositionAlerts(row) {
  const alerts = [];
  const price = row.quote?.price;
  const reading = row.quote?.chartReading;
  const isTactical = tacticalTypes.includes(row.type);

  if (price && row.stop) {
    const stopDistance = ((price - row.stop) / price) * 100;
    if (price <= row.stop) {
      alerts.push("Stop atingido");
    } else if (stopDistance <= 3) {
      alerts.push("Perto do stop");
    }
  }

  if (price && row.target) {
    const targetDistance = ((row.target - price) / price) * 100;
    if (price >= row.target) {
      alerts.push("Alvo atingido");
    } else if (targetDistance <= 3) {
      alerts.push("Alvo proximo");
    }
  }

  if (reading?.rsi14 >= 70) {
    alerts.push("RSI sobrecomprado");
  }

  if (reading?.rsi14 <= 30) {
    alerts.push("RSI sobrevendido");
  }

  if (row.score < 45) {
    alerts.push("Tecnico enfraquecido");
  }

  if (reading?.trend === "alta" && reading?.volumeRatio < 0.75) {
    alerts.push("Alta com volume fraco");
  }

  if (row.score >= 75 && reading?.volumeRatio >= 0.9) {
    alerts.push("Oportunidade tecnica");
  }

  if (isTactical && row.score >= 70 && row.resultPercent > 20) {
    alerts.push("Proteger lucro");
  }

  if (isTactical && row.score < 60) {
    alerts.push("Nao tratar como hold");
  }

  if (String(row.type || "").includes("Nucleo") && row.score < 45) {
    alerts.push("Nucleo em revisao");
  }

  return alerts;
}

function riskReward(row) {
  const price = row.quote?.price;

  if (!price || !row.stop || !row.target || row.stop >= price) {
    return null;
  }

  const risk = price - row.stop;
  const reward = row.target - price;

  if (reward <= 0) {
    return 0;
  }

  return reward / risk;
}

function resolveTradingViewSymbol(quote) {
  const exchange = exchangeMap[quote.exchange] || quote.exchange || "";
  return exchange ? `${exchange}:${quote.symbol}` : quote.symbol;
}

function renderEmptyAnalysis(message) {
  analysisSource.textContent = "Indisponivel";
  recommendationLabel.textContent = "Dados indisponiveis";
  targetMean.textContent = "--";
  analystCount.textContent = message;
  targetLow.textContent = "--";
  targetMedian.textContent = "--";
  targetHigh.textContent = "--";
  recommendationBars.innerHTML = "";
  upgradeList.innerHTML = `<p class="muted-note">${message}</p>`;
}

function renderRecommendationBars(trend) {
  const current = trend.find((item) => item.period === "0m") || trend[0];

  if (!current) {
    recommendationBars.innerHTML = `<p class="muted-note">Sem distribuicao de recomendacoes.</p>`;
    return;
  }

  const rows = [
    ["Compra forte", current.strongBuy],
    ["Compra", current.buy],
    ["Manter", current.hold],
    ["Venda", current.sell],
    ["Venda forte", current.strongSell]
  ];
  const max = Math.max(...rows.map((row) => row[1]), 1);

  recommendationBars.innerHTML = rows.map(([label, value]) => `
    <div class="bar-row">
      <span>${escapeHtml(label)}</span>
      <div class="bar-track"><i style="width:${(value / max) * 100}%"></i></div>
      <strong>${value}</strong>
    </div>
  `).join("");
}

function renderUpgrades(upgrades) {
  if (!upgrades.length) {
    upgradeList.innerHTML = `<p class="muted-note">Sem upgrades ou downgrades recentes.</p>`;
    return;
  }

  upgradeList.innerHTML = upgrades.map((item) => {
    const grades = [item.fromGrade, item.toGrade].filter(Boolean).join(" -> ");
    return `
      <article class="upgrade-item">
        <strong>${escapeHtml(item.firm)}</strong>
        <span>${escapeHtml(item.action)}${grades ? `: ${escapeHtml(grades)}` : ""}</span>
        <small>${formatDateFromEpoch(item.epochGradeDate)}</small>
      </article>
    `;
  }).join("");
}

function renderAnalysis(analysis, currency) {
  const money = currencyFormatter(currency);
  const label = recommendationLabels[analysis.recommendationKey] || analysis.recommendationKey || "Sem consenso";

  if (analysis.demo) {
    renderEmptyAnalysis("Yahoo bloqueou este ticker — sem dados de analistas.");
    analysisSource.textContent = "Indisponivel";
    return;
  }

  const src = analysis.source === "python"
    ? (analysis.cached ? "yfinance, cache" : "yfinance")
    : (analysis.cached ? "Yahoo, cache" : "Yahoo");
  analysisSource.textContent = src;
  recommendationLabel.textContent = label;
  targetMean.textContent = analysis.targetMeanPrice ? money.format(analysis.targetMeanPrice) : "--";
  analystCount.textContent = analysis.numberOfAnalystOpinions
    ? `${analysis.numberOfAnalystOpinions} analistas${analysis.recommendationMean ? `, nota ${formatNumber(analysis.recommendationMean)}` : ""}`
    : "Número de analistas não informado";
  targetLow.textContent    = analysis.targetLowPrice    ? money.format(analysis.targetLowPrice)    : "--";
  targetMedian.textContent = analysis.targetMedianPrice ? money.format(analysis.targetMedianPrice) : "--";
  targetHigh.textContent   = analysis.targetHighPrice   ? money.format(analysis.targetHighPrice)   : "--";

  renderRecommendationBars(analysis.trend || []);
  if (analysis.partialData) {
    upgradeList.innerHTML = `<p class="muted-note">Dados via yfinance — histórico de upgrades indisponível nesta fonte.</p>`;
  } else {
    renderUpgrades(analysis.upgrades || []);
  }
}

function renderList(element, items) {
  element.innerHTML = items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderChartReading(reading) {
  if (!reading) {
    readingBias.textContent = "--";
    readingTrend.textContent = "--";
    readingMomentum.textContent = "--";
    readingRsi.textContent = "--";
    readingVolume.textContent = "--";
    renderList(readingAnalytical, ["Sem candles suficientes para leitura."]);
    renderList(readingPrescriptive, ["Aguarde mais dados antes de montar um cenario."]);
    renderList(readingDidactic, ["Toda leitura grafica depende de contexto e confirmacao."]);
    return;
  }

  readingBias.textContent = reading.bias || "--";
  readingTrend.textContent = reading.trend || "--";
  readingMomentum.textContent = reading.momentum || "--";
  readingRsi.textContent = reading.rsi14 === null ? "--" : formatNumber(reading.rsi14);
  readingVolume.textContent = reading.volumeRatio === null ? "--" : `${formatNumber(reading.volumeRatio)}x`;
  renderList(readingAnalytical, reading.analytical || []);
  renderList(readingPrescriptive, reading.prescriptive || []);
  renderList(readingDidactic, reading.didactic || []);
}

function formatNewsDate(value) {
  if (!value || value.length < 8) {
    return "";
  }

  const year = value.slice(0, 4);
  const month = value.slice(4, 6);
  const day = value.slice(6, 8);
  const hour = value.slice(9, 11) || "00";
  const minute = value.slice(11, 13) || "00";
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(`${year}-${month}-${day}T${hour}:${minute}:00Z`));
}

function renderEmptySentiment(message) {
  sentimentSource.textContent = "Alpha Vantage";
  sentimentLabel.textContent = "--";
  sentimentScore.textContent = "--";
  sentimentRelevance.textContent = "--";
  sentimentCount.textContent = "--";
  newsList.innerHTML = `<p class="muted-note">${escapeHtml(message)}</p>`;
}

function renderSentiment(data) {
  sentimentSource.textContent = data.cached ? "Alpha Vantage, cache" : "Alpha Vantage";
  sentimentLabel.textContent = data.label || "--";
  decisionSentiment.textContent = data.label || "--";
  sentimentScore.textContent = data.averageSentiment === null ? "--" : `${formatNumber(data.averageSentiment)} / +1`;
  sentimentRelevance.textContent = data.averageRelevance === null ? "--" : `${formatNumber(data.averageRelevance)} / 1`;
  sentimentCount.textContent = data.articleCount ?? "--";

  if (!data.news?.length) {
    newsList.innerHTML = `<p class="muted-note">Sem noticias recentes para este ticker.</p>`;
    return;
  }

  newsList.innerHTML = data.news.map((item) => `
    <article class="news-item">
      <div>
        <a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.title)}</a>
        <small>${escapeHtml(item.source)} · ${escapeHtml(formatNewsDate(item.timePublished))}</small>
      </div>
      <strong>${escapeHtml(item.tickerSentimentLabel || item.overallSentimentLabel || "--")}</strong>
    </article>
  `).join("");
}

function renderEmptyAlternative(message) {
  alternativeSource.textContent = "OpenInsider · Quiver";
  insiderSignal.textContent = "--";
  insiderPurchases.textContent = "--";
  insiderOfficerPurchases.textContent = "--";
  insiderTotalBought.textContent = "--";
  insiderSales.textContent = "--";
  insiderList.innerHTML = `<p class="muted-note">${escapeHtml(message)}</p>`;
  congressSignal.textContent = "--";
  congressNote.textContent = message;
}

function renderAlternativeSignals(data, currency = "USD") {
  const money = currencyFormatter(currency);
  const insiders = data.insiders || {};
  const congress = data.congress || {};
  const provider = insiders.provider || "Finnhub";

  alternativeSource.textContent = data.cached ? `${provider} · Quiver, cache` : `${provider} · Quiver`;
  insiderSignal.textContent = insiders.signal || "--";

  // Finnhub doesn't return per-transaction counts — show totals instead
  const hasCounts = insiders.purchases > 0 || insiders.sales > 0;
  insiderPurchases.textContent       = hasCounts ? insiders.purchases : "--";
  insiderOfficerPurchases.textContent = hasCounts ? insiders.officerPurchases : "--";
  insiderSales.textContent            = hasCounts ? insiders.sales : "--";
  insiderTotalBought.textContent = insiders.totalBought
    ? money.format(insiders.totalBought) : "--";

  // Trades: Finnhub returns summary strings, not structured objects
  if (insiders.trades?.length) {
    insiderList.innerHTML = insiders.trades.map(t => {
      const text = typeof t === "string" ? t : (t.insider || "");
      return `<div style="font-size:11px;color:var(--muted);padding:3px 0;border-top:1px solid var(--surface-2)">${escapeHtml(text)}</div>`;
    }).join("");
  } else {
    insiderList.innerHTML = `<p class="muted-note">${escapeHtml(insiders.status || "Sem movimentação recente de insiders")}</p>`;
  }

  congressSignal.textContent = congress.signal || "--";
  congressNote.textContent   = congress.note || congress.status || "--";
  congressLink.href          = congress.url || "https://www.quiverquant.com/congresstrading/";
}

function pointsFromValues(values, width, height, padding, min, max) {
  const range = max - min || 1;
  const step = (width - padding * 2) / Math.max(values.length - 1, 1);

  return values.map((value, index) => {
    const x = padding + index * step;
    const y = height - padding - ((value - min) / range) * (height - padding * 2);
    return { x, y };
  });
}

function movingAverage(values, period) {
  return values.map((_, index) => {
    if (index + 1 < period) {
      return null;
    }

    return averageClient(values.slice(index + 1 - period, index + 1));
  });
}

function averageClient(values) {
  const filtered = values.filter((value) => Number.isFinite(value));
  return filtered.length ? filtered.reduce((sum, value) => sum + value, 0) / filtered.length : null;
}

function pathFromPoints(points) {
  return points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(" ");
}

function renderLocalChart(quote) {
  const candles = quote.candles || [];

  if (candles.length < 2) {
    localChart.innerHTML = `<p class="muted-note">Sem candles suficientes para desenhar o grafico.</p>`;
    return;
  }

  const width = 900;
  const height = 430;
  const padding = 46;
  const closes = candles.map((candle) => candle.close);
  const highs = candles.map((candle) => candle.high ?? candle.close);
  const lows = candles.map((candle) => candle.low ?? candle.close);
  const min = Math.min(...lows);
  const max = Math.max(...highs);
  const closePoints = pointsFromValues(closes, width, height, padding, min, max);
  const sma5 = movingAverage(closes, 5);
  const sma20 = movingAverage(closes, 20);
  const sma5Points = pointsFromValues(sma5.map((value) => value ?? min), width, height, padding, min, max)
    .filter((_, index) => sma5[index] !== null);
  const sma20Points = pointsFromValues(sma20.map((value) => value ?? min), width, height, padding, min, max)
    .filter((_, index) => sma20[index] !== null);
  const support = quote.chartReading?.support ?? Math.min(...lows.slice(-20));
  const resistance = quote.chartReading?.resistance ?? Math.max(...highs.slice(-20));
  const supportY = height - padding - ((support - min) / (max - min || 1)) * (height - padding * 2);
  const resistanceY = height - padding - ((resistance - min) / (max - min || 1)) * (height - padding * 2);
  const area = [
    `${padding},${height - padding}`,
    ...closePoints.map((point) => `${point.x.toFixed(2)},${point.y.toFixed(2)}`),
    `${width - padding},${height - padding}`
  ].join(" ");

  localChart.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Grafico de ${escapeHtml(quote.symbol)} com fechamento, medias, suporte e resistencia">
      <rect x="0" y="0" width="${width}" height="${height}" rx="8" fill="oklch(98% 0.005 230)"></rect>
      <line x1="${padding}" x2="${width - padding}" y1="${resistanceY}" y2="${resistanceY}" stroke="oklch(56% 0.18 28)" stroke-width="1.5" stroke-dasharray="6 6"></line>
      <line x1="${padding}" x2="${width - padding}" y1="${supportY}" y2="${supportY}" stroke="oklch(50% 0.13 152)" stroke-width="1.5" stroke-dasharray="6 6"></line>
      <polygon points="${area}" fill="oklch(58% 0.16 168 / 12%)"></polygon>
      <path d="${pathFromPoints(closePoints)}" fill="none" stroke="oklch(42% 0.13 168)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></path>
      <path d="${pathFromPoints(sma5Points)}" fill="none" stroke="oklch(62% 0.14 230)" stroke-width="2.5" stroke-linecap="round"></path>
      <path d="${pathFromPoints(sma20Points)}" fill="none" stroke="oklch(58% 0.11 72)" stroke-width="2.5" stroke-linecap="round"></path>
      <text x="${padding}" y="24" fill="oklch(23% 0.018 238)" font-size="16" font-weight="700">${escapeHtml(quote.symbol)} · 1 mês</text>
      <text x="${padding}" y="${resistanceY - 8}" fill="oklch(56% 0.18 28)" font-size="12">Resistência ${currencyFormatter(quote.currency).format(resistance)}</text>
      <text x="${padding}" y="${supportY + 18}" fill="oklch(50% 0.13 152)" font-size="12">Suporte ${currencyFormatter(quote.currency).format(support)}</text>
      <g transform="translate(${width - 260} 22)">
        <circle cx="0" cy="0" r="5" fill="oklch(42% 0.13 168)"></circle><text x="12" y="4" font-size="12" fill="oklch(49% 0.024 238)">Fechamento</text>
        <circle cx="95" cy="0" r="5" fill="oklch(62% 0.14 230)"></circle><text x="107" y="4" font-size="12" fill="oklch(49% 0.024 238)">MM5</text>
        <circle cx="155" cy="0" r="5" fill="oklch(58% 0.11 72)"></circle><text x="167" y="4" font-size="12" fill="oklch(49% 0.024 238)">MM20</text>
      </g>
    </svg>
  `;
}

function drawMiniChart(candles) {
  if (!candles.length) {
    miniChart.innerHTML = "";
    return;
  }

  const width = 320;
  const height = 180;
  const padding = 18;
  const values = candles.map((point) => point.close);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = (width - padding * 2) / Math.max(candles.length - 1, 1);
  const points = values.map((value, index) => {
    const x = padding + index * step;
    const y = height - padding - ((value - min) / range) * (height - padding * 2);
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  });

  const area = `${padding},${height - padding} ${points.join(" ")} ${width - padding},${height - padding}`;

  miniChart.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Historico de fechamento de 1 mes">
      <polygon points="${area}" fill="oklch(58% 0.16 168 / 14%)"></polygon>
      <polyline points="${points.join(" ")}" fill="none" stroke="oklch(42% 0.13 168)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></polyline>
    </svg>
  `;
}

function loadTradingView(symbol) {
  const container = document.querySelector("#tradingview-widget");
  container.innerHTML = "";

  const script = document.createElement("script");
  script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
  script.async = true;
  script.textContent = JSON.stringify({
    autosize: true,
    symbol,
    interval: "D",
    timezone: "America/Sao_Paulo",
    theme: "light",
    style: "1",
    locale: "br",
    allow_symbol_change: true,
    calendar: false,
    support_host: "https://www.tradingview.com"
  });
  container.appendChild(script);
  tradingViewLink.href = `https://www.tradingview.com/chart/?symbol=${encodeURIComponent(symbol)}`;
}

function renderQuote(quote) {
  const money = currencyFormatter(quote.currency);
  const directionClass = quote.change >= 0 ? "positive" : "negative";
  const tradingViewSymbol = resolveTradingViewSymbol(quote);

  marketState.textContent = quote.marketState || "--";
  quoteSymbol.textContent = quote.symbol;
  quotePrice.textContent = money.format(quote.price);
  quoteChange.textContent = `${quote.change >= 0 ? "+" : ""}${money.format(quote.change)} (${formatPercent(quote.changePercent)})`;
  quoteChange.className = directionClass;
  quoteExchange.textContent = quote.exchange || "--";
  quoteCurrency.textContent = quote.currency || "--";
  quotePrevious.textContent = money.format(quote.previousClose);

  drawMiniChart(quote.candles);
  renderLocalChart(quote);
  renderChartReading(quote.chartReading);
  loadTradingView(tradingViewSymbol);
}

async function fetchQuote(symbol) {
  setStatus(`Consultando ${symbol} no Yahoo Finance...`);
  form.querySelector("button").disabled = true;
  renderEmptyAnalysis("Carregando dados de analistas...");
  renderEmptySentiment("Carregando sentimento de mercado...");
  renderEmptyAlternative("Carregando sinais alternativos...");

  try {
    const [response, analysisResponse, sentimentResponse, alternativeResponse] = await Promise.all([
      fetch(`/api/quote?symbol=${encodeURIComponent(symbol)}`),
      fetch(`/api/analysis?symbol=${encodeURIComponent(symbol)}`),
      fetch(`/api/sentiment?symbol=${encodeURIComponent(symbol)}`),
      fetch(`/api/alternative-signals?symbol=${encodeURIComponent(symbol)}`)
    ]);
    const payload = await response.json();
    const analysisPayload = await analysisResponse.json();
    const sentimentPayload = await sentimentResponse.json();
    const alternativePayload = await alternativeResponse.json();

    if (!response.ok) {
      throw new Error(payload.error || "Nao foi possivel consultar o ticker.");
    }

    renderQuote(payload);
    loadSwingAnalysis(payload.symbol);  // fire and forget — loads in parallel
    if (analysisResponse.ok) {
      renderAnalysis(analysisPayload, payload.currency);
      setStatus(`${payload.symbol} atualizado. Tecnico e sentimento carregados.`);
    } else {
      renderEmptyAnalysis(analysisPayload.error || "Yahoo limitou os dados de analistas.");
      setStatus(`${payload.symbol} atualizado. Tecnico e sentimento carregados.`);
    }

    if (sentimentResponse.ok) {
      renderSentiment(sentimentPayload);
    } else {
      renderEmptySentiment(sentimentPayload.error || "Sentimento indisponivel.");
    }

    if (alternativeResponse.ok) {
      renderAlternativeSignals(alternativePayload, payload.currency);
    } else {
      renderEmptyAlternative(alternativePayload.error || "Sinais alternativos indisponiveis.");
    }
  } catch (error) {
    setStatus(error.message, true);
    renderEmptyAnalysis(error.message);
    renderEmptySentiment(error.message);
    renderEmptyAlternative(error.message);
  } finally {
    form.querySelector("button").disabled = false;
  }
}

async function fetchQuoteOnly(symbol) {
  const response = await fetch(`/api/quote?symbol=${encodeURIComponent(symbol)}`);
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.error || `Nao foi possivel consultar ${symbol}.`);
  }

  return payload;
}

function renderPortfolioLoading() {
  portfolioRows.innerHTML = `
    <tr>
      <td colspan="9">Atualizando carteira...</td>
    </tr>
  `;
}

function renderPortfolioEmpty() {
  portfolioTotal.textContent = "0 ativos";
  portfolioInvested.textContent = "--";
  portfolioCurrent.textContent = "--";
  portfolioResult.textContent = "--";
  portfolioScore.textContent = "--";
  decisionPortfolio.textContent = "Sem posições";
  portfolioRows.innerHTML = `
    <tr>
      <td colspan="9">Cadastre uma posição para monitorar sua carteira.</td>
    </tr>
  `;
}

async function refreshPortfolio() {
  const positions = loadPortfolio();

  if (!positions.length) {
    renderPortfolioEmpty();
    return;
  }

  renderPortfolioLoading();

  const rows = await Promise.all(positions.map(async (position) => {
    try {
      const quote = await fetchQuoteOnly(position.symbol);
      const invested = position.quantity * position.average;
      const current = position.quantity * quote.price;
      const result = current - invested;
      const resultPercent = invested ? (result / invested) * 100 : 0;
      const score = technicalScore(quote.chartReading);

      return {
        ...position,
        quote,
        invested,
        current,
        result,
        resultPercent,
        score,
        alerts: [],
        error: null
      };
    } catch (error) {
      return { ...position, error: error.message, invested: position.quantity * position.average, current: 0, result: 0, score: 0 };
    }
  }));

  const totalInvested = rows.reduce((sum, row) => sum + row.invested, 0);
  const totalCurrent = rows.reduce((sum, row) => sum + row.current, 0);
  const totalResult = totalCurrent - totalInvested;
  const weightedScore = totalCurrent
    ? rows.reduce((sum, row) => sum + row.score * (row.current / totalCurrent), 0)
    : 0;
  const baseCurrency = rows.find((row) => row.quote?.currency)?.quote.currency || "USD";
  const money = currencyFormatter(baseCurrency);

  portfolioTotal.textContent = `${rows.length} ${rows.length === 1 ? "ativo" : "ativos"}`;
  portfolioInvested.textContent = money.format(totalInvested);
  portfolioCurrent.textContent = money.format(totalCurrent);
  portfolioResult.textContent = `${totalResult >= 0 ? "+" : ""}${money.format(totalResult)} (${formatPercent(totalInvested ? (totalResult / totalInvested) * 100 : 0)})`;
  portfolioResult.className = totalResult >= 0 ? "positive" : "negative";
  portfolioScore.textContent = `${Math.round(weightedScore)}/100`;
  decisionPortfolio.textContent = `${rows.length} ativos · ${Math.round(weightedScore)}/100`;

  portfolioRows.innerHTML = rows.map((row) => {
    const alerts = row.error ? [] : buildPositionAlerts(row);
    const rr = row.error ? null : riskReward(row);

    if (row.error) {
      return `
        <tr>
          <td><strong>${escapeHtml(row.symbol)}</strong></td>
          <td colspan="7">${escapeHtml(row.error)}</td>
          <td><button class="icon-button" data-remove="${escapeHtml(row.id)}" type="button" aria-label="Remover ${escapeHtml(row.symbol)}">Remover</button></td>
        </tr>
      `;
    }

    const rowMoney = currencyFormatter(row.quote.currency);
    const resultClass = row.result >= 0 ? "positive" : "negative";
    const weight = totalCurrent ? (row.current / totalCurrent) * 100 : 0;

    return `
      <tr>
        <td>
          <button class="link-button" data-load-symbol="${escapeHtml(row.symbol)}" type="button" aria-label="Carregar ${escapeHtml(row.symbol)}">${escapeHtml(row.symbol)}</button>
          <small>${escapeHtml(row.type || "Swing")} · ${escapeHtml(row.quote.exchange || "")}</small>
        </td>
        <td>
          <strong>${rowMoney.format(row.current)}</strong>
          <small>${formatNumber(row.quantity)} un, peso ${formatNumber(weight)}%</small>
        </td>
        <td>
          <strong class="${resultClass}">${row.result >= 0 ? "+" : ""}${rowMoney.format(row.result)}</strong>
          <small>${formatPercent(row.resultPercent)}</small>
        </td>
        <td>
          <strong>${row.score}/100</strong>
          <small>${scoreLabel(row.score)}</small>
        </td>
        <td>
          <strong>${escapeHtml(row.type || "Monitorado")}</strong>
          <small>${escapeHtml(row.mandate || "Definir tese e criterio de saida.")}</small>
        </td>
        <td>
          <strong>${rr === null ? "--" : `${formatNumber(rr)}:1`}</strong>
          <small>Stop ${row.stop ? rowMoney.format(row.stop) : "--"} · Alvo ${row.target ? rowMoney.format(row.target) : "--"}</small>
        </td>
        <td>
          <div class="alert-tags">${alerts.length
            ? alerts.map((alert) => `<span>${escapeHtml(alert)}</span>`).join("")
            : "<small>Sem alertas</small>"}
          </div>
        </td>
        <td>${escapeHtml(row.thesis || "Sem tese registrada")}</td>
        <td><button class="icon-button" data-remove="${escapeHtml(row.id)}" type="button" aria-label="Remover ${escapeHtml(row.symbol)}">Remover</button></td>
      </tr>
    `;
  }).join("");
}


form.addEventListener("submit", (event) => {
  event.preventDefault();
  const symbol = input.value.trim().toUpperCase();

  if (symbol) {
    input.value = symbol;
    fetchQuote(symbol);
  }
});

fetchQuote(input.value);
loadMarketSentiment();

// ═══════════════════════════════════════════════════════════════
// MARKET SENTIMENT (decision strip — always visible)
// ═══════════════════════════════════════════════════════════════

const decisionVix   = document.querySelector("#decision-vix");
const decisionSwing = document.querySelector("#decision-swing");

async function loadMarketSentiment() {
  try {
    const res  = await fetch("/api/py/market-sentiment");
    const data = await res.json();
    if (data.error) return;

    const vixEl   = decisionVix;
    const swingEl = decisionSwing;
    const regimeEl = document.querySelector("#decision-regime");

    if (regimeEl) {
      regimeEl.textContent = data.regime_label || "—";
      regimeEl.className = data.regime_color === "good" ? "text-good" : data.regime_color === "bad" ? "text-bad" : "text-watch";
    }
    if (vixEl) {
      vixEl.textContent = `${data.vix} — ${data.vix_label}`;
      vixEl.className = data.vix_color === "good" ? "text-good" : data.vix_color === "bad" ? "text-bad" : "text-watch";
    }
    if (swingEl) {
      swingEl.textContent = data.swing_ok ? "Permitido" : "Pausado";
      swingEl.className = data.swing_ok ? "text-good" : "text-bad";
    }
  } catch (e) {
    console.error("[market-sentiment] erro:", e);
  }
}

// ═══════════════════════════════════════════════════════════════
// SWING TRADE ANALYSIS
// ═══════════════════════════════════════════════════════════════

const swingPanel       = document.querySelector("#swing-panel");
const swingScoreBadge  = document.querySelector("#swing-score-badge");
const swingDecisionRow = document.querySelector("#swing-decision-row");
const swingLevels      = document.querySelector("#swing-levels");
const swingChecklist   = document.querySelector("#swing-checklist");

async function loadSwingAnalysis(symbol) {
  if (!swingPanel) return;
  swingPanel.style.display = "block";
  swingScoreBadge.textContent = "...";
  swingDecisionRow.innerHTML = "";
  swingLevels.innerHTML      = "";
  swingChecklist.innerHTML   = `<p class="muted-note">Calculando análise swing...</p>`;

  try {
    const res  = await fetch(`/api/py/swing/${encodeURIComponent(symbol)}`);
    const data = await res.json();

    if (data.error) {
      swingChecklist.innerHTML = `<p class="muted-note" style="color:var(--danger)">${escapeHtml(data.error)}</p>`;
      return;
    }

    // Score badge
    const scoreColor = data.score >= 80 ? "var(--success)" : data.score >= 65 ? "#D97706" : "var(--danger)";
    swingScoreBadge.textContent = `${data.score}/100`;
    swingScoreBadge.style.color = scoreColor;

    // Decision row
    const dcColor = data.decision_color === "good" ? "var(--success)" : data.decision_color === "bad" ? "var(--danger)" : "#D97706";
    const setupHtml = data.setup
      ? `<span style="font-size:11px;color:var(--muted);margin-left:8px">${escapeHtml(data.setup)}</span>`
      : `<span style="font-size:11px;color:var(--muted);margin-left:8px">Sem setup</span>`;

    swingDecisionRow.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid var(--surface-2);margin-bottom:10px">
        <span style="font-size:14px;font-weight:800;color:${dcColor}">${escapeHtml(data.decision)}</span>
        ${setupHtml}
        ${data.blockers.length ? `<span style="font-size:11px;color:var(--danger);margin-left:auto">⚠️ ${data.blockers.length} bloqueio${data.blockers.length > 1 ? "s" : ""}</span>` : ""}
      </div>`;

    // Levels grid
    if (data.entry && data.stop && data.target) {
      const riskDollar = data.risk_per_trade ? `$${data.risk_per_trade.toLocaleString("en-US")} risco` : "";
      swingLevels.innerHTML = `
        <div class="swing-levels-grid">
          <div><span>Entrada</span><strong>$${data.entry}</strong></div>
          <div><span>Stop</span><strong style="color:var(--danger)">$${data.stop}</strong></div>
          <div><span>Alvo</span><strong style="color:var(--success)">$${data.target}</strong></div>
          <div><span>R:R</span><strong>${data.rr}:1</strong></div>
        </div>
        ${data.position_shares ? `
        <div style="font-size:11px;color:var(--muted);margin-top:6px;padding:6px 10px;background:var(--surface-2);border-radius:var(--radius-sm)">
          Tamanho sugerido: <strong>${data.position_shares} ações · $${data.position_value?.toLocaleString("en-US")}</strong>
          · ${riskDollar} · 0.5% da conta
        </div>` : ""}`;
    } else {
      swingLevels.innerHTML = `<p class="muted-note">Níveis não calculáveis — sem setup válido.</p>`;
    }

    // Blockers
    const blockersHtml = data.blockers.length
      ? `<div style="margin-bottom:8px">${data.blockers.map(b => `<div style="font-size:11px;color:var(--danger);padding:2px 0">🔴 ${escapeHtml(b)}</div>`).join("")}</div>`
      : "";

    // Checklist
    const checkRows = (data.checklist || []).map(item => {
      const icon = item.ok === true ? "✅" : item.ok === "partial" ? "⚠️" : "❌";
      const color = item.ok === true ? "var(--text)" : item.ok === "partial" ? "#D97706" : "var(--muted)";
      return `<div style="font-size:11px;color:${color};padding:3px 0;display:flex;gap:6px">
        <span style="flex-shrink:0">${icon}</span>
        <span>${escapeHtml(item.item)}</span>
      </div>`;
    }).join("");

    swingChecklist.innerHTML = blockersHtml + `<div style="margin-top:4px">${checkRows}</div>`;

  } catch (e) {
    console.error("[swing] erro:", e);
    swingChecklist.innerHTML = `<p class="muted-note" style="color:var(--danger)">Erro: ${escapeHtml(e.message)}</p>`;
  }
}

// ═══════════════════════════════════════════════════════════════
// MACRO / REGIME
// ═══════════════════════════════════════════════════════════════

const macroSp500   = document.querySelector("#macro-sp500");
const macroVix     = document.querySelector("#macro-vix");
const macroYield10 = document.querySelector("#macro-yield10");
const macroSpread  = document.querySelector("#macro-spread");

async function loadMacro() {
  const ind = document.querySelector("#macro-indicators");
  const sec = document.querySelector("#macro-sectors");
  const cal = document.querySelector("#macro-calendar");
  const ear = document.querySelector("#macro-earnings");

  try {
    const [fullRes, calRes] = await Promise.all([
      fetch("/api/py/macro/full"),
      fetch("/api/py/calendar")
    ]);
    const full     = await fullRes.json();
    const calData  = await calRes.json();
    const macro    = full.raw || {};

    if (macroSp500)   macroSp500.textContent   = macro.sp500       ? macro.sp500.toLocaleString("en-US")                                          : "—";
    if (macroVix)     macroVix.textContent      = macro.vix         ? macro.vix.toFixed(2)                                                         : "—";
    if (macroYield10) macroYield10.textContent  = macro.yield_10y   ? macro.yield_10y.toFixed(2) + "%"                                             : "—";
    if (macroSpread)  macroSpread.textContent   = macro.yield_spread != null ? (macro.yield_spread >= 0 ? "+" : "") + macro.yield_spread.toFixed(2) + "pp" : "—";

    // Macro indicator cards — from backend rich descriptions
    if (ind) {
      ind.innerHTML = renderMacroCards(full);
      ind.style.display = "grid";
      ind.style.gridTemplateColumns = "repeat(2, minmax(0,1fr))";
      ind.style.gap = "14px";
    }
    if (sec) await loadSectors(sec);
    if (cal) renderCalendar(cal, calData.events || []);
    if (ear) renderEarnings(ear, calData.earnings || []);

  } catch (e) {
    console.error('[loadMacro] erro:', e);
    if (ind) ind.innerHTML = `<p class="muted-note">Erro ao carregar macro: ${escapeHtml(e.message)}</p>`;
  }
}

function renderMacroCards(full) {
  // full = { raw, shiller_pe, buffett_indicator, vix, yield_curve }
  const toneMap = { "🟢": "good", "🟡": "watch", "🔴": "bad", "⚪": "watch" };

  function cardTone(ind) {
    if (!ind) return "watch";
    const color = (ind.color || "").toLowerCase();
    if (color.includes("green") || color.includes("verde") || color === "#2e7d52" || color === "#3a7d52") return "good";
    if (color.includes("red")   || color.includes("verm")  || color === "#b84040" || color === "#dc2626") return "bad";
    return "watch";
  }

  const indicators = [
    { key: "shiller_pe",        name: "O mercado está caro?",               sub: `CAPE — ${full.shiller_pe?.value ?? ""}` },
    { key: "buffett_indicator",  name: "Tamanho do mercado vs. a economia",   sub: `Indicador Buffett — ${full.buffett_indicator?.value ?? ""}` },
    { key: "vix",               name: "Nível de nervosismo do mercado",      sub: `VIX — ${full.vix?.value ?? ""}` },
    { key: "yield_curve",       name: "Os juros favorecem crescimento?",     sub: `Curva 10Y−3M — ${full.yield_curve?.value ?? ""}` },
  ];

  return indicators.map(({ key, name, sub }) => {
    const ind  = full[key] || {};
    const tone = cardTone(ind);
    return `
    <div class="macro-ind-card ${tone}">
      <div class="macro-ind-head">
        <div>
          <div class="macro-ind-name">${escapeHtml(name)}</div>
          <div style="font-size:11px;color:var(--muted);margin-top:1px">${escapeHtml(sub)}</div>
        </div>
        <span style="font-size:22px;line-height:1">${ind.emoji || ""}</span>
      </div>
      <div class="macro-ind-sent">${escapeHtml(ind.sentiment || "—")}</div>
      <div class="macro-ind-what">${escapeHtml(ind.what || "")}</div>
      <div class="macro-ind-what"><strong>Leitura:</strong> ${escapeHtml(ind.reading || "")}</div>
      <div class="macro-ind-impl"><strong>Sua carteira:</strong> ${escapeHtml(ind.implication || "")}</div>
    </div>`;
  }).join("");
}

async function loadSectors(el) {
  try {
    const res  = await fetch("/api/py/sectors");
    const data = await res.json();
    const sectors = data.sectors || {};
    if (!Object.keys(sectors).length) { el.innerHTML = `<p class="muted-note">Dados de setores indisponíveis.</p>`; return; }

    const rows = Object.entries(sectors).slice(0, 11).map(([name, p]) => {
      const today = parseFloat((p.today || "0").replace("%",""));
      const ytd   = parseFloat((p.ytd   || "0").replace("%",""));
      return `<tr>
        <td>${escapeHtml(name.replace("Information Technology","Tech").replace("Consumer Discretionary","Cons. Discr.").replace("Consumer Staples","Cons. Staples").replace("Communication Services","Comm. Services"))}</td>
        <td class="${today >= 0 ? "pos" : "neg"}">${p.today || "—"}</td>
        <td class="${ytd   >= 0 ? "pos" : "neg"}">${p.ytd   || "—"}</td>
        <td style="color:var(--muted)">${p.month || "—"}</td>
      </tr>`;
    }).join("");

    el.innerHTML = `<table class="sectors-table">
      <thead><tr><th>Setor</th><th>Hoje</th><th>YTD</th><th>1 Mês</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  } catch (e) {
    el.innerHTML = `<p class="muted-note">Erro setores: ${escapeHtml(e.message)}</p>`;
  }
}

function renderCalendar(el, events) {
  if (!events.length) { el.innerHTML = `<p class="muted-note">Sem eventos de alto impacto nos próximos 14 dias.</p>`; return; }
  el.innerHTML = events.slice(0, 10).map(ev => {
    const high = (ev.impact || "").toLowerCase() === "high";
    return `<div class="cal-item">
      <span class="cal-icon">${high ? "⚠️" : "·"}</span>
      <div><div class="cal-name">${escapeHtml(ev.event || "")}</div>
      <div class="cal-meta">${escapeHtml((ev.time || "").slice(0,10))} · ${escapeHtml(ev.country || "")}</div></div>
    </div>`;
  }).join("");
}

function renderEarnings(el, earnings) {
  if (!earnings.length) { el.innerHTML = `<p class="muted-note">Nenhum earnings da carteira nos próximos 60 dias.</p>`; return; }
  el.innerHTML = earnings.slice(0, 10).map(ev => `
    <div class="cal-item">
      <span class="cal-icon" style="color:var(--accent);font-weight:800;min-width:44px">${escapeHtml(ev.symbol || "")}</span>
      <div><div class="cal-name">${escapeHtml(ev.date || "")}</div>
      <div class="cal-meta">Est. EPS: $${ev.epsEstimate ?? "—"}</div></div>
    </div>`).join("");
}


// ═══════════════════════════════════════════════════════════════
// INVESTIDORES
// ═══════════════════════════════════════════════════════════════

const invRefreshBtn = document.querySelector("#inv-refresh-btn");
const CHANGE_COLORS = { new: "#059669", increased: "#059669", held: "#6B7280", reduced: "#DC2626", closed: "#DC2626" };
const CHANGE_LABELS_JS = { new: "🆕 Nova", increased: "⬆️ Aumentou", held: "→ Manteve", reduced: "⬇️ Reduziu", closed: "❌ Encerrou" };

// Contextualiza mudanças com base no estilo do manager e no ticker
function getChangeContext(managerName, holding, change) {
  if (change === "held") return "";
  const ticker = holding.ticker;
  const pct    = holding.pct ? holding.pct.toFixed(1) + "%" : "";
  const act    = holding.activity || "";

  const styles = {
    "Berkshire Hathaway": "Value / concentrado. Buffett só aumenta quando vê margem de segurança clara.",
    "Scion Asset Mgmt":   "Contrarian / deep value. Burry opera assimetrias e costuma sair antes do consenso.",
    "Pershing Square":    "Activist / concentrado. Ackman exige alta convicção antes de entrar ou sair.",
    "Tiger Global":       "Growth / tech. Coleman aumenta quando há aceleração de receita ou expansão de mercado.",
    "Lone Pine Capital":  "Growth quality. Mandel foca em vantagem competitiva e crescimento sustentável.",
    "Viking Global":      "Long/short. Halvorsen reduz quando momentum técnico enfraquece ou valuation estica.",
    "Appaloosa Management": "Macro / ciclo. Tepper reduz em antecipação a mudanças de ciclo ou política monetária.",
  };

  const context = {
    new:       `Nova posição para ${managerName.split(" ")[0]} — peso inicial de ${pct}. ${styles[managerName] || ""}`,
    increased: `Aumento de ${act || "posição"} — peso atual ${pct}. ${managerName.includes("Tiger") ? "Sinal de aceleração identificada." : managerName.includes("Buffett") || managerName.includes("Berkshire") ? "Reforço da tese de longo prazo." : "Convicção crescente na tese."}`,
    reduced:   `Redução de ${act || "posição"} — peso atual ${pct}. ${managerName.includes("Burry") ? "Possível antecipação de reversão." : managerName.includes("Viking") || managerName.includes("Tepper") ? "Pode indicar enfraquecimento de momentum ou rebalanceamento macro." : "Realização parcial ou revisão de tese."}`,
    closed:    `Posição encerrada. ${managerName.includes("Burry") ? "Saída típica de Burry após capturar assimetria." : "Tese encerrada ou ativo não atende mais os critérios do fundo."}`,
  };

  return context[change] || "";
}

async function loadInvestors() {
  const grid    = document.querySelector("#investor-list");
  const arkPanel = document.querySelector("#ark-panel");

  try {
    const [invRes, arkRes] = await Promise.all([
      fetch("/api/py/investors"),
      fetch("/api/py/ark")
    ]);
    const invData = await invRes.json();
    const arkData = await arkRes.json();

    // Render investor cards
    if (grid) {
      grid.innerHTML = Object.entries(invData).map(([name, inv]) => {
        if (inv.error) return `<div class="inv-card"><div class="inv-manager">${escapeHtml(inv.emoji || "")} ${escapeHtml(inv.manager || name)}</div><p class="muted-note" style="color:var(--danger)">${escapeHtml(inv.error)}</p></div>`;

        const holdings  = inv.holdings || [];
        const portfolio = currentPositions.map(p => p.symbol);
        const overlaps  = holdings.filter(h => portfolio.includes(h.ticker)).map(h => h.ticker);

        // Sentimento baseado nas mudanças
        const newPos  = holdings.filter(h => h.change === "new").length;
        const incr    = holdings.filter(h => h.change === "increased").length;
        const reduced = holdings.filter(h => h.change === "reduced").length;
        const total   = holdings.length || 1;
        const bullishScore = Math.round(((newPos + incr) / total) * 100);
        const bearishScore = Math.round((reduced / total) * 100);
        const sentiment = bullishScore > bearishScore + 10
          ? { label: "Bullish", color: "var(--success)", emoji: "📈" }
          : bearishScore > bullishScore + 10
            ? { label: "Bearish / Reduzindo risco", color: "var(--danger)", emoji: "📉" }
            : { label: "Neutro / Seletivo", color: "#D97706", emoji: "➡️" };

        // Holdings com "por quê" baseado no contexto do manager
        const holdRows = holdings.slice(0, 12).map(h => {
          const chg   = h.change || "held";
          const color = CHANGE_COLORS[chg] || "#6B7280";
          const lbl   = CHANGE_LABELS_JS[chg] || "→";
          const why   = getChangeContext(name, h, chg);
          return `<div class="inv-holding-row" style="flex-direction:column;align-items:flex-start;gap:2px;padding:8px 0">
            <div style="display:flex;width:100%;align-items:center;gap:8px">
              <span class="inv-ticker">${escapeHtml(h.ticker)}</span>
              <span class="inv-hname">${escapeHtml(h.name)}</span>
              <span class="inv-hpct">${h.pct ? h.pct.toFixed(1) + "%" : ""}</span>
              <span class="inv-change" style="color:${color};margin-left:auto">${lbl}</span>
            </div>
            ${why ? `<div style="font-size:11px;color:var(--muted);padding-left:56px;line-height:1.4">${escapeHtml(why)}</div>` : ""}
          </div>`;
        }).join("");

        const overlapHtml = overlaps.length
          ? `<div class="inv-overlap">🔗 Na sua carteira: <strong>${escapeHtml(overlaps.join(", "))}</strong></div>` : "";

        const sentimentHtml = `
          <div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--surface-2);margin-bottom:10px">
            <span style="font-size:18px">${sentiment.emoji}</span>
            <div>
              <div style="font-size:13px;font-weight:700;color:${sentiment.color}">${sentiment.label}</div>
              <div style="font-size:11px;color:var(--muted)">${newPos} novas · ${incr} aumentos · ${reduced} reduções · ${holdings.filter(h=>h.change==="held").length} mantidas</div>
            </div>
          </div>`;

        return `<div class="inv-card">
          <div class="inv-card-head">
            <div>
              <div class="inv-manager">${escapeHtml(inv.emoji || "")} ${escapeHtml(inv.manager || name)}</div>
              <div class="inv-style">${escapeHtml(inv.style || "")}</div>
            </div>
            <div class="inv-asof">${inv.as_of ? "Base " + escapeHtml(inv.as_of) : "Dataroma"}</div>
          </div>
          <div class="inv-knownfor">${escapeHtml(inv.known_for || "")}</div>
          ${sentimentHtml}
          ${overlapHtml}
          <div class="inv-holdings">${holdRows}</div>
        </div>`;
      }).join("");
    }

    // ARK panel
    if (arkPanel && !arkData.error) {
      const arkHoldings = (arkData.holdings || []).slice(0, 15);
      const portfolio = currentPositions.map(p => p.symbol);
      const arkOverlaps = arkHoldings.filter(h => portfolio.includes(h.ticker)).map(h => h.ticker);
      const overlapHtml = arkOverlaps.length ? `<div class="inv-overlap">🔗 Na sua carteira: ${escapeHtml(arkOverlaps.join(", "))}</div>` : "";

      const rows = arkHoldings.map(h => `
        <div class="inv-holding-row">
          <span class="inv-ticker" ${portfolio.includes(h.ticker) ? 'style="color:var(--accent)"' : ""}>${escapeHtml(h.ticker)}</span>
          <span class="inv-hname">${escapeHtml(h.company || "")}</span>
          <span class="inv-hpct">${h.weight ? parseFloat(h.weight).toFixed(2) + "%" : ""}</span>
          <span class="inv-change" style="color:var(--muted)">$${h.share_price ? parseFloat(h.share_price).toFixed(2) : "—"}</span>
        </div>`).join("");

      arkPanel.innerHTML = `<div class="inv-card" style="max-width:600px">
        <div class="inv-card-head">
          <div><div class="inv-manager">🚀 Cathie Wood — ARK Innovation ETF</div>
          <div class="inv-style">Disruptive Innovation · Publicação diária</div></div>
          <div class="inv-asof">${escapeHtml(arkData.as_of || "")}</div>
        </div>
        ${overlapHtml}
        <div class="inv-holdings">${rows}</div>
      </div>`;
    } else if (arkPanel && arkData.error) {
      arkPanel.innerHTML = `<p class="muted-note" style="color:var(--danger)">ARK: ${escapeHtml(arkData.error)}</p>`;
    }

  } catch (e) {
    console.error('[loadInvestors] erro:', e);
    if (grid) grid.innerHTML = `<p class="muted-note">Erro ao carregar investidores: ${escapeHtml(e.message)}</p>`;
  }
}

async function loadInvestorsAndMacro() {
  console.log('[investidores] carregando macro + investidores...');
  await Promise.all([loadMacro(), loadInvestors()]);
  console.log('[investidores] renderização completa');
}

invRefreshBtn?.addEventListener("click", loadInvestorsAndMacro);

// ═══════════════════════════════════════════════════════════════
// HOJE — BRIEFING DIÁRIO
// ═══════════════════════════════════════════════════════════════

async function loadBriefing() {
  const loadingEl  = document.querySelector("#briefing-loading");
  const headerEl   = document.querySelector("#briefing-header");
  const totalsEl   = document.querySelector("#briefing-totals");
  const dateEl     = document.querySelector("#briefing-date");
  const actionEl   = document.querySelector("#briefing-action");
  const watchEl    = document.querySelector("#briefing-watch");
  const okEl       = document.querySelector("#briefing-ok");
  const sectorsEl  = document.querySelector("#briefing-sectors");

  if (loadingEl) loadingEl.style.display = "block";

  try {
    const [res] = await Promise.all([
      fetch("/api/py/briefing"),
      Object.keys(thesisCache).length === 0 ? loadThesis() : Promise.resolve()
    ]);
    const data = await res.json();
    if (loadingEl) loadingEl.style.display = "none";

    // ── Header ────────────────────────────────────────────────────
    const d = new Date(data.date + "T12:00:00");
    const dateStr = d.toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" });
    const spyStr  = data.spy_chg != null
      ? `<span>SPY</span><strong class="${data.spy_chg >= 0 ? "text-good" : "text-bad"}">${data.spy_chg >= 0 ? "+" : ""}${data.spy_chg.toFixed(2)}%</strong>`
      : "";

    if (dateEl)   dateEl.innerHTML  = `<span style="font-size:14px;font-weight:600;color:var(--text)">${dateStr}</span>`;
    if (totalsEl) totalsEl.innerHTML = `
      ${spyStr}
      <span>Carteira</span>
      <strong>$${(data.totals?.mkt_val || 0).toLocaleString("en-US", { maximumFractionDigits: 0 })}</strong>
      <strong class="${(data.totals?.gain_pct || 0) >= 0 ? "text-good" : "text-bad"}">
        ${(data.totals?.gain_pct || 0) >= 0 ? "+" : ""}${(data.totals?.gain_pct || 0).toFixed(1)}%
      </strong>`;

    // ── Render helper ─────────────────────────────────────────────
    function renderRow(p, type) {
      const gainCls  = p.gain_pct >= 0 ? "text-good" : "text-bad";
      const dayCls   = p.day_chg  >= 0 ? "text-good" : "text-bad";
      const alertStr = p.alerts.join(" · ");
      return `
        <div class="briefing-row ${type}">
          <span class="briefing-sym">${escapeHtml(p.symbol)}</span>
          <span class="briefing-horizon ${p.horizon}">${p.horizon === "long" ? "LT" : "SW"}</span>
          <span class="briefing-alerts">${escapeHtml(alertStr)}</span>
          <span class="briefing-day ${dayCls}">${p.day_chg >= 0 ? "+" : ""}${p.day_chg.toFixed(1)}%</span>
          <span class="briefing-pnl ${gainCls}">${p.gain_pct >= 0 ? "+" : ""}${p.gain_pct.toFixed(1)}%</span>
        </div>`;
    }

    // ── Ação necessária ────────────────────────────────────────────
    const action = data.needs_action || [];
    if (actionEl) {
      if (action.length) {
        actionEl.innerHTML = `
          <div class="briefing-section-title urgent">
            Ação necessária
            <span class="count">${action.length}</span>
          </div>
          <div class="briefing-rows">
            ${action.map(p => renderRow(p, "urgent")).join("")}
          </div>`;
      } else {
        actionEl.innerHTML = `
          <div class="briefing-section-title">Ação necessária <span class="count">0</span></div>
          <p class="muted-note">Nenhuma posição exige decisão imediata.</p>`;
      }
    }

    // ── Monitorar ──────────────────────────────────────────────────
    const wlist = data.watch || [];
    if (watchEl) {
      if (wlist.length) {
        watchEl.innerHTML = `
          <div class="briefing-section-title">
            Monitorar
            <span class="count">${wlist.length}</span>
          </div>
          <div class="briefing-rows">
            ${wlist.map(p => renderRow(p, "watch")).join("")}
          </div>`;
      } else {
        watchEl.innerHTML = "";
      }
    }

    // ── Tudo OK ────────────────────────────────────────────────────
    const oklist = data.ok || [];
    if (okEl && oklist.length) {
      const allPos = [...(data.needs_action || []), ...(data.watch || []), ...oklist];
      const noThesis = allPos.filter(p => !thesisCache[p.symbol]);

      const chips = oklist.map(p => {
        const pnlCls = p.gain_pct >= 0 ? "pos" : "neg";
        const dayStr = `${p.day_chg >= 0 ? "+" : ""}${p.day_chg.toFixed(1)}%`;
        const noT = !thesisCache[p.symbol] ? `<span title="Sem tese" style="color:var(--muted);font-size:10px">·</span>` : "";
        return `<div class="briefing-ok-chip">
          <span class="sym">${escapeHtml(p.symbol)}</span>
          <span class="pnl ${pnlCls}">${p.gain_pct >= 0 ? "+" : ""}${p.gain_pct.toFixed(0)}%</span>
          <span class="pnl" style="color:var(--muted)">${dayStr}</span>
          ${noT}
        </div>`;
      }).join("");

      const noThesisNote = noThesis.length
        ? `<p style="font-size:12px;color:var(--muted);margin-top:10px">${noThesis.length} posição${noThesis.length > 1 ? "ões" : ""} sem tese definida: ${noThesis.map(p => p.symbol).join(", ")}</p>`
        : "";

      okEl.innerHTML = `
        <div class="briefing-section-title">
          Estáveis
          <span class="count">${oklist.length}</span>
        </div>
        <div class="briefing-ok-grid">${chips}</div>
        ${noThesisNote}`;
    }

    // ── Concentração setorial ──────────────────────────────────────
    const sectors = data.sector_concentration || {};
    if (sectorsEl && Object.keys(sectors).length) {
      const sorted = Object.entries(sectors).sort((a, b) => b[1] - a[1]);
      const bars = sorted.map(([name, pct]) => {
        const isHigh = pct > 50;
        return `<div class="sector-bar-row">
          <span class="sector-bar-label">${escapeHtml(name)}</span>
          <div class="sector-bar-track">
            <div class="sector-bar-fill ${isHigh ? "high" : ""}" style="width:${Math.min(pct, 100)}%"></div>
          </div>
          <span class="sector-bar-pct ${isHigh ? "text-bad" : ""}">${pct.toFixed(0)}%</span>
        </div>`;
      }).join("");

      const techPct = sectors["Technology"] || 0;
      const concAlert = techPct > 60
        ? `<p style="font-size:12px;color:var(--danger);margin:8px 0 0">⚠️ Concentração em Tecnologia (${techPct.toFixed(0)}%) acima do recomendado.</p>`
        : "";

      sectorsEl.innerHTML = `
        <div class="briefing-section-title">Concentração setorial</div>
        <div class="sector-bars">${bars}</div>
        ${concAlert}`;
    }

    // ── Política de investimento ───────────────────────────────────
    loadPolicy();
    loadWeeklyCommittee();

  } catch (e) {
    if (loadingEl) loadingEl.textContent = `Erro: ${e.message}`;
  }
}

// ═══════════════════════════════════════════════════════════════
// POLICY
// ═══════════════════════════════════════════════════════════════

async function loadPolicy() {
  const section  = document.querySelector("#policy-section");
  const violEl   = document.querySelector("#policy-violations");
  const editBtn  = document.querySelector("#policy-edit-btn");
  const editPanel = document.querySelector("#policy-edit-panel");

  if (!section || !violEl) return;

  try {
    const [checkRes, policyRes] = await Promise.all([
      fetch("/api/py/policy/check"),
      fetch("/api/py/policy")
    ]);
    const check  = await checkRes.json();
    const policy = await policyRes.json();

    section.style.display = "block";

    const sevIcon = { high: "⚠️", medium: "◆" };
    const sevCls  = { high: "policy-violation high", medium: "policy-violation medium" };

    if (!check.violations || check.violations.length === 0) {
      violEl.innerHTML = `<div class="policy-ok">
        <span>✓</span>
        <div>
          <strong>Política OK</strong>
          <p>Caixa ${check.stats?.cash_pct ?? "--"}% · Conta $${(check.stats?.account ?? 0).toLocaleString("en-US", { maximumFractionDigits: 0 })}</p>
        </div>
      </div>`;
    } else {
      violEl.innerHTML = check.violations.map(v => `
        <div class="${sevCls[v.severity] || "policy-violation medium"}">
          <div class="policy-violation-head">
            <span>${sevIcon[v.severity] || "◆"} ${escapeHtml(v.title)}</span>
            <span class="policy-numbers">${v.current ?? ""}% / lim ${v.limit ?? ""}%</span>
          </div>
          <p>${escapeHtml(v.detail)}</p>
          <p class="policy-action">${escapeHtml(v.action)}</p>
        </div>`).join("") + `
        <p class="muted-note" style="margin-top:8px">
          Caixa estimado: ${check.stats?.cash_pct ?? "--"}% · Investido: $${(check.stats?.invested ?? 0).toLocaleString("en-US", { maximumFractionDigits: 0 })}
        </p>`;
    }

    // ── Edit panel ─────────────────────────────────────────────────
    editBtn?.addEventListener("click", () => {
      const visible = editPanel.style.display !== "none";
      editPanel.style.display = visible ? "none" : "block";
      editBtn.textContent = visible ? "Editar regras" : "Fechar";
      if (!visible && !editPanel.dataset.rendered) {
        renderPolicyEditPanel(editPanel, policy);
        editPanel.dataset.rendered = "1";
      }
    }, { once: false });

  } catch (e) {
    if (section) section.style.display = "block";
    if (violEl) violEl.innerHTML = `<p class="muted-note">Política indisponível: ${escapeHtml(e.message)}</p>`;
  }
}

function renderPolicyEditPanel(el, policy) {
  const fields = [
    { key: "account_total_usd", label: "Total da conta (USD)", step: "1000" },
    { key: "max_position_pct",  label: "Posição máxima (%)",    step: "1" },
    { key: "max_sector_pct",    label: "Setor máximo (%)",       step: "1" },
    { key: "min_cash_pct",      label: "Caixa mínimo (%)",       step: "1" },
    { key: "swing_max_loss_pct",label: "Perda max swing (%)",    step: "1" },
    { key: "macro_shiller_pe",  label: "Shiller PE (CAPE)",      step: "0.1" },
    { key: "macro_buffett_ind", label: "Buffett Indicator (%)",  step: "1" },
  ];

  el.innerHTML = `
    <form id="policy-form" class="policy-form">
      ${fields.map(f => `
        <label class="policy-field">
          <span>${escapeHtml(f.label)}</span>
          <input type="number" name="${f.key}" value="${policy[f.key] ?? ""}" step="${f.step}" />
        </label>`).join("")}
      <div style="display:flex;gap:8px;margin-top:12px">
        <button type="submit" class="policy-save-btn">Salvar</button>
        <span id="policy-save-status" style="font-size:12px;color:var(--muted);align-self:center"></span>
      </div>
    </form>`;

  el.querySelector("#policy-form").addEventListener("submit", async e => {
    e.preventDefault();
    const statusEl = el.querySelector("#policy-save-status");
    const formData = Object.fromEntries(new FormData(e.target));
    const payload = {};
    for (const [k, v] of Object.entries(formData)) {
      if (v !== "") payload[k] = Number(v);
    }
    try {
      statusEl.textContent = "Salvando...";
      const res = await fetch("/api/py/policy", {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      statusEl.textContent = "Salvo.";
      setTimeout(() => { statusEl.textContent = ""; }, 2000);
      // Reload violations after save
      const violEl = document.querySelector("#policy-violations");
      const muted  = document.querySelector("#policy-section .muted-note");
      if (violEl) violEl.innerHTML = `<p class="muted-note">Recarregando...</p>`;
      const checkRes = await fetch("/api/py/policy/check");
      const check = await checkRes.json();
      // Re-render violations
      const sevIcon = { high: "⚠️", medium: "◆" };
      const sevCls  = { high: "policy-violation high", medium: "policy-violation medium" };
      if (!check.violations || check.violations.length === 0) {
        violEl.innerHTML = `<div class="policy-ok"><span>✓</span><div><strong>Política OK</strong><p>Caixa ${check.stats?.cash_pct ?? "--"}%</p></div></div>`;
      } else {
        violEl.innerHTML = check.violations.map(v => `
          <div class="${sevCls[v.severity] || "policy-violation medium"}">
            <div class="policy-violation-head">
              <span>${sevIcon[v.severity] || "◆"} ${escapeHtml(v.title)}</span>
              <span class="policy-numbers">${v.current ?? ""}% / lim ${v.limit ?? ""}%</span>
            </div>
            <p>${escapeHtml(v.detail)}</p>
            <p class="policy-action">${escapeHtml(v.action)}</p>
          </div>`).join("");
      }
    } catch (err) {
      statusEl.textContent = `Erro: ${err.message}`;
    }
  });
}

// ═══════════════════════════════════════════════════════════════
// SCREENER
// ═══════════════════════════════════════════════════════════════

const screenerRunBtn   = document.querySelector("#screener-run-btn");
const screenerStatus   = document.querySelector("#screener-status");
const screenerCards    = document.querySelector("#screener-cards");

screenerRunBtn?.addEventListener("click", async () => {
  screenerRunBtn.disabled = true;
  screenerRunBtn.textContent = "Analisando...";
  if (screenerCards)  screenerCards.innerHTML = "";

  // Progress feedback while waiting
  const msgs = [
    "Filtrando liquidez e volume...",
    "Calculando upside vs target de analistas...",
    "Buscando métricas EBITDA e EV/EBITDA...",
    "Calculando receita YoY e crescimento...",
    "Calculando RSI, MACD e médias móveis...",
    "Ordenando por score combinado...",
  ];
  let msgIdx = 0;
  if (screenerStatus) screenerStatus.textContent = msgs[0];
  const progressTimer = setInterval(() => {
    msgIdx = (msgIdx + 1) % msgs.length;
    if (screenerStatus) screenerStatus.textContent = msgs[msgIdx];
  }, 8000);

  try {
    const res     = await fetch("/api/py/screener", { signal: AbortSignal.timeout(360000) });
    const results = await res.json();
    clearInterval(progressTimer);

    if (!results.length) {
      if (screenerStatus) screenerStatus.textContent = "Nenhum setup forte no momento.";
      return;
    }
    if (screenerStatus) screenerStatus.textContent = `${results.length} oportunidades · score combina upside, fundamentos e técnico`;
    if (screenerCards) screenerCards.innerHTML = results.map((c, i) => renderScreenerCard(c, i + 1)).join("");
  } catch (e) {
    clearInterval(progressTimer);
    if (screenerStatus) screenerStatus.textContent = e.name === "TimeoutError"
      ? "Timeout — o screener pode demorar 3-5 min na primeira vez. Tente novamente."
      : `Erro: ${e.message}`;
  } finally {
    screenerRunBtn.disabled = false;
    screenerRunBtn.textContent = "▶ Rodar screener";
  }
});

function renderScreenerCard(c, rank) {
  const upside    = c.upside || 0;
  const upsideCls = upside >= 0 ? "pos" : "neg";
  const upsideArrow = upside >= 0 ? "▲" : "▼";

  const margin = c.margin    ? `<div><div class="pos-stat-label">Margem EBITDA</div><div class="pos-stat-value ${c.margin > 20 ? "positive" : ""}">${c.margin.toFixed(0)}%</div></div>` : "";
  const ev     = c.ev_ebitda ? `<div><div class="pos-stat-label">EV/EBITDA</div><div class="pos-stat-value">${c.ev_ebitda.toFixed(1)}x</div></div>` : "";
  const revG   = c.rev_growth != null ? `<div><div class="pos-stat-label">Receita YoY</div><div class="pos-stat-value ${c.rev_growth > 0 ? "positive" : "negative"}">${c.rev_growth > 0 ? "+" : ""}${c.rev_growth.toFixed(0)}%</div></div>` : "";
  const pe     = c.pe_forward ? `<div><div class="pos-stat-label">P/E Forward</div><div class="pos-stat-value">${c.pe_forward.toFixed(1)}x</div></div>` : "";

  const reasons = (c.reasons || []).slice(0, 5).map(r =>
    `<span class="sc-reason">${escapeHtml(r)}</span>`).join("");

  const rsi  = c.rsi  ? `<div class="sc-signal"><div class="pos-signal-label">${escapeHtml(c.rsi.emoji || "")} ${escapeHtml(c.rsi.label || "")}</div><div class="pos-signal-action">${escapeHtml(c.rsi.action || "")}</div></div>` : "";
  const macd = c.macd ? `<div class="sc-signal"><div class="pos-signal-label">${escapeHtml(c.macd.emoji || "")} ${escapeHtml(c.macd.label || "")}</div><div class="pos-signal-action">${escapeHtml(c.macd.action || "")}</div></div>` : "";

  return `<div class="screener-card">
    <div class="sc-header">
      <div class="sc-left">
        <span class="sc-rank">#${rank}</span>
        <div>
          <div style="display:flex;align-items:center;gap:8px">
            <span class="sc-symbol">${escapeHtml(c.symbol)}</span>
            <span class="sc-score-badge">${escapeHtml(c.score_label || "")} · Score ${c.score || 0}</span>
          </div>
          <div class="sc-name">${escapeHtml(c.name || "")}</div>
        </div>
      </div>
      <div style="text-align:right">
        <div class="sc-price">${c.price ? fmtUSD(c.price) : "—"}</div>
        <div class="sc-upside ${upsideCls}">${upsideArrow} ${Math.abs(upside).toFixed(1)}% upside</div>
        <div style="font-size:11px;color:var(--muted)">${escapeHtml(c.rec || "")} · ${c.n_analysts || 0} casas · Target ${c.target ? fmtUSD(c.target) : "—"}</div>
      </div>
    </div>

    <div class="sc-metrics pos-stats">${margin}${ev}${revG}${pe}</div>
    <div class="sc-reasons">${reasons}</div>
    <div class="sc-signals">${rsi}${macd}</div>
  </div>`;
}

// ═══════════════════════════════════════════════════════════════
// BRASIL
// ═══════════════════════════════════════════════════════════════

async function loadBrasil() {
  const el = document.querySelector("#brasil-content");
  if (!el) return;
  try {
    const res  = await fetch("/api/py/brasil");
    const data = await res.json();
    el.innerHTML = renderBrasil(data);
  } catch (e) {
    el.innerHTML = `<p class="muted-note">Erro: ${escapeHtml(e.message)}</p>`;
  }
}

function renderBrasil(data) {
  const pct     = data.crypto_pct || 0;
  const band    = data.crypto_band || { low: 8, high: 12 };
  const barPct  = Math.min(100, Math.max(0, (pct / band.high) * 100));
  const onTarget = data.on_target;
  const statusColor = onTarget ? "var(--success)" : "var(--danger)";
  const statusTxt   = onTarget ? "Na faixa alvo" : "Fora da faixa — rebalancear via HASH11";
  const fillClass   = onTarget ? "crypto-ok" : "crypto-warn";

  const positions = (data.positions || []);
  const CAT_LABEL = { crypto: "Cripto", fii: "FII", fundo: "Fundo", acao: "Ação", rf: "Renda Fixa" };
  const posRows = positions.map(p => {
    const val = p.valor_investido ?? p.value ?? 0;
    // categoria (e.g. "crypto") prevails over tipo (e.g. "acao") so HASH11 shows as Cripto
    const cat = (p.categoria || p.category || p.tipo || p.type || "").toLowerCase();
    const retorno = p.return_pct ?? p.retorno_pct ?? null;
    return `<tr>
      <td><strong>${escapeHtml(p.ticker || p.asset || "")}</strong><br><span style="font-size:11px;color:var(--muted)">${escapeHtml(p.nome || p.name || "")}</span></td>
      <td><span class="dt-badge ${cat === "crypto" ? "watch" : "setup"}" style="font-size:10px">${escapeHtml(CAT_LABEL[cat] || cat)}</span></td>
      <td style="text-align:right;font-weight:700">R$ ${val ? parseFloat(val).toLocaleString("pt-BR", {maximumFractionDigits:0}) : "—"}</td>
      <td style="text-align:right;color:${retorno == null ? "var(--muted)" : retorno >= 0 ? "var(--success)" : "var(--danger)"};font-weight:700">${retorno != null ? (retorno >= 0 ? "+" : "") + parseFloat(retorno).toFixed(1) + "%" : "—"}</td>
    </tr>`;
  }).join("");

  return `
  <div class="brasil-overview">
    <div class="brasil-kpis">
      <div>
        <div class="brasil-kpi-label">Total Itaú Personnalité</div>
        <div class="brasil-kpi-val">R$ ${(data.total || 0).toLocaleString("pt-BR", {maximumFractionDigits:0})}</div>
      </div>
      <div>
        <div class="brasil-kpi-label">Exposição Cripto</div>
        <div class="brasil-kpi-val" style="color:${statusColor}">${pct.toFixed(1)}%</div>
        <div class="brasil-kpi-sub" style="color:${statusColor}">${statusTxt}</div>
      </div>
      <div>
        <div class="brasil-kpi-label">Valor em Cripto</div>
        <div class="brasil-kpi-val">R$ ${(data.crypto_total || 0).toLocaleString("pt-BR", {maximumFractionDigits:0})}</div>
        <div class="brasil-kpi-sub">Faixa alvo: ${band.low}%–${band.high}%</div>
      </div>
    </div>
    <div style="font-size:12px;color:var(--muted);margin-bottom:4px">
      Exposição cripto: ${pct.toFixed(1)}% (faixa ${band.low}%–${band.high}%)
    </div>
    <div class="crypto-track"><div class="crypto-fill ${fillClass}" style="width:${barPct.toFixed(0)}%"></div></div>
  </div>

  ${posRows ? `
  <div class="section-label">Posições</div>
  <table class="brasil-positions-table">
    <thead><tr><th>Ativo</th><th>Tipo</th><th style="text-align:right">Valor</th><th style="text-align:right">Retorno</th></tr></thead>
    <tbody>${posRows}</tbody>
  </table>` : ""}`;
}

// ═══════════════════════════════════════════════════════════════
// ENRICHMENT PER POSITION (Carteira expandível)
// ═══════════════════════════════════════════════════════════════

async function loadPositionEnrichment(symbol, toggleBtn, panel) {
  if (panel.classList.contains("open")) {
    panel.classList.remove("open");
    toggleBtn.textContent = "▼ Ver análise completa";
    return;
  }

  toggleBtn.textContent = "Carregando...";
  toggleBtn.disabled = true;

  try {
    const [enrRes, ebRes] = await Promise.all([
      fetch(`/api/py/enrichment/${symbol}`),
      fetch(`/api/py/ebitda/${symbol}`)
    ]);
    const enr = await enrRes.json();
    const eb  = await ebRes.json();

    panel.innerHTML = renderEnrichment(symbol, enr, eb);
    panel.classList.add("open");
    toggleBtn.textContent = "▲ Fechar";
  } catch (e) {
    panel.innerHTML = `<p style="color:var(--danger);font-size:12px">Erro: ${escapeHtml(e.message)}</p>`;
    panel.classList.add("open");
    toggleBtn.textContent = "▲ Fechar";
  } finally {
    toggleBtn.disabled = false;
  }
}

function renderEnrichment(symbol, enr, eb) {
  let html = "";

  // EBITDA block
  if (eb && !eb.error) {
    html += `<div class="enrich-section">
      <div class="enrich-title">EBITDA &amp; Fundamentais</div>
      <div class="enrich-row">
        ${eb.ebitda_fmt ? `<div class="enrich-item"><div class="enrich-label">EBITDA TTM</div><div class="enrich-value">${escapeHtml(eb.ebitda_fmt)}</div></div>` : ""}
        ${eb.margin_pct ? `<div class="enrich-item"><div class="enrich-label">Margem EBITDA</div><div class="enrich-value" style="color:${eb.margin_color}">${escapeHtml(eb.margin_pct)} — ${escapeHtml(eb.margin_label)}</div></div>` : ""}
        ${eb.ev_fmt    ? `<div class="enrich-item"><div class="enrich-label">EV/EBITDA</div><div class="enrich-value" style="color:${eb.ev_color}">${escapeHtml(eb.ev_fmt)}</div></div>` : ""}
        ${eb.growth_fmt ? `<div class="enrich-item"><div class="enrich-label">Crescimento YoY</div><div class="enrich-value" style="color:${eb.growth_color}">${escapeHtml(eb.growth_fmt)}</div></div>` : ""}
      </div>
    </div>`;
  }

  // Finnhub news sentiment
  const news = enr.news;
  if (news && !news.error) {
    html += `<div class="enrich-section">
      <div class="enrich-title">Finnhub — Sentimento de Notícias</div>
      <div class="enrich-row">
        <div class="enrich-item"><div class="enrich-label">Leitura</div>
          <div class="enrich-value" style="color:${news.color}">${escapeHtml(news.label)}</div></div>
        <div class="enrich-item"><div class="enrich-label">Bullish / Bearish</div>
          <div class="enrich-value">${news.bullish || 0}% / ${news.bearish || 0}%</div></div>
        <div class="enrich-item"><div class="enrich-label">Artigos esta semana</div>
          <div class="enrich-value">${news.articles || 0}</div></div>
      </div>
    </div>`;
  }

  // Insider signal
  const insider = enr.insider;
  if (insider && !insider.error) {
    const rows = (insider.summary || []).slice(0, 3).map(s =>
      `<div style="font-size:12px;color:var(--muted);margin-top:3px">${escapeHtml(s)}</div>`).join("");
    html += `<div class="enrich-section">
      <div class="enrich-title">Insiders — Finnhub</div>
      <div style="font-size:13px;font-weight:700;color:${insider.color}">${escapeHtml(insider.signal)}</div>
      ${rows}
    </div>`;
  }

  // Earnings trend
  const earn = enr.earnings;
  if (earn && !earn.error) {
    const beats = (earn.quarters || []).slice(0, 4).map(q =>
      `<span style="margin-right:8px;font-size:12px">${q.beat ? "✅" : "❌"} ${escapeHtml(q.period?.slice(0,7) || "")} ${q.surprise != null ? (q.surprise >= 0 ? "+" : "") + q.surprise.toFixed(1) + "%" : ""}</span>`
    ).join("");
    html += `<div class="enrich-section">
      <div class="enrich-title">Earnings — Histórico de surpresas</div>
      <div style="font-size:13px;font-weight:700;color:${earn.color}">${escapeHtml(earn.trend || "")}</div>
      <div style="margin-top:5px">${beats}</div>
    </div>`;
  }

  // Analyst consensus (Finnhub)
  const reco = enr.reco;
  if (reco && !reco.error) {
    html += `<div class="enrich-section">
      <div class="enrich-title">Consenso Analistas — Finnhub</div>
      <div style="font-size:13px;font-weight:700;color:${reco.color}">${escapeHtml(reco.consensus)}</div>
      <div style="font-size:12px;color:var(--muted);margin-top:3px">
        💪 ${(reco.strong_buy || 0) + (reco.buy || 0)} compra &nbsp;·&nbsp;
        ⚖️ ${reco.hold || 0} neutro &nbsp;·&nbsp;
        👎 ${(reco.sell || 0) + (reco.strong_sell || 0)} venda
      </div>
    </div>`;
  }

  return html || `<p class="muted-note">Dados de enriquecimento indisponíveis.</p>`;
}

// ═══════════════════════════════════════════════════════════════
// TAB NAVIGATION
// ═══════════════════════════════════════════════════════════════

const tabBtns   = document.querySelectorAll(".tab-btn");
const tabPanels = document.querySelectorAll(".tab-panel");

tabBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.tab;
    tabBtns.forEach(b => b.classList.toggle("active", b === btn));
    tabPanels.forEach(p => p.classList.toggle("active", p.id === `tab-${target}`));
  });
});

// ═══════════════════════════════════════════════════════════════
// CARTEIRA — Upload & Analysis
// ═══════════════════════════════════════════════════════════════

const uploadZone    = document.querySelector("#upload-zone");
const uploadSub     = document.querySelector("#upload-sub");
const loadLocalBtn  = document.querySelector("#load-local-btn");
const csvFileInput  = document.querySelector("#csv-file-input");
const portHeader    = document.querySelector("#port-header");
const portKpis      = document.querySelector("#port-kpis");
const positionsList = document.querySelector("#positions-list");
const filterBtns    = document.querySelectorAll("#port-header .filter-btn");

let currentPositions = [];

function fmtUSD(n) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);
}
function fmtPct(n) { return `${n >= 0 ? "+" : ""}${n.toFixed(1)}%`; }

// ── Load from local Downloads (primary path) ──────────────────────

loadLocalBtn.addEventListener("click", async () => {
  loadLocalBtn.textContent = "Carregando...";
  loadLocalBtn.disabled = true;
  try {
    await loadFromServer("/api/import-portfolio");
  } catch (err) {
    uploadSub.textContent = `❌ ${err.message}`;
    loadLocalBtn.textContent = "Carregar extrato mais recente";
    loadLocalBtn.disabled = false;
  }
});

// ── Manual file upload (fallback) ────────────────────────────────

csvFileInput.addEventListener("change", async e => {
  const file = e.target.files[0];
  if (!file) return;
  uploadSub.textContent = `Enviando ${file.name}...`;
  try {
    const text = await file.text();
    const res  = await fetch("/api/upload-portfolio", {
      method: "POST",
      headers: { "content-type": "text/plain" },
      body: text
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    onPortfolioLoaded(data);
  } catch (err) {
    uploadSub.textContent = `❌ ${err.message}`;
  }
});

// ── Drag & drop ───────────────────────────────────────────────────

uploadZone.addEventListener("dragover", e => { e.preventDefault(); uploadZone.classList.add("drag-over"); });
uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("drag-over"));
uploadZone.addEventListener("drop", async e => {
  e.preventDefault();
  uploadZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (!file) return;
  csvFileInput.files = e.dataTransfer.files;
  csvFileInput.dispatchEvent(new Event("change"));
});

// ── Core load functions ───────────────────────────────────────────

async function loadFromServer(endpoint) {
  const res  = await fetch(endpoint);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  onPortfolioLoaded(data);
}

function onPortfolioLoaded(data) {
  if (!data.positions?.length) throw new Error("Nenhuma posição encontrada");
  uploadSub.textContent = `✓ ${data.count} posições — ${data.source ? data.source.split("/").pop() : "carregadas"}`;
  uploadZone.classList.add("loaded");
  currentPositions = data.positions;
  renderPortfolio(data.positions);
}

// ── render ────────────────────────────────────────────────────────

// Thesis cache — loaded once per session, updated on save
let thesisCache = {};

async function loadThesis() {
  try {
    const res = await fetch("/api/py/thesis");
    thesisCache = await res.json();
  } catch (_) {}
}

function rewireThesis(block, sym) {
  const editBtn = block.querySelector(".pos-thesis-edit-btn");
  const form    = block.querySelector(".pos-thesis-form");
  const cancelBtn = block.querySelector(".pos-thesis-cancel");

  editBtn?.addEventListener("click", () => {
    const view = block.querySelector(".pos-thesis-view") || block.querySelector(".pos-thesis-empty");
    if (form)    form.style.display = "flex";
    if (view)    view.style.display = "none";
    if (editBtn) editBtn.style.display = "none";
  });

  cancelBtn?.addEventListener("click", () => {
    block.innerHTML = renderThesisBlock(sym);
    rewireThesis(block, sym);
  });

  form?.addEventListener("submit", async e => {
    e.preventDefault();
    const data = {
      reason:      form.querySelector('[name="reason"]').value.trim(),
      sell_if:     form.querySelector('[name="sell_if"]').value.trim(),
      main_risk:   form.querySelector('[name="main_risk"]').value.trim(),
      last_review: new Date().toISOString().slice(0, 10),
    };
    const saveBtn = form.querySelector(".pos-thesis-save");
    saveBtn.textContent = "Salvando…";
    saveBtn.disabled = true;
    try {
      const res = await fetch(`/api/py/thesis/${sym}`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(data)
      });
      if (!res.ok) throw new Error();
      thesisCache[sym] = data;
      block.innerHTML = renderThesisBlock(sym);
      rewireThesis(block, sym);
    } catch {
      saveBtn.textContent = "Erro — tentar de novo";
      saveBtn.disabled = false;
    }
  });
}

function renderThesisBlock(symbol) {
  const t = thesisCache[symbol] || {};
  const hasThesis = t.reason || t.sell_if || t.main_risk;
  const reviewDate = t.last_review
    ? new Date(t.last_review + "T12:00:00").toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" })
    : null;

  const viewHtml = hasThesis ? `
    <div class="pos-thesis-view">
      ${t.reason   ? `<p class="pos-thesis-reason">${escapeHtml(t.reason)}</p>` : ""}
      ${t.sell_if  ? `<div class="pos-thesis-field"><span class="pos-thesis-lbl">Sair quando</span><span>${escapeHtml(t.sell_if)}</span></div>` : ""}
      ${t.main_risk? `<div class="pos-thesis-field"><span class="pos-thesis-lbl">Risco</span><span>${escapeHtml(t.main_risk)}</span></div>` : ""}
      ${reviewDate ? `<div class="pos-thesis-meta">Revisado ${reviewDate}</div>` : ""}
    </div>` : `<p class="pos-thesis-empty">Sem tese definida.</p>`;

  return `
    <div class="pos-thesis" id="thesis-${escapeHtml(symbol)}">
      <div class="pos-thesis-header">
        <span class="pos-thesis-label">Tese</span>
        <button class="pos-thesis-edit-btn" data-symbol="${escapeHtml(symbol)}">${hasThesis ? "Editar" : "Adicionar"}</button>
      </div>
      ${viewHtml}
      <form class="pos-thesis-form" id="thesis-form-${escapeHtml(symbol)}" style="display:none"
            data-symbol="${escapeHtml(symbol)}">
        <textarea name="reason"    placeholder="Por que está na carteira?" rows="2">${escapeHtml(t.reason    || "")}</textarea>
        <textarea name="sell_if"   placeholder="Sair quando…"               rows="2">${escapeHtml(t.sell_if   || "")}</textarea>
        <textarea name="main_risk" placeholder="Risco principal…"            rows="2">${escapeHtml(t.main_risk || "")}</textarea>
        <div class="pos-thesis-form-actions">
          <button type="submit" class="pos-thesis-save">Salvar</button>
          <button type="button" class="pos-thesis-cancel">Cancelar</button>
        </div>
      </form>
    </div>`;
}

async function renderPortfolio(positions) {
  portHeader.hidden = false;
  positionsList.innerHTML = "";

  // Load thesis data alongside portfolio
  await loadThesis();

  // Render skeleton cards first
  positions.forEach(pos => {
    const card = document.createElement("div");
    card.className = "position-card";
    card.dataset.symbol  = pos.symbol;
    card.dataset.horizon = pos.horizon || "unknown";
    card.innerHTML = `
      <div class="pos-header">
        <div class="pos-left">
          <span class="${pos.horizon === "long" ? "pos-tag-lt" : "pos-tag-swing"}">
            ${pos.horizon === "long" ? "Long Term" : "Swing"}
          </span>
          <span class="pos-symbol">${escapeHtml(pos.symbol)}</span>
          <span class="pos-name pos-loading">Carregando...</span>
        </div>
        <div class="pos-right">
          <span class="pos-price pos-loading">—</span>
        </div>
      </div>`;
    positionsList.appendChild(card);
  });

  // Fetch analysis for all positions in parallel
  const results = await Promise.allSettled(
    positions.map(pos => fetchAssetAnalysis(pos.symbol))
  );

  let totalCost = 0, totalMkt = 0;

  results.forEach((result, i) => {
    const pos  = positions[i];
    const card = positionsList.querySelector(`[data-symbol="${pos.symbol}"]`);
    if (!card) return;

    const qty       = pos.quantity || 1;
    const costBasis = pos.average * qty;

    if (result.status === "fulfilled" && result.value) {
      const d       = result.value;
      const price   = d.price || 0;
      const mktVal  = price * qty;
      const gainU   = mktVal - costBasis;
      const gainP   = costBasis ? gainU / costBasis * 100 : 0;
      const dayChg  = d.day_chg_pct || 0;
      const target  = d.target_mean || 0;
      const upside  = target && price ? (target - price) / price * 100 : 0;
      const rec     = d.recommendation || "N/A";
      const nAn     = d.n_analysts || 0;
      const pe      = d.pe_forward ? `${d.pe_forward.toFixed(1)}x` : "—";
      const h52     = d.week52_high || 0;
      const l52     = d.week52_low  || 0;
      const barPct  = h52 > l52 ? Math.max(0, Math.min(100, (price - l52) / (h52 - l52) * 100)) : 0;
      const pfHigh  = d.pct_from_high || 0;

      const mandate = pos.strategy || {};
      const tag     = pos.horizon === "long"
        ? `<span class="pos-tag-lt">Long Term</span>`
        : `<span class="pos-tag-swing">Swing</span>`;

      totalCost += costBasis;
      totalMkt  += mktVal;

      card.innerHTML = `
        <div class="pos-header">
          <div class="pos-left">
            ${tag}
            <span class="pos-symbol">${escapeHtml(pos.symbol)}</span>
            <span class="pos-name">${escapeHtml(d.name || pos.symbol)}</span>
          </div>
          <div class="pos-right">
            <span class="pos-price">${fmtUSD(price)}</span>
            <span class="pos-day ${dayChg >= 0 ? "up" : "dn"}">
              ${dayChg >= 0 ? "▲" : "▼"} ${Math.abs(dayChg).toFixed(2)}% hoje
            </span>
          </div>
        </div>

        <div class="pos-stats">
          <div>
            <div class="pos-stat-label">P&L acumulado</div>
            <div class="pos-stat-value ${gainU >= 0 ? "positive" : "negative"}">
              ${fmtUSD(gainU)} &nbsp; ${fmtPct(gainP)}
            </div>
            <div class="pos-stat-sub">${qty} ações · PM ${fmtUSD(pos.average)}</div>
          </div>
          <div>
            <div class="pos-stat-label">Fair Price</div>
            <div class="pos-stat-value">${target ? fmtUSD(target) : "—"}
              ${upside ? `<span class="${upside >= 0 ? "positive" : "negative"}" style="font-size:13px">
                ${upside >= 0 ? "▲" : "▼"} ${Math.abs(upside).toFixed(1)}%</span>` : ""}
            </div>
            <div class="pos-stat-sub">${rec} · ${nAn} casas</div>
          </div>
          <div>
            <div class="pos-stat-label">P/E Forward</div>
            <div class="pos-stat-value">${pe}</div>
            <div class="pos-stat-sub">${pfHigh.toFixed(1)}% da máxima</div>
          </div>
          <div>
            <div class="pos-stat-label">Valor atual</div>
            <div class="pos-stat-value">${fmtUSD(mktVal)}</div>
            <div class="pos-stat-sub">Custo ${fmtUSD(costBasis)}</div>
          </div>
        </div>

        <div class="pos-range-label">
          52 semanas &nbsp; ${fmtUSD(l52)} — ${fmtUSD(h52)}
        </div>
        <div class="pos-range-track">
          <div class="pos-range-fill" style="width:${barPct.toFixed(0)}%"></div>
        </div>

        ${mandate.type ? `
        <div class="pos-mandate">
          <div class="pos-mandate-type">${escapeHtml(mandate.type)}</div>
          <div class="pos-mandate-text">${escapeHtml(mandate.mandate)}</div>
        </div>` : ""}

        ${renderThesisBlock(pos.symbol)}

        <button class="pos-enrich-toggle" data-symbol="${escapeHtml(pos.symbol)}">▼ Ver análise completa</button>
        <div class="pos-enrich-panel"></div>
      `;
    } else {
      card.innerHTML += `<p class="pos-loading" style="color:var(--danger)">
        Erro ao carregar ${pos.symbol}
      </p>`;
    }
  });

  // Wire up enrichment toggles
  document.querySelectorAll(".pos-enrich-toggle").forEach(btn => {
    btn.addEventListener("click", () => {
      const panel = btn.nextElementSibling;
      loadPositionEnrichment(btn.dataset.symbol, btn, panel);
    });
  });

  // Wire up thesis edit/save/cancel
  document.querySelectorAll(".pos-thesis-edit-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const sym  = btn.dataset.symbol;
      const form = document.querySelector(`#thesis-form-${sym}`);
      const view = document.querySelector(`#thesis-${sym} .pos-thesis-view`) ||
                   document.querySelector(`#thesis-${sym} .pos-thesis-empty`);
      if (form) form.style.display = "flex";
      if (view) view.style.display = "none";
      btn.style.display = "none";
    });
  });

  document.querySelectorAll(".pos-thesis-cancel").forEach(btn => {
    btn.addEventListener("click", () => {
      const form = btn.closest(".pos-thesis-form");
      const sym  = form.dataset.symbol;
      const block = document.querySelector(`#thesis-${sym}`);
      block.innerHTML = renderThesisBlock(sym);
      rewireThesis(block, sym);
    });
  });

  document.querySelectorAll(".pos-thesis-form").forEach(form => {
    form.addEventListener("submit", async e => {
      e.preventDefault();
      const sym  = form.dataset.symbol;
      const data = {
        reason:      form.querySelector('[name="reason"]').value.trim(),
        sell_if:     form.querySelector('[name="sell_if"]').value.trim(),
        main_risk:   form.querySelector('[name="main_risk"]').value.trim(),
        last_review: new Date().toISOString().slice(0, 10),
      };
      const saveBtn = form.querySelector(".pos-thesis-save");
      saveBtn.textContent = "Salvando…";
      saveBtn.disabled = true;
      try {
        const res = await fetch(`/api/py/thesis/${sym}`, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error("Erro ao salvar");
        thesisCache[sym] = data;
        const block = document.querySelector(`#thesis-${sym}`);
        block.innerHTML = renderThesisBlock(sym);
        rewireThesis(block, sym);
      } catch (err) {
        saveBtn.textContent = "Erro — tentar de novo";
        saveBtn.disabled = false;
      }
    });
  });

  // Summary KPIs
  const totalGain = totalMkt - totalCost;
  const totalGainP = totalCost ? totalGain / totalCost * 100 : 0;
  portKpis.innerHTML = `
    <div class="port-kpi">
      <div class="port-kpi-label">Posições</div>
      <div class="port-kpi-value">${positions.length}</div>
    </div>
    <div class="port-kpi">
      <div class="port-kpi-label">Investido</div>
      <div class="port-kpi-value">${fmtUSD(totalCost)}</div>
    </div>
    <div class="port-kpi">
      <div class="port-kpi-label">Valor atual</div>
      <div class="port-kpi-value">${fmtUSD(totalMkt)}</div>
    </div>
    <div class="port-kpi">
      <div class="port-kpi-label">P&L total</div>
      <div class="port-kpi-value ${totalGain >= 0 ? "positive" : "negative"}">
        ${fmtUSD(totalGain)} (${fmtPct(totalGainP)})
      </div>
    </div>
  `;
}

async function fetchAssetAnalysis(symbol) {
  const res = await fetch(`/api/py/asset/${symbol}`);
  if (!res.ok) throw new Error(`${symbol}: ${res.status}`);
  return res.json();
}

// ═══════════════════════════════════════════════════════════════
// DAY TRADE ADVISOR
// ═══════════════════════════════════════════════════════════════

const dtRefreshBtn = document.querySelector("#dt-refresh-btn");
const dtLoading    = document.querySelector("#dt-loading");
const dtCards      = document.querySelector("#dt-cards");
const dtRegime     = document.querySelector("#dt-regime");

let dtData = [];
let investorSymbols = {};  // symbol → [manager names]

async function loadInvestorSymbols() {
  try {
    const res  = await fetch("/api/py/investors");
    const data = await res.json();
    investorSymbols = {};
    for (const [managerName, inv] of Object.entries(data)) {
      for (const h of (inv.holdings || [])) {
        if (!investorSymbols[h.ticker]) investorSymbols[h.ticker] = [];
        investorSymbols[h.ticker].push(inv.manager || managerName);
      }
    }
  } catch (_) {}
}

async function loadDayTrade() {
  dtLoading.style.display = "block";
  dtCards.innerHTML = "";
  try {
    const [res] = await Promise.all([
      fetch("/api/py/intraday"),
      Object.keys(investorSymbols).length === 0 ? loadInvestorSymbols() : Promise.resolve()
    ]);
    const data = await res.json();
    dtData = data;
    renderDayTrade(data);
  } catch (e) {
    dtLoading.textContent = `Erro: ${e.message}`;
  } finally {
    dtLoading.style.display = "none";
  }
}

function renderDayTrade(data) {
  if (!data?.length) { dtCards.innerHTML = `<p style="color:var(--muted)">Nenhum dado disponível.</p>`; return; }

  // Market regime from SPY
  const spyAbove = data.some(d => d.spy_above_vwap);
  if (dtRegime) {
    dtRegime.textContent  = spyAbove ? "🟢 Risk-On · SPY acima do VWAP" : "🔴 Risk-Off · SPY abaixo do VWAP";
    dtRegime.style.color  = spyAbove ? "var(--success)" : "var(--danger)";
  }

  // Sort: SETUP first, then WATCH, then EVITAR; within each group by RVOL desc
  const order = { SETUP: 0, WATCH: 1, EVITAR: 2 };
  data.sort((a, b) => {
    const ra = order[(a.signal?.rating) ?? "EVITAR"] ?? 2;
    const rb = order[(b.signal?.rating) ?? "EVITAR"] ?? 2;
    if (ra !== rb) return ra - rb;
    return (b.rvol ?? 0) - (a.rvol ?? 0);
  });

  dtCards.innerHTML = data.map(d => renderDtCard(d)).join("");
}

function dtSentimentText(d, rating) {
  const sym = d.symbol;
  const rvol = d.rvol ?? 0;
  const rs   = d.relative_strength ?? 0;
  const gap  = d.gap_pct ?? 0;

  if (rating === "SETUP") {
    const rvolStr = rvol >= 3 ? "volume muito acima do normal" : "volume elevado";
    const rsStr   = rs > 2 ? "claramente mais forte que o mercado" : "um pouco mais forte que o mercado";
    return `${sym} reúne hoje as condições ideais para day trade. ${rvolStr.charAt(0).toUpperCase() + rvolStr.slice(1)}, ${rsStr} e abrindo com gap dentro da faixa ideal. Se romper o OR High com volume, é o sinal de entrada.`;
  }
  if (rating === "WATCH") {
    const weak = [];
    if (rvol < 2)   weak.push("volume ainda baixo");
    if (rs < 0)     weak.push("mais fraco que o SPY hoje");
    if (gap < 2)    weak.push("gap pequeno");
    const issues = weak.length ? weak.join(" e ") : "alguns critérios ainda não atendidos";
    return `${sym} está quase lá mas ainda com ${issues}. Vale observar: se o volume aumentar e o preço segurar acima do VWAP, o setup pode se formar. Não antecipar entrada.`;
  }
  return `${sym} não tem as condições mínimas para day trade hoje. ${rvol < 1 ? "Sem volume suficiente. " : ""}${rs < -2 ? "Fraco vs. mercado. " : ""}Aguardar outro dia ou outro ativo.`;
}

function renderDtCard(d) {
  const sig       = d.signal || {};
  const rating    = sig.rating || "EVITAR";
  const ratingCls = rating.toLowerCase();
  const checks    = sig.checks || [];
  const or        = d.opening_range || {};
  const trade     = d.trade;

  const tag = d.horizon === "long"
    ? `<span class="pos-tag-lt">📌 Long Term</span>`
    : `<span class="pos-tag-swing">⚡ Swing</span>`;

  // Investor overlap
  const managers = investorSymbols[d.symbol] || [];
  const investorBadge = managers.length
    ? `<span class="dt-investor-badge" title="${escapeHtml(managers.join(", "))}">🏛️ ${managers.length === 1 ? managers[0].split(" ")[0] : managers.length + " fundos"}</span>`
    : "";

  const rvolCls = (d.rvol >= 2) ? "good" : (d.rvol >= 1.5) ? "warn" : "bad";
  const gapCls  = (d.gap_pct >= 2 && d.gap_pct <= 8) ? "good" : (d.gap_pct >= 1) ? "warn" : "bad";

  const checksHtml = checks.map(c => `
    <div class="dt-check ${c.ok ? "ok" : ""}">
      <span class="dt-check-icon">${c.ok ? "✅" : "⬜"}</span>
      <span>${escapeHtml(c.label)}</span>
      <span class="dt-check-val">${escapeHtml(c.value)}</span>
    </div>`).join("");

  const tradeHtml = trade && rating === "SETUP" ? `
    <div class="dt-trade">
      <div class="dt-trade-item"><div class="dt-trade-label">Entrada</div><div class="dt-trade-value">${fmtUSD(trade.entry)}</div></div>
      <div class="dt-trade-item"><div class="dt-trade-label">Stop</div><div class="dt-trade-value" style="color:#DC2626">${fmtUSD(trade.stop)}</div></div>
      <div class="dt-trade-item"><div class="dt-trade-label">Alvo 1 (1.5R)</div><div class="dt-trade-value">${fmtUSD(trade.target1)}</div></div>
      <div class="dt-trade-item"><div class="dt-trade-label">Alvo 2 (2R)</div><div class="dt-trade-value">${fmtUSD(trade.target2)}</div></div>
      <div class="dt-trade-item"><div class="dt-trade-label">Risco/ação</div><div class="dt-trade-value">${fmtUSD(trade.risk)}</div></div>
    </div>` : "";

  const sentiment = dtSentimentText(d, rating);
  const sentimentBg = rating === "SETUP" ? "var(--accent-light)" : rating === "WATCH" ? "#FEF3C7" : "var(--surface-2)";
  const sentimentColor = rating === "SETUP" ? "var(--accent-text)" : rating === "WATCH" ? "#92400E" : "var(--muted)";

  return `
  <div class="dt-card dt-${ratingCls}" data-dtrating="${rating}" data-dthorizon="${d.horizon || ""}">
    <div class="dt-card-header">
      <div class="dt-card-left">
        ${tag}
        <span class="dt-symbol">${escapeHtml(d.symbol)}</span>
        <span class="dt-rating ${ratingCls}">${rating} ${sig.score ?? 0}/${sig.total ?? 0}</span>
        ${investorBadge}
      </div>
      <div class="dt-card-right">
        <span class="dt-price">${d.price ? fmtUSD(d.price) : "—"}</span>
        <span class="dt-change ${(d.relative_strength ?? 0) >= 0 ? "up" : "dn"}">
          vs SPY ${d.relative_strength != null ? (d.relative_strength >= 0 ? "+" : "") + d.relative_strength.toFixed(2) + "%" : "—"}
        </span>
      </div>
    </div>

    <div style="font-size:12px;color:${sentimentColor};background:${sentimentBg};border-radius:var(--radius-sm);padding:8px 12px;margin:8px 0;line-height:1.5">
      ${escapeHtml(sentiment)}
    </div>

    <div class="dt-metrics">
      <div><div class="dt-metric-label">Volume relativo</div><div class="dt-metric-value ${rvolCls}">${d.rvol != null ? d.rvol.toFixed(1) + "×" : "—"}</div></div>
      <div><div class="dt-metric-label">Gap abertura</div><div class="dt-metric-value ${gapCls}">${d.gap_pct != null ? (d.gap_pct >= 0 ? "+" : "") + d.gap_pct.toFixed(1) + "%" : "—"}</div></div>
      <div><div class="dt-metric-label">Preço vs VWAP</div><div class="dt-metric-value ${d.above_vwap ? "good" : "bad"}">${d.vwap ? fmtUSD(d.vwap) : "—"} ${d.above_vwap ? "▲" : "▼"}</div></div>
      <div><div class="dt-metric-label">ATR (volatilidade)</div><div class="dt-metric-value">${d.atr != null ? fmtUSD(d.atr) : "—"}</div></div>
      <div><div class="dt-metric-label">Máx. OR</div><div class="dt-metric-value">${or.high != null ? fmtUSD(or.high) : "—"}</div></div>
      <div><div class="dt-metric-label">Mín. OR</div><div class="dt-metric-value">${or.low != null ? fmtUSD(or.low) : "—"}</div></div>
    </div>

    ${tradeHtml}
    <div class="dt-checklist">${checksHtml}</div>
    <div style="font-size:11px;color:var(--muted);margin-top:10px">Atualizado: ${d.timestamp || "—"} ET · ${d.market_regime || "—"}</div>
  </div>`;
}

dtRefreshBtn?.addEventListener("click", loadDayTrade);

async function autoLoadCarteira() {
  if (currentPositions.length) return; // already loaded
  try {
    await loadFromServer("/api/import-portfolio");
  } catch (_) {
    // silently fall through — upload zone remains visible
  }
}

// ═══════════════════════════════════════════════════════════════
// WEEKLY COMMITTEE
// ═══════════════════════════════════════════════════════════════

async function loadWeeklyCommittee() {
  const section  = document.querySelector("#wc-section");
  const postureEl = document.querySelector("#wc-posture");
  const bodyEl    = document.querySelector("#wc-body");
  if (!section) return;

  try {
    const res  = await fetch("/api/py/weekly-committee");
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Erro");

    section.style.display = "block";

    const lvlCls = { ok: "wc-ok", watch: "wc-watch", critical: "wc-critical" };
    const cls = lvlCls[data.posture_level] || "wc-watch";

    if (postureEl) postureEl.innerHTML = `
      <div class="wc-posture ${cls}">
        <div class="wc-posture-text">${escapeHtml(data.posture)}</div>
        <div class="wc-posture-meta">
          SPY ${data.market?.spy_chg >= 0 ? "+" : ""}${(data.market?.spy_chg ?? 0).toFixed(2)}% hoje
          &nbsp;·&nbsp; ${data.portfolio?.positions ?? 0} posições
          &nbsp;·&nbsp; Política: ${escapeHtml(data.policy?.status ?? "—")}
        </div>
      </div>`;

    const actionHtml = (data.suggested_actions || []).map(a => `
      <div class="wc-action wc-action-${a.priority === "alta" ? "high" : a.priority === "média" ? "mid" : "low"}">
        <span class="wc-action-priority">${escapeHtml(a.priority)}</span>
        <div>
          <strong>${escapeHtml(a.action)}</strong>
          <p>${escapeHtml(a.detail)}</p>
        </div>
      </div>`).join("");

    const best  = (data.best3  || []).map(p => `<span class="wc-chip up">▲ ${escapeHtml(p.symbol)} +${p.gain_pct}%</span>`).join("");
    const worst = (data.worst3 || []).map(p => `<span class="wc-chip dn">▼ ${escapeHtml(p.symbol)} ${p.gain_pct}%</span>`).join("");

    if (bodyEl) bodyEl.innerHTML = `
      <div class="wc-body">
        <div class="wc-col">
          <div class="wc-col-title">Ações sugeridas</div>
          ${actionHtml || "<p class='muted-note'>Nenhuma ação necessária.</p>"}
        </div>
        <div class="wc-col">
          <div class="wc-col-title">Melhores</div>
          <div class="wc-chips">${best}</div>
          <div class="wc-col-title" style="margin-top:12px">Piores</div>
          <div class="wc-chips">${worst}</div>
        </div>
      </div>`;
  } catch (e) {
    if (section) section.style.display = "block";
    if (postureEl) postureEl.innerHTML = `<p class="muted-note">Committee indisponível: ${escapeHtml(e.message)}</p>`;
  }
}

// ═══════════════════════════════════════════════════════════════
// RISK BOOK
// ═══════════════════════════════════════════════════════════════

async function loadRiskBook() {
  const loadEl   = document.querySelector("#rb-loading");
  const contentEl = document.querySelector("#rb-content");
  if (!loadEl) return;

  loadEl.style.display = "block";
  if (contentEl) contentEl.style.display = "none";

  try {
    const res  = await fetch("/api/py/risk-book");
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Erro");

    loadEl.style.display = "none";
    if (contentEl) contentEl.style.display = "block";

    // ── Summary ──────────────────────────────────────────────────
    const summEl = document.querySelector("#rb-summary");
    if (summEl) {
      const s = data.summary || {};
      summEl.innerHTML = `
        <div class="rb-card">
          <div class="rb-card-title">Conta</div>
          <div class="rb-stat-grid">
            <div><span>Total</span><strong>$${(s.account_total||0).toLocaleString("en-US",{maximumFractionDigits:0})}</strong></div>
            <div><span>Investido</span><strong>$${(s.total_invested||0).toLocaleString("en-US",{maximumFractionDigits:0})}</strong></div>
            <div><span>Caixa</span><strong>${s.cash_pct ?? "--"}%</strong></div>
            <div><span>Posições</span><strong>${s.positions ?? "--"}</strong></div>
          </div>
        </div>`;
    }

    // ── Exposure ─────────────────────────────────────────────────
    const expEl = document.querySelector("#rb-exposure");
    if (expEl) {
      const e = data.exposure || {};
      expEl.innerHTML = `
        <div class="rb-card">
          <div class="rb-card-title">Exposição</div>
          <div class="rb-stat-grid">
            <div><span>Long Term</span><strong>${e.long_pct ?? "--"}%</strong></div>
            <div><span>Swing</span><strong>${e.swing_pct ?? "--"}%</strong></div>
            <div><span>US</span><strong>${e.us_pct ?? "--"}%</strong></div>
            <div><span>Brasil</span><strong>${e.br_pct ?? "--"}%</strong></div>
          </div>
        </div>`;
    }

    // ── Crypto BR ────────────────────────────────────────────────
    const cryptoEl = document.querySelector("#rb-crypto");
    if (cryptoEl && data.crypto_br) {
      const c = data.crypto_br;
      const ok = c.on_target;
      cryptoEl.innerHTML = `
        <div class="rb-card">
          <div class="rb-card-title">Cripto BR</div>
          <div class="rb-stat-grid">
            <div><span>Alocação</span><strong class="${ok === false ? "text-bad" : ok ? "text-good" : ""}">${c.pct ?? "--"}%</strong></div>
            <div><span>Faixa alvo</span><strong>${c.band?.low ?? "--"}–${c.band?.high ?? "--"}%</strong></div>
            <div><span>Status</span><strong>${ok == null ? "—" : ok ? "✓ OK" : "Fora da faixa"}</strong></div>
          </div>
        </div>`;
    }

    // ── Top 5 ────────────────────────────────────────────────────
    const top5El = document.querySelector("#rb-top5");
    if (top5El) {
      top5El.innerHTML = `
        <div class="rb-table">
          <div class="rb-table-head"><span>Ativo</span><span>Valor</span><span>% Conta</span><span>P&L</span><span>Horizonte</span></div>
          ${(data.top5 || []).map(p => `
            <div class="rb-table-row">
              <span class="rb-sym">${escapeHtml(p.symbol)}</span>
              <span>$${(p.mkt_val||0).toLocaleString("en-US",{maximumFractionDigits:0})}</span>
              <span>${p.pct_account}%</span>
              <span class="${p.gain_pct >= 0 ? "text-good" : "text-bad"}">${p.gain_pct >= 0 ? "+" : ""}${p.gain_pct}%</span>
              <span>${escapeHtml(p.horizon === "long" ? "Long Term" : "Swing")}</span>
            </div>`).join("")}
          <div class="rb-table-footer"><span>Concentração top 5</span><span></span><span>${data.top5_concentration ?? "--"}% do investido</span><span></span><span></span></div>
        </div>`;
    }

    // ── Sectors ──────────────────────────────────────────────────
    const secEl = document.querySelector("#rb-sectors");
    if (secEl) {
      const sectors = data.sectors || {};
      const sorted  = Object.entries(sectors).sort((a, b) => b[1] - a[1]);
      secEl.innerHTML = `<div class="sector-bars">
        ${sorted.map(([name, pct]) => `
          <div class="sector-bar-row">
            <span class="sector-bar-label">${escapeHtml(name)}</span>
            <div class="sector-bar-track"><div class="sector-bar-fill ${pct > 50 ? "high" : ""}" style="width:${Math.min(pct,100)}%"></div></div>
            <span class="sector-bar-pct ${pct > 50 ? "text-bad" : ""}">${pct.toFixed(0)}%</span>
          </div>`).join("")}
      </div>`;
    }

    // ── Alerts ───────────────────────────────────────────────────
    const alertsEl = document.querySelector("#rb-alerts");
    if (alertsEl) {
      const alerts = [...(data.alerts || []), ...(data.policy_violations || []).map(v => ({
        level: v.severity, area: v.rule, message: v.detail
      }))];
      if (!alerts.length) {
        alertsEl.innerHTML = `<div class="policy-ok"><span>✓</span><div><strong>Sem alertas</strong><p>Carteira dentro dos parâmetros de risco.</p></div></div>`;
      } else {
        alertsEl.innerHTML = alerts.map(a => `
          <div class="policy-violation ${a.level === "high" ? "high" : "medium"}">
            <div class="policy-violation-head">
              <span>${a.level === "high" ? "⚠️" : "◆"} ${escapeHtml(a.area || "")}</span>
            </div>
            <p>${escapeHtml(a.message || "")}</p>
          </div>`).join("");
      }
    }

    // ── Recommendations ──────────────────────────────────────────
    const recEl = document.querySelector("#rb-recommendations");
    if (recEl) {
      recEl.innerHTML = (data.recommendations || []).map(r => `
        <div class="rb-rec rb-rec-${r.priority}">
          <span class="rb-rec-tag">${escapeHtml(r.priority)}</span>
          <div>
            <strong>${escapeHtml(r.action)}</strong>
            <p>${escapeHtml(r.rationale)}</p>
          </div>
        </div>`).join("");
    }

    // ── Populate decision memo symbol selector ────────────────────
    const dmSymbol = document.querySelector("#dm-symbol");
    if (dmSymbol && data.top5?.length) {
      const allSymbols = (data.top5 || []).map(p => p.symbol);
      // Add all from briefing if available
      allSymbols.forEach(sym => {
        if (!dmSymbol.querySelector(`option[value="${sym}"]`)) {
          const opt = document.createElement("option");
          opt.value = sym; opt.textContent = sym;
          dmSymbol.appendChild(opt);
        }
      });
    }

  } catch (e) {
    if (loadEl) loadEl.textContent = `Erro: ${e.message}`;
  }
}

// ── Decision Memo form ────────────────────────────────────────────────────────

document.querySelector("#rb-refresh-btn")?.addEventListener("click", loadRiskBook);

document.querySelector("#dm-form")?.addEventListener("submit", async e => {
  e.preventDefault();
  const btn    = e.target.querySelector("button[type=submit]");
  const result = document.querySelector("#dm-result");
  const fd     = new FormData(e.target);

  btn.disabled = true; btn.textContent = "Analisando...";
  if (result) result.innerHTML = "";

  try {
    const res  = await fetch("/api/py/decision-memo", {
      method:  "POST",
      headers: { "content-type": "application/json" },
      body:    JSON.stringify({ symbol: fd.get("symbol"), action: fd.get("action"), rationale: fd.get("rationale") || null }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Erro");
    if (result) result.innerHTML = renderDecisionMemo(data);
    loadDecisionHistory();
  } catch (err) {
    if (result) result.innerHTML = `<p class="muted-note" style="color:var(--danger)">${escapeHtml(err.message)}</p>`;
  } finally {
    btn.disabled = false; btn.textContent = "Analisar";
  }
});

async function loadDecisionHistory() {
  const el = document.querySelector("#dh-list");
  if (!el) return;
  try {
    const res = await fetch("/api/py/decisions?limit=30");
    const rows = await res.json();
    if (!Array.isArray(rows) || rows.length === 0) {
      el.innerHTML = `<p class="muted-note">Nenhuma decisão registrada ainda.</p>`;
      return;
    }
    const ACTION_LABEL = { buy:"Comprar", add:"Aumentar", hold:"Manter", reduce:"Reduzir", sell:"Vender" };
    const VERDICT_CLS  = { ok:"dh-verdict-ok", warning:"dh-verdict-warn", neutral:"dh-verdict-neutral" };
    el.innerHTML = rows.map(r => {
      const dt    = new Date(r.created_at).toLocaleString("pt-BR", { day:"2-digit", month:"2-digit", year:"numeric", hour:"2-digit", minute:"2-digit" });
      const rec   = r.result?.recommendation || {};
      const cls   = VERDICT_CLS[rec.color] || "dh-verdict-neutral";
      const why   = r.rationale ? `<p class="dh-rationale">${escapeHtml(r.rationale)}</p>` : "";
      return `
        <div class="dh-row">
          <div class="dh-row-head">
            <span class="dh-sym">${escapeHtml(r.symbol)}</span>
            <span class="dh-action">${escapeHtml(ACTION_LABEL[r.action] || r.action)}</span>
            <span class="dh-verdict ${cls}">${escapeHtml(rec.verdict || "—")}</span>
            <span class="dh-date">${dt}</span>
          </div>
          ${why}
        </div>`;
    }).join("");
  } catch (err) {
    el.innerHTML = `<p class="muted-note" style="color:var(--danger)">Erro: ${escapeHtml(err.message)}</p>`;
  }
}

document.querySelector("#dh-refresh-btn")?.addEventListener("click", loadDecisionHistory);

function renderDecisionMemo(d) {
  const verdictCls = { ok: "dm-ok", warning: "dm-warning", neutral: "dm-neutral" };
  const cls = verdictCls[d.recommendation?.color] || "dm-neutral";

  const flags = (d.policy_flags || []).map(f => `<li>${escapeHtml(f)}</li>`).join("");
  const risks = (d.risks || []).map(r => `
    <div class="dm-risk">
      <span>${escapeHtml(r.source)}</span>
      <p>${escapeHtml(r.risk)}</p>
    </div>`).join("");
  const checks = (d.checklist || []).map(c => `
    <div class="dm-check ${c.done ? "done" : ""}">
      <span>${c.done ? "✓" : "○"}</span>
      <span>${escapeHtml(c.check)}</span>
    </div>`).join("");

  return `
    <div class="dm-memo">
      <div class="dm-verdict ${cls}">
        <strong>${escapeHtml(d.recommendation?.verdict || "—")}</strong>
        <p>${escapeHtml(d.recommendation?.detail || "")}</p>
      </div>

      <div class="dm-section">
        <div class="dm-section-title">Situação atual — ${escapeHtml(d.symbol)}</div>
        <div class="dm-kpis">
          <div><span>Preço</span><strong>$${(d.current?.price||0).toFixed(2)}</strong></div>
          <div><span>P&L</span><strong class="${(d.current?.gain_pct||0)>=0?"text-good":"text-bad"}">${(d.current?.gain_pct||0)>=0?"+":""}${d.current?.gain_pct??0}%</strong></div>
          <div><span>% da conta</span><strong>${d.current?.pos_pct_account??0}%</strong></div>
          <div><span>Upside analistas</span><strong>${(d.current?.upside_pct||0)>=0?"+":""}${d.current?.upside_pct??0}%</strong></div>
        </div>
      </div>

      ${d.thesis_summary?.reason && d.thesis_summary.reason !== "Não definida." ? `
      <div class="dm-section">
        <div class="dm-section-title">Tese</div>
        <p class="dm-thesis-text">${escapeHtml(d.thesis_summary.reason)}</p>
        ${d.thesis_summary.sell_if !== "Não definido." ? `<p class="dm-thesis-sub">Encerrar se: ${escapeHtml(d.thesis_summary.sell_if)}</p>` : ""}
      </div>` : ""}

      ${flags ? `<div class="dm-section"><div class="dm-section-title">⚠️ Pontos de política</div><ul class="dm-flags">${flags}</ul></div>` : ""}
      ${risks  ? `<div class="dm-section"><div class="dm-section-title">Riscos</div>${risks}</div>` : ""}

      <div class="dm-section">
        <div class="dm-section-title">Checklist</div>
        <div class="dm-checklist">${checks}</div>
      </div>
    </div>`;
}

// ═══════════════════════════════════════════════════════════════
// Lazy-load each tab on first visit
const tabLoaded = {};
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const tab = btn.dataset.tab;
    if (tabLoaded[tab]) return;
    tabLoaded[tab] = true;
    if (tab === "hoje")         loadBriefing();
    if (tab === "carteira")     autoLoadCarteira();
    if (tab === "daytrade")     loadDayTrade();
    if (tab === "investidores") loadInvestorsAndMacro();
    if (tab === "brasil")       loadBrasil();
    if (tab === "riskbook")     { loadRiskBook(); loadDecisionHistory(); }
    // screener is on-demand (button click)
  });
});

// DT filter buttons
document.querySelector("#dt-filter-bar")?.addEventListener("click", e => {
  const btn = e.target.closest(".filter-btn");
  if (!btn) return;
  document.querySelectorAll("#dt-filter-bar .filter-btn").forEach(b => b.classList.toggle("active", b === btn));
  const f = btn.dataset.dtfilter;
  document.querySelectorAll(".dt-card").forEach(card => {
    const match = f === "all"
      || card.dataset.dtrating === f
      || card.dataset.dthorizon === f;
    card.classList.toggle("dt-hidden", !match);
  });
});

// ── filter buttons ────────────────────────────────────────────────

function applyPortfolioFilter(filter) {
  filterBtns.forEach(b => b.classList.toggle("active", b.dataset.filter === filter));
  document.querySelectorAll(".position-card").forEach(card => {
    const show = filter === "all" || card.dataset.horizon === filter;
    card.classList.toggle("hidden", !show);
  });
}

filterBtns.forEach(btn => {
  btn.addEventListener("click", () => applyPortfolioFilter(btn.dataset.filter));
});

// Clicking horizon tags on the cards also triggers filter
document.addEventListener("click", e => {
  const tag = e.target.closest(".pos-tag-lt, .pos-tag-swing");
  if (!tag) return;
  const filter = tag.classList.contains("pos-tag-lt") ? "long" : "swing";
  applyPortfolioFilter(filter);
});

// Pre-load on startup
tabLoaded["hoje"]         = true;
tabLoaded["investidores"] = true;
tabLoaded["carteira"]     = true;
loadBriefing();
loadInvestorsAndMacro();
autoLoadCarteira();

// Pre-populate decision memo symbol selector from portfolio_us.csv symbols
(async () => {
  try {
    const res  = await fetch("/api/import-portfolio");
    const data = await res.json();
    const sel  = document.querySelector("#dm-symbol");
    if (!sel || !data.positions) return;
    data.positions.forEach(p => {
      if (!sel.querySelector(`option[value="${p.symbol}"]`)) {
        const opt = document.createElement("option");
        opt.value = p.symbol; opt.textContent = p.symbol;
        sel.appendChild(opt);
      }
    });
  } catch (_) {}
})();
