"""
Update Momentum tab in Google Sheets with latest yfinance data.
Always reads current ticker order from the sheet and matches by ticker.
"""
import yfinance as yf
import json
import sys
import subprocess
from datetime import datetime

SHEET_ID = "1Ga8z-OJNk7lk5jJK0ZYWPgE_HZBuaXWR-p1rA-2Bn_M"
TAB = "📈 Momentum"
AUTH_SCRIPT = "/Users/nicolai.winch/.claude/plugins/cache/fe-vibe/fe-google-tools/1.2.3/skills/google-auth/resources/google_auth.py"

# --- Step 1: Get access token ---
def get_token():
    result = subprocess.run(["python3", AUTH_SCRIPT, "token"], capture_output=True, text=True)
    return result.stdout.strip()

# --- Step 2: Read current ticker order from sheet ---
def read_sheet_tickers(token):
    import urllib.request
    import urllib.parse
    encoded_range = urllib.parse.quote(f"{TAB}!A2:A200")
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{encoded_range}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "x-goog-user-project": "gcp-sandbox-field-eng",
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return [r[0] for r in data.get("values", []) if r]

# --- Step 3: Fetch momentum data from yfinance ---
def fetch_momentum(tickers):
    results = {}
    total = len(tickers)
    for i, short in enumerate(tickers, 1):
        yf_ticker = short + ".CO"
        try:
            t = yf.Ticker(yf_ticker)
            hist = t.history(period="1y", auto_adjust=False)
            if len(hist) < 10:
                print(f"[{i}/{total}] SKIP: {short} (no data)", file=sys.stderr)
                results[short] = {}
                continue

            current = float(hist["Close"].iloc[-1])

            m1w = ((current - hist["Close"].iloc[-5]) / hist["Close"].iloc[-5] * 100) if len(hist) > 5 else None
            m1 = ((current - hist["Close"].iloc[-21]) / hist["Close"].iloc[-21] * 100) if len(hist) > 21 else None
            m3 = ((current - hist["Close"].iloc[-63]) / hist["Close"].iloc[-63] * 100) if len(hist) > 63 else None
            m6 = ((current - hist["Close"].iloc[-126]) / hist["Close"].iloc[-126] * 100) if len(hist) > 126 else None
            m200d = ((current - hist["Close"].iloc[-200]) / hist["Close"].iloc[-200] * 100) if len(hist) >= 200 else None

            vs_ma200 = None
            if len(hist) >= 200:
                ma200 = float(hist["Close"].iloc[-200:].mean())
                vs_ma200 = (current - ma200) / ma200 * 100

            m50d = ((current - hist["Close"].iloc[-50]) / hist["Close"].iloc[-50] * 100) if len(hist) >= 50 else None

            vs_ma50 = None
            if len(hist) >= 50:
                ma50 = float(hist["Close"].iloc[-50:].mean())
                vs_ma50 = (current - ma50) / ma50 * 100

            drawdown_1m = None
            if len(hist) > 21:
                high_1m = float(hist["Close"].iloc[-21:].max())
                drawdown_1m = (current - high_1m) / high_1m * 100

            results[short] = {
                "price": round(current, 2),
                "m1w": round(m1w, 1) if m1w is not None else None,
                "m1": round(m1, 1) if m1 is not None else None,
                "m3": round(m3, 1) if m3 is not None else None,
                "m6": round(m6, 1) if m6 is not None else None,
                "m200d": round(m200d, 1) if m200d is not None else None,
                "vs_ma200": round(vs_ma200, 1) if vs_ma200 is not None else None,
                "m50d": round(m50d, 1) if m50d is not None else None,
                "vs_ma50": round(vs_ma50, 1) if vs_ma50 is not None else None,
                "drawdown_1m": round(drawdown_1m, 1) if drawdown_1m is not None else None,
            }
            print(f"[{i}/{total}] OK: {short} @ {results[short]['price']}", file=sys.stderr)
        except Exception as e:
            print(f"[{i}/{total}] ERROR: {short} - {e}", file=sys.stderr)
            results[short] = {}
    return results

# --- Step 4: Calculate percentile ranks and scores ---
def percentile_rank(values, value):
    if value is None:
        return None
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    below = sum(1 for v in valid if v < value)
    equal = sum(1 for v in valid if v == value)
    return round((below + equal * 0.5) / len(valid) * 100, 1)

def calc_scores(results):
    all_metrics = ["m1w", "m1", "m3", "m6", "m200d", "vs_ma200", "m50d", "vs_ma50", "drawdown_1m"]
    all_vals = {m: [r.get(m) for r in results.values()] for m in all_metrics}
    # m200d has no weight — it's context only, not part of score
    score_metrics = ["m1w", "m1", "m3", "m6", "vs_ma200", "vs_ma50", "drawdown_1m"]
    weights = {"m1w": 0.10, "m1": 0.15, "m3": 0.25, "m6": 0.25, "vs_ma200": 0.15, "vs_ma50": 0.10, "drawdown_1m": 0.10}

    for short, r in results.items():
        if not r:
            continue
        ranks = {}
        for m in all_metrics:
            ranks[m] = percentile_rank(all_vals[m], r.get(m))

        parts = []
        ws = []
        for m in score_metrics:
            if ranks[m] is not None:
                parts.append(ranks[m] / 100 * weights[m])
                ws.append(weights[m])

        r["ranks"] = ranks
        if ws:
            raw = sum(parts) / sum(ws)
            r["score"] = round(raw * 9 + 1, 1)
        else:
            r["score"] = None

# --- Step 5: Build sheet payload matched by ticker ---
def build_payload(sheet_tickers, results):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = []
    for ticker in sheet_tickers:
        r = results.get(ticker, {})
        ranks = r.get("ranks", {})
        def val(key):
            v = r.get(key)
            return v if v is not None else ""
        def rnk(key):
            v = ranks.get(key)
            return v if v is not None else ""

        row = [
            val("price"),
            val("m1w"), rnk("m1w"),
            val("m1"), rnk("m1"),
            val("m3"), rnk("m3"),
            val("m6"), rnk("m6"),
            val("m200d"), rnk("m200d"),
            val("vs_ma200"), rnk("vs_ma200"),
            val("m50d"), rnk("m50d"),
            val("vs_ma50"), rnk("vs_ma50"),
            val("drawdown_1m"), rnk("drawdown_1m"),
            r.get("score", "") if r.get("score") is not None else "",
            timestamp,
        ]
        rows.append(row)

    last_row = len(sheet_tickers) + 1
    return {
        "valueInputOption": "USER_ENTERED",
        "data": [
            {"range": f"{TAB}!F1:Z1", "values": [["Kurs", "1U Afkast %", "1U Rank %", "1M Afkast %", "1M Rank %", "3M Afkast %", "3M Rank %", "6M Afkast %", "6M Rank %", "200d Afkast %", "200d Afk Rank %", "Kurs vs 200d MA %", "vs MA200 Rank %", "50d Afkast %", "50d Afk Rank %", "Kurs vs 50d MA %", "vs MA50 Rank %", "Drawdown 1M %", "DD Rank %", "📈 Momentum Score", "Sidst opdateret"]]},
            {"range": f"{TAB}!F2:Z{last_row}", "values": rows},
        ],
    }

# --- Step 6: Write to sheet ---
def write_to_sheet(token, payload):
    import urllib.request
    import urllib.parse
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values:batchUpdate"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "x-goog-user-project": "gcp-sandbox-field-eng",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    return result

# --- Main ---
if __name__ == "__main__":
    print("Getting auth token...", file=sys.stderr)
    token = get_token()

    print("Reading ticker order from sheet...", file=sys.stderr)
    sheet_tickers = read_sheet_tickers(token)
    print(f"Found {len(sheet_tickers)} tickers in sheet", file=sys.stderr)

    print("Fetching momentum data from yfinance...", file=sys.stderr)
    results = fetch_momentum(sheet_tickers)

    print("Calculating scores...", file=sys.stderr)
    calc_scores(results)

    print("Writing to sheet...", file=sys.stderr)
    token = get_token()  # refresh token in case fetch took long
    payload = build_payload(sheet_tickers, results)
    result = write_to_sheet(token, payload)
    print(f"Updated {result.get('totalUpdatedCells', 0)} cells", file=sys.stderr)
    print("Done!", file=sys.stderr)
