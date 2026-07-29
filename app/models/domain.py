from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Asset:
    """Corresponde a la tabla 'activo'."""
    ticker: str
    nombre: str
    tipo_activo: str  # 'EQUITY' o 'BOND'
    moneda: str = "USD"
    exchange: Optional[str] = None
    pais: Optional[str] = None
    id_activo: Optional[int] = None

    def __post_init__(self):
        self.ticker = self.ticker.upper()
        self.tipo_activo = self.tipo_activo.upper()


@dataclass
class EquityDetails:
    """Corresponde a la tabla 'equity' (subtipo ISA de activo)."""
    id_activo: int
    sector: Optional[str] = None
    industria: Optional[str] = None
    earnings_date: Optional[date] = None


@dataclass
class BondDetails:
    """Corresponde a la tabla 'bond' (subtipo ISA de activo).
    Yahoo Finance no ofrece datos confiables de bonos individuales,
    por lo que este DTO existe para completar el esquema pero el
    pipeline de sincronización no lo llena automáticamente.
    """
    id_activo: int
    fecha_maduracion: Optional[date] = None
    tasa_cupon: Optional[float] = None
    frecuencia_pago: Optional[str] = None  # 'MENSUAL', 'TRIMESTRAL', 'SEMESTRAL', 'ANUAL'
    valor_nominal: Optional[float] = None
    calificacion: Optional[str] = None
    emisor: str = "SOBERANO"  # 'SOBERANO' o 'CORPORATIVO'


@dataclass
class HistoricalPrice:
    """Corresponde a la tabla 'historico' (serie OHLCV)."""
    id_activo: int
    fecha: date
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: float = 0.0
    volumen: Optional[int] = None


@dataclass
class MarketMetrics:
    """Corresponde a la tabla 'metricas_mercado'."""
    id_activo: int
    fecha: date
    precio: Optional[float] = None
    market_cap: Optional[int] = None
    enterprise_value: Optional[int] = None
    pe_ratio: Optional[float] = None
    pe_forward: Optional[float] = None
    beta: Optional[float] = None
    dividend_yield: Optional[float] = None
    id_metricas: Optional[int] = None
