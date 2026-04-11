"""Price history routes."""

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException

from config import STORAGE

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.get("/{ticker}")
def get_prices(ticker: str, days: int = 365) -> list[dict]:
    """Get price history for a ticker."""
    stock = STORAGE.get_stock(ticker)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    start = date.today() - timedelta(days=days)
    return STORAGE.get_prices(ticker, start=start)
