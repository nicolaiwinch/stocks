"""Valuation data routes — reads cached data from last sync."""

from fastapi import APIRouter, HTTPException

from config import STORAGE
from scoring.valuation import (
    score_valuation,
    percentile_rank_inverted,
    percentile_rank_normal,
)

router = APIRouter(prefix="/api/valuation", tags=["valuation"])


@router.get("/")
def get_valuation() -> list[dict]:
    """All stocks with valuation factor values and score (from last sync)."""
    stocks = STORAGE.get_stocks()
    details = STORAGE.get_valuation_details()
    detail_map = {d["ticker"]: d for d in details}

    result = []
    for stock in stocks:
        ticker = stock["ticker"]
        d = detail_map.get(ticker, {})
        result.append({
            "ticker": ticker,
            "name": stock["name"],
            "segment": stock["segment"],
            "forward_pe": d.get("forward_pe"),
            "pb": d.get("pb"),
            "ev_ebitda": d.get("ev_ebitda"),
            "fcf_yield": d.get("fcf_yield"),
            "score": d.get("score"),
        })

    result.sort(key=lambda x: x["score"] if x["score"] is not None else -1, reverse=True)
    return result


@router.get("/{ticker}/explain")
def explain_stock_valuation(ticker: str) -> dict:
    """Full calculation breakdown for a single stock's valuation score."""
    stock = STORAGE.get_stock(ticker)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Get all fundamentals for percentile ranking
    stocks = STORAGE.get_stocks()
    all_fundamentals = {}
    for s in stocks:
        t = s["ticker"]
        fund = STORAGE.get_fundamentals(t)
        if fund:
            all_fundamentals[t] = fund

    if ticker not in all_fundamentals:
        raise HTTPException(status_code=404, detail="No fundamental data for ticker")

    f = all_fundamentals[ticker]

    # Collect all values for ranking (same filtering as score_valuation)
    all_fpe = [v.get("forward_pe") for v in all_fundamentals.values()]
    all_ev = [v.get("ev_ebitda") for v in all_fundamentals.values()]
    all_pb = [v.get("pb") for v in all_fundamentals.values()]
    all_fcfy = [v.get("fcf_yield") for v in all_fundamentals.values()]

    all_fpe = [v for v in all_fpe if v is not None and 0 < v <= 200]
    all_ev = [v for v in all_ev if v is not None and v > 0]
    all_pb = [v for v in all_pb if v is not None and v > 0]
    all_fcfy = [v for v in all_fcfy if v is not None]

    fpe = f.get("forward_pe")
    ev = f.get("ev_ebitda")
    pb = f.get("pb")
    fcfy = f.get("fcf_yield")

    # Same filtering
    if fpe is not None and (fpe < 0 or fpe > 200):
        fpe = None
    if ev is not None and ev < 0:
        ev = None
    if pb is not None and pb <= 0:
        pb = None

    p_ev = percentile_rank_inverted(all_ev, ev)
    p_fpe = percentile_rank_inverted(all_fpe, fpe)
    p_pb = percentile_rank_inverted(all_pb, pb)
    p_fcfy = percentile_rank_normal(all_fcfy, fcfy)

    factors = [
        {
            "factor": "EV/EBITDA",
            "value": ev,
            "percentile": p_ev,
            "weight": "30%",
            "contribution": (p_ev if p_ev is not None else 0.0) * 0.30,
            "inverted": True,
        },
        {
            "factor": "Forward P/E",
            "value": fpe,
            "percentile": p_fpe,
            "weight": "25%",
            "contribution": (p_fpe if p_fpe is not None else 0.0) * 0.25,
            "inverted": True,
        },
        {
            "factor": "P/B",
            "value": pb,
            "percentile": p_pb,
            "weight": "20%",
            "contribution": (p_pb if p_pb is not None else 0.0) * 0.20,
            "inverted": True,
        },
        {
            "factor": "FCF Yield",
            "value": fcfy,
            "percentile": p_fcfy,
            "weight": "25%",
            "contribution": (p_fcfy if p_fcfy is not None else 0.0) * 0.25,
            "inverted": False,
        },
    ]

    # Get stored score
    detail = STORAGE.get_valuation_detail(ticker)
    score = detail["score"] if detail else None

    return {
        "ticker": ticker,
        "score": score,
        "total_stocks": len(all_fundamentals),
        "factors": factors,
    }
