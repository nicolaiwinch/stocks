"""
Google Sheets sync — push score summaries to the existing Google Sheet.

This is a one-way push: app → Google Sheets (the human-readable backup).
Reads manual data (industry, product, revisions) from Sheets.
"""

import json
import subprocess
import urllib.request
import urllib.parse

from config import SHEET_ID

AUTH_SCRIPT = None  # Set at runtime or via env var


def _get_token() -> str:
    """Get OAuth token via the google-auth helper."""
    import os
    script = AUTH_SCRIPT or os.environ.get(
        "GOOGLE_AUTH_SCRIPT",
        os.path.expanduser("~/.claude/plugins/cache/fe-vibe/fe-google-tools/1.2.3/skills/google-auth/resources/google_auth.py")
    )
    result = subprocess.run(["python3", script, "token"], capture_output=True, text=True)
    return result.stdout.strip()


def _sheets_request(token: str, url: str, method: str = "GET",
                    body: dict | None = None) -> dict:
    """Make authenticated request to Sheets API."""
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "x-goog-user-project": "gcp-sandbox-field-eng",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def read_range(token: str, range_str: str) -> list[list[str]]:
    """Read a range from the sheet."""
    encoded = urllib.parse.quote(range_str)
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{encoded}"
    data = _sheets_request(token, url)
    return data.get("values", [])


def write_ranges(token: str, ranges: list[dict]) -> dict:
    """Batch write to multiple ranges."""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values:batchUpdate"
    payload = {
        "valueInputOption": "USER_ENTERED",
        "data": ranges,
    }
    return _sheets_request(token, url, method="POST", body=payload)


def push_scores_to_sheet(storage) -> dict:
    """
    Push latest scores from the database to the Main tab of Google Sheets.
    Matches by ticker (column A).
    """
    token = _get_token()

    # Read tickers from Main tab
    main_tickers = read_range(token, "Main!A2:A200")
    main_tickers = [r[0] for r in main_tickers if r]

    # Get latest scores from database
    scores = storage.get_scores()
    score_map = {s["ticker"]: s for s in scores}

    # Build rows: W=Momentum, X=Revisions(skip), Y=Valuation, Z=Total
    rows = []
    for ticker in main_tickers:
        s = score_map.get(ticker, {})
        rows.append([
            s.get("momentum", ""),
            "",  # Revisions — don't overwrite manual data
            s.get("valuation", ""),
            s.get("total", ""),
        ])

    # Write
    token = _get_token()  # Refresh token
    last_row = len(main_tickers) + 1
    result = write_ranges(token, [
        {"range": f"Main!W2:Z{last_row}", "values": rows},
    ])

    return {"cells_updated": result.get("totalUpdatedCells", 0)}


def read_manual_data(storage) -> dict:
    """
    Read manually-entered data from Google Sheets (industry, product, revisions)
    and store in the database.
    """
    token = _get_token()

    # Read Main tab: A=Ticker, D=Industry, E=Product, X=Revisions
    rows = read_range(token, "Main!A2:AA200")

    updated = 0
    for row in rows:
        if not row:
            continue
        ticker = row[0]
        industry = row[3] if len(row) > 3 and row[3] else None
        product = row[4] if len(row) > 4 and row[4] else None
        revisions = None
        if len(row) > 23 and row[23]:
            try:
                revisions = float(row[23])
            except ValueError:
                pass

        # Update stock with manual fields
        stock = storage.get_stock(ticker)
        if stock:
            storage.upsert_stock(ticker, stock["name"], stock["segment"],
                                 industry=industry, product=product)

            # If we got a revisions score, update it
            if revisions is not None:
                from datetime import date
                storage.upsert_score(
                    ticker, date.today().isoformat(), revisions=revisions
                )
            updated += 1

    return {"stocks_updated": updated}
