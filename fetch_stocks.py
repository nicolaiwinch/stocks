import yfinance as yf
import json

# C25 tickers - Yahoo Finance uses .CO suffix for Copenhagen
tickers_map = {
    "DSV.CO": "DSV",
    "NOVO-B.CO": "NOVO-B",
    "DANSKE.CO": "DANSKE",
    "VWS.CO": "VWS",
    "NSIS-B.CO": "NSIS",
    "GMAB.CO": "GMAB",
    "COLO-B.CO": "COLO-B",
    "ORSTED.CO": "ORSTED",
    "MAERSK-B.CO": "MAERSK-B",
    "MAERSK-A.CO": "MAERSK-A",
    "TRYG.CO": "TRYG",
    "NKT.CO": "NKT",
    "JYSK.CO": "JYSK",
    "PNDORA.CO": "PNDORA",
    "RILBA.CO": "RILBA",
    "NDA-DK.CO": "NDAFI",
    "ISS.CO": "ISS",
    "SYDB.CO": "SYDB",
    "ZEAL.CO": "ZEAL",
    "FLS.CO": "FLS",
    "ROCK-B.CO": "ROCK-B",
    "DEMANT.CO": "DEMANT",
    "BAVA.CO": "BAVA",
    "AMBU-B.CO": "AMBU",
    "GN.CO": "GN",
}

results = []

for yf_ticker, sheet_ticker in tickers_map.items():
    try:
        t = yf.Ticker(yf_ticker)
        info = t.info

        # Basic
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        market_cap = info.get("marketCap")
        eps = info.get("trailingEps")
        pe = info.get("trailingPE")
        pb = info.get("priceToBook")
        roe = info.get("returnOnEquity")
        ebit_margin = info.get("operatingMargins")
        net_margin = info.get("profitMargins")
        debt_equity = info.get("debtToEquity")

        # Interest coverage - not directly available, skip if missing
        interest_coverage = None
        total_debt = info.get("totalDebt")
        interest_expense = info.get("interestExpense")
        ebit = info.get("ebitda")  # approximation
        if interest_expense and ebit and interest_expense != 0:
            interest_coverage = round(abs(ebit / interest_expense), 2)

        fcf = info.get("freeCashflow")

        # FCF yield
        fcf_yield = None
        if fcf and market_cap and market_cap > 0:
            fcf_yield = fcf / market_cap

        dividend = info.get("dividendRate")
        div_yield = info.get("dividendYield")
        payout = info.get("payoutRatio")

        # Buybacks - not directly in yfinance, use share repurchase if available
        buybacks = info.get("shareRepurchase")

        # Total shareholder return 5yr - not directly available
        # We can approximate from 5yr price change + dividends
        tsr_5y = None
        try:
            hist = t.history(period="5y")
            if len(hist) > 0:
                start_price = hist["Close"].iloc[0]
                end_price = hist["Close"].iloc[-1]
                if start_price > 0:
                    price_return = (end_price - start_price) / start_price
                    tsr_5y = price_return  # simplified, doesn't include reinvested dividends
        except:
            pass

        def fmt_pct(v):
            if v is None:
                return ""
            return f"{v * 100:.1f}%"

        def fmt_num(v):
            if v is None:
                return ""
            if abs(v) >= 1e9:
                return f"{v / 1e9:.1f} mia"
            if abs(v) >= 1e6:
                return f"{v / 1e6:.0f} mio"
            return f"{v:.2f}"

        row = [
            sheet_ticker,
            info.get("shortName", ""),
            "",  # Segment (not in this script)
            "",  # Industri (manual)
            "",  # Produkt (manual)
            f"{price:.2f}" if price else "",
            fmt_num(market_cap),
            f"{eps:.2f}" if eps else "",
            f"{pe:.1f}" if pe else "",
            f"{pb:.2f}" if pb else "",
            fmt_pct(roe),
            fmt_pct(ebit_margin),
            fmt_pct(net_margin),
            f"{debt_equity:.1f}" if debt_equity else "",
            f"{interest_coverage}" if interest_coverage else "",
            fmt_num(fcf),
            fmt_pct(fcf_yield),
            f"{dividend:.2f}" if dividend else "",
            fmt_pct(div_yield),
            fmt_pct(payout),
            fmt_num(buybacks) if buybacks else "",
            fmt_pct(tsr_5y),
        ]
        results.append(row)
        print(f"OK: {sheet_ticker}")
    except Exception as e:
        print(f"ERROR: {sheet_ticker} - {e}")
        results.append([sheet_ticker, "", "", "", ""] + [""] * 17)

# Output as JSON for use in curl
print("\n---JSON---")
print(json.dumps(results))
