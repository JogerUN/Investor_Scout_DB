"""
Investor Scout — ETL: Yahoo Finance -> MySQL

Script de EJECUCIÓN DIRECTA. 

Uso:
    python main.py                  # usa los tickers de config/tickers.txt
    python main.py AAPL MSFT NVDA   # usa estos tickers en vez del archivo
"""
import logging
import os
import sys
import time

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

from scripts.init_db import initialize_database
from app.services.yahoo_provider import YahooFinanceProvider
from app.services.sync_service import SyncService
from app.data_structures.stock_cache import StockCache

TICKERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "tickers.txt")


def load_tickers_from_file(path: str):
    if not os.path.exists(path):
        return []
    tickers = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tickers.append(line.upper())
    return tickers


def get_tickers():
    # Si se pasan tickers como argumentos de línea de comandos, tienen prioridad.
    if len(sys.argv) > 1:
        return [t.strip().upper() for t in sys.argv[1:] if t.strip()]
    return load_tickers_from_file(TICKERS_FILE)


def run():
    print("========================================================")
    print("   INVESTOR SCOUT — ETL: Yahoo Finance -> MySQL")
    print("========================================================")

    # 1. Asegura que las tablas existan (idempotente, no borra datos)
    if not initialize_database():
        print("[ABORTADO] No se pudo preparar la base de datos.")
        sys.exit(1)

    # 2. Tickers a sincronizar
    tickers = get_tickers()
    if not tickers:
        print(f"[ABORTADO] No hay tickers para sincronizar. "
              f"Agrégalos en {TICKERS_FILE} o pásalos como argumento: "
              f"python main.py AAPL MSFT")
        sys.exit(1)

    print(f"\nTickers a sincronizar ({len(tickers)}): {', '.join(tickers)}")

    provider = YahooFinanceProvider()
    stock_cache = StockCache()
    sync_service = SyncService(provider=provider, stock_cache=stock_cache)

    exitosos = []
    fallidos = []
    start = time.time()

    for ticker in tickers:
        print(f"\n-> Procesando {ticker}...")
        try:
            ok = sync_service.sync_initial(ticker)
            if ok:
                print(f"   [OK] {ticker} sincronizado y guardado en MySQL.")
                exitosos.append(ticker)
            else:
                print(f"   [FALLO] {ticker} no se pudo sincronizar (ver log).")
                fallidos.append(ticker)
        except Exception as e:
            print(f"   [ERROR] Excepción al sincronizar {ticker}: {e}")
            fallidos.append(ticker)

    elapsed = time.time() - start
    print("\n========================================================")
    print("   RESUMEN")
    print("========================================================")
    print(f"Exitosos ({len(exitosos)}): {', '.join(exitosos) if exitosos else '-'}")
    print(f"Fallidos ({len(fallidos)}): {', '.join(fallidos) if fallidos else '-'}")
    print(f"Tiempo total: {elapsed:.1f}s")

    sys.exit(0 if not fallidos else 2)


if __name__ == "__main__":
    run()
