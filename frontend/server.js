import { createServer } from "node:http";
import { existsSync, readFileSync } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { randomBytes, timingSafeEqual } from "node:crypto";

const root = fileURLToPath(new URL(".", import.meta.url));
const publicDir = join(root, "public");
const dataDir = join(root, ".data");
const arkSnapshotPath = join(dataDir, "ark-arkk-snapshot.json");
const defaultPortfolioPath = "/Users/macbook/Downloads/Individual-Positions-2026-04-28-115955.csv";

function loadLocalEnv() {
  const envPath = join(root, ".env");

  if (!existsSync(envPath)) {
    return {};
  }

  return Object.fromEntries(readFileSync(envPath, "utf8")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#") && line.includes("="))
    .map((line) => {
      const separator = line.indexOf("=");
      const key = line.slice(0, separator).trim();
      const value = line.slice(separator + 1).trim().replace(/^["']|["']$/g, "");
      return [key, value];
    }));
}

const localEnv = loadLocalEnv();
const port = Number(process.env.PORT || localEnv.PORT || 3001);
const host = process.env.HOST || localEnv.HOST || "127.0.0.1";
const alphaVantageApiKey = process.env.ALPHA_VANTAGE_API_KEY || localEnv.ALPHA_VANTAGE_API_KEY || "";

// ── Auth ──────────────────────────────────────────────────────────────────────

const APP_PASSWORD       = process.env.APP_PASSWORD       || localEnv.APP_PASSWORD       || "";
const INTERNAL_API_TOKEN = process.env.INTERNAL_API_TOKEN || localEnv.INTERNAL_API_TOKEN || "";
const IS_PRODUCTION      = (process.env.NODE_ENV || localEnv.NODE_ENV || "development") === "production";

if (IS_PRODUCTION && !APP_PASSWORD) {
  console.error("FATAL: APP_PASSWORD is required in production (NODE_ENV=production)");
  process.exit(1);
}
const sessions = new Map(); // token → expiresAt (ms)
const SESSION_TTL = 24 * 60 * 60 * 1000; // 24 h

function createSession() {
  const token = randomBytes(32).toString("hex");
  sessions.set(token, Date.now() + SESSION_TTL);
  return token;
}

function isValidSession(token) {
  if (!token) return false;
  const exp = sessions.get(token);
  if (!exp) return false;
  if (Date.now() > exp) { sessions.delete(token); return false; }
  return true;
}

function bearerToken(request) {
  const h = request.headers["authorization"] || "";
  return h.startsWith("Bearer ") ? h.slice(7) : "";
}

// Returns true if request is authenticated (or no password is set).
// Sends 401 and returns false otherwise.
function requireAuth(request, response) {
  if (!APP_PASSWORD) return true;
  if (isValidSession(bearerToken(request))) return true;
  sendJson(response, 401, { error: "Unauthorized" });
  return false;
}

async function readBody(request) {
  return new Promise((resolve, reject) => {
    let body = "";
    request.on("data", c => { body += c; });
    request.on("end",  () => resolve(body));
    request.on("error", reject);
  });
}

const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml"
};

const analysisCache = new Map();
const analysisCacheTtl = 10 * 60 * 1000;
const sentimentCache = new Map();
const sentimentCacheTtl = 20 * 60 * 1000;
const marketRegimeCache = new Map();
const marketRegimeCacheTtl = 15 * 60 * 1000;
const investorsCache = new Map();
const investors13fCacheTtl = 6 * 60 * 60 * 1000;
const arkCacheTtl = 60 * 60 * 1000;
const alternativeCache = new Map();
const alternativeCacheTtl = 60 * 60 * 1000;

const strategyProfiles = {
  AAPL: ["Nucleo LP", "Empresa solida; manter como nucleo, mas rebalancear se peso ou valuation ficarem esticados."],
  AMZN: ["Nucleo LP", "Nucleo de crescimento/consumo/cloud; monitorar margem e tendencia."],
  GOOG: ["Nucleo LP", "Nucleo de qualidade; monitorar regulacao, IA e momentum tecnico."],
  META: ["Nucleo LP", "Nucleo de crescimento com caixa forte; realizar parcial se tecnica ficar euforica."],
  MSFT: ["Nucleo LP", "Nucleo defensivo de tecnologia; bom candidato a carregar, com rebalanceamento."],
  NVDA: ["Nucleo LP rebalanceavel", "Ativo lider, mas nao hold cego: monitorar concentracao, euforia e oportunidade de realizar na forca."],
  JPM: ["Nucleo financeiro", "Banco de maior qualidade relativa; monitorar ciclo de credito e juros."],
  LLY: ["Nucleo saude", "Qualidade alta, mas valuation costuma pesar; monitorar preco versus crescimento."],
  SAP: ["LP monitorado", "Software maduro; manter se fundamentos e tendencia continuarem saudaveis."],
  PANW: ["LP monitorado", "Ciberseguranca solida; monitorar execucao e suporte tecnico."],
  NOW: ["LP monitorado", "Software de qualidade; manter se crescimento e tendencia sustentarem."],
  CRWD: ["LP monitorado", "Ciberseguranca forte, porem volatil; nao ignorar sinais tecnicos de distribuicao."],
  AMD: ["Tatico/semicondutores", "Bom ativo, mas ciclico; vender/reduzir na forca pode fazer sentido quando tecnico esticar."],
  CEG: ["Tatico/energia", "Tema interessante, mas sensivel a narrativa; monitorar tendencia e realizacao."],
  BAC: ["Ciclico/valor", "Banco mais ciclico; nao tratar como nucleo sem confirmacao de ciclo e tendencia."],
  CRM: ["Revisao de qualidade", "Empresa relevante, mas posicao exige reavaliar tese, margem e momentum."],
  CELH: ["Tatico", "Consumo/growth volatil; nao tratar como hold estrutural sem fundamentos fortes."],
  DDOG: ["Tatico growth", "Growth de software volatil; monitorar tecnica e valuation."],
  FSLR: ["Tatico tematico", "Solar/energia e politica industrial; operar com disciplina de ciclo."],
  MDB: ["Tatico growth", "Software growth de maior risco; nao transformar em hold sem confirmacao."],
  NET: ["Tatico growth", "Infra/cloud growth; exige confirmacao tecnica e fundamental."],
  TTD: ["Tatico growth", "Adtech volatil; bom para oportunidade, mas precisa de controle de risco."],
  XYZ: ["Revisao de qualidade", "Fintech/cripto-adjacente; tratar como posicao de maior risco."],
  ZS: ["Tatico growth", "Ciberseguranca growth; monitorar tendencia e valuation."]
};

function strategyForSymbol(symbol) {
  const [type, mandate] = strategyProfiles[symbol] || ["Monitorado", "Classificacao pendente; definir tese antes de aumentar exposicao."];
  return { type, mandate };
}

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store"
  });
  response.end(JSON.stringify(payload));
}

function rawValue(value) {
  if (value && typeof value === "object" && "raw" in value) {
    return value.raw;
  }
  return value ?? null;
}

function formatValue(value) {
  if (value && typeof value === "object" && "fmt" in value) {
    return value.fmt;
  }
  return value ?? null;
}

function normalizeSymbol(value) {
  return String(value || "")
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9.^=-]/g, "");
}

function parseCsvLine(line) {
  const cells = [];
  let cell = "";
  let inQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];

    if (char === "\"" && next === "\"") {
      cell += "\"";
      index += 1;
    } else if (char === "\"") {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      cells.push(cell);
      cell = "";
    } else {
      cell += char;
    }
  }

  cells.push(cell);
  return cells;
}

function parseMoney(value) {
  const clean = String(value || "")
    .replace(/\$/g, "")
    .replace(/,/g, "")
    .replace(/%/g, "")
    .trim();
  const isNegative = clean.startsWith("-") || String(value || "").includes("($");
  const parsed = Number(clean.replace(/[()]/g, "").replace(/-/g, ""));

  if (!Number.isFinite(parsed)) {
    return null;
  }

  return isNegative ? -parsed : parsed;
}

function parsePercent(value) {
  const parsed = parseMoney(value);
  return parsed === null ? null : parsed;
}

function stripTags(value) {
  return String(value || "")
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ")
    .trim();
}

function parsePortfolioCsv(text) {
  const lines = text.split(/\r?\n/).filter((line) => line.trim());
  const headerIndex = lines.findIndex((line) => line.includes("\"Symbol\""));

  if (headerIndex === -1) {
    throw new Error("Cabecalho de posicoes nao encontrado no CSV.");
  }

  const headers = parseCsvLine(lines[headerIndex]).map((header) => header.trim());
  const rows = lines.slice(headerIndex + 1).map(parseCsvLine);
  const indexOf = (name) => headers.indexOf(name);
  const symbolIndex = indexOf("Symbol");
  const descriptionIndex = indexOf("Description");
  const quantityIndex = indexOf("Qty (Quantity)");
  const costBasisIndex = indexOf("Cost Basis");
  const assetTypeIndex = indexOf("Asset Type");

  return rows.map((row) => {
    const symbol = normalizeSymbol(row[symbolIndex]);
    const quantity = parseMoney(row[quantityIndex]);
    const costBasis = parseMoney(row[costBasisIndex]);

    if (!symbol || !quantity || !costBasis) {
      return null;
    }

    const strategy = strategyForSymbol(symbol);

    return {
      id: `${symbol}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
      symbol,
      type: strategy.type,
      mandate: strategy.mandate,
      quantity,
      average: costBasis / quantity,
      stop: null,
      target: null,
      thesis: [row[descriptionIndex], row[assetTypeIndex]].filter(Boolean).join(" · ")
    };
  }).filter(Boolean);
}

function getDefaultPortfolioSymbols() {
  try {
    const csv = readFileSync(defaultPortfolioPath, "utf8");
    return new Set(parsePortfolioCsv(csv).map((position) => position.symbol));
  } catch {
    return new Set();
  }
}

function average(values) {
  const filtered = values.filter((value) => Number.isFinite(value));
  return filtered.length
    ? filtered.reduce((total, value) => total + value, 0) / filtered.length
    : null;
}

function calculateRsi(values, period = 14) {
  if (values.length <= period) {
    return null;
  }

  const changes = values.slice(1).map((value, index) => value - values[index]);
  const recent = changes.slice(-period);
  const gains = recent.map((change) => Math.max(change, 0));
  const losses = recent.map((change) => Math.max(-change, 0));
  const averageGain = average(gains);
  const averageLoss = average(losses);

  if (!averageLoss) {
    return 100;
  }

  const relativeStrength = averageGain / averageLoss;
  return 100 - (100 / (1 + relativeStrength));
}

function buildChartReading(candles) {
  const closes = candles.map((candle) => candle.close).filter(Number.isFinite);
  const highs = candles.map((candle) => candle.high).filter(Number.isFinite);
  const lows = candles.map((candle) => candle.low).filter(Number.isFinite);
  const volumes = candles.map((candle) => candle.volume).filter(Number.isFinite);
  const latest = candles.at(-1);
  const lastClose = latest?.close ?? closes.at(-1);
  const sma5 = average(closes.slice(-5));
  const sma20 = average(closes.slice(-20));
  const rsi14 = calculateRsi(closes);
  const support = Math.min(...lows.slice(-20));
  const resistance = Math.max(...highs.slice(-20));
  const averageVolume = average(volumes.slice(-20));
  const volumeRatio = latest?.volume && averageVolume ? latest.volume / averageVolume : null;
  const trend = sma5 && sma20
    ? sma5 > sma20 * 1.01 ? "alta" : sma5 < sma20 * 0.99 ? "baixa" : "lateral"
    : "indefinida";
  const resistanceDistance = resistance && lastClose ? ((resistance - lastClose) / lastClose) * 100 : null;
  const supportDistance = support && lastClose ? ((lastClose - support) / lastClose) * 100 : null;
  const momentum = rsi14 === null
    ? "indefinido"
    : rsi14 >= 70 ? "sobrecomprado" : rsi14 <= 30 ? "sobrevendido" : rsi14 >= 55 ? "positivo" : rsi14 <= 45 ? "fraco" : "neutro";
  const volumeTone = volumeRatio === null
    ? "sem leitura clara de volume"
    : volumeRatio >= 1.4 ? "volume acima da media" : volumeRatio <= 0.7 ? "volume abaixo da media" : "volume perto da media";
  const bias = trend === "alta" && ["positivo", "neutro"].includes(momentum)
    ? "construtivo"
    : trend === "baixa" && ["fraco", "neutro"].includes(momentum)
      ? "defensivo"
      : "neutro";

  return {
    trend,
    momentum,
    bias,
    support,
    resistance,
    sma5,
    sma20,
    rsi14,
    volumeRatio,
    analytical: [
      `Tendencia de curto prazo em ${trend}, comparando media de 5 periodos com media de 20 periodos.`,
      `RSI de 14 periodos em ${rsi14 === null ? "leitura insuficiente" : rsi14.toFixed(1)}, indicando momento ${momentum}.`,
      `Preco negocia a ${supportDistance === null ? "--" : supportDistance.toFixed(1)}% do suporte recente e ${resistanceDistance === null ? "--" : resistanceDistance.toFixed(1)}% abaixo da resistencia recente.`,
      `Volume atual sugere ${volumeTone}.`
    ],
    prescriptive: [
      bias === "construtivo"
        ? "Cenario educativo: favorece buscar continuacao apenas se o preco sustentar acima das medias e romper resistencia com volume."
        : bias === "defensivo"
          ? "Cenario educativo: pede cautela; repiques contra a tendencia precisam confirmar forca antes de qualquer leitura positiva."
          : "Cenario educativo: aguardar rompimento claro ou retorno ao suporte tende a gerar leitura mais limpa.",
      "Invalidacao tecnica: perda do suporte recente enfraquece o cenario; rejeicao na resistencia reduz a qualidade do rompimento."
    ],
    didactic: [
      "Price action: primeiro leia tendencia, estrutura de topos/fundos e regioes de rejeicao.",
      "Wyckoff/VSA: volume confirma ou questiona o movimento; preco subindo sem volume merece desconfiança.",
      "Candles: a leitura melhora quando candle, suporte/resistencia e contexto apontam para a mesma direcao."
    ]
  };
}

async function getYahooQuote(symbol) {
  const url = new URL(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}`);
  url.searchParams.set("interval", "1d");
  url.searchParams.set("range", "1mo");

  const yahooResponse = await fetch(url, {
    headers: {
      "accept": "application/json",
      "user-agent": "Mozilla/5.0 finance-connect"
    }
  });

  if (!yahooResponse.ok) {
    throw new Error(`Yahoo Finance returned ${yahooResponse.status}`);
  }

  const data = await yahooResponse.json();
  const result = data?.chart?.result?.[0];
  const meta = result?.meta;

  if (!meta) {
    throw new Error(data?.chart?.error?.description || "Symbol not found");
  }

  const quotes = result.indicators?.quote?.[0] || {};
  const timestamps = result.timestamp || [];
  const open = quotes.open || [];
  const high = quotes.high || [];
  const low = quotes.low || [];
  const close = quotes.close || [];
  const volume = quotes.volume || [];
  const candles = timestamps.map((time, index) => ({
    time: time * 1000,
    open: open[index] ?? null,
    high: high[index] ?? null,
    low: low[index] ?? null,
    volume: volume[index] ?? null,
    close: close[index] ?? null
  })).filter((point) => point.close !== null);

  return {
    symbol: meta.symbol,
    exchange: meta.exchangeName,
    currency: meta.currency,
    price: meta.regularMarketPrice,
    previousClose: meta.chartPreviousClose,
    change: meta.regularMarketPrice - meta.chartPreviousClose,
    changePercent: ((meta.regularMarketPrice - meta.chartPreviousClose) / meta.chartPreviousClose) * 100,
    marketState: meta.marketState,
    range: meta.range,
    candles,
    chartReading: buildChartReading(candles)
  };
}

async function getYahooSnapshot(symbol) {
  const quote = await getYahooQuote(symbol);
  return {
    symbol: quote.symbol,
    price: quote.price,
    previousClose: quote.previousClose,
    changePercent: quote.changePercent,
    currency: quote.currency
  };
}

function scoreVix(value) {
  if (!Number.isFinite(value)) return 50;
  if (value < 15) return 70;
  if (value < 22) return 58;
  if (value < 30) return 42;
  return 25;
}

function scoreYieldCurve(spread) {
  if (!Number.isFinite(spread)) return 50;
  if (spread > 0.8) return 68;
  if (spread > 0.1) return 56;
  if (spread > -0.5) return 42;
  return 28;
}

function indicatorTone(score) {
  if (score >= 65) return { label: "favoravel", emoji: "🟢" };
  if (score >= 45) return { label: "neutro", emoji: "🟡" };
  return { label: "alerta", emoji: "🔴" };
}

async function getMarketRegime() {
  const cached = marketRegimeCache.get("latest");

  if (cached && Date.now() - cached.createdAt < marketRegimeCacheTtl) {
    return { ...cached.payload, cached: true };
  }

  const [vixResult, tenYearResult, threeMonthResult] = await Promise.allSettled([
    getYahooSnapshot("^VIX"),
    getYahooSnapshot("^TNX"),
    getYahooSnapshot("^IRX")
  ]);
  const vix = vixResult.status === "fulfilled" ? vixResult.value : null;
  const tenYear = tenYearResult.status === "fulfilled" ? tenYearResult.value : null;
  const threeMonth = threeMonthResult.status === "fulfilled" ? threeMonthResult.value : null;
  const yieldSpread = tenYear?.price && threeMonth?.price ? tenYear.price - threeMonth.price : null;
  const vixScore = scoreVix(vix?.price);
  const curveScore = scoreYieldCurve(yieldSpread);
  const score = Math.round((vixScore * 0.45) + (curveScore * 0.35) + (50 * 0.2));
  const scoreTone = indicatorTone(score);
  const vixTone = indicatorTone(vixScore);
  const curveTone = indicatorTone(curveScore);

  const payload = {
    score,
    label: score >= 65 ? "Risco controlado" : score >= 45 ? "Neutro / seletivo" : "Defensivo",
    tone: scoreTone,
    updatedAt: new Date().toISOString(),
    indicators: [
      {
        id: "vix",
        pillar: "Sentimento",
        name: "VIX",
        measures: "Custo de protecao e incerteza esperada no S&P 500.",
        current: vix ? `${vix.price.toFixed(2)}` : "Indisponivel",
        context: vix
          ? `${vix.changePercent >= 0 ? "+" : ""}${vix.changePercent.toFixed(2)}% no dia. Abaixo de 20 sugere calma; acima de 30 indica estresse.`
          : "Nao foi possivel capturar via Yahoo agora.",
        tone: vixTone,
        implication: vixScore >= 65
          ? "Permite manter risco, mas nao elimina necessidade de stop em taticos."
          : vixScore >= 45
            ? "Evitar aumentar risco sem confirmacao tecnica."
            : "Priorizar protecao, realizacao parcial e reducao de posicoes frageis."
      },
      {
        id: "yield-curve",
        pillar: "Macro e credito",
        name: "Curva de juros 10Y - 3M",
        measures: "Diferenca entre juros longos e curtos dos Treasuries.",
        current: yieldSpread === null ? "Indisponivel" : `${yieldSpread.toFixed(2)} p.p.`,
        context: yieldSpread === null
          ? "Nao foi possivel capturar ^TNX e ^IRX agora."
          : yieldSpread < 0 ? "Curva invertida, historicamente associada a risco macro." : "Curva positiva, condicao macro menos pressionada.",
        tone: curveTone,
        implication: curveScore >= 65
          ? "Ambiente macro menos restritivo para risco."
          : curveScore >= 45
            ? "Manter seletividade, principalmente em growth caro."
            : "Aumentar exigencia de qualidade e evitar transformar taticos em hold."
      },
      {
        id: "cape",
        pillar: "Valuation",
        name: "Shiller P/E / CAPE",
        measures: "Preco do mercado versus media real dos lucros dos ultimos 10 anos.",
        current: "Pendente",
        context: "Fonte planejada: base Robert Shiller/Yale.",
        tone: { label: "pendente", emoji: "⚪" },
        implication: "Quando extremo, reduz apetite para novas compras e aumenta foco em margem de seguranca."
      },
      {
        id: "buffett",
        pillar: "Valuation",
        name: "Buffett Indicator",
        measures: "Valor de mercado das empresas versus PIB.",
        current: "Pendente",
        context: "Fonte planejada: FRED/BEA + valor de mercado agregado.",
        tone: { label: "pendente", emoji: "⚪" },
        implication: "Ajuda a distinguir crescimento real de excesso de expectativa."
      },
      {
        id: "margin-debt",
        pillar: "Macro e credito",
        name: "Margin debt",
        measures: "Alavancagem dos investidores usando dinheiro emprestado.",
        current: "Pendente",
        context: "Fonte planejada: FINRA Margin Statistics, atualizacao mensal.",
        tone: { label: "pendente", emoji: "⚪" },
        implication: "Alavancagem alta aumenta risco de venda forcada em quedas."
      }
    ],
    cached: false
  };

  marketRegimeCache.set("latest", { createdAt: Date.now(), payload });
  return payload;
}

async function getYahooAnalysis(symbol) {
  const cached = analysisCache.get(symbol);
  if (cached && Date.now() - cached.createdAt < analysisCacheTtl) {
    return { ...cached.payload, cached: true };
  }

  // Yahoo Finance v10 blocks server-side requests — use Finnhub + yfinance via Python
  const py = await proxyPython(`/analyst/${symbol}`);

  const payload = {
    symbol,
    source:                  "finnhub+yfinance",
    recommendationKey:       py.recKey        || null,
    recommendationMean:      py.recMean       || null,
    numberOfAnalystOpinions: py.nAnalysts     || null,
    targetMeanPrice:         py.targetMean    || null,
    targetMedianPrice:       py.targetMedian  || null,
    targetHighPrice:         py.targetHigh    || null,
    targetLowPrice:          py.targetLow     || null,
    currentPrice:            null,
    trend:    py.trend    || [],
    upgrades: [],
    earnings: [],
    cached: false,
  };

  analysisCache.set(symbol, { createdAt: Date.now(), payload });
  return payload;
}

async function getAlphaVantageSentiment(symbol) {
  if (!alphaVantageApiKey) {
    throw new Error("ALPHA_VANTAGE_API_KEY nao configurada.");
  }

  const cached = sentimentCache.get(symbol);

  if (cached && Date.now() - cached.createdAt < sentimentCacheTtl) {
    return { ...cached.payload, cached: true };
  }

  const url = new URL("https://www.alphavantage.co/query");
  url.searchParams.set("function", "NEWS_SENTIMENT");
  url.searchParams.set("tickers", symbol);
  url.searchParams.set("sort", "LATEST");
  url.searchParams.set("limit", "25");
  url.searchParams.set("apikey", alphaVantageApiKey);

  const response = await fetch(url, {
    headers: {
      "accept": "application/json",
      "user-agent": "finance-connect"
    }
  });

  if (!response.ok) {
    throw new Error(`Alpha Vantage returned ${response.status}`);
  }

  const data = await response.json();

  if (data.Information || data.Note || data["Error Message"]) {
    throw new Error(data.Information || data.Note || data["Error Message"]);
  }

  const feed = data.feed || [];
  const scored = feed.map((item) => {
    const tickerSentiment = (item.ticker_sentiment || []).find((entry) => entry.ticker === symbol);
    return {
      title: item.title || "",
      url: item.url || "",
      source: item.source || "",
      timePublished: item.time_published || "",
      summary: item.summary || "",
      overallSentimentScore: Number(item.overall_sentiment_score ?? 0),
      overallSentimentLabel: item.overall_sentiment_label || "",
      relevanceScore: Number(tickerSentiment?.relevance_score ?? 0),
      tickerSentimentScore: Number(tickerSentiment?.ticker_sentiment_score ?? item.overall_sentiment_score ?? 0),
      tickerSentimentLabel: tickerSentiment?.ticker_sentiment_label || item.overall_sentiment_label || ""
    };
  });
  const relevant = scored.filter((item) => Number.isFinite(item.tickerSentimentScore));
  const averageSentiment = average(relevant.map((item) => item.tickerSentimentScore));
  const averageRelevance = average(relevant.map((item) => item.relevanceScore));
  const label = averageSentiment === null
    ? "Sem leitura"
    : averageSentiment >= 0.35 ? "Bullish"
      : averageSentiment >= 0.15 ? "Levemente positivo"
        : averageSentiment <= -0.35 ? "Bearish"
          : averageSentiment <= -0.15 ? "Levemente negativo"
            : "Neutro";
  const payload = {
    symbol,
    source: "Alpha Vantage",
    articleCount: feed.length,
    averageSentiment,
    averageRelevance,
    label,
    news: scored.slice(0, 8),
    cached: false
  };

  sentimentCache.set(symbol, { createdAt: Date.now(), payload });
  return payload;
}

function parseOpenInsiderRows(html, symbol) {
  const rows = [...html.matchAll(/<tr[^>]*>([\s\S]*?)<\/tr>/gi)]
    .map((match) => [...match[1].matchAll(/<td[^>]*>([\s\S]*?)<\/td>/gi)].map((cell) => stripTags(cell[1])))
    .filter((cells) => cells.length >= 13 && cells.some((cell) => cell === symbol));

  return rows.map((cells) => {
    const tickerIndex = cells.findIndex((cell) => cell === symbol);
    const filingDate = cells[tickerIndex - 2] || "";
    const tradeDate = cells[tickerIndex - 1] || "";
    const company = cells[tickerIndex + 1] || "";
    const insider = cells[tickerIndex + 2] || "";
    const title = cells[tickerIndex + 3] || "";
    const tradeType = cells[tickerIndex + 4] || "";
    const price = cells[tickerIndex + 5] || "";
    const quantity = cells[tickerIndex + 6] || "";
    const valueText = cells[tickerIndex + 10] || "";

    return {
      filingDate,
      tradeDate,
      company,
      insider,
      title,
      tradeType,
      price,
      quantity,
      value: parseMoney(valueText),
      valueText
    };
  }).filter((trade) => trade.tradeType);
}

async function fetchTextWithTimeout(url, timeoutMs = 7000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        "accept": "text/html,*/*",
        "user-agent": "Mozilla/5.0 finance-connect"
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.text();
  } finally {
    clearTimeout(timer);
  }
}

async function getOpenInsiderSignal(symbol) {
  const url = `https://openinsider.com/screener?s=${encodeURIComponent(symbol)}&fd=90&xp=1`;

  try {
    const html = await fetchTextWithTimeout(url);
    const trades = parseOpenInsiderRows(html, symbol).slice(0, 20);
    const purchases = trades.filter((trade) => trade.tradeType.includes("P - Purchase"));
    const sales = trades.filter((trade) => trade.tradeType.includes("S - Sale"));
    const officerPurchases = purchases.filter((trade) => /CEO|CFO|Chief|Pres|Dir/i.test(trade.title));
    const totalBought = purchases.reduce((sum, trade) => sum + Math.max(trade.value || 0, 0), 0);
    const totalSold = sales.reduce((sum, trade) => sum + Math.abs(Math.min(trade.value || 0, 0)), 0);
    const signal = purchases.length
      ? "Insiders acumulando"
      : sales.length ? "So vendas recentes" : "Sem compras recentes";

    return {
      provider: "OpenInsider",
      status: "carregado",
      url,
      signal,
      purchases: purchases.length,
      officerPurchases: officerPurchases.length,
      sales: sales.length,
      totalBought,
      totalSold,
      trades: trades.slice(0, 8)
    };
  } catch (error) {
    return {
      provider: "OpenInsider",
      status: "indisponivel",
      url,
      signal: "Fonte indisponivel agora",
      error: error.message,
      purchases: 0,
      officerPurchases: 0,
      sales: 0,
      totalBought: 0,
      totalSold: 0,
      trades: []
    };
  }
}

async function getQuiverCongressSignal(symbol) {
  const url = `https://www.quiverquant.com/congresstrading/stock/${encodeURIComponent(symbol)}`;

  try {
    const html = await fetchTextWithTimeout(url);
    const text = stripTags(html);
    const noActivity = /No Congressional activity found/i.test(text) || /No Congress Trading data/i.test(text);

    return {
      provider: "Quiver Quant",
      status: noActivity ? "sem atividade publica detectada" : "pagina publica detectada",
      url,
      signal: noActivity ? "Sem trades recentes do Congresso" : "Verificar atividade no Quiver",
      requiresApi: true,
      note: "Dados estruturados por trade/setor exigem Quiver API. O app abre a pagina do ticker e marca alertas quando houver parser/API."
    };
  } catch (error) {
    return {
      provider: "Quiver Quant",
      status: "API/pagina indisponivel",
      url,
      signal: "Quiver requer API para dados estruturados",
      requiresApi: true,
      note: error.message
    };
  }
}

async function getAlternativeSignals(symbol) {
  const cached = alternativeCache.get(symbol);
  if (cached && Date.now() - cached.createdAt < alternativeCacheTtl) {
    return { ...cached.payload, cached: true };
  }

  // Use Finnhub via Python backend (reliable) + Quiver in parallel
  const [pyEnrich, congress] = await Promise.all([
    proxyPython(`/enrichment/${symbol}`).catch(() => null),
    getQuiverCongressSignal(symbol)
  ]);

  const pyInsider = pyEnrich?.insider || {};
  const insiders = pyInsider.error
    ? { provider: "Finnhub", status: "indisponivel", signal: "Finnhub sem dados", purchases: 0, officerPurchases: 0, sales: 0, totalBought: 0, totalSold: 0, trades: [] }
    : {
        provider: "Finnhub",
        status: "carregado",
        signal: pyInsider.signal || "—",
        purchases: 0,
        officerPurchases: 0,
        sales: 0,
        totalBought: pyInsider.buy_val || 0,
        totalSold:   pyInsider.sell_val || 0,
        trades: (pyInsider.summary || []).map(s => ({ insider: s, title: "", tradeType: "", valueText: "", tradeDate: "" }))
      };

  const payload = { symbol, insiders, congress, cached: false };
  alternativeCache.set(symbol, { createdAt: Date.now(), payload });
  return payload;
}

async function getInvestorMonitor() {
  const cached = investorsCache.get("latest");

  if (cached && Date.now() - cached.createdAt < investors13fCacheTtl) {
    return { ...cached.payload, cached: true };
  }

  let arkInvestor;

  try {
    arkInvestor = await getArkInvestorMonitor();
  } catch (error) {
    arkInvestor = {
      id: "ark",
      name: "Cathie Wood / ARK",
      source: "ARK daily holdings",
      cacheTtl: "1h",
      status: "erro ao carregar",
      focus: "Inovacao, crescimento disruptivo e ativos de alta volatilidade.",
      overlapHint: error.message,
      changes: { newPositions: [], increases: [], reductions: [] },
      topHoldings: []
    };
  }

  const investors = [
    {
      id: "berkshire",
      name: "Warren Buffett / Berkshire Hathaway",
      source: "SEC EDGAR 13F",
      cacheTtl: "6h",
      status: "parser pendente",
      focus: "Qualidade, caixa, seguros, bancos e consumo.",
      overlapHint: "AAPL e BAC tendem a ser os principais pontos de sobreposicao com sua carteira.",
      changes: { newPositions: [], increases: [], reductions: [] },
      topHoldings: [
        { symbol: "AAPL", weight: null, direction: "monitorar", overlap: true },
        { symbol: "BAC", weight: null, direction: "monitorar", overlap: true },
        { symbol: "AXP", weight: null, direction: "monitorar", overlap: false }
      ]
    },
    {
      id: "burry",
      name: "Michael Burry / Scion",
      source: "SEC EDGAR 13F",
      cacheTtl: "6h",
      status: "parser pendente",
      focus: "Assimetria, shorts, value contrarian e protecoes.",
      overlapHint: "Usar como alerta de risco narrativo, nao como copia automatica.",
      changes: { newPositions: [], increases: [], reductions: [] },
      topHoldings: []
    },
    {
      id: "ackman",
      name: "Bill Ackman / Pershing Square",
      source: "SEC EDGAR 13F",
      cacheTtl: "6h",
      status: "parser pendente",
      focus: "Carteira concentrada, qualidade, marcas fortes e ativismo.",
      overlapHint: "Comparar concentracao e qualidade com seus nucleos LP.",
      changes: { newPositions: [], increases: [], reductions: [] },
      topHoldings: []
    },
    {
      id: "dalio",
      name: "Ray Dalio / Bridgewater",
      source: "SEC EDGAR 13F",
      cacheTtl: "6h",
      status: "parser pendente",
      focus: "Diversificacao macro, ETFs, defensivos e alocacao por regime.",
      overlapHint: "Bom para comparar sua exposicao tech/growth contra uma leitura macro.",
      changes: { newPositions: [], increases: [], reductions: [] },
      topHoldings: []
    },
    arkInvestor
  ];
  const payload = {
    updatedAt: new Date().toISOString(),
    note: "Estrutura pronta. Proxima etapa: parser SEC EDGAR 13F e ARK daily holdings com comparacao vs trimestre anterior.",
    investors,
    cached: false
  };

  investorsCache.set("latest", { createdAt: Date.now(), payload });
  return payload;
}

async function fetchArkHoldings() {
  const url = "https://assets.ark-funds.com/fund-documents/funds-etf-csv/ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv";
  const response = await fetch(url, {
    headers: {
      "accept": "text/csv,*/*",
      "user-agent": "finance-connect"
    }
  });

  if (!response.ok) {
    throw new Error(`ARK holdings returned ${response.status}`);
  }

  const csv = await response.text();
  const lines = csv.split(/\r?\n/).filter((line) => line.trim());
  const headers = parseCsvLine(lines[0]).map((header) => header.trim().toLowerCase());
  const indexOf = (name) => headers.indexOf(name);
  const dateIndex = indexOf("date");
  const fundIndex = indexOf("fund");
  const companyIndex = indexOf("company");
  const tickerIndex = indexOf("ticker");
  const sharesIndex = indexOf("shares");
  const marketValueIndex = indexOf("market value ($)");
  const weightIndex = indexOf("weight (%)");

  return lines.slice(1).map(parseCsvLine).map((row) => ({
    date: row[dateIndex],
    fund: row[fundIndex],
    company: row[companyIndex],
    symbol: normalizeSymbol(row[tickerIndex]),
    shares: parseMoney(row[sharesIndex]),
    marketValue: parseMoney(row[marketValueIndex]),
    weight: parsePercent(row[weightIndex])
  })).filter((holding) => holding.symbol);
}

async function getArkInvestorMonitor() {
  const cached = investorsCache.get("ark");

  if (cached && Date.now() - cached.createdAt < arkCacheTtl) {
    return { ...cached.payload, cached: true };
  }

  const holdings = await fetchArkHoldings();
  let previous = [];

  try {
    previous = JSON.parse(await readFile(arkSnapshotPath, "utf8")).holdings || [];
  } catch {
    previous = [];
  }

  const previousBySymbol = new Map(previous.map((holding) => [holding.symbol, holding]));
  const portfolioSymbols = getDefaultPortfolioSymbols();
  const compared = holdings.map((holding) => {
    const previousHolding = previousBySymbol.get(holding.symbol);
    const shareChange = previousHolding && holding.shares !== null && previousHolding.shares !== null
      ? holding.shares - previousHolding.shares
      : null;
    const direction = shareChange === null
      ? "base"
      : shareChange > 0 ? "aumentou" : shareChange < 0 ? "reduziu" : "sem mudanca";

    return {
      ...holding,
      direction,
      shareChange,
      overlap: portfolioSymbols.has(holding.symbol)
    };
  });
  const newPositions = compared.filter((holding) => !previousBySymbol.has(holding.symbol)).slice(0, 10);
  const increases = compared.filter((holding) => holding.shareChange > 0).slice(0, 10);
  const reductions = compared.filter((holding) => holding.shareChange < 0).slice(0, 10);
  const payload = {
    id: "ark",
    name: "Cathie Wood / ARK Innovation ETF",
    source: "ARK daily holdings CSV",
    cacheTtl: "1h",
    status: previous.length ? "carregado" : "base criada",
    focus: "Inovacao, crescimento disruptivo e ativos de alta volatilidade.",
    overlapHint: "Sobreposicoes marcadas com 🔗 indicam ativos presentes tambem na sua carteira atual.",
    changes: {
      newPositions,
      increases,
      reductions
    },
    topHoldings: compared.slice(0, 10),
    date: holdings[0]?.date || null,
    holdingCount: holdings.length,
    cached: false
  };

  await mkdir(dataDir, { recursive: true });
  await writeFile(arkSnapshotPath, JSON.stringify({ createdAt: new Date().toISOString(), holdings }, null, 2));
  investorsCache.set("ark", { createdAt: Date.now(), payload });
  return payload;
}

function getDemoAnalysis(symbol, reason) {
  return {
    symbol,
    recommendationKey: "buy",
    recommendationMean: 2.1,
    numberOfAnalystOpinions: 31,
    targetMeanPrice: 286,
    targetMedianPrice: 282,
    targetHighPrice: 330,
    targetLowPrice: 232,
    currentPrice: null,
    trend: [
      {
        period: "0m",
        strongBuy: 9,
        buy: 16,
        hold: 6,
        sell: 0,
        strongSell: 0
      },
      {
        period: "-1m",
        strongBuy: 8,
        buy: 15,
        hold: 7,
        sell: 1,
        strongSell: 0
      }
    ],
    upgrades: [
      {
        firm: "Exemplo Research",
        action: "main",
        fromGrade: "Buy",
        toGrade: "Buy",
        epochGradeDate: Math.floor(Date.now() / 1000) - 86400 * 5
      },
      {
        firm: "Amostra Capital",
        action: "up",
        fromGrade: "Neutral",
        toGrade: "Buy",
        epochGradeDate: Math.floor(Date.now() / 1000) - 86400 * 18
      }
    ],
    earnings: [],
    cached: false,
    demo: true,
    unavailableReason: reason
  };
}

async function serveStatic(request, response, pathname) {
  const requestedPath = pathname === "/" ? "/index.html" : pathname;
  const filePath = normalize(join(publicDir, requestedPath));

  if (!filePath.startsWith(publicDir)) {
    response.writeHead(403);
    response.end("Forbidden");
    return;
  }

  try {
    const body = await readFile(filePath);
    response.writeHead(200, {
      "content-type": contentTypes[extname(filePath)] || "application/octet-stream"
    });
    response.end(body);
  } catch {
    response.writeHead(404);
    response.end("Not found");
  }
}

const PYTHON_API = process.env.PYTHON_API_URL || "http://127.0.0.1:8000";

// ── Horizon map — read once from portfolio_us.csv ──────────────────────────
function loadHorizonMap() {
  const csvPath = join(root, "..", "src", "data", "portfolio_us.csv");
  try {
    const lines = readFileSync(csvPath, "utf8").split(/\r?\n/).filter(l => l.trim());
    const headers = parseCsvLine(lines[0]).map(h => h.trim().toLowerCase());
    const symIdx = headers.indexOf("symbol");
    const horIdx = headers.indexOf("horizon");
    if (symIdx === -1 || horIdx === -1) return {};
    const map = {};
    for (const line of lines.slice(1)) {
      const cols = parseCsvLine(line);
      if (cols[symIdx]) map[cols[symIdx].trim().toUpperCase()] = cols[horIdx]?.trim() || "swing";
    }
    return map;
  } catch {
    return {};
  }
}
const horizonMap = loadHorizonMap();

async function proxyPython(path) {
  const headers = { "accept": "application/json" };
  if (INTERNAL_API_TOKEN) headers["x-internal-token"] = INTERNAL_API_TOKEN;
  const res = await fetch(`${PYTHON_API}${path}`, { headers });
  if (!res.ok) throw new Error(`Python API ${res.status}: ${path}`);
  return res.json();
}

createServer(async (request, response) => {
  const url = new URL(request.url, `http://${request.headers.host}`);

  // ── Health check (public) ─────────────────────────────────────────────────
  if (url.pathname === "/health") {
    sendJson(response, 200, { status: "ok", ts: new Date().toISOString() });
    return;
  }

  // ── Auth endpoints (public) ───────────────────────────────────────────────
  if (url.pathname === "/api/auth/login" && request.method === "POST") {
    if (!APP_PASSWORD) {
      sendJson(response, 200, { token: "no-auth" });
      return;
    }
    try {
      const body = await readBody(request);
      const { password = "" } = JSON.parse(body);
      const exp = Buffer.from(APP_PASSWORD);
      const got = Buffer.from(String(password));
      const match = exp.length === got.length && timingSafeEqual(exp, got);
      if (match) {
        sendJson(response, 200, { token: createSession() });
      } else {
        sendJson(response, 401, { error: "Senha incorreta" });
      }
    } catch {
      sendJson(response, 400, { error: "Requisição inválida" });
    }
    return;
  }

  if (url.pathname === "/api/auth/check") {
    sendJson(response, 200, { ok: isValidSession(bearerToken(request)) || !APP_PASSWORD });
    return;
  }

  // ── Protect all /api/* routes ─────────────────────────────────────────────
  if (url.pathname.startsWith("/api/") && !requireAuth(request, response)) return;

  // ── Python API proxy ──────────────────────────────────────────────────────
  if (url.pathname === "/api/py/portfolio") {
    try { sendJson(response, 200, await proxyPython("/portfolio")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/portfolio/summary") {
    try { sendJson(response, 200, await proxyPython("/portfolio/summary")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/briefing") {
    try { sendJson(response, 200, await proxyPython("/briefing")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/policy" && request.method === "GET") {
    try { sendJson(response, 200, await proxyPython("/policy")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/policy" && request.method === "PUT") {
    try {
      const body = await readBody(request);
      const pHeaders = { "content-type": "application/json", "accept": "application/json" };
      if (INTERNAL_API_TOKEN) pHeaders["x-internal-token"] = INTERNAL_API_TOKEN;
      const res = await fetch(`${PYTHON_API}/policy`, {
        method: "PUT",
        headers: pHeaders,
        body
      });
      if (!res.ok) throw new Error(`Python API ${res.status}`);
      sendJson(response, 200, await res.json());
    } catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/policy/check") {
    try { sendJson(response, 200, await proxyPython("/policy/check")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/thesis" && request.method === "GET") {
    try { sendJson(response, 200, await proxyPython("/thesis")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname.startsWith("/api/py/thesis/")) {
    const sym = url.pathname.split("/").pop().toUpperCase();
    if (request.method === "GET") {
      try { sendJson(response, 200, await proxyPython(`/thesis/${sym}`)); }
      catch (e) { sendJson(response, 502, { error: e.message }); }
      return;
    }
    if (request.method === "PUT") {
      try {
        const body = await readBody(request);
        const tHeaders = { "content-type": "application/json", "accept": "application/json" };
        if (INTERNAL_API_TOKEN) tHeaders["x-internal-token"] = INTERNAL_API_TOKEN;
        const res = await fetch(`${PYTHON_API}/thesis/${sym}`, {
          method: "PUT",
          headers: tHeaders,
          body
        });
        if (!res.ok) throw new Error(`Python API ${res.status}`);
        sendJson(response, 200, await res.json());
      } catch (e) { sendJson(response, 502, { error: e.message }); }
      return;
    }
  }

  if (url.pathname === "/api/py/macro") {
    try { sendJson(response, 200, await proxyPython("/macro")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/macro/full") {
    try { sendJson(response, 200, await proxyPython("/macro/full")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/market-status") {
    try { sendJson(response, 200, await proxyPython("/market-status")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/investors") {
    try { sendJson(response, 200, await proxyPython("/investors")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/ark") {
    try { sendJson(response, 200, await proxyPython("/ark")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/screener") {
    try { sendJson(response, 200, await proxyPython("/screener")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/sectors") {
    try { sendJson(response, 200, await proxyPython("/sectors")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/calendar") {
    try { sendJson(response, 200, await proxyPython("/calendar")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/intraday") {
    try { sendJson(response, 200, await proxyPython("/intraday")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname.startsWith("/api/py/intraday/")) {
    const sym = normalizeSymbol(url.pathname.split("/").pop());
    try { sendJson(response, 200, await proxyPython(`/intraday/${sym}`)); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/brasil") {
    try { sendJson(response, 200, await proxyPython("/brasil")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname.startsWith("/api/py/asset/")) {
    const sym = normalizeSymbol(url.pathname.split("/").pop());
    try { sendJson(response, 200, await proxyPython(`/asset/${sym}`)); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname.startsWith("/api/py/enrichment/")) {
    const sym = normalizeSymbol(url.pathname.split("/").pop());
    try { sendJson(response, 200, await proxyPython(`/enrichment/${sym}`)); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname.startsWith("/api/py/ebitda/")) {
    const sym = normalizeSymbol(url.pathname.split("/").pop());
    try { sendJson(response, 200, await proxyPython(`/ebitda/${sym}`)); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname.startsWith("/api/py/polygon/")) {
    const sym = normalizeSymbol(url.pathname.split("/").pop());
    try { sendJson(response, 200, await proxyPython(`/polygon/${sym}`)); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname.startsWith("/api/py/alternative/")) {
    const sym = normalizeSymbol(url.pathname.split("/").pop());
    try { sendJson(response, 200, await proxyPython(`/alternative/${sym}`)); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname.startsWith("/api/py/analyst/")) {
    const sym = normalizeSymbol(url.pathname.split("/").pop());
    try { sendJson(response, 200, await proxyPython(`/analyst/${sym}`)); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname.startsWith("/api/py/swing/")) {
    const sym = normalizeSymbol(url.pathname.split("/").pop());
    try { sendJson(response, 200, await proxyPython(`/swing/${sym}`)); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/market-sentiment") {
    try { sendJson(response, 200, await proxyPython("/market-sentiment")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/risk-book") {
    try { sendJson(response, 200, await proxyPython("/risk-book")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/weekly-committee") {
    try { sendJson(response, 200, await proxyPython("/weekly-committee")); }
    catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/py/decision-memo" && request.method === "POST") {
    try {
      const body = await readBody(request);
      const dmHeaders = { "content-type": "application/json", "accept": "application/json" };
      if (INTERNAL_API_TOKEN) dmHeaders["x-internal-token"] = INTERNAL_API_TOKEN;
      const res  = await fetch(`${PYTHON_API}/decision-memo`, {
        method:  "POST",
        headers: dmHeaders,
        body,
      });
      if (!res.ok) throw new Error(`Python API ${res.status}`);
      sendJson(response, 200, await res.json());
    } catch (e) { sendJson(response, 502, { error: e.message }); }
    return;
  }

  if (url.pathname === "/api/quote") {
    const symbol = normalizeSymbol(url.searchParams.get("symbol"));

    if (!symbol) {
      sendJson(response, 400, { error: "Informe um ticker valido." });
      return;
    }

    try {
      sendJson(response, 200, await getYahooQuote(symbol));
    } catch (error) {
      sendJson(response, 502, { error: error.message });
    }
    return;
  }

  if (url.pathname === "/api/analysis") {
    const symbol = normalizeSymbol(url.searchParams.get("symbol"));

    if (!symbol) {
      sendJson(response, 400, { error: "Informe um ticker valido." });
      return;
    }

    try {
      sendJson(response, 200, await getYahooAnalysis(symbol));
    } catch (error) {
      sendJson(response, 200, getDemoAnalysis(symbol, error.message));
    }
    return;
  }

  if (url.pathname === "/api/upload-portfolio" && request.method === "POST") {
    let body = "";
    request.on("data", chunk => { body += chunk; });
    request.on("end", () => {
      try {
        const positions = parsePortfolioCsv(body).map(p => ({
          ...p,
          horizon:  horizonMap[p.symbol] || "swing",
          strategy: strategyForSymbol(p.symbol)
        }));
        sendJson(response, 200, { count: positions.length, positions });
      } catch (error) {
        sendJson(response, 400, { error: error.message });
      }
    });
    return;
  }

  if (url.pathname === "/api/import-portfolio") {
    try {
      const downloadsDir = "/Users/macbook/Downloads";
      const { readdirSync } = await import("node:fs");
      const files = readdirSync(downloadsDir)
        .filter(f => f.startsWith("Individual-Positions-") && f.endsWith(".csv"))
        .sort().reverse();
      const csvPath = files.length ? join(downloadsDir, files[0]) : defaultPortfolioPath;
      const csv = await readFile(csvPath, "utf8");
      const positions = parsePortfolioCsv(csv).map(p => ({
        ...p,
        horizon:  horizonMap[p.symbol] || "swing",
        strategy: strategyForSymbol(p.symbol)
      }));
      sendJson(response, 200, { count: positions.length, positions, source: csvPath });
    } catch (error) {
      sendJson(response, 500, { error: error.message });
    }
    return;
  }

  if (url.pathname === "/api/sentiment") {
    const symbol = normalizeSymbol(url.searchParams.get("symbol"));

    if (!symbol) {
      sendJson(response, 400, { error: "Informe um ticker valido." });
      return;
    }

    try {
      sendJson(response, 200, await getAlphaVantageSentiment(symbol));
    } catch (error) {
      sendJson(response, 503, { error: error.message, provider: "Alpha Vantage" });
    }
    return;
  }

  if (url.pathname === "/api/alternative-signals") {
    const symbol = normalizeSymbol(url.searchParams.get("symbol"));

    if (!symbol) {
      sendJson(response, 400, { error: "Informe um ticker valido." });
      return;
    }

    try {
      sendJson(response, 200, await getAlternativeSignals(symbol));
    } catch (error) {
      sendJson(response, 503, { error: error.message });
    }
    return;
  }

  if (url.pathname === "/api/market-regime") {
    try {
      sendJson(response, 200, await getMarketRegime());
    } catch (error) {
      sendJson(response, 503, { error: error.message });
    }
    return;
  }

  if (url.pathname === "/api/investors") {
    try {
      sendJson(response, 200, await getInvestorMonitor());
    } catch (error) {
      sendJson(response, 503, { error: error.message });
    }
    return;
  }

  await serveStatic(request, response, url.pathname);
}).listen(port, host, () => {
  process.stdout.write("\x1b]0;Investment\x07");
  console.log(`Investment running at http://${host}:${port}`);
});
