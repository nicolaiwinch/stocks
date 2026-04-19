"""Push sector/industry data to production."""

import sys
import json
import urllib.request

sys.path.insert(0, "api")
from config import STORAGE

API_URL = "https://stock-screener-production-8ae6.up.railway.app"

stocks = STORAGE.get_stocks()
industries = [
    {"ticker": s["ticker"], "industry": s["industry"]}
    for s in stocks if s.get("industry")
]

print(f"Pushing {len(industries)} stock industries to production...")

payload = json.dumps({
    "prices": [],
    "fundamentals": [],
    "scores": [],
    "momentum_details": [],
    "valuation_details": [],
    "revisions_details": [],
    "stock_industries": industries,
}).encode()

req = urllib.request.Request(
    f"{API_URL}/api/sync/push",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)

resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
print(f"Result: {json.dumps(result, indent=2)}")
