import yfinance as yf
import json
import sys

# All Danish stocks organized by category
stocks = {
    # C25
    "MAERSK-A.CO": ("A.P. Møller - Mærsk A", "C25"),
    "MAERSK-B.CO": ("A.P. Møller - Mærsk B", "C25"),
    "AMBU-B.CO": ("Ambu B", "C25"),
    "BAVA.CO": ("Bavarian Nordic", "C25"),
    "CARL-B.CO": ("Carlsberg B", "C25"),
    "COLO-B.CO": ("Coloplast B", "C25"),
    "DANSKE.CO": ("Danske Bank", "C25"),
    "DEMANT.CO": ("Demant", "C25"),
    "DSV.CO": ("DSV", "C25"),
    "GMAB.CO": ("Genmab", "C25"),
    "GN.CO": ("GN Store Nord", "C25"),
    "ISS.CO": ("ISS", "C25"),
    "JYSK.CO": ("Jyske Bank", "C25"),
    "NKT.CO": ("NKT", "C25"),
    "NDA-DK.CO": ("Nordea Bank (DK)", "C25"),
    "NOVO-B.CO": ("Novo Nordisk B", "C25"),
    "NSIS-B.CO": ("Novonesis (Novozymes)", "C25"),
    "PNDORA.CO": ("Pandora", "C25"),
    "ROCK-B.CO": ("Rockwool B", "C25"),
    "RBREW.CO": ("Royal Unibrew", "C25"),
    "TRMD-A.CO": ("TORM plc", "C25"),
    "TRYG.CO": ("Tryg", "C25"),
    "VWS.CO": ("Vestas Wind Systems", "C25"),
    "ZEAL.CO": ("Zealand Pharma", "C25"),
    "ORSTED.CO": ("Ørsted", "C25"),
    # Large Cap
    "ALK-B.CO": ("ALK-Abelló B", "Large Cap"),
    "ALMB.CO": ("Alm. Brand", "Large Cap"),
    "DNORD.CO": ("D/S Norden", "Large Cap"),
    "DFDS.CO": ("DFDS", "Large Cap"),
    "FLS.CO": ("FLSmidth & Co.", "Large Cap"),
    "HLUN-B.CO": ("H. Lundbeck B", "Large Cap"),
    "NETC.CO": ("Netcompany Group", "Large Cap"),
    "RILBA.CO": ("Ringkjøbing Landbobank", "Large Cap"),
    "SCHO.CO": ("Schouw & Co.", "Large Cap"),
    "SPNO.CO": ("Spar Nord Bank", "Large Cap"),
    "SYDB.CO": ("Sydbank", "Large Cap"),
    "TOP.CO": ("Topdanmark", "Large Cap"),
    # Mid Cap
    "BO.CO": ("Bang & Olufsen", "Mid Cap"),
    "BORD.CO": ("Bording Group", "Mid Cap"),
    "CBRAIN.CO": ("cBrain", "Mid Cap"),
    "CHEMM.CO": ("ChemoMetec", "Mid Cap"),
    "JEUDAN.CO": ("Jeudan", "Mid Cap"),
    "MATAS.CO": ("Matas", "Mid Cap"),
    "MTHH.CO": ("MT Højgaard Holding", "Mid Cap"),
    "NLFSK.CO": ("Nilfisk Holding", "Mid Cap"),
    "NTG.CO": ("NTG (Nordic Transport Group)", "Mid Cap"),
    "PAAL-B.CO": ("Per Aarsleff Holding", "Mid Cap"),
    "SOLAR-B.CO": ("Solar B", "Mid Cap"),
    "SPZ.CO": ("Sparekassen Sjælland-Fyn", "Mid Cap"),
    "UIE.CO": ("United International Enterprises", "Mid Cap"),
    # Small Cap
    "AAB.CO": ("AaB (Aalborg Boldspilklub)", "Small Cap"),
    "AGAT.CO": ("Agat Ejendomme", "Small Cap"),
    "AQP.CO": ("Aquaporin", "Small Cap"),
    "AOJ-B.CO": ("Brdr. A&O Johansen", "Small Cap"),
    "FED.CO": ("Fast Ejendom Danmark", "Small Cap"),
    "GABR.CO": ("Gabriel Holding", "Small Cap"),
    "GJ.CO": ("Glunz & Jensen", "Small Cap"),
    "GREENH.CO": ("Green Hydrogen Systems", "Small Cap"),
    "GRLA.CO": ("GrønlandsBANKEN", "Small Cap"),
    "LASP.CO": ("Lån & Spar Bank", "Small Cap"),
    "NORTHM.CO": ("North Media", "Small Cap"),
    "PARKEN.CO": ("Parken Sport & Entertainment", "Small Cap"),
    "RTX.CO": ("RTX", "Small Cap"),
    "SKAKO.CO": ("SKAKO", "Small Cap"),
    "TIV.CO": ("Tivoli", "Small Cap"),
}

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

results = []
total = len(stocks)

for i, (yf_ticker, (name, category)) in enumerate(stocks.items(), 1):
    ticker_short = yf_ticker.replace(".CO", "")
    try:
        t = yf.Ticker(yf_ticker)
        info = t.info

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        market_cap = info.get("marketCap")
        eps = info.get("trailingEps")
        pe = info.get("trailingPE")
        pb = info.get("priceToBook")
        roe = info.get("returnOnEquity")
        ebit_margin = info.get("operatingMargins")
        net_margin = info.get("profitMargins")
        debt_equity = info.get("debtToEquity")

        # Interest coverage approximation
        interest_coverage = None
        interest_expense = info.get("interestExpense")
        ebit = info.get("ebitda")
        if interest_expense and ebit and interest_expense != 0:
            interest_coverage = round(abs(ebit / interest_expense), 2)

        fcf = info.get("freeCashflow")
        fcf_yield = None
        if fcf and market_cap and market_cap > 0:
            fcf_yield = fcf / market_cap

        dividend = info.get("dividendRate")
        div_yield = info.get("dividendYield")
        payout = info.get("payoutRatio")
        buybacks = info.get("shareRepurchase")

        # TSR 5yr approximation
        tsr_5y = None
        try:
            hist = t.history(period="5y")
            if len(hist) > 0:
                start_price = hist["Close"].iloc[0]
                end_price = hist["Close"].iloc[-1]
                if start_price > 0:
                    tsr_5y = (end_price - start_price) / start_price
        except:
            pass

        row = [
            ticker_short,
            name,
            category,
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
        print(f"[{i}/{total}] OK: {ticker_short}", file=sys.stderr)
    except Exception as e:
        print(f"[{i}/{total}] ERROR: {ticker_short} - {e}", file=sys.stderr)
        results.append([ticker_short, name, category, "", ""] + [""] * 17)

# Output JSON to stdout
print(json.dumps(results))
