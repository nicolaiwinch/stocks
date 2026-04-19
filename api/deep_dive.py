"""
Deep Dive Data Collector
========================
Gathers all available data for a single stock to support investment analysis.
Pulls from: local SQLite DB (scores, prices, momentum) + fresh yfinance data.

Usage: python deep_dive.py NKT
"""

import sys
import json
import sqlite3
import os
from datetime import datetime, timedelta

import yfinance as yf


DB_PATH = os.path.join(os.path.dirname(__file__), "data", "stocks.db")


def get_db_data(ticker: str) -> dict:
    """Pull everything we already have in the local database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Stock info
    stock = conn.execute(
        "SELECT * FROM stocks WHERE ticker = ?", (ticker,)
    ).fetchone()

    # Latest scores
    scores = conn.execute(
        "SELECT * FROM scores WHERE ticker = ? ORDER BY date DESC LIMIT 1",
        (ticker,),
    ).fetchone()

    # Momentum breakdown
    momentum = conn.execute(
        "SELECT * FROM momentum_details WHERE ticker = ?", (ticker,)
    ).fetchone()

    # Latest fundamentals
    fundamentals = conn.execute(
        "SELECT * FROM fundamentals WHERE ticker = ? ORDER BY date DESC LIMIT 1",
        (ticker,),
    ).fetchone()

    # Price history (last 12 months for charting context)
    prices = conn.execute(
        "SELECT date, close, volume FROM prices WHERE ticker = ? ORDER BY date DESC LIMIT 252",
        (ticker,),
    ).fetchall()

    # Peer scores (same segment, latest date)
    segment = stock["segment"] if stock else None
    peers = []
    if segment and scores:
        peers = conn.execute(
            """SELECT s.ticker, st.name, sc.momentum, sc.total
               FROM scores sc
               JOIN stocks st ON st.ticker = sc.ticker
               JOIN stocks s ON s.ticker = sc.ticker
               WHERE st.segment = ? AND sc.date = ? AND sc.ticker != ?
               ORDER BY sc.total DESC""",
            (segment, scores["date"], ticker),
        ).fetchall()

    conn.close()

    return {
        "stock": dict(stock) if stock else None,
        "scores": dict(scores) if scores else None,
        "momentum": dict(momentum) if momentum else None,
        "fundamentals": dict(fundamentals) if fundamentals else None,
        "price_history": {
            "latest": dict(prices[0]) if prices else None,
            "count": len(prices),
            "oldest": dict(prices[-1]) if prices else None,
        },
        "peers": [dict(p) for p in peers],
    }


def get_yfinance_data(ticker: str) -> dict:
    """Fetch fresh data from yfinance for fields we don't store locally."""
    from stocks import STOCKS, ticker_short
    yf_map = {ticker_short(yf_t): yf_t for yf_t in STOCKS}
    yf_ticker = yf_map.get(ticker, ticker)
    t = yf.Ticker(yf_ticker)
    info = t.info

    # Extract the most useful fields for a deep dive
    return {
        "company": {
            "name": info.get("longName"),
            "summary": info.get("longBusinessSummary"),
            "sector": info.get("sectorDisp"),
            "industry": info.get("industryDisp"),
            "employees": info.get("fullTimeEmployees"),
            "website": info.get("website"),
        },
        "price": {
            "current": info.get("currentPrice"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "52w_change_pct": info.get("fiftyTwoWeekChangePercent"),
            "50d_avg": info.get("fiftyDayAverage"),
            "200d_avg": info.get("twoHundredDayAverage"),
            "beta": info.get("beta"),
            "avg_volume": info.get("averageVolume"),
        },
        "valuation": {
            "market_cap": info.get("marketCap"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "price_to_book": info.get("priceToBook"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "ev_revenue": info.get("enterpriseToRevenue"),
        },
        "fundamentals": {
            "revenue": info.get("totalRevenue"),
            "revenue_growth": info.get("revenueGrowth"),
            "ebitda": info.get("ebitda"),
            "ebitda_margin": info.get("ebitdaMargins"),
            "operating_margin": info.get("operatingMargins"),
            "profit_margin": info.get("profitMargins"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "earnings_growth": info.get("earningsGrowth"),
            "eps_trailing": info.get("trailingEps"),
            "eps_forward": info.get("epsForward"),
        },
        "balance_sheet": {
            "total_cash": info.get("totalCash"),
            "total_debt": info.get("totalDebt"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "free_cashflow": info.get("freeCashflow"),
        },
        "dividend": {
            "dividend_yield": info.get("dividendYield"),
            "payout_ratio": info.get("payoutRatio"),
        },
        "analyst": {
            "target_high": info.get("targetHighPrice"),
            "target_low": info.get("targetLowPrice"),
            "target_mean": info.get("targetMeanPrice"),
            "target_median": info.get("targetMedianPrice"),
            "num_analysts": info.get("numberOfAnalystOpinions"),
            "recommendation": info.get("recommendationKey"),
        },
        "risk": {
            "audit_risk": info.get("auditRisk"),
            "board_risk": info.get("boardRisk"),
            "compensation_risk": info.get("compensationRisk"),
            "overall_risk": info.get("overallRisk"),
        },
    }


def get_ranking(ticker: str) -> dict:
    """Where does this stock rank among all tracked stocks?"""
    conn = sqlite3.connect(DB_PATH)

    # Get latest date
    row = conn.execute("SELECT MAX(date) as d FROM scores").fetchone()
    latest_date = row[0] if row else None

    if not latest_date:
        conn.close()
        return {"rank": None, "total_stocks": 0}

    rows = conn.execute(
        "SELECT ticker, total FROM scores WHERE date = ? AND total IS NOT NULL ORDER BY total DESC",
        (latest_date,),
    ).fetchall()
    conn.close()

    total = len(rows)
    rank = None
    for i, r in enumerate(rows, 1):
        if r[0] == ticker:
            rank = i
            break

    return {"rank": rank, "total_scored": total, "date": latest_date}


def main():
    if len(sys.argv) < 2:
        print("Usage: python deep_dive.py <TICKER>")
        print("Example: python deep_dive.py NKT")
        sys.exit(1)

    ticker = sys.argv[1].upper().replace(".CO", "")
    print(f"Collecting deep dive data for {ticker}...", file=sys.stderr)

    db_data = get_db_data(ticker)
    if not db_data["stock"]:
        print(f"Error: {ticker} not found in database", file=sys.stderr)
        sys.exit(1)

    yf_data = get_yfinance_data(ticker)
    ranking = get_ranking(ticker)

    report = {
        "ticker": ticker,
        "generated": datetime.now().isoformat(),
        "ranking": ranking,
        "db": db_data,
        "live": yf_data,
    }

    # Output as JSON — this is what the skill will read
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
