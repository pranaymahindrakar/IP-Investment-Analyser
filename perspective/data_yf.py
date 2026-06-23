"""Structured company data from Yahoo Finance (free, no API key).

All functions are pure and return plain Python types so they can be cached by
the Streamlit layer. Network/parse failures degrade gracefully to partial data
rather than raising, so a flaky field never takes down the whole profile.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import pandas as pd
import requests
import yfinance as yf


def _domain(website: str | None) -> str | None:
    if not website:
        return None
    netloc = urlparse(website if "//" in website else f"http://{website}").netloc or website
    return netloc.replace("www.", "").strip("/") or None


def get_logo(website: str | None) -> str | None:
    """Best logo URL for a company: Clearbit if available, else Google favicon."""
    domain = _domain(website)
    if not domain:
        return None
    clearbit = f"https://logo.clearbit.com/{domain}"
    try:
        r = requests.get(clearbit, timeout=4, stream=True)
        if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image"):
            return clearbit
    except Exception:
        pass
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"


def logo_for_ticker(symbol: str) -> str | None:
    """Ticker-keyed logo (for search results, where we don't yet have a website)."""
    if not symbol:
        return None
    base = symbol.split(".")[0].upper()  # strip exchange suffix, e.g. RY.TO
    url = f"https://financialmodelingprep.com/image-stock/{base}.png"
    try:
        r = requests.get(url, timeout=3, stream=True)
        if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image"):
            return url
    except Exception:
        pass
    return None


def _safe_info(ticker: str) -> dict[str, Any]:
    """Yahoo's `.info` dict, or {} if the ticker is unknown/unreachable."""
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception:
        return {}
    # Yahoo returns a near-empty dict for invalid tickers.
    if not info or info.get("quoteType") is None and not info.get("longName"):
        return info
    return info


def is_valid(ticker: str) -> bool:
    info = _safe_info(ticker)
    return bool(info.get("longName") or info.get("shortName"))


def get_profile(ticker: str) -> dict[str, Any]:
    """Identity + business description fields."""
    info = _safe_info(ticker)
    return {
        "ticker": ticker.upper(),
        "name": info.get("longName") or info.get("shortName") or ticker.upper(),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "summary": info.get("longBusinessSummary"),
        "country": info.get("country"),
        "website": info.get("website"),
        "logo": get_logo(info.get("website")),
        "employees": info.get("fullTimeEmployees"),
        "city": info.get("city"),
        "state": info.get("state"),
    }


def _fmt_big(n: Any) -> str | None:
    """Human-readable money: 1.23T / 45.6B / 789.0M."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return None
    for unit, size in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(n) >= size:
            return f"{n / size:.2f}{unit}"
    return f"{n:.0f}"


def _pct(n: Any) -> str | None:
    try:
        return f"{float(n) * 100:.1f}%"
    except (TypeError, ValueError):
        return None


def get_key_stats(ticker: str) -> dict[str, Any]:
    """Headline valuation / size / profitability metrics, pre-formatted."""
    info = _safe_info(ticker)
    return {
        "Market cap": _fmt_big(info.get("marketCap")),
        "Revenue (ttm)": _fmt_big(info.get("totalRevenue")),
        "Gross margin": _pct(info.get("grossMargins")),
        "Operating margin": _pct(info.get("operatingMargins")),
        "Profit margin": _pct(info.get("profitMargins")),
        "P/E (trailing)": _round(info.get("trailingPE")),
        "P/E (forward)": _round(info.get("forwardPE")),
        "Price / sales": _round(info.get("priceToSalesTrailing12Months")),
        "Rev. growth (YoY)": _pct(info.get("revenueGrowth")),
        "Earnings growth": _pct(info.get("earningsGrowth")),
        "Return on equity": _pct(info.get("returnOnEquity")),
        "Debt / equity": _round(info.get("debtToEquity")),
        "52-wk change": _pct(info.get("52WeekChange")),
        "Analyst target": (f"${_round(info.get('targetMeanPrice'))}"
                           if info.get("targetMeanPrice") else None),
        "Beta": _round(info.get("beta")),
        "Dividend yield": _pct(info.get("dividendYield"))
        if info.get("dividendYield") and info["dividendYield"] < 1
        else (f"{info.get('dividendYield')}%" if info.get("dividendYield") else None),
        "Cash": _fmt_big(info.get("totalCash")),
        "Debt": _fmt_big(info.get("totalDebt")),
    }


def _round(n: Any) -> float | None:
    try:
        return round(float(n), 2)
    except (TypeError, ValueError):
        return None


def get_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Closing-price series. Empty DataFrame if unavailable."""
    try:
        hist = yf.Ticker(ticker).history(period=period)
    except Exception:
        return pd.DataFrame()
    if hist is None or hist.empty:
        return pd.DataFrame()
    return hist[["Close"]].reset_index()


def get_news(ticker: str, limit: int = 6) -> list[dict[str, str]]:
    """Recent Yahoo news headlines. Best-effort; shape varies across yfinance versions."""
    try:
        raw = yf.Ticker(ticker).news or []
    except Exception:
        return []
    items: list[dict[str, str]] = []
    for entry in raw[:limit]:
        content = entry.get("content", entry)  # newer yfinance nests under "content"
        title = content.get("title") or entry.get("title")
        if not title:
            continue
        url = (
            (content.get("clickThroughUrl") or {}).get("url")
            or (content.get("canonicalUrl") or {}).get("url")
            or entry.get("link")
        )
        publisher = (
            (content.get("provider") or {}).get("displayName")
            or entry.get("publisher")
            or ""
        )
        items.append({"title": title, "url": url or "", "publisher": publisher})
    return items


def get_numeric_stats(ticker: str) -> dict[str, float | None]:
    """Raw numeric (percent) metrics for side-by-side bar charts."""
    info = _safe_info(ticker)

    def pct(x: Any) -> float | None:
        try:
            return round(float(x) * 100, 1)
        except (TypeError, ValueError):
            return None

    return {
        "Gross margin": pct(info.get("grossMargins")),
        "Operating margin": pct(info.get("operatingMargins")),
        "Profit margin": pct(info.get("profitMargins")),
        "Rev. growth": pct(info.get("revenueGrowth")),
        "Return on equity": pct(info.get("returnOnEquity")),
    }


def get_snapshot(ticker: str) -> dict[str, Any]:
    """Everything the rest of the app needs about one company, in one call."""
    profile = get_profile(ticker)
    return {
        "profile": profile,
        "key_stats": get_key_stats(ticker),
        "num": get_numeric_stats(ticker),
        "news": get_news(ticker),
        "valid": bool(profile.get("name") and profile["name"] != ticker.upper())
        or is_valid(ticker),
    }


def snapshot_to_text(snapshot: dict[str, Any]) -> str:
    """Flatten a snapshot into a compact text block for LLM context."""
    p = snapshot["profile"]
    lines = [
        f"Company: {p.get('name')} ({p.get('ticker')})",
        f"Sector / Industry: {p.get('sector')} / {p.get('industry')}",
        f"HQ: {p.get('city')}, {p.get('state')}, {p.get('country')}",
        f"Employees: {p.get('employees')}",
        "",
        "Business summary:",
        p.get("summary") or "(not available)",
        "",
        "Key metrics:",
    ]
    for k, v in snapshot["key_stats"].items():
        if v is not None:
            lines.append(f"  - {k}: {v}")
    if snapshot.get("news"):
        lines.append("\nRecent Yahoo headlines:")
        for n in snapshot["news"]:
            lines.append(f"  - {n['title']} ({n['publisher']})")
    return "\n".join(lines)
