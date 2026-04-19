"""
Revisions scoring — 3-factor model based on analyst EPS estimate changes.

  EPS Revision Ratio 30d (40%) — up/(up+down) for current year
  EPS Trend Change 30d (35%) — % change in consensus EPS vs 30 days ago
  EPS Trend Change 90d (25%) — % change in consensus EPS vs 90 days ago

Higher = better (analysts are upgrading estimates).
Need at least 1 factor with data for a score.
Missing data → 0% rank penalty.
"""


def percentile_rank(values: list, value):
    """Higher value = higher rank."""
    if value is None:
        return None
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    below = sum(1 for v in valid if v < value)
    equal = sum(1 for v in valid if v == value)
    return (below + equal * 0.5) / len(valid)


def fetch_revisions_data(yf_ticker: str) -> dict | None:
    """Fetch EPS revision data from yfinance for a single ticker.
    Returns dict with revision metrics, or None if no data."""
    import yfinance as yf

    try:
        t = yf.Ticker(yf_ticker)

        # eps_revisions: up/down counts over 7d and 30d
        eps_rev = t.eps_revisions
        # eps_trend: consensus EPS now vs 7/30/60/90 days ago
        eps_trend = t.eps_trend

        if eps_rev is None or eps_rev.empty:
            return None
        if eps_trend is None or eps_trend.empty:
            return None

        result = {}

        # --- Factor 1: Revision ratio (30d) for current year ---
        # eps_revisions has rows: 0q, +1q, 0y, +1y
        # We want "0y" (current year)
        if "0y" in eps_rev.index:
            up30 = eps_rev.loc["0y", "upLast30days"]
            down30 = eps_rev.loc["0y", "downLast30days"]
            if up30 is not None and down30 is not None:
                total = up30 + down30
                if total > 0:
                    result["rev_ratio_30d"] = round(up30 / total, 3)
                else:
                    result["rev_ratio_30d"] = None  # No revisions at all
            else:
                result["rev_ratio_30d"] = None
        else:
            result["rev_ratio_30d"] = None

        # --- Factor 2: EPS trend change 30d for current year ---
        if "0y" in eps_trend.index:
            current = eps_trend.loc["0y", "current"]
            ago_30 = eps_trend.loc["0y", "30daysAgo"]
            if current is not None and ago_30 is not None and ago_30 != 0:
                result["eps_change_30d"] = round((current - ago_30) / abs(ago_30) * 100, 2)
            else:
                result["eps_change_30d"] = None
        else:
            result["eps_change_30d"] = None

        # --- Factor 3: EPS trend change 90d for current year ---
        if "0y" in eps_trend.index:
            current = eps_trend.loc["0y", "current"]
            ago_90 = eps_trend.loc["0y", "90daysAgo"]
            if current is not None and ago_90 is not None and ago_90 != 0:
                result["eps_change_90d"] = round((current - ago_90) / abs(ago_90) * 100, 2)
            else:
                result["eps_change_90d"] = None
        else:
            result["eps_change_90d"] = None

        # Count how many analysts cover this stock (for context)
        if "0y" in eps_rev.index:
            result["num_analysts"] = int(
                (eps_rev.loc["0y", "upLast30days"] or 0) +
                (eps_rev.loc["0y", "downLast30days"] or 0)
            )
        else:
            result["num_analysts"] = 0

        return result

    except Exception:
        return None


def score_revisions(all_revisions: dict[str, dict]) -> tuple[dict[str, float | None], dict[str, dict]]:
    """
    Given {ticker: revisions_dict}, calculate revisions scores (1-10).

    Returns (scores_by_ticker, details_by_ticker).
    """
    # Collect all values for percentile ranking
    all_ratio = [r.get("rev_ratio_30d") for r in all_revisions.values()]
    all_change_30 = [r.get("eps_change_30d") for r in all_revisions.values()]
    all_change_90 = [r.get("eps_change_90d") for r in all_revisions.values()]

    # Filter nulls for ranking
    all_ratio = [v for v in all_ratio if v is not None]
    all_change_30 = [v for v in all_change_30 if v is not None]
    all_change_90 = [v for v in all_change_90 if v is not None]

    scores = {}
    details = {}
    for ticker, r in all_revisions.items():
        ratio = r.get("rev_ratio_30d")
        change_30 = r.get("eps_change_30d")
        change_90 = r.get("eps_change_90d")

        p_ratio = percentile_rank(all_ratio, ratio)
        p_change_30 = percentile_rank(all_change_30, change_30)
        p_change_90 = percentile_rank(all_change_90, change_90)

        # 0% penalty for missing
        p_ratio_score = p_ratio if p_ratio is not None else 0.0
        p_change_30_score = p_change_30 if p_change_30 is not None else 0.0
        p_change_90_score = p_change_90 if p_change_90 is not None else 0.0

        data_count = sum(1 for v in [ratio, change_30, change_90] if v is not None)

        if data_count >= 1:
            raw = (p_ratio_score * 0.40 +
                   p_change_30_score * 0.35 +
                   p_change_90_score * 0.25)
            score = round(raw * 9 + 1, 1)
            scores[ticker] = score
        else:
            score = None
            scores[ticker] = None

        details[ticker] = {
            "rev_ratio_30d": ratio,
            "eps_change_30d": change_30,
            "eps_change_90d": change_90,
            "num_analysts": r.get("num_analysts", 0),
            "score": score,
        }

    return scores, details
