"""
Push local DB data to the remote Railway backend.
Use this when yfinance is blocked on the server.

Usage: python push_to_remote.py [URL]
Default URL: https://stock-screener-production-8ae6.up.railway.app
"""

import sys
import json
import sqlite3
import os
import urllib.request

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "stocks.db")
DEFAULT_URL = "https://stock-screener-production-8ae6.up.railway.app"


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("Reading local database...")

    # Prices (last 2 years)
    prices = [dict(r) for r in conn.execute(
        "SELECT ticker, date, open, high, low, close, volume FROM prices"
    ).fetchall()]
    print(f"  Prices: {len(prices)} rows")

    # Fundamentals (latest per ticker)
    fundamentals = [dict(r) for r in conn.execute(
        """SELECT * FROM fundamentals WHERE (ticker, date) IN
           (SELECT ticker, MAX(date) FROM fundamentals GROUP BY ticker)"""
    ).fetchall()]
    print(f"  Fundamentals: {len(fundamentals)} rows")

    # Scores (latest per ticker)
    scores = [dict(r) for r in conn.execute(
        """SELECT * FROM scores WHERE (ticker, date) IN
           (SELECT ticker, MAX(date) FROM scores GROUP BY ticker)"""
    ).fetchall()]
    print(f"  Scores: {len(scores)} rows")

    # Momentum details
    momentum = [dict(r) for r in conn.execute(
        "SELECT * FROM momentum_details"
    ).fetchall()]
    print(f"  Momentum details: {len(momentum)} rows")

    # Valuation details
    valuation = [dict(r) for r in conn.execute(
        "SELECT * FROM valuation_details"
    ).fetchall()]
    print(f"  Valuation details: {len(valuation)} rows")

    conn.close()

    # Push in chunks (prices can be large)
    CHUNK = 5000
    total_pushed = 0

    for i in range(0, len(prices), CHUNK):
        chunk = prices[i:i + CHUNK]
        payload = json.dumps({
            "prices": chunk,
            "fundamentals": fundamentals if i == 0 else [],
            "scores": scores if i == 0 else [],
            "momentum_details": momentum if i == 0 else [],
            "valuation_details": valuation if i == 0 else [],
        }).encode()

        print(f"Pushing chunk {i // CHUNK + 1} ({len(chunk)} prices)...")
        req = urllib.request.Request(
            f"{url}/api/sync/push",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read().decode())
        total_pushed += result.get("prices", 0)
        print(f"  Done: {result}")

    print(f"\nTotal pushed: {total_pushed} prices to {url}")


if __name__ == "__main__":
    main()
