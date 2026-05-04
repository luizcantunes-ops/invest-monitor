from __future__ import annotations
import os, sys, time, json, logging
sys.path.insert(0, os.path.dirname(__file__))

logger = logging.getLogger(__name__)

from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from core.fetcher     import get_asset_data, get_macro_data, get_br_asset_data
from core.enricher    import get_ticker_enrichment, get_sector_performance, get_economic_calendar, get_upcoming_earnings, get_ebitda_metrics, get_analyst_full
from core.alternative import get_alternative_signals
from core.polygon     import get_full_enrichment, get_history, get_market_status
from core.investors   import INVESTORS, get_investor_holdings, get_ark_holdings
from core.screener    import screen_swing_candidates
from core.swing       import get_swing_analysis, get_market_sentiment
from core.briefing    import get_briefing
from core.policy      import check_policy
from core.indicators  import (
    describe_shiller_pe,
    describe_buffett_indicator,
    describe_vix_full,
    describe_yield_curve_full,
)
from data.config      import (
    PORTFOLIO_TOTAL_BR, CRYPTO_BAND_LOW, CRYPTO_BAND_HIGH,
    MACRO_SHILLER_PE, MACRO_BUFFETT_IND, INTERNAL_API_TOKEN,
)
from core.brasil      import get_brasil_summary

import pandas as pd

app = FastAPI(title="Investment Monitor API", version="1.0.0")

_allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:3001").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)

# ── Internal token auth middleware ────────────────────────────────────────────

from fastapi import Request

@app.middleware("http")
async def _auth_middleware(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)
    if INTERNAL_API_TOKEN:
        token = request.headers.get("x-internal-token", "")
        if token != INTERNAL_API_TOKEN:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "ok"}

# ── Simple in-memory cache ────────────────────────────────────────────────────

_cache: dict[str, tuple[float, object]] = {}

def _cached(key: str, ttl: int, fn):
    now = time.time()
    if key in _cache and now - _cache[key][0] < ttl:
        return _cache[key][1]
    result = fn()
    _cache[key] = (now, result)
    return result


def _load_portfolio() -> list[dict]:
    csv = os.path.join(os.path.dirname(__file__), "data", "portfolio_us.csv")
    df  = pd.read_csv(csv)
    return df.to_dict(orient="records")


def _load_portfolio_br() -> list[dict]:
    csv = os.path.join(os.path.dirname(__file__), "data", "portfolio_br.csv")
    df  = pd.read_csv(csv)
    return df.to_dict(orient="records")


# ── Briefing ──────────────────────────────────────────────────────────────────

@app.get("/briefing")
def briefing():
    csv = os.path.join(os.path.dirname(__file__), "data", "portfolio_us.csv")
    return _cached("briefing", 600, lambda: get_briefing(csv))


# ── Policy ────────────────────────────────────────────────────────────────────

_POLICY_PATH = os.path.join(os.path.dirname(__file__), "data", "policy.json")
_THESIS_PATH  = os.path.join(os.path.dirname(__file__), "data", "thesis.json")


def _atomic_write_json(path: str, data: dict) -> None:
    """Write JSON atomically using a temp file + os.replace to avoid corruption."""
    tmp = f"{path}.tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def _load_json(path: str, label: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        logger.error("Corrupt JSON at %s: %s", path, e)
        raise HTTPException(status_code=500, detail=f"Config file corrupted: {label}")


def _load_policy() -> dict:
    return _load_json(_POLICY_PATH, "policy.json")

def _save_policy(data: dict) -> None:
    _atomic_write_json(_POLICY_PATH, data)


class PolicyUpdate(BaseModel):
    account_total_usd:   Optional[float] = None
    max_position_pct:    Optional[float] = None
    max_sector_pct:      Optional[float] = None
    min_cash_pct:        Optional[float] = None
    swing_max_loss_pct:  Optional[float] = None
    crypto_br_min_pct:   Optional[float] = None
    crypto_br_max_pct:   Optional[float] = None
    note:                Optional[str]   = None


@app.get("/policy")
def get_policy_endpoint():
    return _load_policy()


@app.put("/policy")
def update_policy(updates: PolicyUpdate):
    from datetime import date
    current = _load_policy()
    for field, val in updates.model_dump(exclude_none=True).items():
        current[field] = val
    current["updated_at"] = date.today().isoformat()
    _save_policy(current)
    _cache.pop("policy-check", None)
    return current


@app.get("/policy/check")
def policy_check():
    def _run():
        csv = os.path.join(os.path.dirname(__file__), "data", "portfolio_us.csv")
        b = get_briefing(csv)
        p = _load_policy()
        return check_policy(b, p)
    return _cached("policy-check", 600, _run)


# ── Thesis ────────────────────────────────────────────────────────────────────

def _load_thesis() -> dict:
    return _load_json(_THESIS_PATH, "thesis.json")

def _save_thesis(data: dict) -> None:
    _atomic_write_json(_THESIS_PATH, data)


class ThesisEntry(BaseModel):
    reason:      str = ""
    sell_if:     str = ""
    main_risk:   str = ""
    last_review: str = ""


@app.get("/thesis")
def get_all_thesis():
    return _load_thesis()


@app.get("/thesis/{symbol}")
def get_thesis(symbol: str):
    all_thesis = _load_thesis()
    return all_thesis.get(symbol.upper(), {})


@app.put("/thesis/{symbol}")
def upsert_thesis(symbol: str, entry: ThesisEntry):
    from datetime import date
    all_thesis = _load_thesis()
    sym = symbol.upper()
    all_thesis[sym] = {
        "reason":      entry.reason.strip(),
        "sell_if":     entry.sell_if.strip(),
        "main_risk":   entry.main_risk.strip(),
        "last_review": entry.last_review or date.today().isoformat(),
    }
    _save_thesis(all_thesis)
    # Invalidate briefing cache so it reflects updated thesis state
    _cache.pop("briefing", None)
    return all_thesis[sym]


# ── Portfolio ─────────────────────────────────────────────────────────────────

@app.get("/portfolio")
def portfolio():
    rows = _load_portfolio()
    result = []
    for row in rows:
        try:
            d = _cached(f"asset:{row['symbol']}", 3600, lambda s=row["symbol"]: get_asset_data(s))
            if not d:
                continue
            price   = d["price"] or 0
            mkt_val = price * row["qty"]
            gain_u  = mkt_val - row["cost_basis"]
            gain_p  = gain_u / row["cost_basis"] * 100 if row["cost_basis"] else 0
            result.append({
                "symbol":      row["symbol"],
                "description": row.get("description", row["symbol"]),
                "horizon":     row["horizon"],
                "sector":      row.get("sector", ""),
                "qty":         row["qty"],
                "cost_basis":  row["cost_basis"],
                "price":       round(price, 2),
                "mkt_val":     round(mkt_val, 2),
                "gain_usd":    round(gain_u, 2),
                "gain_pct":    round(gain_p, 2),
                "day_chg_pct": d.get("day_chg_pct", 0),
                "target_mean": d.get("target_mean", 0),
                "upside_pct":  d.get("upside_pct", 0),
                "recommendation": d.get("recommendation", ""),
                "n_analysts":  d.get("n_analysts", 0),
                "pe_forward":  d.get("pe_forward"),
                "week52_high": d.get("week52_high", 0),
                "week52_low":  d.get("week52_low", 0),
                "pct_from_high": d.get("pct_from_high", 0),
            })
        except Exception as e:
            result.append({"symbol": row["symbol"], "error": str(e)})
    return result


@app.get("/portfolio/summary")
def portfolio_summary():
    rows = _load_portfolio()
    total_cost = total_mkt = 0.0
    for row in rows:
        try:
            d = _cached(f"asset:{row['symbol']}", 3600, lambda s=row["symbol"]: get_asset_data(s))
            if not d:
                continue
            price = d["price"] or 0
            total_cost += row["cost_basis"]
            total_mkt  += price * row["qty"]
        except Exception:
            pass
    gain_u = total_mkt - total_cost
    gain_p = gain_u / total_cost * 100 if total_cost else 0
    return {
        "total_cost":  round(total_cost, 2),
        "total_mkt":   round(total_mkt, 2),
        "gain_usd":    round(gain_u, 2),
        "gain_pct":    round(gain_p, 2),
        "positions":   len(rows),
    }


# ── Asset ─────────────────────────────────────────────────────────────────────

@app.get("/asset/{symbol}")
def asset(symbol: str):
    sym = symbol.upper()
    try:
        d = _cached(f"asset:{sym}", 3600, lambda: get_asset_data(sym))
        if not d:
            raise HTTPException(status_code=404, detail="Ativo não encontrado")
        # Remove hist (não serializável via JSON)
        return {k: v for k, v in d.items() if k != "hist"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/analyst/{symbol}")
def analyst(symbol: str):
    sym = symbol.upper()
    return _cached(f"analyst:{sym}", 3600, lambda: get_analyst_full(sym))


@app.get("/enrichment/{symbol}")
def enrichment(symbol: str):
    sym = symbol.upper()
    try:
        return _cached(f"enr:{sym}", 3600, lambda: get_ticker_enrichment(sym)) or {}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/ebitda/{symbol}")
def ebitda(symbol: str):
    sym = symbol.upper()
    try:
        return _cached(f"ebitda:{sym}", 3600, lambda: get_ebitda_metrics(sym)) or {}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/alternative/{symbol}")
def alternative(symbol: str):
    sym = symbol.upper()
    try:
        return _cached(f"alt:{sym}", 3600, lambda: get_alternative_signals(sym)) or {}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/polygon/{symbol}")
def polygon(symbol: str):
    sym = symbol.upper()
    try:
        return _cached(f"poly:{sym}", 3600, lambda: get_full_enrichment(sym)) or {}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ── Macro ─────────────────────────────────────────────────────────────────────

@app.get("/macro")
def macro():
    try:
        return _cached("macro", 900, get_macro_data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/macro/full")
def macro_full():
    try:
        raw = _cached("macro", 900, get_macro_data)
        return {
            "raw":               raw,
            "shiller_pe":        describe_shiller_pe(MACRO_SHILLER_PE),
            "buffett_indicator": describe_buffett_indicator(MACRO_BUFFETT_IND),
            "vix":               describe_vix_full(raw.get("vix")),
            "yield_curve":       describe_yield_curve_full(
                                     raw.get("yield_spread"),
                                     raw.get("yield_10y"),
                                     raw.get("yield_3m"),
                                 ),
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/market-status")
def market_status():
    try:
        return _cached("mkt-status", 300, get_market_status)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/sectors")
def sectors():
    try:
        return _cached("sectors", 3600, get_sector_performance)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/calendar")
def calendar():
    try:
        symbols = [r["symbol"] for r in _load_portfolio()]
        events  = _cached("calendar", 3600, get_economic_calendar)
        earnings = _cached("earnings", 3600, lambda: get_upcoming_earnings(symbols))
        return {"events": events or [], "earnings": earnings or []}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ── Investors ─────────────────────────────────────────────────────────────────

@app.get("/investors")
def investors():
    result = {}
    for name in INVESTORS:
        try:
            data = _cached(f"inv:{name}", 21600, lambda n=name: get_investor_holdings(n))
            holdings = data.get("holdings", pd.DataFrame())
            result[name] = {
                "manager":   data.get("manager", ""),
                "style":     data.get("style", ""),
                "known_for": data.get("known_for", ""),
                "emoji":     data.get("emoji", ""),
                "as_of":     data.get("as_of", ""),
                "error":     data.get("error"),
                "holdings":  holdings.head(15).to_dict(orient="records") if isinstance(holdings, pd.DataFrame) and not holdings.empty else [],
            }
        except Exception as e:
            result[name] = {"error": str(e), "holdings": []}
    return result


@app.get("/ark")
def ark():
    try:
        data     = _cached("ark", 3600, lambda: get_ark_holdings("ARKK"))
        holdings = data.get("holdings", pd.DataFrame())
        return {
            **{k: v for k, v in data.items() if k != "holdings"},
            "holdings": holdings.head(20).to_dict(orient="records") if isinstance(holdings, pd.DataFrame) and not holdings.empty else [],
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ── Screener ──────────────────────────────────────────────────────────────────

@app.get("/screener")
def screener(max_results: int = 20):
    try:
        portfolio_syms = [r["symbol"] for r in _load_portfolio()]
        results = _cached("screener", 1800, lambda: screen_swing_candidates(
            max_results=max_results, portfolio_symbols=portfolio_syms
        ))
        # Remove non-serializable objects
        clean = []
        for c in (results or []):
            row = {k: v for k, v in c.items() if k not in ("hist",)}
            if "rsi" in row and isinstance(row["rsi"], dict):
                pass
            if "macd" in row and isinstance(row["macd"], dict):
                pass
            clean.append(row)
        return clean
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ── Intraday / Day Trade ─────────────────────────────────────────────────────

from core.intraday import get_intraday_snapshot

@app.get("/intraday/{symbol}")
def intraday_symbol(symbol: str):
    sym = symbol.upper()
    try:
        return _cached(f"intraday:{sym}", 60, lambda: get_intraday_snapshot(sym))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/intraday")
def intraday_portfolio():
    rows = _load_portfolio()
    results = []
    for row in rows:
        try:
            prev_close = None
            cached_asset = _cache.get(f"asset:{row['symbol']}")
            if cached_asset:
                prev_close = cached_asset[1].get("prev_close")
            snap = _cached(
                f"intraday:{row['symbol']}", 60,
                lambda s=row["symbol"], p=prev_close: get_intraday_snapshot(s, p)
            )
            snap["horizon"] = row.get("horizon", "")
            snap["qty"]     = row.get("qty", 0)
            results.append(snap)
        except Exception as e:
            results.append({"symbol": row["symbol"], "error": str(e)})
    return results


# ── Brasil ────────────────────────────────────────────────────────────────────

@app.get("/brasil")
def brasil():
    return get_brasil_summary()


# ── Swing Trade Decision Support ──────────────────────────────────────────────

@app.get("/swing/{symbol}")
def swing(symbol: str):
    s = symbol.upper()
    return _cached(f"swing:{s}", 900, lambda: get_swing_analysis(s))


@app.get("/market-sentiment")
def market_sentiment():
    return _cached("market-sentiment", 1800, get_market_sentiment)


# ── Risk Book ─────────────────────────────────────────────────────────────────

@app.get("/risk-book")
def risk_book():
    from core.risk_book import get_risk_book
    def _run():
        csv = os.path.join(os.path.dirname(__file__), "data", "portfolio_us.csv")
        b   = get_briefing(csv)
        p   = _load_policy()
        try:
            br_data = get_brasil_summary()
        except Exception:
            br_data = None
        return get_risk_book(b, p, br_data)
    return _cached("risk-book", 600, _run)


# ── Decision Memo ─────────────────────────────────────────────────────────────

class DecisionMemoRequest(BaseModel):
    symbol:    str
    action:    str
    rationale: Optional[str] = None

@app.post("/decision-memo")
def decision_memo(req: DecisionMemoRequest):
    from core.decision_memo import get_decision_memo
    sym   = req.symbol.upper()
    asset = {}
    try:
        asset = get_asset_data(sym) or {}
    except Exception:
        pass
    thesis = _load_thesis().get(sym, {})
    policy = _load_policy()
    csv    = os.path.join(os.path.dirname(__file__), "data", "portfolio_us.csv")
    b      = _cached("briefing", 600, lambda: get_briefing(csv))
    return get_decision_memo(sym, req.action, req.rationale or "", asset, thesis, policy, b)


# ── Weekly Committee ──────────────────────────────────────────────────────────

@app.get("/weekly-committee")
def weekly_committee():
    from core.weekly_committee import get_weekly_committee
    def _run():
        csv = os.path.join(os.path.dirname(__file__), "data", "portfolio_us.csv")
        b   = get_briefing(csv)
        p   = _load_policy()
        pc  = check_policy(b, p)
        try:
            br_data = get_brasil_summary()
        except Exception:
            br_data = None
        return get_weekly_committee(b, pc, br_data)
    return _cached("weekly-committee", 3600, _run)
