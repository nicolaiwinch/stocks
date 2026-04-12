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

router = APIRouter(prefix="/api/sync", tags=["sync"])


class BulkPushRequest(BaseModel):
    """Push locally-synced data to the server (for when yfinance is blocked)."""
    prices: list[dict]           # [{ticker, date, open, high, low, close, volume}, ...]
    fundamentals: list[dict]     # [{ticker, ...fundamentals}, ...]
    scores: list[dict]           # [{ticker, date, momentum, total}, ...]
    momentum_details: list[dict] # [{ticker, m6, m12, ...}, ...]


@router.post("/fetch")
def fetch_data() -> dict:
    """Fetch latest prices + fundamentals from Yahoo Finance."""
    def progress(msg):
        print(msg, file=sys.stderr)

    result = fetch_all(STORAGE, progress_callback=progress)
    return result


@router.post("/scores")
def recalculate_scores() -> dict:
    """Recalculate scores from stored data. Only momentum for now."""
    today = date.today().isoformat()
    stocks = STORAGE.get_stocks()

    # --- Momentum ---
    all_metrics = {}
    for stock in stocks:
        ticker = stock["ticker"]
        prices = STORAGE.get_prices(ticker)
        metrics = calculate_momentum_metrics(prices)
        all_metrics[ticker] = metrics

    momentum_scores = score_momentum(all_metrics)

    # --- Save scores + momentum details ---
    count = 0
    for stock in stocks:
        ticker = stock["ticker"]
        mom = momentum_scores.get(ticker)
        STORAGE.upsert_score(ticker, today, momentum=mom, total=mom)
        STORAGE.upsert_momentum_detail(ticker, all_metrics[ticker], mom, today)
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
                             momentum=s.get("momentum"), total=s.get("total"))

    for m in req.momentum_details:
        ticker = m.pop("ticker")
        score = m.pop("score", None)
        updated = m.pop("updated", date.today().isoformat())
        STORAGE.upsert_momentum_detail(ticker, m, score, updated)

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
    }
