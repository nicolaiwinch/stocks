"""
SQLite storage backend.

Single file database — easy to back up, fast for time-series data.
"""

import sqlite3
from datetime import date

from .base import StorageBackend


class SqliteStorage(StorageBackend):

    def __init__(self, db_path: str = "data/stocks.db"):
        self.db_path = db_path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS stocks (
                    ticker TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    segment TEXT NOT NULL,
                    industry TEXT,
                    product TEXT
                );

                CREATE TABLE IF NOT EXISTS prices (
                    ticker TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    PRIMARY KEY (ticker, date)
                );

                CREATE TABLE IF NOT EXISTS fundamentals (
                    ticker TEXT NOT NULL,
                    date TEXT NOT NULL,
                    price REAL,
                    market_cap REAL,
                    trailing_pe REAL,
                    forward_pe REAL,
                    pb REAL,
                    roe REAL,
                    operating_margin REAL,
                    net_margin REAL,
                    debt_equity REAL,
                    ev_ebitda REAL,
                    fcf REAL,
                    fcf_yield REAL,
                    dividend_rate REAL,
                    dividend_yield REAL,
                    payout_ratio REAL,
                    PRIMARY KEY (ticker, date)
                );

                CREATE TABLE IF NOT EXISTS scores (
                    ticker TEXT NOT NULL,
                    date TEXT NOT NULL,
                    momentum REAL,
                    valuation REAL,
                    revisions REAL,
                    total REAL,
                    PRIMARY KEY (ticker, date)
                );

                CREATE TABLE IF NOT EXISTS momentum_details (
                    ticker TEXT PRIMARY KEY,
                    m6 REAL,
                    m12 REAL,
                    m12_1 REAL,
                    vs_ma200 REAL,
                    ma50_vs_ma200 REAL,
                    score REAL,
                    updated TEXT
                );

                CREATE TABLE IF NOT EXISTS valuation_details (
                    ticker TEXT PRIMARY KEY,
                    forward_pe REAL,
                    pb REAL,
                    ev_ebitda REAL,
                    fcf_yield REAL,
                    score REAL,
                    updated TEXT
                );

                CREATE TABLE IF NOT EXISTS revisions_details (
                    ticker TEXT PRIMARY KEY,
                    rev_ratio_30d REAL,
                    eps_change_30d REAL,
                    eps_change_90d REAL,
                    num_analysts INTEGER,
                    score REAL,
                    updated TEXT
                );

                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    prices_rows INTEGER,
                    scores_calculated INTEGER
                );

                CREATE INDEX IF NOT EXISTS idx_prices_ticker_date
                    ON prices (ticker, date);
                CREATE INDEX IF NOT EXISTS idx_scores_date
                    ON scores (date);
            """)

    # --- Stocks ---

    def upsert_stock(self, ticker: str, name: str, segment: str,
                     industry: str | None = None, product: str | None = None) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO stocks (ticker, name, segment, industry, product)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(ticker) DO UPDATE SET
                    name=excluded.name, segment=excluded.segment,
                    industry=COALESCE(excluded.industry, stocks.industry),
                    product=COALESCE(excluded.product, stocks.product)
            """, (ticker, name, segment, industry, product))

    def get_stocks(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM stocks ORDER BY segment, ticker").fetchall()
            return [dict(r) for r in rows]

    def get_stock(self, ticker: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM stocks WHERE ticker = ?", (ticker,)).fetchone()
            return dict(row) if row else None

    def delete_stock(self, ticker: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM prices WHERE ticker = ?", (ticker,))
            conn.execute("DELETE FROM fundamentals WHERE ticker = ?", (ticker,))
            conn.execute("DELETE FROM scores WHERE ticker = ?", (ticker,))
            conn.execute("DELETE FROM stocks WHERE ticker = ?", (ticker,))

    # --- Prices ---

    def upsert_prices(self, ticker: str, rows: list[dict]) -> int:
        if not rows:
            return 0
        with self._conn() as conn:
            conn.executemany("""
                INSERT INTO prices (ticker, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker, date) DO UPDATE SET
                    open=excluded.open, high=excluded.high,
                    low=excluded.low, close=excluded.close,
                    volume=excluded.volume
            """, [(ticker, r["date"], r.get("open"), r.get("high"),
                   r.get("low"), r.get("close"), r.get("volume")) for r in rows])
        return len(rows)

    def get_prices(self, ticker: str, start: date | None = None,
                   end: date | None = None) -> list[dict]:
        query = "SELECT * FROM prices WHERE ticker = ?"
        params: list = [ticker]
        if start:
            query += " AND date >= ?"
            params.append(start.isoformat())
        if end:
            query += " AND date <= ?"
            params.append(end.isoformat())
        query += " ORDER BY date"
        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_latest_price_date(self, ticker: str) -> str | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT MAX(date) as d FROM prices WHERE ticker = ?", (ticker,)
            ).fetchone()
            return row["d"] if row else None

    # --- Fundamentals ---

    def upsert_fundamentals(self, ticker: str, data: dict) -> None:
        today = date.today().isoformat()
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO fundamentals (ticker, date, price, market_cap, trailing_pe,
                    forward_pe, pb, roe, operating_margin, net_margin, debt_equity,
                    ev_ebitda, fcf, fcf_yield, dividend_rate, dividend_yield, payout_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker, date) DO UPDATE SET
                    price=excluded.price, market_cap=excluded.market_cap,
                    trailing_pe=excluded.trailing_pe, forward_pe=excluded.forward_pe,
                    pb=excluded.pb, roe=excluded.roe,
                    operating_margin=excluded.operating_margin,
                    net_margin=excluded.net_margin, debt_equity=excluded.debt_equity,
                    ev_ebitda=excluded.ev_ebitda, fcf=excluded.fcf,
                    fcf_yield=excluded.fcf_yield, dividend_rate=excluded.dividend_rate,
                    dividend_yield=excluded.dividend_yield,
                    payout_ratio=excluded.payout_ratio
            """, (ticker, today, data.get("price"), data.get("market_cap"),
                  data.get("trailing_pe"), data.get("forward_pe"),
                  data.get("pb"), data.get("roe"),
                  data.get("operating_margin"), data.get("net_margin"),
                  data.get("debt_equity"), data.get("ev_ebitda"),
                  data.get("fcf"), data.get("fcf_yield"),
                  data.get("dividend_rate"), data.get("dividend_yield"),
                  data.get("payout_ratio")))

    def get_fundamentals(self, ticker: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM fundamentals WHERE ticker = ? ORDER BY date DESC LIMIT 1",
                (ticker,)
            ).fetchone()
            return dict(row) if row else None

    # --- Scores ---

    def upsert_score(self, ticker: str, date_str: str, momentum: float | None = None,
                     valuation: float | None = None, revisions: float | None = None,
                     total: float | None = None) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO scores (ticker, date, momentum, valuation, revisions, total)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker, date) DO UPDATE SET
                    momentum=COALESCE(excluded.momentum, scores.momentum),
                    valuation=COALESCE(excluded.valuation, scores.valuation),
                    revisions=COALESCE(excluded.revisions, scores.revisions),
                    total=excluded.total
            """, (ticker, date_str, momentum, valuation, revisions, total))

    def get_scores(self, date_str: str | None = None) -> list[dict]:
        with self._conn() as conn:
            if date_str:
                rows = conn.execute(
                    "SELECT * FROM scores WHERE date = ? ORDER BY total DESC", (date_str,)
                ).fetchall()
            else:
                # Latest date
                latest = conn.execute("SELECT MAX(date) as d FROM scores").fetchone()
                if not latest or not latest["d"]:
                    return []
                rows = conn.execute(
                    "SELECT * FROM scores WHERE date = ? ORDER BY total DESC",
                    (latest["d"],)
                ).fetchall()
            return [dict(r) for r in rows]

    def get_score_history(self, ticker: str, limit: int = 30) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM scores WHERE ticker = ? ORDER BY date DESC LIMIT ?",
                (ticker, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    # --- Momentum details ---

    def upsert_momentum_detail(self, ticker: str, metrics: dict,
                                score: float | None, date_str: str) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO momentum_details (ticker, m6, m12, m12_1, vs_ma200, ma50_vs_ma200, score, updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker) DO UPDATE SET
                    m6=excluded.m6, m12=excluded.m12, m12_1=excluded.m12_1,
                    vs_ma200=excluded.vs_ma200, ma50_vs_ma200=excluded.ma50_vs_ma200,
                    score=excluded.score, updated=excluded.updated
            """, (ticker, metrics.get("m6"), metrics.get("m12"), metrics.get("m12_1"),
                  metrics.get("vs_ma200"), metrics.get("ma50_vs_ma200"), score, date_str))

    def get_momentum_details(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM momentum_details ORDER BY score DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_momentum_detail(self, ticker: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM momentum_details WHERE ticker = ?", (ticker,)
            ).fetchone()
            return dict(row) if row else None

    # --- Valuation details ---

    def upsert_valuation_detail(self, ticker: str, details: dict,
                                 score: float | None, date_str: str) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO valuation_details (ticker, forward_pe, pb, ev_ebitda, fcf_yield, score, updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker) DO UPDATE SET
                    forward_pe=excluded.forward_pe, pb=excluded.pb,
                    ev_ebitda=excluded.ev_ebitda, fcf_yield=excluded.fcf_yield,
                    score=excluded.score, updated=excluded.updated
            """, (ticker, details.get("forward_pe"), details.get("pb"),
                  details.get("ev_ebitda"), details.get("fcf_yield"), score, date_str))

    def get_valuation_details(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM valuation_details ORDER BY score DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_valuation_detail(self, ticker: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM valuation_details WHERE ticker = ?", (ticker,)
            ).fetchone()
            return dict(row) if row else None

    # --- Revisions details ---

    def upsert_revisions_detail(self, ticker: str, details: dict,
                                 score: float | None, date_str: str) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO revisions_details (ticker, rev_ratio_30d, eps_change_30d,
                    eps_change_90d, num_analysts, score, updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker) DO UPDATE SET
                    rev_ratio_30d=excluded.rev_ratio_30d,
                    eps_change_30d=excluded.eps_change_30d,
                    eps_change_90d=excluded.eps_change_90d,
                    num_analysts=excluded.num_analysts,
                    score=excluded.score, updated=excluded.updated
            """, (ticker, details.get("rev_ratio_30d"), details.get("eps_change_30d"),
                  details.get("eps_change_90d"), details.get("num_analysts"),
                  score, date_str))

    def get_revisions_details(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM revisions_details ORDER BY score DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_revisions_detail(self, ticker: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM revisions_details WHERE ticker = ?", (ticker,)
            ).fetchone()
            return dict(row) if row else None

    # --- Sync log ---

    def log_sync(self, timestamp: str, prices_rows: int = 0,
                 scores_calculated: int = 0) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO sync_log (timestamp, prices_rows, scores_calculated)
                VALUES (?, ?, ?)
            """, (timestamp, prices_rows, scores_calculated))

    def get_last_sync(self) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM sync_log ORDER BY id DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None
