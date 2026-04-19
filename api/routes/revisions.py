"""Revisions data routes — reads cached data from last sync."""

from fastapi import APIRouter, HTTPException

from config import STORAGE
from scoring.revisions import score_revisions, percentile_rank

router = APIRouter(prefix="/api/revisions", tags=["revisions"])


@router.get("/")
def get_revisions() -> list[dict]:
    """All stocks with revisions factor values and score (from last sync)."""
    stocks = STORAGE.get_stocks()
    details = STORAGE.get_revisions_details()
    detail_map = {d["ticker"]: d for d in details}

    result = []
    for stock in stocks:
        ticker = stock["ticker"]
        d = detail_map.get(ticker, {})
        result.append({
            "ticker": ticker,
            "name": stock["name"],
            "segment": stock["segment"],
            "industry": stock.get("industry"),
            "rev_ratio_30d": d.get("rev_ratio_30d"),
            "eps_change_30d": d.get("eps_change_30d"),
            "eps_change_90d": d.get("eps_change_90d"),
            "num_analysts": d.get("num_analysts"),
            "score": d.get("score"),
        })

    result.sort(key=lambda x: x["score"] if x["score"] is not None else -1, reverse=True)
    return result


@router.get("/{ticker}/explain")
def explain_stock_revisions(ticker: str) -> dict:
    """Full calculation breakdown for a single stock's revisions score."""
    stock = STORAGE.get_stock(ticker)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Get all revisions data for percentile ranking
    all_details = STORAGE.get_revisions_details()
    if not all_details:
        raise HTTPException(status_code=404, detail="No revisions data — run a sync first")

    all_revisions = {d["ticker"]: d for d in all_details}

    if ticker not in all_revisions:
        raise HTTPException(status_code=404, detail="No revisions data for ticker")

    r = all_revisions[ticker]

    # Collect values for ranking
    all_ratio = [d.get("rev_ratio_30d") for d in all_details if d.get("rev_ratio_30d") is not None]
    all_change_30 = [d.get("eps_change_30d") for d in all_details if d.get("eps_change_30d") is not None]
    all_change_90 = [d.get("eps_change_90d") for d in all_details if d.get("eps_change_90d") is not None]

    p_ratio = percentile_rank(all_ratio, r.get("rev_ratio_30d"))
    p_change_30 = percentile_rank(all_change_30, r.get("eps_change_30d"))
    p_change_90 = percentile_rank(all_change_90, r.get("eps_change_90d"))

    factors = [
        {
            "factor": "EPS Revision Ratio (30d)",
            "value": r.get("rev_ratio_30d"),
            "percentile": p_ratio,
            "weight": "40%",
            "contribution": (p_ratio if p_ratio is not None else 0.0) * 0.40,
        },
        {
            "factor": "EPS Trend Δ 30d",
            "value": r.get("eps_change_30d"),
            "percentile": p_change_30,
            "weight": "35%",
            "contribution": (p_change_30 if p_change_30 is not None else 0.0) * 0.35,
        },
        {
            "factor": "EPS Trend Δ 90d",
            "value": r.get("eps_change_90d"),
            "percentile": p_change_90,
            "weight": "25%",
            "contribution": (p_change_90 if p_change_90 is not None else 0.0) * 0.25,
        },
    ]

    return {
        "ticker": ticker,
        "score": r.get("score"),
        "total_stocks": len([d for d in all_details if d.get("score") is not None]),
        "num_analysts": r.get("num_analysts", 0),
        "factors": factors,
    }
