"""
Pydantic models — shape of data going in and out of the API.
"""

from pydantic import BaseModel


class StockOut(BaseModel):
    ticker: str
    name: str
    segment: str
    industry: str | None = None
    product: str | None = None


class PriceRow(BaseModel):
    ticker: str
    date: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None


class FundamentalsOut(BaseModel):
    ticker: str
    date: str
    price: float | None = None
    market_cap: float | None = None
    trailing_pe: float | None = None
    forward_pe: float | None = None
    pb: float | None = None
    roe: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None
    debt_equity: float | None = None
    ev_ebitda: float | None = None
    fcf: float | None = None
    fcf_yield: float | None = None
    dividend_rate: float | None = None
    dividend_yield: float | None = None
    payout_ratio: float | None = None


class ScoreOut(BaseModel):
    ticker: str
    date: str
    momentum: float | None = None
    valuation: float | None = None
    revisions: float | None = None
    total: float | None = None


class MomentumDetail(BaseModel):
    ticker: str
    m1w: float | None = None
    m1: float | None = None
    m3: float | None = None
    m6: float | None = None
    vs_ma200: float | None = None
    vs_ma50: float | None = None
    drawdown_1m: float | None = None
    score: float | None = None


class ValuationDetail(BaseModel):
    ticker: str
    trailing_pe: float | None = None
    forward_pe: float | None = None
    pb: float | None = None
    ev_ebitda: float | None = None
    fcf_yield: float | None = None
    div_yield: float | None = None
    score: float | None = None


class SyncResult(BaseModel):
    stocks_updated: int
    prices_updated: int
    scores_calculated: int
    sheets_synced: bool
