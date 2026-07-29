import time
import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Any
import yfinance as yf
from app.services.provider_interface import BaseFinancialProvider

logger = logging.getLogger(__name__)


class YahooFinanceProvider(BaseFinancialProvider):
    """
    Yahoo Finance provider implementing the BaseFinancialProvider interface.
    Fetches data using yfinance, handles retries, and extracts raw data.

    Recortado para descargar únicamente los datos que se guardan en el
    esquema adjunto: activo/equity, historico (OHLCV) y metricas_mercado.
    """
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def _execute_with_retry(self, func, *args, **kwargs) -> Any:
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                wait_time = self.backoff_factor ** attempt
                logger.warning(f"YahooFinance API call failed (attempt {attempt + 1}/{self.max_retries}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
        logger.error(f"YahooFinance API call failed after {self.max_retries} attempts.")
        if last_error is None:
            raise RuntimeError("YahooFinance API call failed with no exception recorded.")
        raise last_error

    def fetch_asset_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Datos generales del instrumento: alimenta 'activo' y, si es EQUITY, 'equity'.
        """
        ticker = ticker.upper()
        try:
            ticker_obj = yf.Ticker(ticker)
            info = self._execute_with_retry(lambda: ticker_obj.info)
            if not info or 'longName' not in info:
                # Fallback: si no hay info detallada, usamos fast_info
                fast_info = ticker_obj.fast_info
                return {
                    "ticker": ticker,
                    "nombre": ticker,
                    "tipo_activo": "EQUITY",
                    "moneda": getattr(fast_info, 'currency', 'USD'),
                    "exchange": getattr(fast_info, 'exchange', None),
                    "pais": None,
                    "sector": None,
                    "industria": None,
                    "earnings_date": None,
                }
            return {
                "ticker": ticker,
                "nombre": info.get("longName") or info.get("shortName") or ticker,
                "tipo_activo": "EQUITY" if info.get("quoteType", "EQUITY") == "EQUITY" else "BOND",
                "moneda": info.get("currency", "USD"),
                "exchange": info.get("exchange"),
                "pais": info.get("country"),
                "sector": info.get("sector"),
                "industria": info.get("industry"),
                "earnings_date": info.get("nextEarningsDate"),
            }
        except Exception as e:
            logger.error(f"Error fetching asset info for {ticker}: {e}")
            return None

    def fetch_historical_prices(self, ticker: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Serie OHLCV diaria: alimenta la tabla 'historico'.
        """
        ticker = ticker.upper()
        try:
            ticker_obj = yf.Ticker(ticker)
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            df = self._execute_with_retry(
                lambda: ticker_obj.history(start=start_str, end=end_str, interval="1d")
            )

            prices = []
            for dt, row in df.iterrows():
                prices.append({
                    "fecha": dt.date() if hasattr(dt, 'date') else dt,
                    "open_price": float(row.get("Open", 0.0)),
                    "high_price": float(row.get("High", 0.0)),
                    "low_price": float(row.get("Low", 0.0)),
                    "close_price": float(row.get("Close", 0.0)),
                    "volumen": int(row.get("Volume", 0)) if row.get("Volume") is not None else None,
                })
            return prices
        except Exception as e:
            logger.error(f"Error fetching historical prices for {ticker}: {e}")
            return []

    def fetch_market_metrics(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Métricas de valuación dependientes del precio: alimenta 'metricas_mercado'.
        Solo se descargan los campos que existen en esa tabla (precio, market_cap,
        enterprise_value, pe_ratio, pe_forward, beta, dividend_yield).
        """
        ticker = ticker.upper()
        try:
            ticker_obj = yf.Ticker(ticker)
            info = self._execute_with_retry(lambda: ticker_obj.info)
            if not info:
                # Fallback: al menos el precio de cierre más reciente
                hist = ticker_obj.history(period="1d")
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    return {
                        "fecha": date.today(),
                        "precio": current_price
                    }
                return None

            return {
                "fecha": date.today(),
                "precio": info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose"),
                "market_cap": info.get("marketCap"),
                "enterprise_value": info.get("enterpriseValue"),
                "pe_ratio": info.get("trailingPE"),
                "pe_forward": info.get("forwardPE"),
                "beta": info.get("beta"),
                "dividend_yield": info.get("dividendYield")
            }
        except Exception as e:
            logger.error(f"Error fetching market metrics for {ticker}: {e}")
            return None
