from __future__ import annotations
import os
import asyncio
import logging
from collections import deque, defaultdict
from datetime import datetime, timezone
from typing import Optional, Iterable

import pandas as pd

logger = logging.getLogger(__name__)

try:
    from alpaca.data.live import StockDataStream
    from alpaca.data.enums import DataFeed
except Exception as e:  # pragma: no cover
    StockDataStream = None
    DataFeed = None
    logger.warning("alpaca-py not available: %s", e)

from core.db import log_market_event
from core.intraday import (
    calc_vwap, calc_rvol, calc_opening_range, calc_atr,
    calc_relative_strength, calc_gap, _score_signal, _to_python,
    _get_hist_bars,
)

_SESSION_BAR_LIMIT = 400  # ~ full RTH session of 1-min bars

_RVOL_SPIKE   = 3.0
_GAP_LARGE    = 5.0


class IntradayStream:
    """Singleton-style background WS consumer for Alpaca IEX 1-min bars.

    Maintains in-memory ring buffer of session bars per symbol, scores each
    new bar via existing intraday helpers, fans out snapshots to any SSE
    subscriber queues, and persists notable signals to Neon.
    """

    def __init__(self, api_key: str, secret_key: str, symbols: Iterable[str]):
        if StockDataStream is None:
            raise RuntimeError("alpaca-py is not installed")
        self._key = api_key
        self._secret = secret_key
        self._symbols = sorted({s.upper() for s in symbols} | {"SPY"})
        self._client: Optional["StockDataStream"] = None
        self._task: Optional[asyncio.Task] = None
        self._bars: dict[str, deque] = defaultdict(lambda: deque(maxlen=_SESSION_BAR_LIMIT))
        self._hist_cache: dict[str, pd.DataFrame] = {}
        self._prev_close: dict[str, float] = {}
        self._signals_seen: set[tuple[str, str]] = set()  # dedupe per session
        self._subscribers: set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    # ── lifecycle ──────────────────────────────────────────────────

    async def start(self) -> None:
        if self._task is not None:
            return
        self._client = StockDataStream(self._key, self._secret, feed=DataFeed.IEX)
        self._client.subscribe_bars(self._on_bar, *self._symbols)
        self._task = asyncio.create_task(self._run(), name="intraday-stream")
        logger.info("IntradayStream started for %d symbols", len(self._symbols))

    async def _run(self) -> None:
        try:
            await self._client._run_forever()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("IntradayStream loop error: %s", e)

    async def stop(self) -> None:
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                pass
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None
        logger.info("IntradayStream stopped")

    # ── subscriptions (SSE) ────────────────────────────────────────

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    # ── bar handler ────────────────────────────────────────────────

    async def _on_bar(self, bar) -> None:
        try:
            sym = (bar.symbol or "").upper()
            if not sym:
                return
            row = {
                "Datetime": bar.timestamp,
                "Open":   float(bar.open),
                "High":   float(bar.high),
                "Low":    float(bar.low),
                "Close":  float(bar.close),
                "Volume": float(bar.volume or 0),
            }
            self._bars[sym].append(row)

            snapshot = await asyncio.to_thread(self._score, sym)
            if not snapshot:
                return

            payload = {"type": "snapshot", "data": snapshot}
            for q in list(self._subscribers):
                try:
                    q.put_nowait(payload)
                except asyncio.QueueFull:
                    pass

            await self._maybe_emit_signals(sym, snapshot)
        except Exception as e:
            logger.error("on_bar error %s: %s", getattr(bar, "symbol", "?"), e)

    # ── scoring ────────────────────────────────────────────────────

    @staticmethod
    def _frame(rows) -> pd.DataFrame:
        rows = list(rows)
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True)
        df = df.set_index("Datetime")
        try:
            df.index = df.index.tz_convert("America/New_York")
        except Exception:
            pass
        return df

    def _score(self, sym: str) -> dict | None:
        bars_today = self._frame(self._bars[sym])
        if bars_today.empty:
            return None

        if sym not in self._hist_cache:
            try:
                self._hist_cache[sym] = _get_hist_bars(sym)
            except Exception:
                self._hist_cache[sym] = pd.DataFrame()
        hist = self._hist_cache[sym]

        spy_today = self._frame(self._bars.get("SPY", deque()))

        prev_close = self._prev_close.get(sym)
        if prev_close is None and not hist.empty:
            try:
                prev_close = float(hist["Close"].iloc[-1])
                self._prev_close[sym] = prev_close
            except Exception:
                prev_close = None

        vwap = calc_vwap(bars_today)
        rvol = calc_rvol(bars_today, hist) if not hist.empty else None
        opening = calc_opening_range(bars_today)
        atr = calc_atr(hist) if not hist.empty else None
        rs = calc_relative_strength(bars_today, spy_today) if not spy_today.empty else None
        gap = calc_gap(bars_today, prev_close) if prev_close else None
        last = float(bars_today["Close"].iloc[-1])
        spy_above_vwap = False
        if not spy_today.empty:
            spy_vwap = calc_vwap(spy_today)
            spy_last = float(spy_today["Close"].iloc[-1])
            if spy_vwap is not None:
                spy_above_vwap = spy_last >= spy_vwap

        snap = {
            "symbol": sym,
            "price": last,
            "vwap": vwap,
            "rvol": rvol,
            "atr": atr,
            "gap_pct": gap,
            "relative_strength": rs,
            "opening_range": opening,
            "above_vwap": (vwap is not None and last >= vwap),
            "spy_above_vwap": spy_above_vwap,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        snap["signal"] = _score_signal(snap)
        return _to_python(snap)

    # ── signal persistence ─────────────────────────────────────────

    async def _maybe_emit_signals(self, sym: str, snap: dict) -> None:
        events: list[tuple[str, dict]] = []
        rvol = snap.get("rvol") or 0
        gap = snap.get("gap_pct") or 0
        opening = snap.get("opening_range") or {}
        price = snap.get("price")

        if rvol >= _RVOL_SPIKE:
            events.append(("rvol_spike", {"rvol": rvol, "price": price}))
        if abs(gap) >= _GAP_LARGE:
            events.append(("large_gap", {"gap_pct": gap, "price": price}))
        if opening and price is not None:
            oh = opening.get("high")
            ol = opening.get("low")
            if oh and price > oh:
                events.append(("or_break_high", {"or_high": oh, "price": price}))
            if ol and price < ol:
                events.append(("or_break_low", {"or_low": ol, "price": price}))

        for event_type, payload in events:
            key = (sym, event_type)
            if key in self._signals_seen:
                continue
            self._signals_seen.add(key)
            try:
                await asyncio.to_thread(log_market_event, sym, event_type, payload)
            except Exception as e:
                logger.error("log_market_event failed %s/%s: %s", sym, event_type, e)


# ── module-level singleton ─────────────────────────────────────────

_stream: Optional[IntradayStream] = None


def get_stream() -> Optional[IntradayStream]:
    return _stream


async def start_stream(symbols: Iterable[str]) -> Optional[IntradayStream]:
    global _stream
    if _stream is not None:
        return _stream
    key = os.getenv("ALPACA_KEY", "")
    secret = os.getenv("ALPACA_SECRET", "")
    if not key or not secret:
        logger.warning("ALPACA_KEY/SECRET missing — intraday stream disabled")
        return None
    if StockDataStream is None:
        logger.warning("alpaca-py missing — intraday stream disabled")
        return None
    try:
        _stream = IntradayStream(key, secret, symbols)
        await _stream.start()
        return _stream
    except Exception as e:
        logger.error("Failed to start IntradayStream: %s", e)
        _stream = None
        return None


async def stop_stream() -> None:
    global _stream
    if _stream is not None:
        await _stream.stop()
        _stream = None
