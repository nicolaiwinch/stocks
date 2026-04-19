"""
Data sync routes — trigger refreshes and recalculations.
"""

import sys
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from config import STORAGE
from data_sources.yfinance_source import fetch_all
from scoring.momentum import calculate_momentum_metrics, score_momentum
from scoring.valuation import score_valuation
from scoring.revisions import fetch_revisions_data, score_revisions
from scoring.total import calculate_total
from stocks import STOCKS, ticker_short

router = APIRouter(prefix="/api/sync", tags=["sync"])


class BulkPushRequest(BaseModel):
    """Push locally-synced data to the server (for when yfinance is blocked)."""
    prices: list[dict]           # [{ticker, date, open, high, low, close, volume}, ...]
    fundamentals: list[dict]     # [{ticker, ...fundamentals}, ...]
    scores: list[dict]           # [{ticker, date, momentum, valuation, total}, ...]
    momentum_details: list[dict] # [{ticker, m6, m12, ...}, ...]
    valuation_details: list[dict] = []  # [{ticker, forward_pe, pb, ev_ebitda, fcf_yield, score, updated}, ...]
    revisions_details: list[dict] = []  # [{ticker, rev_ratio_30d, eps_change_30d, eps_change_90d, num_analysts, score, updated}, ...]


@router.post("/fetch")
def fetch_data() -> dict:
    """Fetch latest prices + fundamentals from Yahoo Finance."""
    def progress(msg):
        print(msg, file=sys.stderr)

    result = fetch_all(STORAGE, progress_callback=progress)
    return result


@router.post("/scores")
def recalculate_scores() -> dict:
    """Recalculate all scores: momentum + valuation → total."""
    today = date.today().isoformat()
    stocks = STORAGE.get_stocks()

    # --- Momentum ---
    all_momentum_metrics = {}
    for stock in stocks:
        ticker = stock["ticker"]
        prices = STORAGE.get_prices(ticker)
        metrics = calculate_momentum_metrics(prices)
        all_momentum_metrics[ticker] = metrics

    momentum_scores = score_momentum(all_momentum_metrics)

    # --- Valuation ---
    all_fundamentals = {}
    for stock in stocks:
        ticker = stock["ticker"]
        fund = STORAGE.get_fundamentals(ticker)
        if fund:
            all_fundamentals[ticker] = fund

    valuation_scores, valuation_details = score_valuation(all_fundamentals)

    # --- Revisions ---
    all_revisions = {}
    yf_map = {ticker_short(yf_t): yf_t for yf_t in STOCKS}
    for stock in stocks:
        ticker = stock["ticker"]
        yf_ticker = yf_map.get(ticker)
        if yf_ticker:
            import sys, time
            print(f"  Revisions: {ticker}", file=sys.stderr)
            rev_data = fetch_revisions_data(yf_ticker)
            if rev_data:
                all_revisions[ticker] = rev_data
            time.sleep(1)  # Rate limit

    if all_revisions:
        revisions_scores, revisions_details = score_revisions(all_revisions)
    else:
        revisions_scores, revisions_details = {}, {}

    # --- Save scores + details ---
    count = 0
    for stock in stocks:
        ticker = stock["ticker"]
        mom = momentum_scores.get(ticker)
        val = valuation_scores.get(ticker)
        rev = revisions_scores.get(ticker)
        total = calculate_total(mom, rev, val)

        STORAGE.upsert_score(ticker, today, momentum=mom, valuation=val,
                             revisions=rev, total=total)
        STORAGE.upsert_momentum_detail(ticker, all_momentum_metrics[ticker], mom, today)
        if ticker in valuation_details:
            STORAGE.upsert_valuation_detail(ticker, valuation_details[ticker], val, today)
        if ticker in revisions_details:
            STORAGE.upsert_revisions_detail(ticker, revisions_details[ticker], rev, today)
        count += 1

    return {"scores_calculated": count, "date": today}


@router.post("/full")
def full_sync() -> dict:
    """Full sync: fetch data → calculate scores."""
    fetch_result = fetch_data()
    score_result = recalculate_scores()

    STORAGE.log_sync(
        timestamp=datetime.now().isoformat(),
        prices_rows=fetch_result.get("prices_rows", 0),
        scores_calculated=score_result.get("scores_calculated", 0),
    )

    return {
        "fetch": fetch_result,
        "scores": score_result,
    }


@router.get("/status")
def sync_status() -> dict:
    """Get last sync info."""
    last = STORAGE.get_last_sync()
    return last or {"timestamp": None}


@router.post("/push")
def push_data(req: BulkPushRequest) -> dict:
    """Receive locally-synced data (prices, fundamentals, scores, momentum).
    Use this when yfinance is blocked on the server."""
    prices_count = 0
    for p in req.prices:
        ticker = p.pop("ticker")
        date_val = p.pop("date")
        STORAGE.upsert_prices(ticker, [{"date": date_val, **p}])
        prices_count += 1

    for f in req.fundamentals:
        ticker = f.pop("ticker")
        STORAGE.upsert_fundamentals(ticker, f)

    for s in req.scores:
        STORAGE.upsert_score(s["ticker"], s["date"],
                             momentum=s.get("momentum"), valuation=s.get("valuation"),
                             revisions=s.get("revisions"), total=s.get("total"))

    for m in req.momentum_details:
        ticker = m.pop("ticker")
        score = m.pop("score", None)
        updated = m.pop("updated", date.today().isoformat())
        STORAGE.upsert_momentum_detail(ticker, m, score, updated)

    for v in req.valuation_details:
        ticker = v.pop("ticker")
        score = v.pop("score", None)
        updated = v.pop("updated", date.today().isoformat())
        STORAGE.upsert_valuation_detail(ticker, v, score, updated)

    for r in req.revisions_details:
        ticker = r.pop("ticker")
        score = r.pop("score", None)
        updated = r.pop("updated", date.today().isoformat())
        STORAGE.upsert_revisions_detail(ticker, r, score, updated)

    STORAGE.log_sync(
        timestamp=datetime.now().isoformat(),
        prices_rows=prices_count,
        scores_calculated=len(req.scores),
    )

    return {
        "prices": prices_count,
        "fundamentals": len(req.fundamentals),
        "scores": len(req.scores),
        "momentum_details": len(req.momentum_details),
        "valuation_details": len(req.valuation_details),
        "revisions_details": len(req.revisions_details),
    }
