"""
Data sync routes — trigger refreshes and recalculations.
"""

import sys
from datetime import date

from fastapi import APIRouter

from config import STORAGE
from data_sources.yfinance_source import fetch_all
from data_sources.sheets_sync import push_scores_to_sheet, read_manual_data
from scoring.momentum import calculate_momentum_metrics, score_momentum
from scoring.valuation import score_valuation
from scoring.total import calculate_total

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("/fetch")
def fetch_data() -> dict:
    """Fetch latest prices + fundamentals from Yahoo Finance."""
    def progress(msg):
        print(msg, file=sys.stderr)

    result = fetch_all(STORAGE, progress_callback=progress)
    return result


@router.post("/scores")
def recalculate_scores() -> dict:
    """Recalculate all scores from stored data."""
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

    # --- Valuation ---
    all_fundamentals = {}
    for stock in stocks:
        ticker = stock["ticker"]
        f = STORAGE.get_fundamentals(ticker)
        if f:
            all_fundamentals[ticker] = f

    valuation_scores = score_valuation(all_fundamentals)

    # --- Read existing revisions from DB (manually entered via Sheets) ---
    existing_scores = STORAGE.get_scores()
    revisions_map = {s["ticker"]: s.get("revisions") for s in existing_scores}

    # --- Total + save ---
    count = 0
    for stock in stocks:
        ticker = stock["ticker"]
        mom = momentum_scores.get(ticker)
        val = valuation_scores.get(ticker)
        rev = revisions_map.get(ticker)
        total = calculate_total(mom, rev, val)

        STORAGE.upsert_score(ticker, today, momentum=mom, valuation=val,
                             revisions=rev, total=total)
        count += 1

    return {"scores_calculated": count, "date": today}


@router.post("/sheets/push")
def push_to_sheets() -> dict:
    """Push latest scores to Google Sheets."""
    return push_scores_to_sheet(STORAGE)


@router.post("/sheets/pull")
def pull_from_sheets() -> dict:
    """Read manual data (industry, product, revisions) from Google Sheets."""
    return read_manual_data(STORAGE)


@router.post("/full")
def full_sync() -> dict:
    """Full sync: fetch data → calculate scores → push to sheets."""
    fetch_result = fetch_data()
    pull_result = pull_from_sheets()
    score_result = recalculate_scores()
    push_result = push_to_sheets()

    return {
        "fetch": fetch_result,
        "pull": pull_result,
        "scores": score_result,
        "push": push_result,
    }
