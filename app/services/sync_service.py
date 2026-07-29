import logging
import time
from datetime import date, timedelta
from typing import Optional

from app.models.domain import Asset
from app.services.provider_interface import BaseFinancialProvider
from app.services.mapper import FinancialMapper
from app.data_structures.stock_cache import StockCache

from app.repositories.activo_repository import ActivoRepository
from app.repositories.equity_repository import EquityRepository
from app.repositories.historico_repository import HistoricoRepository
from app.repositories.metrics_repository import MetricsRepository

logger = logging.getLogger(__name__)


class SyncService:
    """
    Orquesta el pipeline ETL (Extract, Transform, Load):
    descarga de Yahoo Finance -> limpieza (mapper) -> inserción en MySQL.

    Solo sincroniza las tablas que existen en el esquema adjunto:
    activo, equity, historico y metricas_mercado.
    """
    def __init__(self, provider: BaseFinancialProvider, stock_cache: Optional[StockCache] = None):
        self.provider = provider
        self.stock_cache = stock_cache if stock_cache else StockCache()

        self.activo_repo = ActivoRepository()
        self.equity_repo = EquityRepository()
        self.historico_repo = HistoricoRepository()
        self.metrics_repo = MetricsRepository()

    def _get_or_create_asset(self, ticker: str) -> Asset:
        """
        Busca el activo en BD; si no existe, lo descarga de Yahoo Finance y lo crea.
        """
        ticker = ticker.upper()
        asset = self.activo_repo.get_by_ticker(ticker)
        if asset:
            return asset

        logger.info(f"Asset for ticker {ticker} not found in DB. Performing extraction...")
        raw_info = self.provider.fetch_asset_info(ticker)
        if not raw_info:
            raise ValueError(f"Could not fetch asset info for ticker '{ticker}' from provider.")

        asset = FinancialMapper.to_asset(raw_info)
        id_activo = self.activo_repo.save(asset)
        asset.id_activo = id_activo

        if asset.tipo_activo == "EQUITY":
            equity_details = FinancialMapper.to_equity_details(id_activo, raw_info)
            self.equity_repo.save(equity_details)

        logger.info(f"Successfully created asset '{asset.nombre}' with ID {id_activo} in DB.")
        return asset

    def sync_initial(self, ticker: str, years_of_history: int = 5) -> bool:
        """
        Sincronización inicial de un ticker: activo/equity + histórico de precios
        (por defecto 5 años) + métricas de mercado actuales.
        """
        ticker = ticker.upper()
        start_time = time.time()
        logger.info(f"Starting initial sync for {ticker}...")

        inserted_count = 0

        try:
            # 1. Activo / Equity
            asset = self._get_or_create_asset(ticker)
            id_activo = asset.id_activo

            # 2. Histórico de precios (OHLCV)
            end_date = date.today()
            start_date = end_date - timedelta(days=years_of_history * 365)
            logger.info(f"Fetching {years_of_history}-year historical prices for {ticker}...")
            raw_prices = self.provider.fetch_historical_prices(ticker, start_date, end_date)

            prices = [FinancialMapper.to_historical_price(id_activo, p) for p in raw_prices]
            self.historico_repo.save_bulk(prices)
            inserted_count += len(prices)
            logger.info(f"Saved {len(prices)} price bars to DB.")

            # 3. Métricas de mercado actuales
            logger.info(f"Fetching current market metrics for {ticker}...")
            raw_metrics = self.provider.fetch_market_metrics(ticker)
            if raw_metrics:
                metrics = FinancialMapper.to_market_metrics(id_activo, raw_metrics)
                self.metrics_repo.save(metrics)
                inserted_count += 1

                if metrics.precio:
                    self.stock_cache.set_price(ticker, metrics.precio)

            elapsed = time.time() - start_time
            logger.info(f"Completed initial sync for {ticker} in {elapsed:.2f}s. Loaded {inserted_count} records.")
            return True

        except Exception as e:
            logger.error(f"Failed initial sync for {ticker}: {e}", exc_info=True)
            return False

    def sync_daily(self, ticker: str) -> bool:
        """
        Sincronización diaria: precio/métricas actuales + últimos 7 días de histórico
        (para cubrir fines de semana/feriados sin datos).
        """
        ticker = ticker.upper()
        start_time = time.time()
        logger.info(f"Starting daily sync for {ticker}...")

        inserted_count = 0

        try:
            asset = self._get_or_create_asset(ticker)
            id_activo = asset.id_activo

            raw_metrics = self.provider.fetch_market_metrics(ticker)
            if raw_metrics:
                metrics = FinancialMapper.to_market_metrics(id_activo, raw_metrics)
                self.metrics_repo.save(metrics)
                inserted_count += 1

                if metrics.precio:
                    self.stock_cache.set_price(ticker, metrics.precio)

            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            raw_prices = self.provider.fetch_historical_prices(ticker, start_date, end_date)
            prices = [FinancialMapper.to_historical_price(id_activo, p) for p in raw_prices]
            self.historico_repo.save_bulk(prices)
            inserted_count += len(prices)

            elapsed = time.time() - start_time
            logger.info(f"Completed daily sync for {ticker} in {elapsed:.2f}s. Updated {inserted_count} records.")
            return True

        except Exception as e:
            logger.error(f"Failed daily sync for {ticker}: {e}")
            return False
