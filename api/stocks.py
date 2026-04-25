"""
Master list of Danish stocks tracked by the app.
Single source of truth for ticker mapping and segments.
"""

STOCKS = {
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
    # Watchlist (non-Danish)
    "TSM": ("Taiwan Semiconductor", "Watchlist"),
}


def ticker_short(yf_ticker: str) -> str:
    """MAERSK-B.CO → MAERSK-B"""
    return yf_ticker.replace(".CO", "")


def all_tickers() -> list[str]:
    """All Yahoo Finance tickers."""
    return list(STOCKS.keys())


def all_short_tickers() -> list[str]:
    """All short tickers (without .CO)."""
    return [ticker_short(t) for t in STOCKS]


def stock_info(yf_ticker: str) -> tuple[str, str, str]:
    """Returns (short_ticker, name, segment)."""
    name, segment = STOCKS[yf_ticker]
    return ticker_short(yf_ticker), name, segment
