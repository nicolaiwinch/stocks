"""
Momentum scoring — 5-factor model.

Price-based:
  6M Return (20%) + 12M Return (20%) + 12-1M Return (25%)
Trend / Moving Averages:
  Price vs 200d MA (20%) + 50d MA vs 200d MA (15%)

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
    closes = [p["close"] for p in prices if p["close"] is not None]

    if len(closes) < 10:
        return {
            "m6": None, "m12": None, "m12_1": None,
            "vs_ma200": None, "ma50_vs_ma200": None,
        }
    current = closes[-1]

    # Price-based
    m6 = ((current - closes[-126]) / closes[-126] * 100) if len(closes) > 126 else None
    m12 = ((current - closes[-252]) / closes[-252] * 100) if len(closes) > 252 else None

    # 12-1M: 12-month return but skip the most recent month (reduces reversal noise)
    m12_1 = None
    if len(closes) > 252:
        price_1m_ago = closes[-21]
        price_12m_ago = closes[-252]
        m12_1 = (price_1m_ago - price_12m_ago) / price_12m_ago * 100

    # Trend / Moving averages
    vs_ma200 = None
    if len(closes) >= 200:
        ma200 = sum(closes[-200:]) / 200
        vs_ma200 = (current - ma200) / ma200 * 100

    ma50_vs_ma200 = None
    if len(closes) >= 200:
        ma50 = sum(closes[-50:]) / 50
        ma200 = sum(closes[-200:]) / 200
        ma50_vs_ma200 = (ma50 - ma200) / ma200 * 100

    return {
        "m6": round(m6, 2) if m6 is not None else None,
        "m12": round(m12, 2) if m12 is not None else None,
        "m12_1": round(m12_1, 2) if m12_1 is not None else None,
        "vs_ma200": round(vs_ma200, 2) if vs_ma200 is not None else None,
        "ma50_vs_ma200": round(ma50_vs_ma200, 2) if ma50_vs_ma200 is not None else None,
    }


# Factor definitions: (metric_key, weight)
FACTORS = [
    ("m6", 0.20),
    ("m12", 0.20),
    ("m12_1", 0.25),
    ("vs_ma200", 0.20),
    ("ma50_vs_ma200", 0.15),
]


def explain_momentum(ticker: str, metrics: dict, all_metrics: dict[str, dict]) -> dict:
    """
    Return full calculation breakdown for a single stock.
    Shows each factor's raw value, percentile rank, weight, and contribution.
    """
    all_values = {
        key: [m[key] for m in all_metrics.values()]
        for key, _ in FACTORS
    }

    factor_names = {
        "m6": "6M Return",
        "m12": "12M Return",
        "m12_1": "12-1M Return",
        "vs_ma200": "Price vs 200d MA",
        "ma50_vs_ma200": "50d MA vs 200d MA",
    }

    breakdown = []
    parts = []
    weights = []

    for key, weight in FACTORS:
        raw = metrics.get(key)
        rank = percentile_rank(all_values[key], raw)
        contribution = None
        if rank is not None:
            contribution = round(rank * weight, 4)
            parts.append(rank * weight)
            weights.append(weight)

        breakdown.append({
            "factor": factor_names.get(key, key),
            "key": key,
            "value": raw,
            "percentile": round(rank, 3) if rank is not None else None,
            "weight": f"{int(weight * 100)}%",
            "contribution": contribution,
        })

    if weights:
        raw_score = sum(parts) / sum(weights)
        final_score = round(raw_score * 9 + 1, 1)
    else:
        raw_score = None
        final_score = None

    return {
        "ticker": ticker,
        "score": final_score,
        "factors": breakdown,
        "total_stocks": len(all_metrics),
    }


def score_momentum(all_metrics: dict[str, dict]) -> dict[str, float | None]:
    """
    Given a dict of {ticker: metrics}, calculate momentum scores (1-10)
    using percentile ranking across all stocks.

    Returns {ticker: score}.
    """
    # Pre-collect all values per factor for ranking
    all_values = {
        key: [m[key] for m in all_metrics.values()]
        for key, _ in FACTORS
    }

    scores = {}
    for ticker, m in all_metrics.items():
        parts = []
        weights = []
        for key, weight in FACTORS:
            rank = percentile_rank(all_values[key], m[key])
            if rank is not None:
                parts.append(rank * weight)
                weights.append(weight)

        if weights:
            raw = sum(parts) / sum(weights)
            scores[ticker] = round(raw * 9 + 1, 1)  # Scale 0-1 → 1-10
        else:
            scores[ticker] = None

    return scores
