"""
Update Valuation tab in Google Sheets with latest yfinance data.
Always reads current ticker order from the sheet and matches by ticker.
"""
import yfinance as yf
import json
import sys
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime

SHEET_ID = "1Ga8z-OJNk7lk5jJK0ZYWPgE_HZBuaXWR-p1rA-2Bn_M"
TAB = "💰 Valuation"
AUTH_SCRIPT = "/Users/nicolai.winch/.claude/plugins/cache/fe-vibe/fe-google-tools/1.2.3/skills/google-auth/resources/google_auth.py"


def get_token():
    result = subprocess.run(["python3", AUTH_SCRIPT, "token"], capture_output=True, text=True)
    return result.stdout.strip()


def read_sheet_tickers(token):
    encoded_range = urllib.parse.quote(f"{TAB}!A2:A200")
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{encoded_range}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "x-goog-user-project": "gcp-sandbox-field-eng",
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return [r[0] for r in data.get("values", []) if r]


def fetch_valuation(tickers):
    results = {}
    total = len(tickers)
    for i, short in enumerate(tickers, 1):
        yf_ticker = short + ".CO"
        try:
            t = yf.Ticker(yf_ticker)
            info = t.info

            trailing_pe = info.get("trailingPE")
            forward_pe = info.get("forwardPE")
            pb = info.get("priceToBook")
            ev_ebitda = info.get("enterpriseToEbitda")
            fcf = info.get("freeCashflow")
            market_cap = info.get("marketCap")
            div_yield = info.get("dividendYield")

            # FCF yield
            fcf_yield = None
            if fcf and market_cap and market_cap > 0:
                fcf_yield = fcf / market_cap * 100

            # Dividend yield normalization
            if div_yield and div_yield > 1:
                pass  # already percentage-ish
            elif div_yield:
                div_yield = div_yield * 100

            # Filter negatives and extremes
            if trailing_pe and trailing_pe < 0:
                trailing_pe = None
            if forward_pe and forward_pe < 0:
                forward_pe = None
            if trailing_pe and trailing_pe > 200:
                trailing_pe = None
            if forward_pe and forward_pe > 200:
                forward_pe = None
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
            print(f"[{i}/{total}] OK: {short}", file=sys.stderr)
        except Exception as e:
            print(f"[{i}/{total}] ERROR: {short} - {e}", file=sys.stderr)
            results[short] = {}
    return results


def percentile_rank_inverted(values, value):
    """Lower value = higher rank (better valuation)"""
    if value is None:
        return None
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    above = sum(1 for v in valid if v > value)
    equal = sum(1 for v in valid if v == value)
    return round((above + equal * 0.5) / len(valid) * 100, 1)


def percentile_rank_normal(values, value):
    if value is None:
        return None
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    below = sum(1 for v in valid if v < value)
    equal = sum(1 for v in valid if v == value)
    return round((below + equal * 0.5) / len(valid) * 100, 1)


def calc_scores(results):
    all_tpe = [r.get("trailing_pe") for r in results.values()]
    all_fpe = [r.get("forward_pe") for r in results.values()]
    all_pb = [r.get("pb") for r in results.values()]
    all_ev = [r.get("ev_ebitda") for r in results.values()]
    all_fcfy = [r.get("fcf_yield") for r in results.values()]
    all_divy = [r.get("div_yield") for r in results.values()]

    for short, r in results.items():
        if not r:
            continue
        p_tpe = percentile_rank_inverted(all_tpe, r.get("trailing_pe"))
        p_fpe = percentile_rank_inverted(all_fpe, r.get("forward_pe"))
        p_pb = percentile_rank_inverted(all_pb, r.get("pb"))
        p_ev = percentile_rank_inverted(all_ev, r.get("ev_ebitda"))
        p_fcfy = percentile_rank_normal(all_fcfy, r.get("fcf_yield"))
        p_divy = percentile_rank_normal(all_divy, r.get("div_yield"))

        r["ranks"] = {
            "trailing_pe": p_tpe, "forward_pe": p_fpe, "pb": p_pb,
            "ev_ebitda": p_ev, "fcf_yield": p_fcfy, "div_yield": p_divy,
        }

        # Score: EV/EBITDA 40%, Forward P/E 30%, FCF Yield 30%
        p_ev_score = p_ev / 100 if p_ev is not None else 0.0
        p_fpe_score = p_fpe / 100 if p_fpe is not None else 0.0
        p_fcfy_score = p_fcfy / 100 if p_fcfy is not None else 0.0

        score_data_count = sum(1 for v in [r.get("ev_ebitda"), r.get("forward_pe"), r.get("fcf_yield")] if v is not None)

        if score_data_count >= 2:
            raw = p_ev_score * 0.40 + p_fpe_score * 0.30 + p_fcfy_score * 0.30
            r["score"] = round(raw * 9 + 1, 1)
        else:
            r["score"] = None


def build_payload(sheet_tickers, results):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = []
    for ticker in sheet_tickers:
        r = results.get(ticker, {})
        ranks = r.get("ranks", {})

        def v(key):
            val = r.get(key)
            return val if val is not None else ""

        def rk(key):
            val = ranks.get(key)
            return val if val is not None else ""

        row = [
            v("trailing_pe"), rk("trailing_pe"),
            v("forward_pe"), rk("forward_pe"),
            v("pb"), rk("pb"),
            v("ev_ebitda"), rk("ev_ebitda"),
            v("fcf_yield"), rk("fcf_yield"),
            v("div_yield"), rk("div_yield"),
            r.get("score", "") if r.get("score") is not None else "",
            timestamp,
        ]
        rows.append(row)

    last_row = len(sheet_tickers) + 1
    return {
        "valueInputOption": "USER_ENTERED",
        "data": [
            {"range": f"{TAB}!F1:S1", "values": [["Trailing P/E", "P/E Rank %", "Forward P/E", "fP/E Rank %", "P/B", "P/B Rank %", "EV/EBITDA", "EV/EBITDA Rank %", "FCF Yield %", "FCF Rank %", "Div Yield %", "Div Rank %", "💰 Valuation Score", "Sidst opdateret"]]},
            {"range": f"{TAB}!F2:S{last_row}", "values": rows},
        ],
    }


def write_to_sheet(token, payload):
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


if __name__ == "__main__":
    print("Getting auth token...", file=sys.stderr)
    token = get_token()

    print("Reading ticker order from sheet...", file=sys.stderr)
    sheet_tickers = read_sheet_tickers(token)
    print(f"Found {len(sheet_tickers)} tickers in sheet", file=sys.stderr)

    print("Fetching valuation data from yfinance...", file=sys.stderr)
    results = fetch_valuation(sheet_tickers)

    print("Calculating scores...", file=sys.stderr)
    calc_scores(results)

    print("Writing to sheet...", file=sys.stderr)
    token = get_token()
    payload = build_payload(sheet_tickers, results)
    result = write_to_sheet(token, payload)
    print(f"Updated {result.get('totalUpdatedCells', 0)} cells", file=sys.stderr)
    print("Done!", file=sys.stderr)
