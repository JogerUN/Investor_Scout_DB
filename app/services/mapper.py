import math
from datetime import date, datetime
from typing import Any, Dict, Optional
from app.models.domain import Asset, EquityDetails, HistoricalPrice, MarketMetrics


class FinancialMapper:
    """
    Maps raw provider responses to internal domain DTOs.
    Converts data types, dates, and cleans values (esto es la 'limpieza' de datos
    antes de insertarlos en MySQL: NaN/Inf -> NULL, strings numéricos -> float/int, etc.).
    """

    @staticmethod
    def _clean_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            val = float(value)
            if math.isnan(val) or math.isinf(val):
                return None
            return val
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _clean_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            val = float(value)  # soporta strings tipo '12345.0'
            if math.isnan(val) or math.isinf(val):
                return None
            return int(val)
        except (ValueError, TypeError):
            return None

    @classmethod
    def to_asset(cls, raw: Dict[str, Any]) -> Asset:
        return Asset(
            ticker=raw["ticker"],
            nombre=raw.get("nombre") or raw.get("longName") or raw["ticker"],
            tipo_activo=raw.get("tipo_activo", "EQUITY"),
            moneda=raw.get("moneda", "USD"),
            exchange=raw.get("exchange"),
            pais=raw.get("pais")
        )

    @classmethod
    def to_equity_details(cls, id_activo: int, raw: Dict[str, Any]) -> EquityDetails:
        earnings_date_raw = raw.get("earnings_date")
        earnings_date = None
        if earnings_date_raw:
            if isinstance(earnings_date_raw, (date, datetime)):
                earnings_date = earnings_date_raw if isinstance(earnings_date_raw, date) else earnings_date_raw.date()
            elif isinstance(earnings_date_raw, int):
                earnings_date = datetime.fromtimestamp(earnings_date_raw).date()
            elif isinstance(earnings_date_raw, str):
                try:
                    earnings_date = datetime.strptime(earnings_date_raw.split("T")[0], "%Y-%m-%d").date()
                except ValueError:
                    pass

        return EquityDetails(
            id_activo=id_activo,
            sector=raw.get("sector"),
            industria=raw.get("industria"),
            earnings_date=earnings_date
        )

    @classmethod
    def to_historical_price(cls, id_activo: int, raw: Dict[str, Any]) -> HistoricalPrice:
        return HistoricalPrice(
            id_activo=id_activo,
            fecha=raw["fecha"],
            open_price=cls._clean_float(raw.get("open_price")),
            high_price=cls._clean_float(raw.get("high_price")),
            low_price=cls._clean_float(raw.get("low_price")),
            close_price=cls._clean_float(raw.get("close_price")) or 0.0,
            volumen=cls._clean_int(raw.get("volumen"))
        )

    @classmethod
    def to_market_metrics(cls, id_activo: int, raw: Dict[str, Any]) -> MarketMetrics:
        return MarketMetrics(
            id_activo=id_activo,
            fecha=raw.get("fecha", date.today()),
            precio=cls._clean_float(raw.get("precio")),
            market_cap=cls._clean_int(raw.get("market_cap")),
            enterprise_value=cls._clean_int(raw.get("enterprise_value")),
            pe_ratio=cls._clean_float(raw.get("pe_ratio")),
            pe_forward=cls._clean_float(raw.get("pe_forward")),
            beta=cls._clean_float(raw.get("beta")),
            dividend_yield=cls._clean_float(raw.get("dividend_yield"))
        )
