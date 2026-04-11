"""
Valuation scoring — migrated from calc_valuation.py.

Simplified 3-factor model:
  EV/EBITDA (40%) + Forward P/E (30%) + FCF Yield (30%)

Lower PE/EV = better (inverted rank).
Higher FCF yield = better (normal rank).
Missing data → 0% rank penalty (not skipped).
Need 2+ of 3 factors for a score.
"""


def percentile_rank_inverted(values: list, value):
    """Lower value = higher rank (cheaper = better)."""
    if value is None:
        return None
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    above = sum(1 for v in valid if v > value)
    equal = sum(1 for v in valid if v == value)
    return (above + equal * 0.5) / len(valid)


def percentile_rank_normal(values: list, value):
    """Higher value = higher rank."""
    if value is None:
        return None
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    below = sum(1 for v in valid if v < value)
    equal = sum(1 for v in valid if v == value)
    return (below + equal * 0.5) / len(valid)


def score_valuation(all_fundamentals: dict[str, dict]) -> dict[str, float | None]:
    """
    Given {ticker: fundamentals_dict}, calculate valuation scores (1-10).

    fundamentals_dict must have: forward_pe, ev_ebitda, fcf_yield
    (all optional, but need at least 2 for a score).

    Returns {ticker: score}.
    """
    all_fpe = [f.get("forward_pe") for f in all_fundamentals.values()]
    all_ev = [f.get("ev_ebitda") for f in all_fundamentals.values()]
    all_fcfy = [f.get("fcf_yield") for f in all_fundamentals.values()]

    # Filter out negative/extreme values (same rules as calc_valuation.py)
    all_fpe = [v for v in all_fpe if v is not None and 0 < v <= 200]
    all_ev = [v for v in all_ev if v is not None and v > 0]
    all_fcfy = [v for v in all_fcfy if v is not None]

    scores = {}
    for ticker, f in all_fundamentals.items():
        fpe = f.get("forward_pe")
        ev = f.get("ev_ebitda")
        fcfy = f.get("fcf_yield")

        # Filter same as above
        if fpe is not None and (fpe < 0 or fpe > 200):
            fpe = None
        if ev is not None and ev < 0:
            ev = None

        p_ev = percentile_rank_inverted(all_ev, ev)
        p_fpe = percentile_rank_inverted(all_fpe, fpe)
        p_fcfy = percentile_rank_normal(all_fcfy, fcfy)

        # 0% penalty for missing, not skip
        p_ev_score = p_ev if p_ev is not None else 0.0
        p_fpe_score = p_fpe if p_fpe is not None else 0.0
        p_fcfy_score = p_fcfy if p_fcfy is not None else 0.0

        data_count = sum(1 for v in [ev, fpe, fcfy] if v is not None)

        if data_count >= 2:
            raw = p_ev_score * 0.40 + p_fpe_score * 0.30 + p_fcfy_score * 0.30
            scores[ticker] = round(raw * 9 + 1, 1)
        else:
            scores[ticker] = None

    return scores
