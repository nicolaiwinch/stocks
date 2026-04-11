"""
Momentum scoring — migrated from calc_momentum.py.

7-factor model:
  1W (10%) + 1M (15%) + 3M (25%) + 6M (25%) +
  vs 200d MA (15%) + vs 50d MA (10%) + Drawdown from 1M high (10%)

Score range: 1-10 via percentile ranking across all stocks.
"""


def percentile_rank(values: list, value):
    """Rank value among values, return 0-1. Higher value = higher rank."""
    if value is None:
        return None
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    below = sum(1 for v in valid if v < value)
    equal = sum(1 for v in valid if v == value)
    return (below + equal * 0.5) / len(valid)


def calculate_momentum_metrics(prices: list[dict]) -> dict:
    """
    Calculate momentum metrics from a list of price dicts (must have 'close' and 'date').
    Prices must be sorted by date ascending.
    Uses raw prices (not adjusted for dividends).
    """
    if len(prices) < 10:
        return {"m1w": None, "m1": None, "m3": None, "m6": None,
                "vs_ma200": None, "vs_ma50": None, "drawdown_1m": None}

    closes = [p["close"] for p in prices]
    current = closes[-1]

    m1w = ((current - closes[-5]) / closes[-5] * 100) if len(closes) > 5 else None
    m1 = ((current - closes[-21]) / closes[-21] * 100) if len(closes) > 21 else None
    m3 = ((current - closes[-63]) / closes[-63] * 100) if len(closes) > 63 else None
    m6 = ((current - closes[-126]) / closes[-126] * 100) if len(closes) > 126 else None

    vs_ma200 = None
    if len(closes) >= 200:
        ma200 = sum(closes[-200:]) / 200
        vs_ma200 = (current - ma200) / ma200 * 100

    vs_ma50 = None
    if len(closes) >= 50:
        ma50 = sum(closes[-50:]) / 50
        vs_ma50 = (current - ma50) / ma50 * 100

    drawdown_1m = None
    if len(closes) > 21:
        high_1m = max(closes[-21:])
        drawdown_1m = (current - high_1m) / high_1m * 100

    return {
        "m1w": round(m1w, 1) if m1w is not None else None,
        "m1": round(m1, 1) if m1 is not None else None,
        "m3": round(m3, 1) if m3 is not None else None,
        "m6": round(m6, 1) if m6 is not None else None,
        "vs_ma200": round(vs_ma200, 1) if vs_ma200 is not None else None,
        "vs_ma50": round(vs_ma50, 1) if vs_ma50 is not None else None,
        "drawdown_1m": round(drawdown_1m, 1) if drawdown_1m is not None else None,
    }


def score_momentum(all_metrics: dict[str, dict]) -> dict[str, float | None]:
    """
    Given a dict of {ticker: metrics}, calculate momentum scores (1-10)
    using percentile ranking across all stocks.

    Returns {ticker: score}.
    """
    all_m1w = [m["m1w"] for m in all_metrics.values()]
    all_m1 = [m["m1"] for m in all_metrics.values()]
    all_m3 = [m["m3"] for m in all_metrics.values()]
    all_m6 = [m["m6"] for m in all_metrics.values()]
    all_ma200 = [m["vs_ma200"] for m in all_metrics.values()]
    all_ma50 = [m["vs_ma50"] for m in all_metrics.values()]
    all_dd = [m["drawdown_1m"] for m in all_metrics.values()]

    scores = {}
    for ticker, m in all_metrics.items():
        components = [
            (percentile_rank(all_m1w, m["m1w"]), 0.10),
            (percentile_rank(all_m1, m["m1"]), 0.15),
            (percentile_rank(all_m3, m["m3"]), 0.25),
            (percentile_rank(all_m6, m["m6"]), 0.25),
            (percentile_rank(all_ma200, m["vs_ma200"]), 0.15),
            (percentile_rank(all_ma50, m["vs_ma50"]), 0.10),
            (percentile_rank(all_dd, m["drawdown_1m"]), 0.10),
        ]

        parts = []
        weights = []
        for p, w in components:
            if p is not None:
                parts.append(p * w)
                weights.append(w)

        if weights:
            raw = sum(parts) / sum(weights)
            scores[ticker] = round(raw * 9 + 1, 1)
        else:
            scores[ticker] = None

    return scores
