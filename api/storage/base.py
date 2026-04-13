"""
Storage abstraction layer.
All storage backends implement this interface.
"""

from abc import ABC, abstractmethod
from datetime import date


class StorageBackend(ABC):

    # --- Stocks ---

    @abstractmethod
    def upsert_stock(self, ticker: str, name: str, segment: str,
                     industry: str | None = None, product: str | None = None) -> None:
        """Insert or update a stock."""

    @abstractmethod
    def get_stocks(self) -> list[dict]:
        """Get all stocks."""

    @abstractmethod
    def get_stock(self, ticker: str) -> dict | None:
        """Get a single stock by ticker."""

    @abstractmethod
    def delete_stock(self, ticker: str) -> None:
        """Remove a stock and all its related data."""

    # --- Prices ---

    @abstractmethod
    def upsert_prices(self, ticker: str, rows: list[dict]) -> int:
        """Bulk insert/update daily prices. Returns count of rows written."""

    @abstractmethod
    def get_prices(self, ticker: str, start: date | None = None,
                   end: date | None = None) -> list[dict]:
        """Get price history for a ticker, optionally filtered by date range."""

    @abstractmethod
    def get_latest_price_date(self, ticker: str) -> str | None:
        """Get the most recent price date for a ticker."""

    # --- Fundamentals ---

    @abstractmethod
    def upsert_fundamentals(self, ticker: str, data: dict) -> None:
        """Insert or update fundamentals snapshot for today."""

    @abstractmethod
    def get_fundamentals(self, ticker: str) -> dict | None:
        """Get latest fundamentals for a ticker."""

    # --- Scores ---

    @abstractmethod
    def upsert_score(self, ticker: str, date_str: str, momentum: float | None = None,
                     valuation: float | None = None, revisions: float | None = None,
                     total: float | None = None) -> None:
        """Insert or update scores for a ticker on a date."""

    @abstractmethod
    def get_scores(self, date_str: str | None = None) -> list[dict]:
        """Get all scores, optionally for a specific date. Defaults to latest."""

    @abstractmethod
    def get_score_history(self, ticker: str, limit: int = 30) -> list[dict]:
        """Get score history for a ticker."""

    # --- Valuation details ---

    @abstractmethod
    def upsert_valuation_detail(self, ticker: str, details: dict,
                                 score: float | None, date_str: str) -> None:
        """Insert or update valuation detail for a ticker."""

    @abstractmethod
    def get_valuation_details(self) -> list[dict]:
        """Get all valuation details."""

    @abstractmethod
    def get_valuation_detail(self, ticker: str) -> dict | None:
        """Get valuation detail for a ticker."""
