"""
Menú de terminal de Investor Scout.

Se estructura con un Menú Principal y submenús jerárquicos:
- Portfolio
- Transactions (integración con Yahoo Finance para precios en tiempo real;
- los bonos se registran a mano, Yahoo no los cubre)
- Stock Screener (consultas SQL de perfil, métricas y precios históricos)
- Reports
"""
import datetime
from app.database.connection import DBConnectionManager
from app.database.sql_loader import ejecutar_sql, ejecutar_insert_y_devolver_id


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


# --- Transactions: acciones (via Yahoo Finance) ---
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


# --- Transactions: bonos (manual, sin Yahoo Finance) ---
def buscar_activo_por_ticker(conexion, ticker):
    filas = ejecutar_sql(conexion, "bond/find_by_ticker.sql", (ticker,))
    return filas[0] if filas else None


def registrar_bono_nuevo(conexion, ticker):
    """
    Pide a mano los datos del bono y lo crea en dos pasos:
    1) fila en 'activo' (tipo_activo = BOND)
    2) fila en 'bond' con el mismo id como id_bond (relacion 1:1)
    El paso 2 dispara el trigger verificar_bond, que confirma que el
    activo recien creado sea BOND.
    """
    print(f"\nEl ticker {ticker} no existe todavia. Vamos a registrarlo como bono nuevo.")
    nombre = input("Nombre del bono / emisor: ").strip()
    moneda = input("Moneda (Enter para USD): ").strip().upper() or "USD"
    pais = input("Pais (Enter para dejar en blanco): ").strip() or None

    fecha_maduracion = input("Fecha de maduracion (YYYY-MM-DD, Enter para dejar en blanco): ").strip() or None
    tasa_cupon = pedir_numero("Tasa de cupon anual, ej. 3.5 para 3.5%: ")

    frecuencia = input("Frecuencia de pago (MENSUAL/TRIMESTRAL/SEMESTRAL/ANUAL): ").strip().upper()
    if frecuencia not in ["MENSUAL", "TRIMESTRAL", "SEMESTRAL", "ANUAL"]:
        print("Frecuencia no reconocida, se usara ANUAL por defecto.")
        frecuencia = "ANUAL"

    valor_nominal = pedir_numero("Valor nominal del bono: ")
    calificacion = input("Calificacion crediticia, ej. AAA (Enter para dejar en blanco): ").strip().upper() or None

    emisor = input("Emisor (SOBERANO/CORPORATIVO): ").strip().upper()
    if emisor not in ["SOBERANO", "CORPORATIVO"]:
        print("Emisor no reconocido, se usara CORPORATIVO por defecto.")
        emisor = "CORPORATIVO"

    id_activo = ejecutar_insert_y_devolver_id(
        conexion, "bond/create_bond_asset.sql", (ticker, nombre, moneda, pais)
    )

    ejecutar_sql(
        conexion, "bond/create_bond_details.sql",
        (id_activo, id_activo, fecha_maduracion, tasa_cupon, frecuencia, valor_nominal, calificacion, emisor)
    )

    print(f"Bono {ticker} registrado correctamente (id_activo = {id_activo}).")
    return id_activo

# modifide start
def registrar_bono_manual_menu(conexion):
    """Permite dar de alta un bono manualmente desde el menú sin comprarlo."""
    print("\n--- Registrar Nuevo Bono (Manual) ---")
    ticker = input("Ticker del bono (ej. ARG29, US10Y): ").strip().upper()
    
    if not ticker:
        print("El ticker no puede estar vacío.")
        return

    activo_existente = buscar_activo_por_ticker(conexion, ticker)
    if activo_existente:
        print(f"El ticker {ticker} ya existe registrado como {activo_existente['tipo_activo']}.")
        return

    try:
        id_activo = registrar_bono_nuevo(conexion, ticker)
        print(f"¡Éxito! Bono {ticker} registrado con ID {id_activo}.")
    except Exception as e:
        print(f"Error al dar de alta el bono: {e}")


def listar_bonos_registrados(conexion):
    """Muestra todos los bonos registrados en la base de datos."""
    print("\n--- Catálogo de Bonos Registrados ---")
    query = """
        SELECT a.id_activo, a.ticker, a.nombre, a.moneda, 
               b.tasa_cupon, b.frecuencia_pago, b.valor_nominal, b.emisor
        FROM activo a
        JOIN bond b ON a.id_activo = b.id_activo
        WHERE a.tipo_activo = 'BOND';
    """
    try:
        # Si usas ejecutar_sql con archivos o directamente la conexión:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(query)
        bonos = cursor.fetchall()
        cursor.close()

        if not bonos:
            print("No hay bonos registrados en el sistema.")
            return

        print(f"{'ID':<5} | {'Ticker':<10} | {'Nombre':<25} | {'Cupón %':<8} | {'Valor Nom.':<10} | {'Emisor':<12}")
        print("-" * 80)
        for b in bonos:
            print(f"{b['id_activo']:<5} | {b['ticker']:<10} | {b['nombre'][:24]:<25} | {b['tasa_cupon']:<8} | {b['valor_nominal']:<10} | {b['emisor']:<12}")
    except Exception as e:
        print(f"Error al consultar bonos: {e}")
# modifide end

# modifide start

def comprar_bono(conexion):
    print("\n--- Buy Bond ---")
    id_portafolio = pedir_entero("id_portafolio: ")
    ticker = input("Ticker del bono: ").strip().upper()
    cantidad = pedir_numero("Cantidad (unidades a comprar): ")
    precio = pedir_numero("Precio por unidad: ")
    fee = pedir_numero("Comisión / Fee (Enter o 0 si no aplica): ") or 0.0
    notas = input("Notas u observaciones (opcional): ").strip() or "Compra de bono registrada desde menú"

    try:
        activo = buscar_activo_por_ticker(conexion, ticker)
        if activo is None:
            registrar_bono_nuevo(conexion, ticker)
        elif activo["tipo_activo"] != "BOND":
            print(f"Error: {ticker} ya existe pero es tipo {activo['tipo_activo']}, no BOND.")
            return

        # --- LLAMADA DIRECTA AL STORED PROCEDURE ---
        cursor = conexion.cursor()
        parametros = [id_portafolio, ticker, 'BUY', cantidad, precio, fee, notas]
        
        cursor.callproc('p_ejecutar_operacion_bono', parametros)
        conexion.commit()
        cursor.close()

        print(f"Compra de bono ejecutada exitosamente ({cantidad} unidades de {ticker} a ${precio:.2f}).")

    except Exception as e:
        conexion.rollback()
        print(f"Error al registrar la compra del bono: {e}")


def vender_bono(conexion):
    print("\n--- Sell Bond ---")
    id_portafolio = pedir_entero("id_portafolio: ")
    ticker = input("Ticker del bono: ").strip().upper()
    cantidad = pedir_numero("Cantidad a vender: ")
    precio = pedir_numero("Precio por unidad: ")
    fee = pedir_numero("Comisión / Fee (Enter o 0 si no aplica): ") or 0.0
    notas = input("Notas u observaciones (opcional): ").strip() or "Venta de bono registrada desde menú"

    try:
        activo = buscar_activo_por_ticker(conexion, ticker)
        if activo is None:
            print(f"Error: el ticker {ticker} no existe. No se puede vender un bono que nunca se compró.")
            return
        if activo["tipo_activo"] != "BOND":
            print(f"Error: {ticker} no es un BOND (es {activo['tipo_activo']}).")
            return

        # --- LLAMADA DIRECTA AL STORED PROCEDURE ---
        cursor = conexion.cursor()
        parametros = [id_portafolio, ticker, 'SELL', cantidad, precio, fee, notas]
        
        cursor.callproc('p_ejecutar_operacion_bono', parametros)
        conexion.commit()
        cursor.close()

        print(f"Venta de bono ejecutada exitosamente ({cantidad} unidades de {ticker} a ${precio:.2f}).")

    except Exception as e:
        conexion.rollback()
        print(f"Error al registrar la venta del bono: {e}")

# modifide end

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
        filas = ejecutar_sql(conexion, "reports/performance.sql", (id_portafolio, id_portafolio, id_portafolio))
        mostrar_filas(filas)
    except Exception as e:
        print(f"Error al consultar resumen de performance: {e}")

# -- llamado de consultar --
import os

RUTA_CONSULTAS = os.path.join("info", "consultas_sql")


def cargar_sql_desde_archivo(num_consulta):
    """Lee el contenido SQL de un archivo de manera segura con codificación UTF-8."""
    nombre_archivo = f"consulta_{int(num_consulta):02d}.sql"
    ruta_archivo = os.path.join(RUTA_CONSULTAS, nombre_archivo)

    if not os.path.exists(ruta_archivo):
        print(f"Error: No se encontró el archivo '{ruta_archivo}'.")
        return None

    try:
        with open(ruta_archivo, "r", encoding="utf-8") as file:
            sql = file.read().strip()
            # Si el script termina con punto y coma, se remueve para evitar errores con conectores de MySQL
            if sql.endswith(";"):
                sql = sql[:-1]
            return sql
    except Exception as e:
        print(f"Error al leer el archivo '{ruta_archivo}': {e}")
        return None


def ejecutar_consulta_menu(conexion, num_consulta, titulo):
    """Carga y ejecuta la consulta SQL individual."""
    print(f"\n--- {titulo} ---")

    sql = cargar_sql_desde_archivo(num_consulta)
    if not sql:
        return

    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(sql)
        resultados = cursor.fetchall()
        cursor.close()

        if not resultados:
            print("La consulta se ejecutó correctamente pero no devolvió datos.")
            return

        # Impresión tabular de resultados
        columnas = list(resultados[0].keys())
        header = " | ".join([f"{col:<20}" for col in columnas])
        print(header)
        print("-" * len(header))

        for fila in resultados:
            valores = [
                str(fila[col]) if fila[col] is not None else "NULL"
                for col in columnas
            ]
            print(" | ".join([f"{val[:19]:<20}" for val in valores]))

    except Exception as e:
        print(f"Error al ejecutar la consulta #{num_consulta}: {e}")



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


def menu_gestion_bonos(conexion):
    """Menú secundario para administrar el catálogo de renta fija."""
    while True:
        print("\n==================================")
        print("    ADMINISTRACIÓN DE BONOS")
        print("==================================")
        print("1. Registrar nuevo bono manualmente")
        print("2. Ver catálogo de bonos registrados")
        print("3. Comprar bono")
        print("4. Vender bono")
        print("5. Transaction History")
        print("6. Volver al menú principal")
        
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            registrar_bono_manual_menu(conexion)
        elif opcion == "2":
            listar_bonos_registrados(conexion)
        elif opcion == "3":
            comprar_bono(conexion)
        elif opcion == "4":
            vender_bono(conexion)
        elif opcion == "5":
            ver_historial(conexion)
        elif opcion == "6":
            break
        else:
            print("Opción inválida, intente de nuevo.")

def menu_consultas(conexion):
    """Menú interactivo de selección de reportes SQL."""
    while True:
        print("\n=========================================================")
        print("                 MENÚ DE CONSULTAS Y REPORTES            ")
        print("=========================================================")
        print("--- Nivel 1: Bajas ---")
        print(" 1. Clientes registrados (ordenados por fecha)")
        print(" 2. Activos EQUITY en NASDAQ")
        print(" 3. Portafolios MODERADO/AGRESIVO con cash > $1,000")
        print(" 4. Bonos con calificación 'AAA' y cupones")
        print(" 5. Empresas de 'Technology' con próximos resultados")
        print("\n--- Nivel 2: Intermedias ---")
        print(" 6. Cantidad de portafolios por cliente")
        print(" 7. Valor total en posiciones por portafolio")
        print(" 8. Total invertido por activo (custodia y mercado)")
        print(" 9. Total de comisiones (fees) por portafolio")
        print("10. Activos con P/E < 25 y Dividend Yield > 1%")
        print("\n--- Nivel 3: Avanzadas ---")
        print("11. Patrimonio neto total acumulado por cliente")
        print("12. Posición con mayor ganancia no realizada por portafolio")
        print("13. Variación diaria de precios de cierre (LAG)")
        print("14. Ranking de portafolios por Sharpe Ratio")
        print("15. Portafolios con efectivo > 30 del patrimonio")
        print("---------------------------------------------------------")
        print(" 0. Volver al Menú Principal")
        print("=========================================================")

        opcion = input("Seleccione una consulta a ejecutar (0-15): ").strip()

        opciones_map = {
            "1": (1, "Clientes Registrados"),
            "2": (2, "Activos EQUITY en NASDAQ"),
            "3": (3, "Portafolios con Cash > $1,000"),
            "4": (4, "Bonos Calificación AAA"),
            "5": (5, "Resultados Sector Tecnología"),
            "6": (6, "Portafolios Activos por Cliente"),
            "7": (7, "Inversión Total en Posiciones"),
            "8": (8, "Capital Total Invertido por Activo"),
            "9": (9, "Comisiones Pagadas por Portafolio"),
            "10": (10, "Activos Valor / Dividendos"),
            "11": (11, "Patrimonio Total por Cliente"),
            "12": (12, "Mayor Ganancia No Realizada"),
            "13": (13, "Variación Diaria de Precios"),
            "14": (14, "Ranking Sharpe Ratio"),
            "15": (15, "Portafolios Liquidez > 30%"),
        }

        if opcion == "0":
            break
        elif opcion in opciones_map:
            num_q, titulo_q = opciones_map[opcion]
            ejecutar_consulta_menu(conexion, num_q, titulo_q)
            input("\nPresione ENTER para continuar...")
        else:
            print("Opción no válida. Intente nuevamente.")

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
            print("2. Gestion de Transactions 'Equity'")
            print("3. Gestion de Bonos")
            print("4. Metricas de Acciones")
            print("5. Reports")
            print("6. Consultas y reportes SQL")
            print("7. Exit")
            print("=========================")

            opcion = input("Escribe tu opcion: ").strip()

            if opcion == "1":
                menu_portfolio(conexion)
            elif opcion == "2":
                menu_transactions(conexion)
            elif opcion == "3":
                menu_gestion_bonos(conexion)
            elif opcion == "4":
                menu_screener(conexion)
            elif opcion == "5":
                menu_reports(conexion)
            elif opcion == "6":
                menu_consultas(conexion)
            elif opcion == "7":
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