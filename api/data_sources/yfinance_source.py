"""
Yahoo Finance data source — fetches prices and fundamentals.

IMPORTANT: Uses auto_adjust=False for raw prices (adjusted prices break around ex-dividend).
"""

import sys
import time
from datetime import date, timedelta

import yfinance as yf

from stocks import STOCKS, ticker_short


def fetch_prices(yf_ticker: str, period: str = "2y") -> list[dict]:
    """
    Fetch daily price history. Returns list of dicts with
    date, open, high, low, close, volume.
    """
    t = yf.Ticker(yf_ticker)
    hist = t.history(period=period, auto_adjust=False)

    if hist.empty:
        return []

    rows = []
    for dt, row in hist.iterrows():
        rows.append({
            "date": dt.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2) if row["Open"] == row["Open"] else None,
            "high": round(float(row["High"]), 2) if row["High"] == row["High"] else None,
            "low": round(float(row["Low"]), 2) if row["Low"] == row["Low"] else None,
            "close": round(float(row["Close"]), 2) if row["Close"] == row["Close"] else None,
            "volume": int(row["Volume"]) if row["Volume"] == row["Volume"] else None,
        })
    return rows


def fetch_fundamentals(yf_ticker: str) -> dict:
    """
    Fetch current fundamentals from yfinance .info.
    Returns a flat dict matching the fundamentals table schema.
    """
    t = yf.Ticker(yf_ticker)
    info = t.info

    price = info.get("currentPrice") or info.get("regularMarketPrice")
    market_cap = info.get("marketCap")
    fcf = info.get("freeCashflow")

    fcf_yield = None
    if fcf and market_cap and market_cap > 0:
        fcf_yield = round(fcf / market_cap * 100, 2)

    div_yield = info.get("dividendYield")
    if div_yield and div_yield <= 1:
        div_yield = div_yield * 100

    trailing_pe = info.get("trailingPE")
    forward_pe = info.get("forwardPE")
    if trailing_pe and trailing_pe < 0:
        trailing_pe = None
    if forward_pe and forward_pe < 0:
        forward_pe = None
    if trailing_pe and trailing_pe > 200:
        trailing_pe = None
    if forward_pe and forward_pe > 200:
        forward_pe = None

    ev_ebitda = info.get("enterpriseToEbitda")
    if ev_ebitda and ev_ebitda < 0:
        ev_ebitda = None

    return {
        "price": round(price, 2) if price else None,
        "market_cap": market_cap,
        "trailing_pe": round(trailing_pe, 1) if trailing_pe else None,
        "forward_pe": round(forward_pe, 1) if forward_pe else None,
        "pb": round(info.get("priceToBook"), 2) if info.get("priceToBook") else None,
        "roe": info.get("returnOnEquity"),
        "operating_margin": info.get("operatingMargins"),
        "net_margin": info.get("profitMargins"),
        "debt_equity": round(info.get("debtToEquity"), 1) if info.get("debtToEquity") else None,
        "ev_ebitda": round(ev_ebitda, 1) if ev_ebitda else None,
        "fcf": fcf,
        "fcf_yield": fcf_yield,
        "dividend_rate": info.get("dividendRate"),
        "dividend_yield": round(div_yield, 1) if div_yield else None,
        "payout_ratio": info.get("payoutRatio"),
    }


def fetch_all(storage, progress_callback=None) -> dict:
    """
    Fetch prices + fundamentals for all stocks and save to storage.
    Returns summary stats.
    """
    total = len(STOCKS)
    prices_count = 0
    fundamentals_count = 0

    for i, (yf_ticker, (name, segment)) in enumerate(STOCKS.items(), 1):
        short = ticker_short(yf_ticker)

        if progress_callback:
            progress_callback(f"[{i}/{total}] {short}")

        # Upsert stock record
        storage.upsert_stock(short, name, segment)

        try:
            # Prices
            rows = fetch_prices(yf_ticker)
            if rows:
                prices_count += storage.upsert_prices(short, rows)

            # Fundamentals
            fundamentals = fetch_fundamentals(yf_ticker)
            storage.upsert_fundamentals(short, fundamentals)
            fundamentals_count += 1

        except Exception as e:
            msg = str(e)
            print(f"[{i}/{total}] ERROR: {short} - {msg}", file=sys.stderr)

            # If rate limited, wait longer before retrying
            if "Rate" in msg or "429" in msg or "Too Many" in msg:
                print(f"[{i}/{total}] Rate limited, waiting 10s...", file=sys.stderr)
                time.sleep(10)
                try:
                    rows = fetch_prices(yf_ticker)
                    if rows:
                        prices_count += storage.upsert_prices(short, rows)
                    fundamentals = fetch_fundamentals(yf_ticker)
                    storage.upsert_fundamentals(short, fundamentals)
                    fundamentals_count += 1
                    print(f"[{i}/{total}] {short} retry OK", file=sys.stderr)
                except Exception as e2:
                    print(f"[{i}/{total}] {short} retry failed: {e2}", file=sys.stderr)

        # Rate limit: delay between requests to avoid Yahoo throttling
        time.sleep(2)

    return {"prices_rows": prices_count, "fundamentals_updated": fundamentals_count}
