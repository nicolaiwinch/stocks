---
name: deep-dive
description: Run a deep investment analysis on a stock candidate from the screener
user_invocable: true
args: ticker
---

# Deep Dive Investment Analysis

You are acting as an investment research analyst. The user has identified a stock candidate from their Danish stock screener and wants a thorough analysis before investing.

## Step 1: Collect data

Run the data collector script to gather all available data:

```bash
source .venv/bin/activate && python api/deep_dive.py ${ticker}
```

If the venv doesn't exist, create it first: `python3 -m venv .venv && source .venv/bin/activate && pip install yfinance -q`

## Step 2: Analyze and write the report

Using the JSON output, write a structured deep dive report with these sections:

### Report structure

**1. Company Overview**
- What does the company do? (use the business summary)
- Sector, industry, number of employees
- One-line thesis: why might this be interesting?

**2. Screener Score & Ranking**
- Where does it rank among all tracked stocks?
- Momentum score breakdown (6M, 12M, 12M-1M, vs MA200, MA50 vs MA200)
- What the momentum tells us about the trend

**3. Valuation Check**
- PE (trailing & forward), P/B, P/S, EV/EBITDA
- Is it expensive relative to earnings growth?
- Compare to sector norms where possible

**4. Financial Health**
- Balance sheet: cash, debt, debt/equity, current ratio
- Profitability: margins (operating, net, EBITDA)
- Cash flow: FCF positive or negative? Why?
- ROE and ROA

**5. Growth Profile**
- Revenue growth trend
- Earnings growth
- EPS trajectory (trailing vs forward)
- What's driving growth?

**6. Analyst Consensus**
- Number of analysts covering
- Price targets: low, median, mean, high
- Current price vs median target — upside/downside?

**7. Peer Comparison**
- How does it score vs C25/segment peers?
- Which peers are closest competitors?

**8. Risk Flags**
- Identify any red flags: negative FCF, extreme valuation, high audit risk, revenue decline, etc.
- Price near 52-week high (momentum risk)
- Beta and volatility context

**9. Bull vs Bear Case**
- 3 bullet points for the bull case
- 3 bullet points for the bear case

**10. Verdict**
- Overall assessment: Strong Buy / Buy / Hold / Cautious
- Key thing to watch before entering

## Step 3: Save the report

After writing the report, save it to the app so it appears on the Reports page.
Use curl to POST to the API:

```bash
curl -s -X POST http://localhost:8000/api/reports/ \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TICKER", "report_html": "<THE FULL REPORT AS HTML>", "summary": {"verdict": "...", "score": ..., "rank": ..., "rank_total": ..., "price": ..., "currency": "DKK"}}'
```

Format the report as HTML using these CSS classes for styling:
- Wrap tables in `class="report-table"`
- Use `class="score-high"` (green), `class="score-mid"` (yellow), `class="score-low"` (red) for colored values
- Wrap the verdict in `<div class="verdict verdict-cautious">` (or verdict-buy, verdict-strong-buy, verdict-hold)
- Bull/bear section: `<div class="bull-bear"><div class="bull">...</div><div class="bear">...</div></div>`
- Use `class="report-date"` on the date paragraph
- Use `class="report-note"` for the closing disclaimer

Tell the user the report has been saved and is now visible on the Reports page in the app.

## Important notes
- Be honest about risks — this is real money
- Flag data gaps (e.g., missing valuation/revisions scores)
- Use DKK for all price references
- Keep it concise but thorough — no fluff
