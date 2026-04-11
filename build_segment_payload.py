import json

sheet1 = json.load(open('/tmp/seg_main.json'))
mom = json.load(open('/tmp/seg_mom.json'))
val = json.load(open('/tmp/seg_val.json'))
rev = json.load(open('/tmp/seg_rev.json'))

seg_map = {}
for r in sheet1.get('values', []):
    if len(r) >= 3:
        seg_map[r[0]] = r[2]

def build_col(tickers_data):
    vals = [["Segment"]]
    for r in tickers_data.get('values', []):
        ticker = r[0] if r else ''
        vals.append([seg_map.get(ticker, '')])
    return vals

payload = {
    "valueInputOption": "RAW",
    "data": [
        {"range": "\U0001f4c8 Momentum!C1:C66", "values": build_col(mom)},
        {"range": "\U0001f4b0 Valuation!C1:C66", "values": build_col(val)},
        {"range": "\U0001f4c9 Revisions!C1:C66", "values": build_col(rev)}
    ]
}
print(json.dumps(payload))
