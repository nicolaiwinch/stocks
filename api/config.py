"""
App configuration.
"""

import os
from storage import SqliteStorage

# --- Storage ---
DATA_DIR = os.environ.get("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)
STORAGE = SqliteStorage(os.path.join(DATA_DIR, "stocks.db"))

# --- Seed stocks into DB on startup ---
from stocks import STOCKS, ticker_short
for yf_ticker, (name, segment) in STOCKS.items():
    STORAGE.upsert_stock(ticker_short(yf_ticker), name, segment)

# --- Google Sheets ---
SHEET_ID = "1Ga8z-OJNk7lk5jJK0ZYWPgE_HZBuaXWR-p1rA-2Bn_M"

# --- Score weights ---
MOMENTUM_WEIGHT = 0.40
REVISIONS_WEIGHT = 0.20
VALUATION_WEIGHT = 0.40
