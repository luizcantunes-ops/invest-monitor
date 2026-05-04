import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from core.fetcher    import get_asset_data, get_macro_data, get_br_asset_data
from core.indicators import (calc_rsi, calc_macd, calc_moving_averages,
                              interpret_rsi, interpret_macd,
                              interpret_moving_averages,
                              interpret_vix, interpret_yield_curve,
                              describe_shiller_pe, describe_buffett_indicator,
                              describe_vix_full, describe_yield_curve_full)
from core.screener   import screen_swing_candidates
from core.investors  import (INVESTORS, ARK_ETFS, CHANGE_LABELS,
                              get_investor_holdings, get_ark_holdings, find_overlaps)
from core.enricher    import (get_ticker_enrichment, get_sector_performance,
                               get_economic_calendar, get_upcoming_earnings,
                               get_ebitda_metrics)
from core.alternative import get_alternative_signals
from core.polygon     import (get_full_enrichment, get_history,
                               get_market_status, get_news as polygon_news)
from data.config      import (PORTFOLIO_TOTAL_BR, CRYPTO_BAND_LOW,
                               CRYPTO_BAND_HIGH, MACRO_SHILLER_PE, MACRO_BUFFETT_IND)

st.set_page_config(
    page_title="Investment Monitor",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design System — Light ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

@keyframes magic-in {
  from { opacity:0; transform:translateY(12px); }
  to   { opacity:1; transform:translateY(0); }
}

/* ── BASE ── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stMain"] {
    background: #F4F5F7 !important;
    font-family:"Inter",-apple-system,BlinkMacSystemFont,system-ui,sans-serif !important;
    color: #111827 !important;
}
[data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]::after { display:none; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E5E7EB !important;
}
[data-testid="stSidebar"] * {
    font-family:"Inter",-apple-system,system-ui,sans-serif !important;
    color: #374151 !important;
}
[data-testid="stSidebar"] label {
    font-size:13px !important; font-weight:500 !important;
}

/* ── METRICS ── */
[data-testid="metric-container"] {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius:10px; padding:14px 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    transition: box-shadow .2s ease;
}
[data-testid="metric-container"]:hover {
    box-shadow: 0 4px 12px rgba(79,70,229,.08);
    border-color: #C7D2FE;
}
[data-testid="stMetricLabel"] {
    font-size:11px !important; letter-spacing:.05em; text-transform:uppercase;
    color:#6B7280 !important; font-weight:700 !important;
}
[data-testid="stMetricValue"] {
    font-size:22px !important; font-weight:700 !important; color:#111827 !important;
}
[data-testid="stMetricDelta"] { font-size:12px !important; }

/* ── BUTTONS ── */
[data-testid="stButton"] > button {
    background: #4F46E5 !important;
    color:#fff !important;
    border:none !important;
    border-radius:8px !important;
    font-weight:600 !important; font-size:13px !important;
    padding:8px 20px !important;
    transition: background .2s ease, box-shadow .2s ease !important;
}
[data-testid="stButton"] > button:hover {
    background: #4338CA !important;
    box-shadow: 0 4px 12px rgba(79,70,229,.25) !important;
    transform:translateY(-1px) !important;
}

/* ── ALERTS / TABS ── */
[data-testid="stAlert"] {
    background:#F0F9FF !important;
    border:1px solid #BAE6FD !important;
    border-radius:8px !important; font-size:13px !important;
    color:#0C4A6E !important;
}
[data-testid="stSpinner"] { color:#4F46E5 !important; }
.js-plotly-plot { border-radius:8px; }

[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #FFFFFF;
    border-bottom: 2px solid #E5E7EB;
    gap: 0;
    padding: 0;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    color: #6B7280 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 12px 20px !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #4F46E5 !important;
    border-bottom-color: #4F46E5 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-panel"] {
    padding-top: 20px !important;
}

/* ── CARD ── */
.asset-row {
    position:relative; overflow:hidden;
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius:12px; padding:20px 24px; margin-bottom:12px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    transition: box-shadow .2s ease, transform .2s ease;
    animation: magic-in .35s ease both;
}

.asset-row::before, .asset-row::after { display:none; }
.asset-row:hover {
    border-color: #C7D2FE;
    box-shadow: 0 4px 16px rgba(79,70,229,.08);
    transform:translateY(-1px);
}

/* ── TYPOGRAPHY ── */
.page-title {
    font-size:22px; font-weight:700; letter-spacing:-.02em;
    color:#111827; margin:0 0 4px;
    animation: magic-in .3s ease both;
}
.page-sub {
    font-size:13px; color:#6B7280; margin-bottom:20px;
}
.section-label {
    font-size:11px; font-weight:700; letter-spacing:.08em;
    text-transform:uppercase; color:#9CA3AF;
    margin:24px 0 10px; padding-bottom:8px;
    border-bottom:1px solid #E5E7EB;
}

/* ── TAGS ── */
.tag-swing {
    font-size:10px; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
    background:#FEF3C7; color:#92400E;
    padding:3px 9px; border-radius:20px;
    border:1px solid #FDE68A;
}
.tag-lt {
    font-size:10px; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
    background:#EEF2FF; color:#3730A3;
    padding:3px 9px; border-radius:20px;
    border:1px solid #C7D2FE;
}

/* ── ASSET ROW ELEMENTS ── */
.ar-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px; }
.ar-left   { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.ar-symbol { font-size:18px; font-weight:700; color:#111827; }
.ar-name   { font-size:13px; color:#6B7280; }
.ar-right  { text-align:right; }
.ar-price  { font-size:24px; font-weight:700; color:#111827; display:block; letter-spacing:-.02em; }
.ar-day-pos { font-size:12px; font-weight:600; color:#059669; }
.ar-day-neg { font-size:12px; font-weight:600; color:#DC2626; }

.ar-stats {
    display:flex; gap:28px; flex-wrap:wrap; padding:12px 0;
    border-top:1px solid #F3F4F6;
    border-bottom:1px solid #F3F4F6;
    margin-bottom:12px;
}
.stat-label { font-size:11px; font-weight:600; letter-spacing:.05em;
              text-transform:uppercase; color:#9CA3AF; margin-bottom:3px; }
.stat-val   { font-size:15px; font-weight:600; color:#111827; }
.stat-pos   { font-size:15px; font-weight:700; color:#059669; }
.stat-neg   { font-size:15px; font-weight:700; color:#DC2626; }
.stat-up    { font-size:13px; color:#059669; font-weight:600; }
.stat-dn    { font-size:13px; color:#DC2626; font-weight:600; }

.range-label { font-size:12px; color:#9CA3AF; margin-bottom:5px; }
.range-track { background:#F3F4F6; border-radius:3px; height:5px;
               position:relative; margin-bottom:12px; }
.range-fill  { background:linear-gradient(90deg,#4F46E5,#818CF8);
               border-radius:3px; height:5px; }

.ar-signals  { display:flex; gap:20px; flex-wrap:wrap; }
.sig-item    { flex:1; min-width:200px; }
.sig-label   { font-size:13px; font-weight:600; color:#374151; }
.sig-action  { font-size:12px; color:#6B7280; margin-top:2px; line-height:1.45; }
.mas-line    { font-size:12px; color:#9CA3AF; margin-top:10px; }

/* ── SCREENER ROW ── */
.screener-row {
    background:#FFFFFF;
    border:1px solid #E5E7EB;
    border-radius:12px; padding:18px 22px; margin-bottom:10px;
    display:flex; gap:20px; align-items:flex-start; flex-wrap:wrap;
    box-shadow: 0 1px 3px rgba(0,0,0,.05);
    transition: box-shadow .2s ease, transform .2s ease;
    animation: magic-in .3s ease both;
}
.screener-row:hover {
    border-color:#C7D2FE;
    box-shadow:0 4px 16px rgba(79,70,229,.08);
    transform:translateY(-1px);
}
.sr-left   { flex:1; min-width:180px; }
.sr-symbol { font-size:16px; font-weight:700; color:#111827; }
.sr-name   { font-size:12px; color:#6B7280; margin-top:2px; }
.sr-right  { display:flex; gap:24px; flex-wrap:wrap; }

/* ── MACRO ── */
.macro-row { display:flex; gap:16px; flex-wrap:wrap; padding:14px 0;
             border-bottom:1px solid #F3F4F6; }
.macro-item { flex:1; min-width:140px; }
.macro-label { font-size:11px; font-weight:700; letter-spacing:.07em;
               text-transform:uppercase; color:#9CA3AF; margin-bottom:4px; }
.macro-val  { font-size:22px; font-weight:700; color:#111827; }
.macro-desc { font-size:12px; color:#6B7280; margin-top:3px; line-height:1.45; }

/* ── CALLOUT BOXES ── */
.warn-box {
    background:#FFFBEB; border:1px solid #FDE68A;
    border-radius:8px; padding:14px 18px; font-size:13px;
    color:#92400E; margin-top:16px; line-height:1.6;
}
.info-box {
    background:#EEF2FF; border:1px solid #C7D2FE;
    border-radius:8px; padding:14px 18px; font-size:13px;
    color:#3730A3; margin-top:10px; line-height:1.6;
}

/* ── OVERVIEW ── */
.overview-summary {
    background:#FFFFFF;
    border:1px solid #E5E7EB;
    border-radius:12px; padding:22px 26px; margin-bottom:20px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    animation: magic-in .3s ease both;
}
.ov-row   { display:flex; gap:40px; flex-wrap:wrap; }
.ov-label { font-size:11px; font-weight:700; letter-spacing:.07em;
            text-transform:uppercase; color:#9CA3AF; margin-bottom:4px; }
.ov-val   { font-size:26px; font-weight:700; color:#111827; letter-spacing:-.02em; }
.ov-sub   { font-size:12px; color:#6B7280; margin-top:3px; }

/* ── CRYPTO BAR ── */
.crypto-bar-track { height:8px; background:#F3F4F6; border-radius:4px; }
.crypto-bar-fill  { height:8px; border-radius:4px;
                    background:linear-gradient(90deg,#4F46E5,#818CF8); }
.crypto-bar-ok    { height:8px; border-radius:4px;
                    background:linear-gradient(90deg,#059669,#34D399); }
.crypto-bar-warn  { height:8px; border-radius:4px;
                    background:linear-gradient(90deg,#D97706,#FBBF24); }

/* ── MISC ── */
.divider { height:1px; background:#E5E7EB; margin:20px 0; }

[data-testid="stMultiSelect"] > div {
    background:#FFFFFF !important;
    border-color:#E5E7EB !important;
}

[data-testid="stCaptionContainer"] { color:#9CA3AF !important; }

code { background:#EEF2FF !important; color:#4338CA !important;
       border-radius:4px; padding:1px 6px; }

::-webkit-scrollbar       { width:5px; height:5px; }
::-webkit-scrollbar-track { background:#F9FAFB; }
::-webkit-scrollbar-thumb { background:#D1D5DB; border-radius:10px; }
::-webkit-scrollbar-thumb:hover { background:#9CA3AF; }

</style>
""", unsafe_allow_html=True)

# Magic UI mouse-tracking glow (MagicCard signature effect)
import streamlit.components.v1 as components
components.html("""
<script>
(function() {
  function attachGlow() {
    const cards = window.parent.document.querySelectorAll('.asset-row, .screener-row, .overview-summary');
    cards.forEach(card => {
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width  * 100).toFixed(1);
        const y = ((e.clientY - rect.top)  / rect.height * 100).toFixed(1);
        card.style.setProperty('--mx', x + '%');
        card.style.setProperty('--my', y + '%');
        card.style.backgroundImage =
          `radial-gradient(400px circle at ${x}% ${y}%, rgba(74,111,212,0.07), transparent 60%), rgba(255,255,255,0.025)`.replace('rgba(255,255,255,0.025)','');
      });
      card.addEventListener('mouseleave', () => {
        card.style.backgroundImage = '';
      });
    });
  }
  // Retry until Streamlit renders cards
  let tries = 0;
  const iv = setInterval(() => {
    attachGlow();
    if (++tries > 30) clearInterval(iv);
  }, 600);
})();
</script>
""", height=0)


# ── Cache ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def cached_asset(symbol):
    try:
        return get_asset_data(symbol)
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def cached_macro():
    try:
        return get_macro_data()
    except Exception:
        return {"vix": 0, "sp500": 0, "yield_10y": 0, "yield_3m": 0, "yield_spread": 0}

@st.cache_data(ttl=3600, show_spinner=False)
def cached_br_asset(ticker):
    try:
        return get_br_asset_data(ticker)
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def cached_enrichment(symbol):
    try:
        return get_ticker_enrichment(symbol)
    except Exception:
        return {}

@st.cache_data(ttl=3600, show_spinner=False)
def cached_ebitda(symbol):
    try:
        return get_ebitda_metrics(symbol)
    except Exception:
        return {"error": "Erro ao buscar"}

@st.cache_data(ttl=86400, show_spinner=False)
def cached_sectors():
    try:
        return get_sector_performance()
    except Exception:
        return {"sectors": {}, "error": "Erro ao buscar"}

@st.cache_data(ttl=3600, show_spinner=False)
def cached_eco_calendar():
    try:
        return get_economic_calendar()
    except Exception:
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def cached_alternative(symbol):
    try:
        return get_alternative_signals(symbol)
    except Exception:
        return {}

@st.cache_data(ttl=3600, show_spinner=False)
def cached_polygon(symbol):
    try:
        return get_full_enrichment(symbol)
    except Exception:
        return {}

@st.cache_data(ttl=86400, show_spinner=False)
def cached_polygon_history(symbol):
    try:
        return get_history(symbol, days=180)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def cached_market_status():
    try:
        return get_market_status()
    except Exception:
        return {}


# ── Header ────────────────────────────────────────────────────────────────────
mkt = cached_market_status()
ny_exch = mkt.get("exchanges", {}).get("nyse", "") if mkt else ""
after_hrs = mkt.get("after_hrs", False) if mkt else False
early_hrs = mkt.get("early_hrs", False) if mkt else False

if ny_exch == "open":
    status_dot, status_txt = "🟢", "Mercado aberto"
elif after_hrs:
    status_dot, status_txt = "🟡", "After hours"
elif early_hrs:
    status_dot, status_txt = "🟡", "Pre-market"
else:
    status_dot, status_txt = "🔴", "Fechado"

col_title, col_status, col_btn = st.columns([3, 2, 1])
with col_title:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;padding:8px 0 16px">
      <div style="width:36px;height:36px;background:#4F46E5;border-radius:9px;
                  display:flex;align-items:center;justify-content:center;
                  font-size:18px;font-weight:700;color:#fff">F</div>
      <div>
        <div style="font-size:16px;font-weight:700;color:#111827;letter-spacing:-.3px">Investment Monitor</div>
        <div style="font-size:12px;color:#9CA3AF">Luiz Cesar Antunes</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
with col_status:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px;padding:8px 0 16px">
      <span style="font-size:13px">{status_dot}</span>
      <div>
        <div style="font-size:13px;font-weight:600;color:#374151">{status_txt}</div>
        <div style="font-size:11px;color:#9CA3AF">NYSE · {datetime.now().strftime('%H:%M')}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
with col_btn:
    st.markdown("<div style='padding-top:8px'>", unsafe_allow_html=True)
    if st.button("↻ Atualizar"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

portfolio_df = pd.read_csv(os.path.join(os.path.dirname(__file__), "../data/portfolio_us.csv"))
br_df        = pd.read_csv(os.path.join(os.path.dirname(__file__), "../data/portfolio_br.csv"))


# ── Asset card ────────────────────────────────────────────────────────────────
def asset_card(symbol: str, qty: float, cost_basis: float, horizon: str):
    with st.spinner(f"Carregando {symbol}"):
        d = cached_asset(symbol)
    if d is None:
        st.warning(f"{symbol} — erro ao buscar dados.")
        return

    hist    = d["hist"]
    rsi     = interpret_rsi(calc_rsi(hist))
    macd    = interpret_macd(calc_macd(hist))
    mas     = calc_moving_averages(hist)
    price   = d["price"] or 0
    mkt_val = price * qty
    gain_u  = mkt_val - cost_basis
    gain_p  = gain_u / cost_basis * 100 if cost_basis else 0
    day_c   = d["day_chg_pct"]

    tag      = '<span class="tag-swing">Swing</span>' if horizon == "swing" else '<span class="tag-lt">Long Term</span>'
    g_cls    = "stat-pos" if gain_u >= 0 else "stat-neg"
    d_cls    = "ar-day-pos" if day_c >= 0 else "ar-day-neg"
    up_cls   = "stat-up" if d["upside_pct"] >= 0 else "stat-dn"
    up_arrow = "▲" if d["upside_pct"] >= 0 else "▼"
    day_arr  = "▲" if day_c >= 0 else "▼"

    l52, h52 = d["week52_low"], d["week52_high"]
    bar_pct  = max(0, min(100, (price - l52) / max(h52 - l52, 1) * 100))
    pf_high  = d["pct_from_high"]
    tgt      = d["target_mean"] or 0
    rec      = d["recommendation"] or "N/A"
    pe       = f"{d['pe_forward']:.1f}x" if d["pe_forward"] else "—"
    n_an     = d["n_analysts"]
    ma_txt   = interpret_moving_averages(price, mas)

    st.markdown(f"""
    <div class="asset-row">
      <div class="ar-header">
        <div class="ar-left">
          {tag}
          <span class="ar-symbol">{symbol}</span>
          <span class="ar-name">{d['name']}</span>
        </div>
        <div class="ar-right">
          <span class="ar-price">${price:.2f}</span>
          <span class="{d_cls}">{day_arr} {abs(day_c):.2f}% hoje</span>
        </div>
      </div>

      <div class="ar-stats">
        <div>
          <div class="stat-label">P&L acumulado</div>
          <div class="{g_cls}">${gain_u:+,.0f} &nbsp; {gain_p:+.1f}%</div>
        </div>
        <div>
          <div class="stat-label">Fair Price</div>
          <div class="stat-val">${tgt:.2f} &nbsp;
            <span class="{up_cls}">{up_arrow} {abs(d['upside_pct']):.1f}%</span>
          </div>
        </div>
        <div>
          <div class="stat-label">Analistas</div>
          <div class="stat-val">{rec} <span style="color:#4a5065;font-size:12px;font-weight:400">({n_an} casas)</span></div>
        </div>
        <div>
          <div class="stat-label">P/E Forward</div>
          <div class="stat-val">{pe}</div>
        </div>
      </div>

      <div>
        <div class="range-label">52 semanas &nbsp; ${l52:.2f} — ${h52:.2f} &nbsp;·&nbsp; {pf_high:.1f}% da máxima</div>
        <div class="range-track">
          <div class="range-fill" style="width:{bar_pct:.0f}%"></div>
        </div>
      </div>

      <div class="ar-signals">
        <div class="sig-item">
          <div class="sig-label">{rsi['emoji']} {rsi['label']}</div>
          <div class="sig-action">{rsi['action']}</div>
        </div>
        <div class="sig-item">
          <div class="sig-label">{macd['emoji']} {macd['label']}</div>
          <div class="sig-action">{macd['action']}</div>
        </div>
      </div>
      <div class="mas-line">{ma_txt}</div>
    </div>
    """, unsafe_allow_html=True)

    # Enrichment — Finnhub
    enr = cached_enrichment(symbol)
    if enr:
        news    = enr.get("news", {})
        insider = enr.get("insider", {})
        earn    = enr.get("earnings", {})
        reco    = enr.get("reco", {})

        news_html = ""
        if news and not news.get("error"):
            news_html = f"""
            <div style="display:flex;gap:6px;align-items:center">
              <span style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                           color:#4a5065">Notícias</span>
              <span style="font-size:13px;font-weight:600;color:{news['color']}">{news['label']}</span>
              <span style="font-size:12px;color:#4a5065">
                · Bullish {news['bullish']}% / Bearish {news['bearish']}%
                · {news['articles']} artigos esta semana
              </span>
            </div>"""

        insider_html = ""
        if insider and not insider.get("error") and insider.get("summary"):
            rows = "".join(f"<div style='font-size:11px;color:#5c6278'>{s}</div>"
                           for s in insider["summary"][:2])
            insider_html = f"""
            <div style="margin-top:6px">
              <span style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                           color:#4a5065">Insiders</span>
              <span style="font-size:13px;font-weight:600;color:{insider['color']};margin-left:6px">
                {insider['signal']}
              </span>
              <div style="margin-top:3px">{rows}</div>
            </div>"""

        earn_html = ""
        if earn and not earn.get("error"):
            quarters_html = ""
            for q in earn.get("quarters", [])[:4]:
                icon  = "✅" if q["beat"] else "❌"
                sup   = f"{q['surprise']:+.1f}%"
                quarters_html += f"<span style='margin-right:8px;font-size:12px'>{icon} {q['period'][:7]} {sup}</span>"
            earn_html = f"""
            <div style="margin-top:6px">
              <span style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                           color:#4a5065">Earnings</span>
              <span style="font-size:13px;font-weight:600;color:{earn['color']};margin-left:6px">
                {earn['trend']}
              </span>
              <div style="margin-top:4px">{quarters_html}</div>
            </div>"""

        reco_html = ""
        if reco and not reco.get("error"):
            reco_html = f"""
            <div style="margin-top:6px">
              <span style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                           color:#4a5065">Analistas</span>
              <span style="font-size:13px;font-weight:600;color:{reco['color']};margin-left:6px">
                {reco['consensus']}
              </span>
              <span style="font-size:12px;color:#4a5065;margin-left:8px">
                💪 {reco['strong_buy']+reco['buy']} compra &nbsp;
                ⚖️ {reco['hold']} neutro &nbsp;
                👎 {reco['sell']+reco['strong_sell']} venda
              </span>
            </div>"""

        enr_block = news_html + insider_html + earn_html + reco_html
        if enr_block.strip():
            st.markdown(f"""
            <div style="background:rgba(99,102,241,.1);border:1px solid rgba(255,255,255,.07);
                        border-radius:6px;padding:12px 16px;margin-top:4px;margin-bottom:8px">
              <div style="font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
                          color:#5c6278;margin-bottom:8px">
                Finnhub Intelligence
              </div>
              {enr_block}
            </div>
            """, unsafe_allow_html=True)

    # ── Sinais Alternativos (OpenInsider + WSB) ───────────────────────────────
    alt = cached_alternative(symbol)
    if alt:
        ins = alt.get("insider", {})
        wsb = alt.get("wsb", {})

        ins_html = ""
        if ins and not ins.get("error"):
            buy_rows = "".join(
                f"<div style='font-size:11px;color:#c8ccdc;padding:3px 0;border-bottom:1px solid rgba(255,255,255,.06)'>"
                f"<b>{t['insider']}</b> ({t['title']}) &nbsp;·&nbsp; {t['qty']} ações @ {t['price']} &nbsp;·&nbsp; {t['trade_date']}"
                f"</div>"
                for t in (ins.get("exec_buys") or ins.get("purchases", []))[:3]
            )
            ins_html = f"""
            <div style="flex:1;min-width:220px">
              <div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                          color:#4a5065;margin-bottom:5px">OpenInsider</div>
              <div style="font-size:13px;font-weight:600;color:{ins['color']}">{ins['emoji']} {ins['signal']}</div>
              <div style="font-size:11px;color:#5c6278;margin-top:2px">{ins['buy_count']} compras · {ins['sell_count']} vendas (180 dias)</div>
              {"<div style='margin-top:6px'>" + buy_rows + "</div>" if buy_rows else ""}
            </div>"""

        wsb_html = ""
        if wsb and not wsb.get("error"):
            top = "".join(
                f"<div style='font-size:11px;color:#c8ccdc;padding:2px 0'>"
                f"&#x2192; {p['title'][:70]} (score: {p['score']:,})</div>"
                for p in wsb.get("top_posts", [])[:2]
            )
            wsb_html = f"""
            <div style="flex:1;min-width:220px">
              <div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                          color:#4a5065;margin-bottom:5px">Reddit WSB</div>
              <div style="font-size:13px;font-weight:600;color:{wsb['color']}">{wsb['emoji']} {wsb['signal']}</div>
              <div style="font-size:11px;color:#5c6278;margin-top:2px">
                {wsb['count']} posts · score total {wsb['total_score']:,} · ratio {wsb['avg_ratio']:.0%}
              </div>
              {"<div style='margin-top:5px'>" + top + "</div>" if top else ""}
            </div>"""

        if ins_html or wsb_html:
            st.markdown(f"""
            <div style="background:#0d0d12;border:1px solid rgba(255,255,255,.08);
                        border-radius:6px;padding:14px 18px;margin-top:4px;margin-bottom:8px">
              <div style="font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
                          color:#5c6278;margin-bottom:12px">Sinais Alternativos</div>
              <div style="display:flex;gap:28px;flex-wrap:wrap">
                {ins_html}
                {wsb_html}
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── EBITDA Panel ──────────────────────────────────────────────────────────
    eb = cached_ebitda(symbol)
    if eb and not eb.get("error"):
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.markdown(f"""
            <div style="background:#0d0d12;border:1px solid rgba(255,255,255,.07);border-radius:6px;padding:14px 16px">
              <div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                          color:#4a5065;margin-bottom:6px">EBITDA TTM</div>
              <div style="font-size:22px;font-weight:700;color:#f0f2f8">{eb['ebitda_fmt']}</div>
              <div style="font-size:11px;color:#4a5065;margin-top:4px">
                Lucro operacional antes de juros, impostos e depreciação
              </div>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
            <div style="background:#0d0d12;border:1px solid rgba(255,255,255,.07);border-radius:6px;padding:14px 16px">
              <div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                          color:#4a5065;margin-bottom:6px">Margem EBITDA</div>
              <div style="font-size:22px;font-weight:700;color:{eb['margin_color']}">{eb['margin_pct']}</div>
              <div style="font-size:11px;font-weight:600;color:{eb['margin_color']};margin-top:4px">
                {eb['margin_label']}
              </div>
            </div>
            """, unsafe_allow_html=True)
        with col_c:
            st.markdown(f"""
            <div style="background:#0d0d12;border:1px solid rgba(255,255,255,.07);border-radius:6px;padding:14px 16px">
              <div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                          color:#4a5065;margin-bottom:6px">EV / EBITDA</div>
              <div style="font-size:22px;font-weight:700;color:{eb['ev_color']}">{eb['ev_fmt']}</div>
              <div style="font-size:11px;font-weight:600;color:{eb['ev_color']};margin-top:4px">
                {eb['ev_label']}
              </div>
            </div>
            """, unsafe_allow_html=True)
        with col_d:
            st.markdown(f"""
            <div style="background:#0d0d12;border:1px solid rgba(255,255,255,.07);border-radius:6px;padding:14px 16px">
              <div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                          color:#4a5065;margin-bottom:6px">Crescimento YoY</div>
              <div style="font-size:22px;font-weight:700;color:{eb['growth_color']}">{eb['growth_fmt']}</div>
              <div style="font-size:11px;font-weight:600;color:{eb['growth_color']};margin-top:4px">
                {eb['growth_label']}
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Polygon Intelligence Panel ────────────────────────────────────────────
    poly = cached_polygon(symbol)
    if poly:
        inc  = poly.get("income", {})
        bal  = poly.get("balance", {})
        divs = poly.get("dividends", [])
        news = poly.get("news", [])
        det  = poly.get("details", {})
        dyld = poly.get("div_yield")

        def _fmt_b(v):
            if v is None: return "—"
            if abs(v) >= 1e12: return f"${v/1e12:.2f}T"
            if abs(v) >= 1e9:  return f"${v/1e9:.1f}B"
            if abs(v) >= 1e6:  return f"${v/1e6:.0f}M"
            return f"${v:,.0f}"

        rev_g_color = "#4ade80" if (inc.get("rev_growth") or 0) > 0 else "#f87171"
        rev_g_txt   = f"{inc.get('rev_growth',0):+.1f}%" if inc.get("rev_growth") is not None else "—"

        # Income metrics row
        inc_html = f"""
        <div style="display:flex;gap:24px;flex-wrap:wrap;padding:12px 0;
                    border-bottom:1px solid rgba(255,255,255,.06)">
          <div>
            <div style="font-size:11px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:#4a5065;margin-bottom:3px">Receita</div>
            <div style="font-size:16px;font-weight:700;color:#e8eaf0">{_fmt_b(inc.get("revenues"))}</div>
            <div style="font-size:11px;font-weight:600;color:{rev_g_color}">YoY {rev_g_txt}</div>
          </div>
          <div>
            <div style="font-size:11px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:#4a5065;margin-bottom:3px">Lucro Líquido</div>
            <div style="font-size:16px;font-weight:700;color:#e8eaf0">{_fmt_b(inc.get("net_income"))}</div>
            <div style="font-size:11px;color:#5c6278">Margem {inc.get('net_margin','—')}%</div>
          </div>
          <div>
            <div style="font-size:11px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:#4a5065;margin-bottom:3px">Lucro Op.</div>
            <div style="font-size:16px;font-weight:700;color:#e8eaf0">{_fmt_b(inc.get("op_income"))}</div>
            <div style="font-size:11px;color:#5c6278">Margem {inc.get('op_margin','—')}%</div>
          </div>
          <div>
            <div style="font-size:11px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:#4a5065;margin-bottom:3px">EPS</div>
            <div style="font-size:16px;font-weight:700;color:#e8eaf0">${inc.get("eps","—")}</div>
            <div style="font-size:11px;color:#5c6278">{inc.get("period","")} {inc.get("end_date","")[:7]}</div>
          </div>
          {f'<div><div style="font-size:11px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:#4a5065;margin-bottom:3px">D/E Ratio</div><div style="font-size:16px;font-weight:700;color:#e8eaf0">{bal.get("debt_to_equity","—")}</div><div style="font-size:11px;color:#5c6278">Alavancagem</div></div>' if bal.get("debt_to_equity") else ""}
          {f'<div><div style="font-size:11px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:#4a5065;margin-bottom:3px">Div. Yield</div><div style="font-size:16px;font-weight:700;color:#4ade80">{dyld}%</div><div style="font-size:11px;color:#5c6278">{divs[0]["ex_date"] if divs else ""}</div></div>' if dyld else ""}
        </div>"""

        # News row
        news_html = ""
        if news:
            news_items = "".join(
                f'<div style="padding:5px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:12px">'
                f'<span style="color:#e8eaf0;font-weight:500">{n["title"][:75]}</span>'
                f'<span style="color:#4a5065;margin-left:8px">{n["source"]} · {n["published"]}</span>'
                f'</div>'
                for n in news[:3]
            )
            news_html = f"""
            <div style="margin-top:10px">
              <div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                          color:#4a5065;margin-bottom:6px">Notícias recentes</div>
              {news_items}
            </div>"""

        st.markdown(f"""
        <div style="background:rgba(99,102,241,.04);border:1px solid rgba(99,102,241,.15);
                    border-radius:8px;padding:14px 18px;margin-top:4px;margin-bottom:8px">
          <div style="font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
                      color:#818cf8;margin-bottom:10px">&#9670; Polygon — Dados Oficiais</div>
          {inc_html}
          {news_html}
        </div>
        """, unsafe_allow_html=True)

    # ── Price chart — use Polygon history if available ─────────────────────
    poly_hist = cached_polygon_history(symbol)
    chart_hist = poly_hist if not poly_hist.empty else hist

    if chart_hist is not None and not chart_hist.empty:
        close_col = "Close" if "Close" in chart_hist.columns else chart_hist.columns[0]
        color     = "#4ade80" if gain_u >= 0 else "#f87171"
        fill_rgba = "rgba(74,222,128,.07)" if gain_u >= 0 else "rgba(248,113,113,.07)"
        fig = go.Figure(go.Scatter(
            x=chart_hist.index, y=chart_hist[close_col],
            fill="tozeroy",
            line=dict(color=color, width=1.5),
            fillcolor=fill_rgba,
        ))
        fig.update_layout(
            height=100, margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor="#09090b",
            paper_bgcolor="#09090b",
            yaxis=dict(showgrid=False, showticklabels=False),
            xaxis=dict(showgrid=False, showticklabels=False),
        )
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{symbol}")


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_carteira, tab_screener, tab_brasil, tab_macro, tab_inv, tab_sinais = st.tabs([
    "Carteira", "Screener", "Brasil", "Macro", "Investidores", "Sinais"
])

# ── Tab: Carteira ──────────────────────────────────────────────────────────────
with tab_carteira:
    st.markdown('<div class="page-title">Visão Geral</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Posição consolidada · 28 abr 2026</div>', unsafe_allow_html=True)

    lt_syms = portfolio_df[portfolio_df["horizon"] == "long"]["symbol"].tolist()
    sw_syms = portfolio_df[portfolio_df["horizon"] == "swing"]["symbol"].tolist()

    st.markdown(f"""
    <div class="overview-summary">
      <div class="ov-row">
        <div class="ov-item">
          <div class="ov-label">Portfólio EUA</div>
          <div class="ov-val">$742,152</div>
          <div class="ov-sub" style="color:#f87171">−$4,823 hoje</div>
        </div>
        <div class="ov-item">
          <div class="ov-label">Portfólio Brasil</div>
          <div class="ov-val">R$ 2.579.940</div>
          <div class="ov-sub">Itaú Personnalité</div>
        </div>
        <div class="ov-item">
          <div class="ov-label">Cash Schwab</div>
          <div class="ov-val">$260.178</div>
          <div class="ov-sub">35% do portfólio — posicionamento estratégico</div>
        </div>
        <div class="ov-item">
          <div class="ov-label">Ganho acumulado EUA</div>
          <div class="ov-val" style="color:#4ade80">+$105.945</div>
          <div class="ov-sub">+28.2% sobre custo</div>
        </div>
      </div>
    </div>

    <div class="warn-box">
      Shiller P/E 38 &nbsp;·&nbsp; Buffett Indicator 198% &nbsp;·&nbsp; Mercado historicamente caro.
      Seu cash de 35% é posicionamento — não ociosidade.
    </div>

    <div class="section-label">Long Term ({len(lt_syms)} posições)</div>
    <div style="font-size:13px;color:#c8ccdc;line-height:1.8">
      {"&nbsp; &nbsp;".join([f"<code style='background:rgba(99,102,241,.08);padding:2px 7px;border-radius:4px;font-family:monospace;font-size:12px'>{s}</code>" for s in lt_syms])}
    </div>

    <div class="section-label">Swing ({len(sw_syms)} posições)</div>
    <div style="font-size:13px;color:#c8ccdc;line-height:1.8">
      {"&nbsp; &nbsp;".join([f"<code style='background:rgba(245,158,11,.1);padding:2px 7px;border-radius:4px;font-family:monospace;font-size:12px'>{s}</code>" for s in sw_syms])}
    </div>
    """, unsafe_allow_html=True)


    st.markdown('<div class="section-label">Long Term</div>', unsafe_allow_html=True)
    for _, row in portfolio_df[portfolio_df["horizon"] == "long"].iterrows():
        asset_card(row["symbol"], row["qty"], row["cost_basis"], "long")

    st.markdown('<div class="section-label">Swing — Carteira</div>', unsafe_allow_html=True)
    for _, row in portfolio_df[portfolio_df["horizon"] == "swing"].iterrows():
        asset_card(row["symbol"], row["qty"], row["cost_basis"], "swing")


with tab_screener:
    st.markdown('<div class="page-title">Swing Radar</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Oportunidades externas identificadas por setup técnico</div>', unsafe_allow_html=True)

    portfolio_syms = portfolio_df["symbol"].tolist()

    if st.button("Rodar screener — 20 melhores oportunidades"):
        with st.spinner("Analisando fundamentos e técnicos em ~200 ativos..."):
            results = screen_swing_candidates(max_results=20, portfolio_symbols=portfolio_syms)

        if not results:
            st.info("Nenhum setup forte identificado no momento.")
        else:
            st.caption(f"{len(results)} oportunidades encontradas · Score combina upside, fundamentos e técnico")

        for i, c in enumerate(results, 1):
            upside     = c.get("upside", 0)
            up_color   = "#3a7d52" if upside > 0 else "#b84040"
            up_arrow   = "▲" if upside > 0 else "▼"

            margin_html = f"<span style='color:#4ade80;font-weight:600'>{c['margin']:.0f}%</span>" if c.get("margin") else "—"
            ev_html     = f"{c['ev_ebitda']:.1f}x" if c.get("ev_ebitda") else "—"
            rev_html    = (f"<span style='color:#4ade80;font-weight:600'>+{c['rev_growth']:.0f}%</span>"
                          if c.get("rev_growth") and c["rev_growth"] > 0
                          else f"<span style='color:#f87171'>{c['rev_growth']:.0f}%</span>"
                          if c.get("rev_growth") else "—")
            pe_html     = f"{c['pe_forward']:.1f}x" if c.get("pe_forward") else "—"

            reasons_html = "".join(
                f"<span style='background:rgba(99,102,241,.08);border:1px solid rgba(99,102,241,.25);"
                f"border-radius:4px;padding:2px 8px;font-size:11px;margin-right:6px;margin-bottom:4px;"
                f"display:inline-block'>{r}</span>"
                for r in c["reasons"][:5]
            )

            w52_low  = c.get("week52_low", 0)
            w52_high = c.get("week52_high", 1)
            bar_pct  = max(0, min(100, (c["price"] - w52_low) / max(w52_high - w52_low, 1) * 100))

            st.markdown(f"""
            <div class="asset-row" style="padding:18px 22px;margin-bottom:10px">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
                <div style="display:flex;align-items:center;gap:12px">
                  <div style="font-size:13px;font-weight:700;color:#4a5065;
                              min-width:20px">#{i}</div>
                  <div>
                    <div style="display:flex;align-items:center;gap:8px">
                      <span style="font-size:11px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
                                   color:#f59e0b">{c['score_label']}</span>
                      <span style="font-size:11px;color:#4a5065">Score: {c['score']}</span>
                    </div>
                    <div style="font-size:18px;font-weight:700;color:#f0f2f8">{c['symbol']}</div>
                    <div style="font-size:12px;color:#5c6278">{c['name']}</div>
                  </div>
                </div>
                <div style="text-align:right">
                  <div style="font-size:22px;font-weight:700">${c['price']:.2f}</div>
                  <div style="font-size:14px;font-weight:700;color:{up_color}">
                    {up_arrow} {abs(upside):.1f}% upside
                  </div>
                  <div style="font-size:12px;color:#5c6278">
                    Target: ${c['target']:.2f} · {c['rec']} ({c['n_analysts']} casas)
                  </div>
                </div>
              </div>

              <div style="display:flex;gap:24px;flex-wrap:wrap;padding:10px 0;
                          border-top:1px solid #e7eaf2;
                          border-bottom:1px solid rgba(255,255,255,.06);margin-bottom:12px">
                <div>
                  <div class="stat-label">Margem EBITDA</div>
                  <div style="font-size:15px">{margin_html}</div>
                </div>
                <div>
                  <div class="stat-label">EV/EBITDA</div>
                  <div style="font-size:15px;font-weight:600">{ev_html}</div>
                </div>
                <div>
                  <div class="stat-label">Receita YoY</div>
                  <div style="font-size:15px">{rev_html}</div>
                </div>
                <div>
                  <div class="stat-label">P/E Forward</div>
                  <div style="font-size:15px;font-weight:600">{pe_html}</div>
                </div>
                <div style="flex:1;min-width:160px">
                  <div class="stat-label">52 semanas</div>
                  <div class="range-track" style="margin-top:6px">
                    <div class="range-fill" style="width:{bar_pct:.0f}%"></div>
                  </div>
                  <div style="font-size:11px;color:#4a5065;margin-top:3px">
                    ${w52_low:.2f} — ${w52_high:.2f}
                  </div>
                </div>
              </div>

              <div style="margin-bottom:10px">
                <div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                            color:#4a5065;margin-bottom:6px">Por que entrou no radar</div>
                <div style="line-height:2">{reasons_html}</div>
              </div>

              <div style="display:flex;gap:20px;flex-wrap:wrap">
                <div class="sig-item">
                  <div class="sig-label">{c['rsi']['emoji']} {c['rsi']['label']}</div>
                  <div class="sig-action">{c['rsi']['action']}</div>
                </div>
                <div class="sig-item">
                  <div class="sig-label">{c['macd']['emoji']} {c['macd']['label']}</div>
                  <div class="sig-action">{c['macd']['action']}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="info-box">Clique em "Rodar screener" para analisar ~200 ativos por upside, '
            'fundamentos (EBITDA, EV/EBITDA, crescimento de receita) e sinais técnicos.</div>',
            unsafe_allow_html=True,
        )


with tab_brasil:
    st.markdown('<div class="page-title">Brasil</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Itaú Personnalité · posição consolidada</div>', unsafe_allow_html=True)

    from core.brasil import get_brasil_summary as _get_br
    _br = _get_br()
    crypto_total = _br["crypto_total"]
    crypto_pct   = _br["crypto_pct"]
    bar_ok       = _br["on_target"]
    bar_cls      = "crypto-bar-ok" if bar_ok else "crypto-bar-warn"
    status_txt   = "Na faixa alvo" if bar_ok else "Fora da faixa — rebalancear via HASH11"
    status_col   = "#3a7d52" if bar_ok else "#b84040"

    st.markdown('<div class="section-label">Monitor Cripto</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="overview-summary">
      <div class="ov-row" style="margin-bottom:16px">
        <div class="ov-item">
          <div class="ov-label">Exposição atual</div>
          <div class="ov-val">{crypto_pct:.1f}%</div>
          <div class="ov-sub" style="color:{status_col};font-weight:600">{status_txt}</div>
        </div>
        <div class="ov-item">
          <div class="ov-label">Valor total</div>
          <div class="ov-val">R$ {crypto_total:,.0f}</div>
          <div class="ov-sub">5 produtos · HASH11 é 72%</div>
        </div>
        <div class="ov-item">
          <div class="ov-label">Meta</div>
          <div class="ov-val">10%</div>
          <div class="ov-sub">Faixa: 8 – 12%</div>
        </div>
      </div>
      <div class="range-label">0% &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 8% (min) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 10% (meta) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 12% (max) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 20%</div>
      <div class="range-track" style="height:10px">
        <div class="{bar_cls}" style="width:{min(crypto_pct/20*100,100):.1f}%;height:10px;border-radius:3px"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">FIIs</div>', unsafe_allow_html=True)
    fiis = br_df[br_df["tipo"] == "fii"]
    for _, row in fiis.iterrows():
        d = cached_br_asset(row["ticker"])
        if d is None:
            st.warning(f"{row['ticker']} — erro ao buscar dados.")
            continue
        rsi_val = calc_rsi(d["hist"])
        rsi     = interpret_rsi(rsi_val)
        price   = d["price"] or 0
        st.markdown(f"""
        <div class="asset-row" style="padding:14px 20px">
          <div class="ar-header" style="margin-bottom:8px">
            <div class="ar-left">
              <span class="ar-symbol" style="font-size:15px">{row['ticker']}</span>
              <span class="ar-name">{row['nome']}</span>
            </div>
            <div class="ar-right">
              <span class="ar-price" style="font-size:16px">R$ {price:.2f}</span>
            </div>
          </div>
          <div style="font-size:12px;color:#5c6278">
            Investido: R$ {row['valor_investido']:,.0f} &nbsp;·&nbsp;
            {rsi['emoji']} {rsi['label']}
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">HASH11 — Crypto Index</div>', unsafe_allow_html=True)
    asset_card("HASH11.SA", 0, 174_545.0, "long")


with tab_macro:
    st.markdown('<div class="page-title">Macro</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Indicadores estruturais do mercado · contexto e sentimento</div>', unsafe_allow_html=True)

    with st.spinner("Buscando dados macro"):
        macro = cached_macro()

    shiller  = describe_shiller_pe(MACRO_SHILLER_PE)
    buffett  = describe_buffett_indicator(MACRO_BUFFETT_IND)
    vix_d    = describe_vix_full(macro["vix"])
    curve_d  = describe_yield_curve_full(macro["yield_spread"], macro["yield_10y"], macro["yield_3m"])

    def macro_card(d: dict, value_fmt: str = "{:.1f}"):
        val_str = value_fmt.format(d["value"]) if d.get("value") is not None else "—"
        return f"""
        <div class="asset-row" style="padding:20px 24px;margin-bottom:14px">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
            <div>
              <div style="font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
                          color:#4a5065;margin-bottom:4px">{d['name']}</div>
              <div style="font-size:28px;font-weight:700;color:{d.get('color','#1e2235')}">{val_str}</div>
            </div>
            <div style="font-size:28px">{d['emoji']}</div>
          </div>
          <div style="font-size:13px;font-weight:600;color:{d.get('color','#1e2235')};margin-bottom:8px">
            {d['sentiment']}
          </div>
          <div style="font-size:12px;color:#a5b4fc;line-height:1.6;margin-bottom:10px">
            <b>O que é:</b> {d['what']}
          </div>
          <div style="font-size:12px;color:#c8ccdc;line-height:1.6;margin-bottom:8px">
            <b>Leitura atual:</b> {d.get('reading', d.get('description',''))}
          </div>
          {"<div style='font-size:12px;color:#818cf8;background:rgba(99,102,241,.08);padding:8px 12px;border-radius:5px;line-height:1.5'><b>Sua carteira:</b> " + d['implication'] + "</div>" if d.get('implication') else ""}
        </div>
        """

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(macro_card(shiller, "{:.0f}"), unsafe_allow_html=True)
        st.markdown(macro_card(vix_d,   "{:.1f}"), unsafe_allow_html=True)
    with col2:
        st.markdown(macro_card(buffett, "{:.0f}%"), unsafe_allow_html=True)
        st.markdown(macro_card(curve_d, "{:+.2f}%"), unsafe_allow_html=True)

    st.markdown(f"""
    <div class="section-label">S&P 500 &amp; Yields</div>
    <div class="overview-summary" style="padding:16px 22px">
      <div class="ov-row">
        <div class="ov-item">
          <div class="ov-label">S&P 500</div>
          <div class="ov-val">{macro['sp500']:,.0f}</div>
        </div>
        <div class="ov-item">
          <div class="ov-label">Yield 10 anos</div>
          <div class="ov-val">{macro['yield_10y']:.2f}%</div>
        </div>
        <div class="ov-item">
          <div class="ov-label">Yield 3 meses</div>
          <div class="ov-val">{macro['yield_3m']:.2f}%</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Sector performance (Alpha Vantage)
    st.markdown('<div class="section-label">Performance por Setor — Alpha Vantage</div>',
                unsafe_allow_html=True)
    with st.spinner("Buscando setores..."):
        sectors_data = cached_sectors()

    if sectors_data.get("error") and not sectors_data.get("sectors"):
        st.warning(f"Setores: {sectors_data['error']}")
    else:
        sectors = sectors_data.get("sectors", {})
        if sectors:
            rows_html = ""
            for name, perf in list(sectors.items())[:11]:
                today_s = perf.get("today", "0%").replace("%", "")
                ytd_s   = perf.get("ytd",   "0%").replace("%", "")
                month_s = perf.get("month", "0%").replace("%", "")
                try:
                    today_f = float(today_s)
                    ytd_f   = float(ytd_s)
                    t_color = "#3a7d52" if today_f >= 0 else "#b84040"
                    y_color = "#3a7d52" if ytd_f   >= 0 else "#b84040"
                except ValueError:
                    t_color = y_color = "#64748b"
                short = name.replace("Information Technology", "Tech").replace(
                    "Consumer Discretionary","Cons. Discr.").replace(
                    "Consumer Staples","Cons. Staples").replace(
                    "Communication Services","Comm. Services").replace(
                    "Real Estate","Real Estate")
                rows_html += f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:6px 0;border-bottom:1px solid rgba(255,255,255,.06);font-size:13px">
                  <div style="flex:1;color:#c8ccdc">{short}</div>
                  <div style="width:80px;text-align:right;font-weight:600;color:{t_color}">
                    {perf.get('today','—')}
                  </div>
                  <div style="width:80px;text-align:right;font-weight:600;color:{y_color}">
                    {perf.get('ytd','—')}
                  </div>
                  <div style="width:80px;text-align:right;color:#5c6278">
                    {perf.get('month','—')}
                  </div>
                </div>"""
            st.markdown(f"""
            <div class="asset-row" style="padding:16px 22px">
              <div style="display:flex;justify-content:space-between;
                          font-size:11px;font-weight:700;letter-spacing:.06em;
                          text-transform:uppercase;color:#4a5065;
                          padding-bottom:8px;border-bottom:1px solid #dbe1ec">
                <div style="flex:1">Setor</div>
                <div style="width:80px;text-align:right">Hoje</div>
                <div style="width:80px;text-align:right">YTD</div>
                <div style="width:80px;text-align:right">1 Mês</div>
              </div>
              {rows_html}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Dados de setores indisponíveis.")

    # Economic calendar (Finnhub)
    st.markdown('<div class="section-label">Calendário Econômico — Próximos 14 dias</div>',
                unsafe_allow_html=True)
    with st.spinner("Buscando eventos..."):
        events      = cached_eco_calendar()
        port_syms   = portfolio_df["symbol"].tolist()
        earnings_ev = get_upcoming_earnings(port_syms)

    col_ev1, col_ev2 = st.columns(2)
    with col_ev1:
        st.markdown("**Eventos macro relevantes**")
        if events:
            for ev in events[:8]:
                impact = ev.get("impact","").lower()
                color  = "#b84040" if impact == "high" else "#b45309"
                st.markdown(f"""
                <div style="display:flex;gap:10px;padding:7px 0;
                            border-bottom:1px solid rgba(255,255,255,.06);font-size:13px">
                  <div style="color:{color};font-weight:700;min-width:16px">
                    {"⚠️" if impact=="high" else "·"}
                  </div>
                  <div>
                    <div style="font-weight:600">{ev.get('event','')}</div>
                    <div style="font-size:11px;color:#5c6278">
                      {ev.get('time','')[:10]} &nbsp;·&nbsp; {ev.get('country','')}
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Sem eventos de alto impacto nos próximos 14 dias.")

    with col_ev2:
        st.markdown("**Earnings da sua carteira**")
        if earnings_ev:
            for ev in earnings_ev[:8]:
                st.markdown(f"""
                <div style="display:flex;gap:10px;padding:7px 0;
                            border-bottom:1px solid rgba(255,255,255,.06);font-size:13px">
                  <div style="font-weight:700;color:#4a6fd4;min-width:50px">
                    {ev.get('symbol','')}
                  </div>
                  <div>
                    <div style="font-size:11px;color:#5c6278">
                      {ev.get('date','')} &nbsp;·&nbsp;
                      Est. EPS: ${ev.get('epsEstimate') or '—'}
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Nenhum earnings da carteira nos próximos 60 dias.")


with tab_inv:
    st.markdown('<div class="page-title">Investidores</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Posições dos grandes fundos · 13F SEC (trimestral) + ARK (diário)</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box" style="margin-bottom:20px">
      <b>Como funciona:</b> Fundos com mais de $100M em ativos são obrigados a reportar suas posições
      trimestralmente à SEC via formulário 13F, com até 45 dias de atraso. ARK é a exceção —
      publica as posições diariamente. Os dados mostram adições, reduções e novas posições
      em relação ao trimestre anterior.
    </div>
    """, unsafe_allow_html=True)

    user_symbols = portfolio_df["symbol"].tolist()

    @st.cache_data(ttl=21600, show_spinner=False)
    def cached_investor(name):
        return get_investor_holdings(name)

    @st.cache_data(ttl=3600, show_spinner=False)
    def cached_ark():
        return get_ark_holdings("ARKK")

    def render_investor(data: dict):
        if data.get("error") and data["error"] not in (None, ""):
            st.markdown(f"""
            <div class="asset-row" style="padding:16px 22px;margin-bottom:10px">
              <div style="font-size:16px;font-weight:700">{data.get('emoji','')} {data.get('manager','')}</div>
              <div style="font-size:12px;color:#f87171;margin-top:6px">⚠️ {data['error']}</div>
            </div>
            """, unsafe_allow_html=True)
            return

        holdings = data.get("holdings", pd.DataFrame())
        overlaps  = find_overlaps(holdings, user_symbols)
        total_val = data.get("total_value", 0)
        as_of     = data.get("as_of", "")

        changes = {}
        if not holdings.empty and "change" in holdings.columns:
            changes = holdings["change"].value_counts().to_dict()

        new_pos = holdings[holdings["change"] == "new"]["name"].tolist()[:5] if not holdings.empty and "change" in holdings.columns else []
        reduced = holdings[holdings["change"] == "reduced"]["name"].tolist()[:5] if not holdings.empty and "change" in holdings.columns else []
        incr    = holdings[holdings["change"] == "increased"]["name"].tolist()[:5] if not holdings.empty and "change" in holdings.columns else []

        overlap_html = ""
        if overlaps:
            overlap_html = f"""
            <div style="background:rgba(99,102,241,.08);border:1px solid rgba(99,102,241,.25);
                        border-radius:5px;padding:8px 12px;margin-top:10px;font-size:12px">
              🔗 <b>Na sua carteira também:</b> {", ".join(overlaps)}
            </div>
            """

        top_html = ""
        if not holdings.empty:
            top10 = holdings.head(10)
            rows_html = ""
            for _, r in top10.iterrows():
                chg = r.get("change", "held") if "change" in r.index else "held"
                c_emoji, c_label, c_color = CHANGE_LABELS.get(chg, ("→", "Manteve", "#6B7280"))
                pct    = r.get("pct", 0)
                ticker = r.get("ticker", "")
                name   = r.get("name", ticker)
                rows_html += f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:7px 0;border-bottom:1px solid #F3F4F6;font-size:13px">
                  <div style="width:52px;font-weight:700;color:#4F46E5;font-size:12px">{ticker}</div>
                  <div style="flex:1;color:#374151;padding:0 10px">{name}</div>
                  <div style="width:48px;text-align:right;color:#6B7280;font-size:12px">{pct:.1f}%</div>
                  <div style="width:80px;text-align:right;color:{c_color};font-weight:600;font-size:12px">
                    {c_emoji} {c_label}
                  </div>
                </div>
                """
            top_html = f"""
            <div class="section-label" style="margin-top:14px">Top 10 Holdings</div>
            {rows_html}
            """

        chg_summary = ""
        if new_pos or reduced or incr:
            chg_summary = f"""
            <div style="display:flex;gap:20px;flex-wrap:wrap;margin-top:12px;font-size:12px">
              {"<div><span style='color:#4ade80;font-weight:700'>🆕 Novas:</span> " + ", ".join(new_pos) + "</div>" if new_pos else ""}
              {"<div><span style='color:#4ade80;font-weight:700'>⬆️ Aumentou:</span> " + ", ".join(incr) + "</div>" if incr else ""}
              {"<div><span style='color:#f87171;font-weight:700'>⬇️ Reduziu:</span> " + ", ".join(reduced) + "</div>" if reduced else ""}
            </div>
            """

        st.markdown(f"""
        <div class="asset-row" style="padding:20px 24px;margin-bottom:12px">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
            <div>
              <div style="font-size:18px;font-weight:700">
                {data.get('emoji','')} {data.get('manager','')}
              </div>
              <div style="font-size:12px;color:#5c6278;margin-top:2px">
                {data.get('name', '')} · {data.get('style','')}
              </div>
            </div>
            <div style="text-align:right">
              <div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                          color:#4a5065">Posição em</div>
              <div style="font-size:14px;font-weight:600">{as_of}</div>
              {"<div style='font-size:12px;color:#5c6278'>$" + f"{total_val/1e9:.1f}B portfólio" + "</div>" if total_val > 0 else ""}
            </div>
          </div>
          <div style="font-size:12px;color:#5c6278;line-height:1.5;margin-bottom:10px;
                      padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,.06)">
            {data.get('known_for','')}
          </div>
          {chg_summary}
          {overlap_html}
          {top_html}
        </div>
        """, unsafe_allow_html=True)

    # ── Grandes fundos (13F) ──────────────────────────────────────────────────
    st.markdown('<div class="section-label">Grandes Fundos — 13F SEC</div>', unsafe_allow_html=True)

    inv_names = list(INVESTORS.keys())
    tabs = st.tabs([f"{INVESTORS[n]['emoji']} {INVESTORS[n]['manager']}" for n in inv_names])

    for tab, name in zip(tabs, inv_names):
        with tab:
            with st.spinner(f"Buscando dados de {INVESTORS[name]['manager']}..."):
                data = cached_investor(name)
            data["name"] = name
            render_investor(data)

    # ── ARK ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">ARK Innovation — Atualização Diária</div>', unsafe_allow_html=True)

    with st.spinner("Buscando holdings ARK..."):
        ark = cached_ark()

    if ark.get("error"):
        st.warning(f"ARK: {ark['error']}")
    else:
        ark_holdings = ark.get("holdings", pd.DataFrame())
        ark_overlaps = []
        if not ark_holdings.empty and "ticker" in ark_holdings.columns:
            ark_overlaps = [s for s in user_symbols if s in ark_holdings["ticker"].values]

        overlap_html = ""
        if ark_overlaps:
            overlap_html = f"""
            <div style="background:rgba(99,102,241,.08);border:1px solid rgba(99,102,241,.25);
                        border-radius:5px;padding:8px 12px;margin-top:10px;font-size:12px">
              🔗 <b>Na sua carteira também:</b> {", ".join(ark_overlaps)}
            </div>
            """

        top_html = ""
        if not ark_holdings.empty and "ticker" in ark_holdings.columns:
            cols_to_show = [c for c in ["ticker", "company", "weight", "market_value"] if c in ark_holdings.columns]
            top_ark = ark_holdings[cols_to_show].head(15)
            rows_html = ""
            for _, r in top_ark.iterrows():
                ticker  = r.get("ticker", "")
                company = r.get("company", "")
                weight  = f"{float(r['weight']):.2f}%" if "weight" in r.index else ""
                in_port = "🔗" if ticker in user_symbols else ""
                rows_html += f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:6px 0;border-bottom:1px solid rgba(255,255,255,.06);font-size:13px">
                  <div style="width:60px;font-weight:700;color:#c8ccdc">{ticker} {in_port}</div>
                  <div style="flex:1;color:#5c6278;padding:0 12px">{company}</div>
                  <div style="width:60px;text-align:right;color:#5c6278">{weight}</div>
                </div>
                """
            top_html = rows_html

        st.markdown(f"""
        <div class="asset-row" style="padding:20px 24px">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
            <div>
              <div style="font-size:18px;font-weight:700">&#x1F680; Cathie Wood &#8212; ARK Innovation (ARKK)</div>
              <div style="font-size:12px;color:#5c6278;margin-top:2px">Disruptive Innovation &middot; Publicação diária</div>
            </div>
            <div style="font-size:12px;font-weight:600;color:#4ade80">Atualizado: {ark.get('as_of','&#8212;')}</div>
          </div>
          <div style="font-size:12px;color:#5c6278;line-height:1.5;margin-bottom:12px;
                      padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,.06)">
            {ark.get('known_for','')}
          </div>
          {overlap_html}
          <div class="section-label" style="margin-top:12px">Top 15 Holdings</div>
          {top_html}
        </div>
        """, unsafe_allow_html=True)


with tab_sinais:
    st.markdown('<div class="page-title">Sinais Alternativos</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">OpenInsider (Form 4) · Reddit WallStreetBets · por ativo</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background:rgba(99,102,241,.08);border:1px solid rgba(99,102,241,.25);border-radius:6px;
                padding:14px 18px;margin-bottom:20px;font-size:13px;color:#818cf8">
      <b>OpenInsider:</b> Compras e vendas de executivos registradas na SEC via Form 4 (mesmo dia).
      Compras de CEO/CFO são o sinal mais confiável — eles compram as próprias ações com dinheiro
      próprio quando acreditam que estão baratas.<br><br>
      <b>Reddit WSB:</b> Volume e sentimento de menções no r/wallstreetbets. Alta euforia pode
      indicar topo de curto prazo; silêncio pode ser acumulação ou desinteresse.
    </div>
    """, unsafe_allow_html=True)

    all_syms = portfolio_df["symbol"].tolist()
    selected = st.multiselect(
        "Selecionar ativos para analisar",
        options=all_syms,
        default=all_syms[:6],
        help="Escolha os ativos que deseja ver os sinais alternativos"
    )

    if not selected:
        st.info("Selecione ao menos um ativo acima.")
    else:
        for symbol in selected:
            with st.spinner(f"Buscando sinais para {symbol}..."):
                alt = cached_alternative(symbol)

            ins = alt.get("insider", {})
            wsb = alt.get("wsb", {})

            horizon = portfolio_df[portfolio_df["symbol"] == symbol]["horizon"].values
            hor_txt = horizon[0].upper() if len(horizon) > 0 else ""
            tag_cls = "tag-swing" if hor_txt == "SWING" else "tag-lt"

            st.markdown(f"""
            <div class="asset-row" style="padding:18px 22px;margin-bottom:10px">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">
                <span class="{tag_cls}">{hor_txt}</span>
                <span style="font-size:18px;font-weight:700;color:#f0f2f8">{symbol}</span>
              </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**OpenInsider — Form 4**")
                if ins.get("error"):
                    st.warning(f"Erro: {ins['error']}")
                else:
                    color = ins.get("color", "#64748b")
                    signal = ins.get("signal", "")
                    emoji  = ins.get("emoji", "")
                    st.markdown(f"""
                    <div style="background:#0d0d12;border:1px solid rgba(255,255,255,.08);border-radius:6px;padding:14px 16px">
                      <div style="font-size:15px;font-weight:600;color:{color}">
                        {emoji} {signal}
                      </div>
                      <div style="font-size:12px;color:#5c6278;margin-top:4px">
                        {ins.get('buy_count',0)} compras · {ins.get('sell_count',0)} vendas (180 dias)
                        · {ins.get('exec_count',0)} C-suite
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    trades = ins.get("trades", [])
                    if trades:
                        rows_html = ""
                        for t in trades[:8]:
                            is_buy = "P -" in t.get("trade_type","") or "Purchase" in t.get("trade_type","")
                            tc = "#3a7d52" if is_buy else "#b84040"
                            tt = "Comprou" if is_buy else "Vendeu"
                            rows_html += f"""
                            <div style="display:flex;justify-content:space-between;padding:5px 0;
                                        border-bottom:1px solid rgba(255,255,255,.06);font-size:12px">
                              <div><b style="color:{tc}">{tt}</b> &nbsp; {t.get('insider','')} ({t.get('title','')})</div>
                              <div style="color:#5c6278">{t.get('qty','')} @ {t.get('price','')} · {t.get('trade_date','')}</div>
                            </div>"""
                        st.markdown(f"""
                        <div style="background:#111118;border:1px solid rgba(255,255,255,.08);border-radius:6px;
                                    padding:12px 16px;margin-top:8px">
                          {rows_html}
                        </div>""", unsafe_allow_html=True)

            with col2:
                st.markdown("**Reddit WallStreetBets**")
                if wsb.get("error"):
                    st.warning(f"Erro: {wsb['error']}")
                else:
                    color  = wsb.get("color", "#64748b")
                    signal = wsb.get("signal", "")
                    emoji  = wsb.get("emoji", "")
                    st.markdown(f"""
                    <div style="background:#0d0d12;border:1px solid rgba(255,255,255,.08);border-radius:6px;padding:14px 16px">
                      <div style="font-size:15px;font-weight:600;color:{color}">
                        {emoji} {signal}
                      </div>
                      <div style="font-size:12px;color:#5c6278;margin-top:4px">
                        {wsb.get('count',0)} posts · score {wsb.get('total_score',0):,}
                        · ratio {wsb.get('avg_ratio',0):.0%}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    for p in wsb.get("top_posts", [])[:3]:
                        st.markdown(f"""
                        <div style="background:#111118;border:1px solid rgba(255,255,255,.08);border-radius:5px;
                                    padding:10px 14px;margin-top:6px;font-size:12px">
                          <div style="color:#f0f2f8;font-weight:500">{p['title']}</div>
                          <div style="color:#5c6278;margin-top:3px">Score: {p['score']:,}</div>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
