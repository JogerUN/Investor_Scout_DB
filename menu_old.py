"""
Menú de terminal de Investor Scout.

Se estructura con un Menú Principal y submenús jerárquicos:
- Portfolio
- Transactions (integración con Yahoo Finance para precios en tiempo real)
- Stock Screener (consultas SQL de perfil, métricas y precios históricos)
- Reports
"""
import datetime
from app.database.connection import DBConnectionManager
from app.database.sql_loader import ejecutar_sql


def mostrar_filas(filas):
    if not filas:
        print("\n(sin resultados)")
        return
    print()
    for fila in filas:
        for columna, valor in fila.items():
            print(f"  {columna}: {valor}")
        print("-" * 40)


def pedir_numero(mensaje):
    while True:
        texto = input(mensaje).strip()
        try:
            val = float(texto)
            return val
        except ValueError:
            print("Por favor escribe un número válido.")


def pedir_entero(mensaje):
    while True:
        texto = input(mensaje).strip()
        try:
            return int(texto)
        except ValueError:
            print("Por favor escribe un número entero válido.")


def obtener_precio_y_sincronizar(ticker: str) -> float:
    """
    Sincroniza el activo en la base de datos desde Yahoo Finance
    y retorna su precio actual de mercado.
    """
    ticker = ticker.upper()
    try:
        from app.services.yahoo_provider import YahooFinanceProvider
        from app.services.sync_service import SyncService
        provider = YahooFinanceProvider()
        service = SyncService(provider)
        
        # Sincroniza o asegura el activo en BD
        service.sync_daily(ticker)
        
        # Obtiene métricas para el precio
        metrics = provider.fetch_market_metrics(ticker)
        if metrics and metrics.get("precio"):
            precio = float(metrics["precio"])
            print(f"[Yahoo Finance] Precio de mercado actual para {ticker}: ${precio:.2f} USD")
            return precio
    except Exception as e:
        print(f"[Yahoo Finance Warning] No se pudo obtener el precio automáticamente: {e}")
    
    # Fallback si no se pudo obtener de Yahoo Finance
    return pedir_numero(f"Ingresa el precio por acción manualmente para {ticker}: ")


def asegurar_sincronizacion(ticker: str):
    """
    Asegura que el ticker exista en la base de datos con información actualizada de Yahoo Finance.
    """
    try:
        from app.services.yahoo_provider import YahooFinanceProvider
        from app.services.sync_service import SyncService
        service = SyncService(YahooFinanceProvider())
        service.sync_daily(ticker)
    except Exception:
        pass


# ======================================================================
# FUNCIONES DE OPERACIÓN SQL
# ======================================================================

# --- Portfolio ---
def crear_portafolio(conexion):
    print("\n--- Create Portfolio ---")
    id_cliente = pedir_entero("id_cliente: ")
    nombre = input("Nombre del portafolio: ").strip()
    perfil = input("Perfil de riesgo (CONSERVADOR / MODERADO / AGRESIVO): ").strip().upper()
    if perfil not in ["CONSERVADOR", "MODERADO", "AGRESIVO"]:
        perfil = "MODERADO"
    cash = pedir_numero("Cash inicial: ")

    try:
        ejecutar_sql(conexion, "portfolio/create_portfolio.sql", (id_cliente, nombre, perfil, cash))
        print("Portafolio creado exitosamente.")
    except Exception as e:
        print(f"Error al crear el portafolio: {e}")


def ver_posiciones(conexion):
    print("\n--- View Positions ---")
    id_portafolio = pedir_entero("id_portafolio: ")
    try:
        filas = ejecutar_sql(conexion, "portfolio/positions.sql", (id_portafolio,))
        mostrar_filas(filas)
    except Exception as e:
        print(f"Error al consultar posiciones: {e}")


def ver_metricas_portafolio(conexion):
    print("\n--- Portfolio Metrics ---")
    id_portafolio = pedir_entero("id_portafolio: ")
    try:
        filas = ejecutar_sql(conexion, "portfolio/metrics.sql", (id_portafolio,))
        mostrar_filas(filas)
    except Exception as e:
        print(f"Error al consultar métricas: {e}")


def eliminar_portafolio(conexion):
    print("\n--- Delete Portfolio ---")
    id_portafolio = pedir_entero("id_portafolio: ")
    try:
        ejecutar_sql(conexion, "portfolio/delete_portfolio.sql", (id_portafolio,))
        print("Portafolio eliminado.")
    except Exception as e:
        print(f"No se pudo eliminar: {e}")
        print("(Nota: No se puede eliminar si tiene movimientos asociados.)")


# --- Transactions ---
def comprar(conexion):
    print("\n--- Buy Stock ---")
    id_portafolio = pedir_entero("id_portafolio: ")
    ticker = input("Ticker: ").strip().upper()
    cantidad = pedir_numero("Cantidad de acciones: ")
    fecha = input("Fecha (YYYY-MM-DD HH:MM:SS) o presiona Enter para fecha/hora actual: ").strip()
    if not fecha:
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    precio = obtener_precio_y_sincronizar(ticker)
    if precio is None or precio <= 0:
        print("Operación cancelada: precio no válido.")
        return

    try:
        ejecutar_sql(conexion, "transaction/buy.sql", (id_portafolio, ticker, cantidad, precio, fecha))
        print(f"Compra registrada exitosamente ({cantidad} acciones de {ticker} a ${precio:.2f}).")
    except Exception as e:
        print(f"Error al registrar la compra: {e}")


def vender(conexion):
    print("\n--- Sell Stock ---")
    id_portafolio = pedir_entero("id_portafolio: ")
    ticker = input("Ticker: ").strip().upper()
    cantidad = pedir_numero("Cantidad de acciones: ")
    fecha = input("Fecha (YYYY-MM-DD HH:MM:SS) o presiona Enter para fecha/hora actual: ").strip()
    if not fecha:
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    precio = obtener_precio_y_sincronizar(ticker)
    if precio is None or precio <= 0:
        print("Operación cancelada: precio no válido.")
        return

    try:
        ejecutar_sql(conexion, "transaction/sell.sql", (id_portafolio, ticker, cantidad, precio, fecha))
        print(f"Venta registrada exitosamente ({cantidad} acciones de {ticker} a ${precio:.2f}).")
    except Exception as e:
        print(f"Error al registrar la venta: {e}")


def ver_historial(conexion):
    print("\n--- Transaction History ---")
    id_portafolio = pedir_entero("id_portafolio: ")
    try:
        filas = ejecutar_sql(conexion, "transaction/history.sql", (id_portafolio,))
        mostrar_filas(filas)
    except Exception as e:
        print(f"Error al consultar el historial: {e}")


# --- Stock Screener ---
def ver_ficha_activo(conexion):
    print("\n--- Company Profile ---")
    ticker = input("Ticker: ").strip().upper()
    asegurar_sincronizacion(ticker)
    try:
        filas = ejecutar_sql(conexion, "company/profile.sql", (ticker,))
        mostrar_filas(filas)
    except Exception as e:
        print(f"Error al consultar perfil de compañía: {e}")


def ver_metricas_mercado(conexion):
    print("\n--- Financial Metrics ---")
    ticker = input("Ticker: ").strip().upper()
    asegurar_sincronizacion(ticker)
    try:
        filas = ejecutar_sql(conexion, "company/financials.sql", (ticker,))
        mostrar_filas(filas)
    except Exception as e:
        print(f"Error al consultar métricas financieras: {e}")


def ver_precios_historicos(conexion):
    print("\n--- Historical Prices ---")
    ticker = input("Ticker: ").strip().upper()
    asegurar_sincronizacion(ticker)
    try:
        filas = ejecutar_sql(conexion, "company/historical.sql", (ticker,))
        mostrar_filas(filas)
    except Exception as e:
        print(f"Error al consultar precios históricos: {e}")


# --- Reports ---
def ver_composicion(conexion):
    print("\n--- Portfolio Allocation ---")
    id_portafolio = pedir_entero("id_portafolio: ")
    try:
        filas = ejecutar_sql(conexion, "reports/allocation.sql", (id_portafolio, id_portafolio))
        mostrar_filas(filas)
    except Exception as e:
        print(f"Error al consultar composición del portafolio: {e}")


def ver_performance(conexion):
    print("\n--- Performance Summary ---")
    id_portafolio = pedir_entero("id_portafolio: ")
    try:
        filas = ejecutar_sql(conexion, "reports/performance.sql", (id_portafolio, id_portafolio))
        mostrar_filas(filas)
    except Exception as e:
        print(f"Error al consultar resumen de performance: {e}")


# ======================================================================
# MENÚS Y NAVEGACIÓN
# ======================================================================

def menu_portfolio(conexion):
    while True:
        print("\n=========================")
        print("        PORTFOLIO        ")
        print("=========================")
        print("1. Create Portfolio")
        print("2. View Positions")
        print("3. Portfolio Metrics")
        print("4. Delete Portfolio")
        print("5. Back")
        print("=========================")

        opcion = input("Escribe tu opcion: ").strip()

        if opcion == "1":
            crear_portafolio(conexion)
        elif opcion == "2":
            ver_posiciones(conexion)
        elif opcion == "3":
            ver_metricas_portafolio(conexion)
        elif opcion == "4":
            eliminar_portafolio(conexion)
        elif opcion == "5":
            break
        else:
            print("Opcion invalida. Intenta nuevamente.")


def menu_transactions(conexion):
    while True:
        print("\n=========================")
        print("      TRANSACTIONS       ")
        print("=========================")
        print("1. Buy Stock")
        print("2. Sell Stock")
        print("3. Transaction History")
        print("4. Back")
        print("=========================")

        opcion = input("Escribe tu opcion: ").strip()

        if opcion == "1":
            comprar(conexion)
        elif opcion == "2":
            vender(conexion)
        elif opcion == "3":
            ver_historial(conexion)
        elif opcion == "4":
            break
        else:
            print("Opcion invalida. Intenta nuevamente.")


def menu_screener(conexion):
    while True:
        print("\n=========================")
        print("     STOCK SCREENER      ")
        print("=========================")
        print("1. Company Profile")
        print("2. Financial Metrics")
        print("3. Historical Prices")
        print("4. Back")
        print("=========================")

        opcion = input("Escribe tu opcion: ").strip()

        if opcion == "1":
            ver_ficha_activo(conexion)
        elif opcion == "2":
            ver_metricas_mercado(conexion)
        elif opcion == "3":
            ver_precios_historicos(conexion)
        elif opcion == "4":
            break
        else:
            print("Opcion invalida. Intenta nuevamente.")


def menu_reports(conexion):
    while True:
        print("\n=========================")
        print("         REPORTS         ")
        print("=========================")
        print("1. Portfolio Allocation")
        print("2. Performance Summary")
        print("3. Back")
        print("=========================")

        opcion = input("Escribe tu opcion: ").strip()

        if opcion == "1":
            ver_composicion(conexion)
        elif opcion == "2":
            ver_performance(conexion)
        elif opcion == "3":
            break
        else:
            print("Opcion invalida. Intenta nuevamente.")


def mostrar_menu(cliente=None):
    """
    Menú Principal de la aplicación Investor Scout.
    """
    try:
        conexion = DBConnectionManager.get_connection()
    except Exception as e:
        print(f"\nError al conectar a la base de datos: {e}")
        return

    try:
        while True:
            print("\n=========================")
            print("      INVESTOR SCOUT     ")
            print("=========================")
            print("1. Portfolio")
            print("2. Transactions")
            print("3. Stock Screener")
            print("4. Reports")
            print("5. Exit")
            print("=========================")

            opcion = input("Escribe tu opcion: ").strip()

            if opcion == "1":
                menu_portfolio(conexion)
            elif opcion == "2":
                menu_transactions(conexion)
            elif opcion == "3":
                menu_screener(conexion)
            elif opcion == "4":
                menu_reports(conexion)
            elif opcion == "5":
                print("¡Hasta pronto!")
                break
            else:
                print("Opcion invalida. Intenta nuevamente.")
    finally:
        try:
            conexion.close()
        except Exception:
            pass


if __name__ == "__main__":
    mostrar_menu()
