"""Momentum data routes — reads cached data from last sync."""

from fastapi import APIRouter, HTTPException

from config import STORAGE
from scoring.momentum import calculate_momentum_metrics, explain_momentum

router = APIRouter(prefix="/api/momentum", tags=["momentum"])


@router.get("/")
def get_momentum() -> list[dict]:
    """All stocks with momentum factor values and score (from last sync)."""
    stocks = STORAGE.get_stocks()
    details = STORAGE.get_momentum_details()
    detail_map = {d["ticker"]: d for d in details}

    result = []
    for stock in stocks:
        ticker = stock["ticker"]
        d = detail_map.get(ticker, {})
        result.append({
            "ticker": ticker,
            "name": stock["name"],
            "segment": stock["segment"],
            "m6": d.get("m6"),
            "m12": d.get("m12"),
            "m12_1": d.get("m12_1"),
            "vs_ma200": d.get("vs_ma200"),
            "ma50_vs_ma200": d.get("ma50_vs_ma200"),
            "score": d.get("score"),
        })

    result.sort(key=lambda x: x["score"] if x["score"] is not None else -1, reverse=True)
    return result


@router.get("/{ticker}/explain")
def explain_stock_momentum(ticker: str) -> dict:
    """Full calculation breakdown for a single stock's momentum score.
    Uses cached prices from last sync for percentile ranking."""
    stock = STORAGE.get_stock(ticker)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Calculate from stored prices (same data as sync used)
    stocks = STORAGE.get_stocks()
    all_metrics = {}
    for s in stocks:
        t = s["ticker"]
        prices = STORAGE.get_prices(t)
        all_metrics[t] = calculate_momentum_metrics(prices)

    if ticker not in all_metrics:
        raise HTTPException(status_code=404, detail="No price data for ticker")

    return explain_momentum(ticker, all_metrics[ticker], all_metrics)
