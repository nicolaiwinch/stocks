import yfinance as yf
import json
import sys

stocks = [
    "MAERSK-A.CO", "MAERSK-B.CO", "AMBU-B.CO", "BAVA.CO", "CARL-B.CO",
    "COLO-B.CO", "DANSKE.CO", "DEMANT.CO", "DSV.CO", "GMAB.CO",
    "GN.CO", "ISS.CO", "JYSK.CO", "NKT.CO", "NDA-DK.CO",
    "NOVO-B.CO", "NSIS-B.CO", "PNDORA.CO", "ROCK-B.CO", "RBREW.CO",
    "TRMD-A.CO", "TRYG.CO", "VWS.CO", "ZEAL.CO", "ORSTED.CO",
    "ALK-B.CO", "ALMB.CO", "DNORD.CO", "DFDS.CO", "FLS.CO",
    "HLUN-B.CO", "NETC.CO", "RILBA.CO", "SCHO.CO", "SPNO.CO",
    "SYDB.CO", "TOP.CO",
    "BO.CO", "BORD.CO", "CBRAIN.CO", "CHEMM.CO", "JEUDAN.CO",
    "MATAS.CO", "MTHH.CO", "NLFSK.CO", "NTG.CO", "PAAL-B.CO",
    "SOLAR-B.CO", "SPZ.CO", "UIE.CO",
    "AAB.CO", "AGAT.CO", "AQP.CO", "AOJ-B.CO", "FED.CO",
    "GABR.CO", "GJ.CO", "GREENH.CO", "GRLA.CO", "LASP.CO",
    "NORTHM.CO", "PARKEN.CO", "RTX.CO", "SKAKO.CO", "TIV.CO",
]

results = {}
total = len(stocks)

for i, ticker in enumerate(stocks, 1):
    short = ticker.replace(".CO", "")
    try:
        t = yf.Ticker(ticker)
        info = t.info

        trailing_pe = info.get("trailingPE")
        forward_pe = info.get("forwardPE")
        pb = info.get("priceToBook")
        ev_ebitda = info.get("enterpriseToEbitda")
        fcf = info.get("freeCashflow")
        market_cap = info.get("marketCap")
        div_yield = info.get("dividendYield")

        # FCF yield (calculated)
        fcf_yield = None
        if fcf and market_cap and market_cap > 0:
            fcf_yield = fcf / market_cap * 100  # as percentage

        # Dividend yield - yfinance returns as decimal (e.g. 6.7 for 6.7%)
        # but sometimes it's already percentage, normalize
        if div_yield and div_yield > 1:
            div_yield = div_yield  # already percentage-ish
        elif div_yield:
            div_yield = div_yield * 100

        # Filter out negative PE (not meaningful for valuation ranking)
        if trailing_pe and trailing_pe < 0:
            trailing_pe = None
        if forward_pe and forward_pe < 0:
            forward_pe = None
        # Filter extreme PE (>200 likely data error)
        if trailing_pe and trailing_pe > 200:
            trailing_pe = None
        if forward_pe and forward_pe > 200:
            forward_pe = None
        # Filter negative EV/EBITDA
        if ev_ebitda and ev_ebitda < 0:
            ev_ebitda = None

        results[short] = {
            "trailing_pe": round(trailing_pe, 1) if trailing_pe else None,
            "forward_pe": round(forward_pe, 1) if forward_pe else None,
            "pb": round(pb, 2) if pb else None,
            "ev_ebitda": round(ev_ebitda, 1) if ev_ebitda else None,
            "fcf_yield": round(fcf_yield, 1) if fcf_yield else None,
            "div_yield": round(div_yield, 1) if div_yield else None,
        }
        print(f"[{i}/{total}] OK: {short} | PE:{trailing_pe} fPE:{forward_pe} P/B:{pb} EV/EBITDA:{ev_ebitda} FCFy:{fcf_yield}", file=sys.stderr)
    except Exception as e:
        print(f"[{i}/{total}] ERROR: {short} - {e}", file=sys.stderr)
        results[short] = {"trailing_pe": None, "forward_pe": None, "pb": None, "ev_ebitda": None, "fcf_yield": None, "div_yield": None}


# Percentile ranking — for valuation, LOWER = CHEAPER = BETTER
# So we INVERT the rank: lowest PE gets highest score
def percentile_rank_inverted(values, value):
    """Lower value = higher rank (better valuation)"""
    if value is None:
        return None
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    above = sum(1 for v in valid if v > value)
    equal = sum(1 for v in valid if v == value)
    return (above + equal * 0.5) / len(valid)

# For FCF yield and div yield: HIGHER = BETTER (not inverted)
def percentile_rank_normal(values, value):
    if value is None:
        return None
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    below = sum(1 for v in valid if v < value)
    equal = sum(1 for v in valid if v == value)
    return (below + equal * 0.5) / len(valid)

all_tpe = [r["trailing_pe"] for r in results.values()]
all_fpe = [r["forward_pe"] for r in results.values()]
all_pb = [r["pb"] for r in results.values()]
all_ev = [r["ev_ebitda"] for r in results.values()]
all_fcfy = [r["fcf_yield"] for r in results.values()]
all_divy = [r["div_yield"] for r in results.values()]

scores = {}
for short, r in results.items():
    p_tpe = percentile_rank_inverted(all_tpe, r["trailing_pe"])
    p_fpe = percentile_rank_inverted(all_fpe, r["forward_pe"])
    p_pb = percentile_rank_inverted(all_pb, r["pb"])
    p_ev = percentile_rank_inverted(all_ev, r["ev_ebitda"])
    p_fcfy = percentile_rank_normal(all_fcfy, r["fcf_yield"])
    p_divy = percentile_rank_normal(all_divy, r["div_yield"])

    # Simplified model: 3 factors only
    # EV/EBITDA 40%, Forward P/E 30%, FCF Yield 30%
    #
    # Missing data rules:
    # - Negative EPS → forward_pe is None → rank 0% (penalty, not skip)
    # - Negative EV/EBITDA → ev_ebitda is None → rank 0% (penalty, not skip)
    # - Missing 2+ of 3 factors → no score
    # - Missing 1 factor → redistribute weight (still 2 of 3)

    # Apply rank 0% penalty for missing score factors (not just skip)
    p_ev_score = p_ev if p_ev is not None else 0.0
    p_fpe_score = p_fpe if p_fpe is not None else 0.0
    p_fcfy_score = p_fcfy if p_fcfy is not None else 0.0

    # Count how many of the 3 score factors have real data
    score_data_count = sum(1 for v in [r["ev_ebitda"], r["forward_pe"], r["fcf_yield"]] if v is not None)

    if score_data_count >= 2:
        # Use all 3, with 0% penalty for missing ones
        components = [
            (p_ev_score, 0.40),
            (p_fpe_score, 0.30),
            (p_fcfy_score, 0.30),
        ]
        raw = sum(p * w for p, w in components)
        score = round(raw * 9 + 1, 1)
    else:
        score = None

    scores[short] = {
        **r,
        "p_tpe": round(p_tpe * 100, 1) if p_tpe is not None else None,
        "p_fpe": round(p_fpe * 100, 1) if p_fpe is not None else None,
        "p_pb": round(p_pb * 100, 1) if p_pb is not None else None,
        "p_ev": round(p_ev * 100, 1) if p_ev is not None else None,
        "p_fcfy": round(p_fcfy * 100, 1) if p_fcfy is not None else None,
        "p_divy": round(p_divy * 100, 1) if p_divy is not None else None,
        "score": score,
    }

print(json.dumps(scores))
