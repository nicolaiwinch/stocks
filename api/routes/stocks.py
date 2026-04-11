"""Stock list and detail routes."""

from fastapi import APIRouter, HTTPException

from config import STORAGE

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/")
def list_stocks() -> list[dict]:
    """All stocks with their latest scores."""
    stocks = STORAGE.get_stocks()
    scores = STORAGE.get_scores()
    score_map = {s["ticker"]: s for s in scores}

    result = []
    for stock in stocks:
        s = score_map.get(stock["ticker"], {})
        result.append({
            **stock,
            "momentum": s.get("momentum"),
            "valuation": s.get("valuation"),
            "revisions": s.get("revisions"),
            "total": s.get("total"),
        })
    return result


@router.get("/{ticker}")
def get_stock(ticker: str) -> dict:
    """Single stock with fundamentals and scores."""
    stock = STORAGE.get_stock(ticker)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    fundamentals = STORAGE.get_fundamentals(ticker)
    scores = STORAGE.get_score_history(ticker, limit=1)
    latest_score = scores[0] if scores else {}

    return {
        **stock,
        "fundamentals": fundamentals,
        "score": latest_score,
    }


@router.get("/{ticker}/scores")
def get_score_history(ticker: str, limit: int = 30) -> list[dict]:
    """Score history for a ticker."""
    stock = STORAGE.get_stock(ticker)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return STORAGE.get_score_history(ticker, limit=limit)
