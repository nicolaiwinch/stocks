import json

data = json.load(open('/tmp/main_all.json'))
rows = data.get('values', [])

# Weights: Momentum 40% + Revisions(proxy) 20% + Valuation 40%
total_scores = []
for row in rows:
    mom = float(row[22]) if len(row) > 22 and row[22] != '' else None
    rev = float(row[23]) if len(row) > 23 and row[23] != '' else None
    val = float(row[24]) if len(row) > 24 and row[24] != '' else None

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

    if weights:
        score = round(sum(parts) / sum(weights), 1)
    else:
        score = ''
    total_scores.append([score])

print(json.dumps({'values': total_scores}))
