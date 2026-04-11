"""
Update Main tab score columns (W=Momentum, Y=Valuation, Z=Total Score)
by reading scores from Momentum and Valuation tabs, matched by ticker.
"""
import json
import sys
import subprocess
import urllib.request
import urllib.parse

SHEET_ID = "1Ga8z-OJNk7lk5jJK0ZYWPgE_HZBuaXWR-p1rA-2Bn_M"
AUTH_SCRIPT = "/Users/nicolai.winch/.claude/plugins/cache/fe-vibe/fe-google-tools/1.2.3/skills/google-auth/resources/google_auth.py"


def get_token():
    result = subprocess.run(["python3", AUTH_SCRIPT, "token"], capture_output=True, text=True)
    return result.stdout.strip()


def read_sheet(token, range_str):
    encoded_range = urllib.parse.quote(range_str)
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{encoded_range}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "x-goog-user-project": "gcp-sandbox-field-eng",
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data.get("values", [])


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

    # Read tickers and current scores from all tabs
    print("Reading Main tab tickers...", file=sys.stderr)
    main_tickers = read_sheet(token, "Main!A2:A200")
    main_tickers = [r[0] for r in main_tickers if r]

    # Read Momentum scores (ticker in col A, score in col U = index 20 from A)
    # After layout: A=Ticker, F=Kurs, G-T=data, U=Score, V=timestamp
    # Score is in column U (index 15 from F, or column 21 from A = index 20)
    print("Reading Momentum scores...", file=sys.stderr)
    mom_data = read_sheet(token, "📈 Momentum!A2:Z200")
    mom_scores = {}
    for row in mom_data:
        if row:
            ticker = row[0]
            # Score is in column Y = index 24 (A=0, ..., Y=24)
            score = row[24] if len(row) > 24 and row[24] != "" else None
            if score is not None:
                try:
                    mom_scores[ticker] = float(score)
                except ValueError:
                    pass

    # Read Valuation scores (ticker in col A, score in col R = index 17)
    # After layout: A=Ticker, F-R=data, R=Score, S=timestamp
    print("Reading Valuation scores...", file=sys.stderr)
    val_data = read_sheet(token, "💰 Valuation!A2:S200")
    val_scores = {}
    for row in val_data:
        if row:
            ticker = row[0]
            # Score is in column R = index 17 (A=0, ..., R=17)
            score = row[17] if len(row) > 17 and row[17] != "" else None
            if score is not None:
                try:
                    val_scores[ticker] = float(score)
                except ValueError:
                    pass

    # Read Revisions scores from Main tab column X (index 23)
    print("Reading current Revisions scores from Main...", file=sys.stderr)
    main_full = read_sheet(token, "Main!A2:AA200")
    rev_scores = {}
    for row in main_full:
        if row:
            ticker = row[0]
            # Revisions is column X = index 23
            score = row[23] if len(row) > 23 and row[23] != "" else None
            if score is not None:
                try:
                    rev_scores[ticker] = float(score)
                except ValueError:
                    pass

    # Calculate Total Score: Momentum 40% + Revisions 20% + Valuation 40%
    print("Calculating total scores...", file=sys.stderr)
    rows = []
    for ticker in main_tickers:
        mom = mom_scores.get(ticker)
        rev = rev_scores.get(ticker)
        val = val_scores.get(ticker)

        parts = []
        weights = []
        if mom is not None:
            parts.append(mom * 0.40)
            weights.append(0.40)
        if rev is not None:
            parts.append(rev * 0.20)
            weights.append(0.20)
        if val is not None:
            parts.append(val * 0.40)
            weights.append(0.40)

        total = round(sum(parts) / sum(weights), 1) if weights else ""

        # Row: W=Momentum, X=Revisions(skip), Y=Valuation, Z=Total
        rows.append([
            mom if mom is not None else "",
            "",  # Revisions - don't overwrite manual data
            val if val is not None else "",
            total,
        ])

    print(f"Writing scores for {len(rows)} stocks...", file=sys.stderr)
    token = get_token()
    last_row = len(main_tickers) + 1
    payload = {
        "valueInputOption": "USER_ENTERED",
        "data": [
            {"range": f"Main!W2:Z{last_row}", "values": rows},
        ],
    }
    result = write_to_sheet(token, payload)
    print(f"Updated {result.get('totalUpdatedCells', 0)} cells", file=sys.stderr)

    stats = {
        "momentum": len(mom_scores),
        "valuation": len(val_scores),
        "revisions": len(rev_scores),
    }
    print(f"Scores found - Momentum: {stats['momentum']}, Valuation: {stats['valuation']}, Revisions: {stats['revisions']}", file=sys.stderr)
    print("Done!", file=sys.stderr)
