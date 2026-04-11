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
        hist = t.history(period="1y", auto_adjust=False)
        if len(hist) < 10:
            print(f"[{i}/{total}] SKIP: {short} (no data)", file=sys.stderr)
            results[short] = {"m1w": None, "m1": None, "m3": None, "m6": None, "vs_ma200": None, "vs_ma50": None, "drawdown_1m": None}
            continue

        current = hist["Close"].iloc[-1]

        m1w = ((current - hist["Close"].iloc[-5]) / hist["Close"].iloc[-5] * 100) if len(hist) > 5 else None
        m1 = ((current - hist["Close"].iloc[-21]) / hist["Close"].iloc[-21] * 100) if len(hist) > 21 else None
        m3 = ((current - hist["Close"].iloc[-63]) / hist["Close"].iloc[-63] * 100) if len(hist) > 63 else None
        m6 = ((current - hist["Close"].iloc[-126]) / hist["Close"].iloc[-126] * 100) if len(hist) > 126 else None

        vs_ma200 = None
        if len(hist) >= 200:
            ma200 = hist["Close"].iloc[-200:].mean()
            vs_ma200 = (current - ma200) / ma200 * 100

        vs_ma50 = None
        if len(hist) >= 50:
            ma50 = hist["Close"].iloc[-50:].mean()
            vs_ma50 = (current - ma50) / ma50 * 100

        # Drawdown from 1-month high (negative = how far below peak)
        drawdown_1m = None
        if len(hist) > 21:
            high_1m = hist["Close"].iloc[-21:].max()
            drawdown_1m = (current - high_1m) / high_1m * 100

        results[short] = {
            "m1w": round(m1w, 1) if m1w is not None else None,
            "m1": round(m1, 1) if m1 is not None else None,
            "m3": round(m3, 1) if m3 is not None else None,
            "m6": round(m6, 1) if m6 is not None else None,
            "vs_ma200": round(vs_ma200, 1) if vs_ma200 is not None else None,
            "vs_ma50": round(vs_ma50, 1) if vs_ma50 is not None else None,
            "drawdown_1m": round(drawdown_1m, 1) if drawdown_1m is not None else None,
        }
        print(f"[{i}/{total}] OK: {short} | 1W:{results[short]['m1w']}% 1M:{results[short]['m1']}% 3M:{results[short]['m3']}% DD:{results[short]['drawdown_1m']}%", file=sys.stderr)
    except Exception as e:
        print(f"[{i}/{total}] ERROR: {short} - {e}", file=sys.stderr)
        results[short] = {"m1w": None, "m1": None, "m3": None, "m6": None, "vs_ma200": None, "vs_ma50": None, "drawdown_1m": None}

# Now calculate momentum score (1-10) based on percentile ranking
# Composite: 1W (10%) + 1M (15%) + 3M (25%) + 6M (25%) + vs_ma200 (15%) + vs_ma50 (10%) + drawdown (10%, inverted: less negative = better but uses normal rank since values are negative)
import statistics

def percentile_rank(values, value):
    """Rank value among values, return 0-1"""
    if value is None:
        return None
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    below = sum(1 for v in valid if v < value)
    equal = sum(1 for v in valid if v == value)
    return (below + equal * 0.5) / len(valid)

# Collect all values for each metric
all_m1w = [r["m1w"] for r in results.values()]
all_m1 = [r["m1"] for r in results.values()]
all_m3 = [r["m3"] for r in results.values()]
all_m6 = [r["m6"] for r in results.values()]
all_ma200 = [r["vs_ma200"] for r in results.values()]
all_ma50 = [r["vs_ma50"] for r in results.values()]
all_dd = [r["drawdown_1m"] for r in results.values()]

# Calculate scores
scores = {}
for short, r in results.items():
    p_m1w = percentile_rank(all_m1w, r["m1w"])
    p_m1 = percentile_rank(all_m1, r["m1"])
    p_m3 = percentile_rank(all_m3, r["m3"])
    p_m6 = percentile_rank(all_m6, r["m6"])
    p_ma200 = percentile_rank(all_ma200, r["vs_ma200"])
    p_ma50 = percentile_rank(all_ma50, r["vs_ma50"])
    # Drawdown: higher (less negative) = better, so normal rank works
    p_dd = percentile_rank(all_dd, r["drawdown_1m"])

    components = [
        (p_m1w, 0.10),
        (p_m1, 0.15),
        (p_m3, 0.25),
        (p_m6, 0.25),
        (p_ma200, 0.15),
        (p_ma50, 0.10),
        (p_dd, 0.10),
    ]

    parts = []
    weights = []
    for p, w in components:
        if p is not None:
            parts.append(p * w)
            weights.append(w)

    if weights:
        raw = sum(parts) / sum(weights)
        score = round(raw * 9 + 1, 1)  # Scale to 1-10
    else:
        score = None

    scores[short] = {
        "m1w": r["m1w"],
        "m1": r["m1"],
        "m3": r["m3"],
        "m6": r["m6"],
        "vs_ma200": r["vs_ma200"],
        "vs_ma50": r["vs_ma50"],
        "drawdown_1m": r["drawdown_1m"],
        "score": score,
    }

# Output ordered by sheet order
sheet_order = [s.replace(".CO", "") for s in stocks]
output = []
for short in sheet_order:
    s = scores.get(short, {})
    output.append({
        "ticker": short,
        "m1w": s.get("m1w"),
        "m1": s.get("m1"),
        "m3": s.get("m3"),
        "m6": s.get("m6"),
        "vs_ma200": s.get("vs_ma200"),
        "vs_ma50": s.get("vs_ma50"),
        "drawdown_1m": s.get("drawdown_1m"),
        "score": s.get("score"),
    })

print(json.dumps(output))
