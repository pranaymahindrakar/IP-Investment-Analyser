"""Ticker search via Yahoo Finance's public search endpoint (no key)."""

from __future__ import annotations

from typing import Any

import requests

_URL = "https://query2.finance.yahoo.com/v1/finance/search"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Counterpoint/1.0)"}


def search_tickers(query: str, limit: int = 7) -> list[dict[str, Any]]:
    """Return matching equities/ETFs: [{symbol, name, exchange, type}]. Empty on failure."""
    query = (query or "").strip()
    if not query:
        return []
    try:
        r = requests.get(
            _URL,
            params={"q": query, "quotesCount": limit, "newsCount": 0},
            headers=_HEADERS,
            timeout=5,
        )
        quotes = r.json().get("quotes", [])
    except Exception:
        return []

    out: list[dict[str, Any]] = []
    for q in quotes:
        sym = q.get("symbol")
        qt = q.get("quoteType", "")
        if not sym or qt not in ("EQUITY", "ETF", "MUTUALFUND", ""):
            continue
        out.append(
            {
                "symbol": sym,
                "name": q.get("shortname") or q.get("longname") or sym,
                "exchange": q.get("exchDisp") or q.get("exchange") or "",
                "type": (qt or "").title() or "Equity",
            }
        )
    return out
