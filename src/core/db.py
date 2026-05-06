from __future__ import annotations
import os
import json
import logging
from contextlib import contextmanager
from datetime import date

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

_DSN: str | None = None


def _dsn() -> str:
    global _DSN
    if _DSN is None:
        _DSN = os.environ.get("DATABASE_URL", "")
        if not _DSN:
            raise RuntimeError("DATABASE_URL env var not set")
    return _DSN


@contextmanager
def _conn():
    conn = psycopg2.connect(_dsn(), cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Policy ────────────────────────────────────────────────────────────────────

def load_policy() -> dict:
    try:
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT data FROM policy WHERE id = 1")
            row = cur.fetchone()
            return dict(row["data"]) if row else {}
    except Exception as e:
        logger.error("load_policy DB error: %s", e)
        return {}


def save_policy(data: dict) -> None:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO policy (id, data) VALUES (1, %s)
            ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data, updated_at = now()
        """, (psycopg2.extras.Json(data),))


# ── Thesis ────────────────────────────────────────────────────────────────────

def load_thesis() -> dict:
    try:
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT symbol, reason, sell_if, main_risk, last_review FROM thesis")
            rows = cur.fetchall()
            return {
                r["symbol"]: {
                    "reason":      r["reason"],
                    "sell_if":     r["sell_if"],
                    "main_risk":   r["main_risk"],
                    "last_review": str(r["last_review"]) if r["last_review"] else "",
                }
                for r in rows
            }
    except Exception as e:
        logger.error("load_thesis DB error: %s", e)
        return {}


def save_thesis_entry(symbol: str, entry: dict) -> None:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO thesis (symbol, reason, sell_if, main_risk, last_review)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (symbol) DO UPDATE
                SET reason = EXCLUDED.reason,
                    sell_if = EXCLUDED.sell_if,
                    main_risk = EXCLUDED.main_risk,
                    last_review = EXCLUDED.last_review,
                    updated_at = now()
        """, (
            symbol.upper(),
            entry.get("reason", ""),
            entry.get("sell_if", ""),
            entry.get("main_risk", ""),
            entry.get("last_review", str(date.today())),
        ))


# ── Decision log ──────────────────────────────────────────────────────────────

def log_decision(symbol: str, action: str, rationale: str, result: dict) -> None:
    try:
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO decision_log (symbol, action, rationale, result)
                VALUES (%s, %s, %s, %s)
            """, (symbol.upper(), action, rationale, psycopg2.extras.Json(result)))
    except Exception as e:
        logger.error("log_decision DB error: %s", e)


def list_decisions(symbol: str | None = None, limit: int = 50) -> list[dict]:
    try:
        with _conn() as conn:
            cur = conn.cursor()
            if symbol:
                cur.execute("""
                    SELECT id, symbol, action, rationale, result, created_at
                    FROM decision_log WHERE symbol = %s
                    ORDER BY created_at DESC LIMIT %s
                """, (symbol.upper(), limit))
            else:
                cur.execute("""
                    SELECT id, symbol, action, rationale, result, created_at
                    FROM decision_log ORDER BY created_at DESC LIMIT %s
                """, (limit,))
            rows = cur.fetchall()
            return [
                {**dict(r), "created_at": str(r["created_at"])}
                for r in rows
            ]
    except Exception as e:
        logger.error("list_decisions DB error: %s", e)
        return []


# ── Market events (intraday stream signals) ──────────────────────────────────

def log_market_event(symbol: str, event_type: str, payload: dict) -> None:
    try:
        with _conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO market_events (symbol, event_type, payload)
                VALUES (%s, %s, %s)
            """, (symbol.upper(), event_type, psycopg2.extras.Json(payload)))
    except Exception as e:
        logger.error("log_market_event DB error: %s", e)


def list_market_events(symbol: str | None = None, event_type: str | None = None, limit: int = 100) -> list[dict]:
    try:
        with _conn() as conn:
            cur = conn.cursor()
            where, params = [], []
            if symbol:
                where.append("symbol = %s")
                params.append(symbol.upper())
            if event_type:
                where.append("event_type = %s")
                params.append(event_type)
            sql = "SELECT id, symbol, event_type, payload, triggered_at FROM market_events"
            if where:
                sql += " WHERE " + " AND ".join(where)
            sql += " ORDER BY triggered_at DESC LIMIT %s"
            params.append(limit)
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            return [
                {**dict(r), "triggered_at": str(r["triggered_at"])}
                for r in rows
            ]
    except Exception as e:
        logger.error("list_market_events DB error: %s", e)
        return []
