from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List, Optional, Any


class BaseFinancialProvider(ABC):
    """
    Abstract interface for financial data providers.
    Ensures the ETL service is decoupled from the specific data source (e.g. Yahoo Finance, Polygon, etc.).
    """

    @abstractmethod
    def fetch_asset_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetches general asset info (para tablas 'activo' y 'equity').
        Returns a raw dictionary that will be mapped.
        """
        pass

    @abstractmethod
    def fetch_historical_prices(self, ticker: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Fetches daily OHLCV historical prices (para la tabla 'historico').
        """
        pass

    @abstractmethod
    def fetch_market_metrics(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetches current valuation/market metrics (para la tabla 'metricas_mercado').
        """
        pass
