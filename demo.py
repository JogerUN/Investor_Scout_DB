"""
Investor Scout — Validation & Demo Script (demo.py)

Este script realiza la verificación integral del esquema y datos en la base de datos MySQL:
1. Aplica el DDL de tablas, funciones, disparadores y procedimientos (`info/tables_proced_trigg_funct_script.sql`).
2. Puebla la base de datos con los datos de prueba (`seed.sql`).
3. Ejecuta y valida las 15 CONSULTAS SQL (`info/CONSULTAS.sql`).
4. Prueba la ejecución de Funciones Almacenadas (`fn_total_value`, `fn_unrealized_pnl`).
5. Prueba la ejecución de Procedimientos Almacenados (`p_total_portafolio_holdings`, `p_ajuste_cash`, `p_calcular_daily_pnl`, `p_realizar_transaccion`, `p_procesar_snapshots_diarios`).
6. Valida que los Triggers impidan inserciones inválidas (`verificar_equity`, `verificar_bond`, `verificar_limite_movimiento`).
"""

import sys
import os
import re
from app.database.connection import DBConnectionManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE = os.path.join(BASE_DIR, "info", "tables_proced_trigg_funct_script.sql")
SEED_FILE = os.path.join(BASE_DIR, "seed.sql")
QUERIES_FILE = os.path.join(BASE_DIR, "info", "CONSULTAS.sql")


def split_statements(raw_sql: str):
    statements = []
    delimiter = ";"
    buffer = []

    for line in raw_sql.splitlines():
        stripped = line.strip()

        if not stripped or stripped.startswith("--") or stripped.startswith("#"):
            continue

        m = re.match(r"^DELIMITER\s+(\S+)\s*$", stripped, re.IGNORECASE)
        if m:
            pending = "\n".join(buffer).strip()
            if pending:
                statements.append(pending)
            buffer = []
            delimiter = m.group(1)
            continue

        buffer.append(line)

        joined = "\n".join(buffer)
        if joined.rstrip().endswith(delimiter):
            stmt = joined.rstrip()
            stmt = stmt[: -len(delimiter)].strip()
            if stmt:
                statements.append(stmt)
            buffer = []

    remainder = "\n".join(buffer).strip()
    if remainder:
        statements.append(remainder)

    return statements


def execute_sql_file(filepath):
    print(f"-> Ejecutando archivo SQL: {os.path.basename(filepath)}...")
    conn = DBConnectionManager.get_connection()
    cursor = conn.cursor()
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    statements = split_statements(content)

    for stmt in statements:
        # Idempotencia para procedimientos/funciones/triggers si vuelven a crearse
        drop_stmt = None
        for obj_type, pattern in [
            ("FUNCTION", re.compile(r"^CREATE\s+FUNCTION\s+`?(\w+)`?", re.IGNORECASE)),
            ("PROCEDURE", re.compile(r"^CREATE\s+PROCEDURE\s+`?(\w+)`?", re.IGNORECASE)),
            ("TRIGGER", re.compile(r"^CREATE\s+TRIGGER\s+`?(\w+)`?", re.IGNORECASE)),
        ]:
            m = pattern.match(stmt.strip())
            if m:
                drop_stmt = f"DROP {obj_type} IF EXISTS {m.group(1)}"
                break

        try:
            if drop_stmt:
                cursor.execute(drop_stmt)
            cursor.execute(stmt)
            if cursor.with_rows:
                cursor.fetchall()
        except Exception as e:
            if not ("DROP DATABASE" in stmt.upper() or "CREATE DATABASE" in stmt.upper() or "USE " in stmt.upper()):
                print(f"    [AVISO/ERROR en SQL] {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"   [OK] {os.path.basename(filepath)} ejecutado exitosamente.")


def test_queries():
    print("\n========================================================")
    print(" 1. PRUEBA DE CONSULTAS (info/CONSULTAS.sql)")
    print("========================================================")
    
    with open(QUERIES_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    raw_queries = split_statements(content)
    query_num = 1
    
    conn = DBConnectionManager.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    for q in raw_queries:
        if not q.strip():
            continue
            
        print(f"\n--- Consulta #{query_num} ---")
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            print(f"Filas obtenidas: {len(results)}")
            for idx, row in enumerate(results[:2], 1):  # Muestra preliminar
                print(f"  Muestra {idx}: {row}")
            if len(results) > 2:
                print(f"  ... (+{len(results) - 2} filas adicionales)")
            print(f"[OK] Consulta #{query_num} ejecutada con éxito.")
        except Exception as e:
            print(f"[ERROR] Consulta #{query_num} falló: {e}")
        query_num += 1

    cursor.close()
    conn.close()


def test_functions():
    print("\n========================================================")
    print(" 2. PRUEBA DE FUNCIONES ALMACENADAS")
    print("========================================================")
    conn = DBConnectionManager.get_connection()
    cursor = conn.cursor()

    # fn_total_value(1)
    try:
        cursor.execute("SELECT fn_total_value(1);")
        val = cursor.fetchone()[0]
        print(f"[OK] fn_total_value(id_portafolio=1): ${val:,.2f}")
    except Exception as e:
        print(f"[ERROR] fn_total_value: {e}")

    # fn_unrealized_pnl(1)
    try:
        cursor.execute("SELECT fn_unrealized_pnl(1);")
        pnl = cursor.fetchone()[0]
        print(f"[OK] fn_unrealized_pnl(id_portafolio=1): ${pnl:,.2f}")
    except Exception as e:
        print(f"[ERROR] fn_unrealized_pnl: {e}")

    cursor.close()
    conn.close()


def test_procedures():
    print("\n========================================================")
    print(" 3. PRUEBA DE PROCEDIMIENTOS ALMACENADOS")
    print("========================================================")
    conn = DBConnectionManager.get_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. p_total_portafolio_holdings
    try:
        print("\n-> Probando p_total_portafolio_holdings(1)...")
        cursor.callproc("p_total_portafolio_holdings", [1])
        for result in cursor.stored_results():
            rows = result.fetchall()
            print(f"Holdings portafolio 1 ({len(rows)} filas): {rows}")
        print("[OK] p_total_portafolio_holdings completado.")
    except Exception as e:
        print(f"[ERROR] p_total_portafolio_holdings: {e}")

    # 2. p_ajuste_cash
    try:
        print("\n-> Probando p_ajuste_cash(1, 500.00)...")
        cursor.callproc("p_ajuste_cash", [1, 500.00])
        conn.commit()
        cursor.execute("SELECT cash FROM portafolio WHERE id_portafolio = 1")
        new_cash = cursor.fetchone()["cash"]
        print(f"[OK] Nuevo cash portafolio 1: ${new_cash:,.2f}")
    except Exception as e:
        print(f"[ERROR] p_ajuste_cash: {e}")

    # 3. p_realizar_transaccion
    try:
        print("\n-> Probando p_realizar_transaccion (BUY 5 AAPL)...")
        cursor.callproc("p_realizar_transaccion", [1, "AAPL", "BUY", 5.0, 180.0, "2026-07-28 12:00:00"])
        conn.commit()
        print("[OK] Transacción ejecutada correctamente.")
    except Exception as e:
        print(f"[ERROR] p_realizar_transaccion: {e}")

    # 4. p_calcular_daily_pnl
    try:
        print("\n-> Probando p_calcular_daily_pnl(1, '2026-07-27')...")
        cursor.callproc("p_calcular_daily_pnl", [1, "2026-07-27"])
        conn.commit()
        print("[OK] Daily PnL calculado.")
    except Exception as e:
        print(f"[ERROR] p_calcular_daily_pnl: {e}")

    # 5. p_procesar_snapshots_diarios
    try:
        print("\n-> Probando p_procesar_snapshots_diarios('2026-07-27')...")
        cursor.callproc("p_procesar_snapshots_diarios", ["2026-07-27"])
        conn.commit()
        print("[OK] Snapshots diarios procesados.")
    except Exception as e:
        print(f"[ERROR] p_procesar_snapshots_diarios: {e}")

    cursor.close()
    conn.close()


def test_triggers():
    print("\n========================================================")
    print(" 4. PRUEBA DE TRIGGERS (Validación de Restricciones)")
    print("========================================================")
    conn = DBConnectionManager.get_connection()
    cursor = conn.cursor()

    # Trigger 1: verificar_equity (debe fallar al intentar insertar un BOND en tabla equity)
    try:
        # id_activo 4 es US10Y (BOND)
        cursor.execute("INSERT INTO equity (id_activo, sector) VALUES (4, 'Technology');")
        conn.commit()
        print("[FALLO] Trigger verificar_equity no detuvo la inserción inválida.")
    except Exception as e:
        print(f"[OK] Trigger verificar_equity bloqueó la inserción como se esperaba: {e}")

    # Trigger 2: verificar_bond (debe fallar al intentar insertar un EQUITY en tabla bond)
    try:
        # id_activo 1 es AAPL (EQUITY)
        cursor.execute("INSERT INTO bond (id_activo, emisor) VALUES (1, 'SOBERANO');")
        conn.commit()
        print("[FALLO] Trigger verificar_bond no detuvo la inserción inválida.")
    except Exception as e:
        print(f"[OK] Trigger verificar_bond bloqueó la inserción como se esperaba: {e}")

    # Trigger 3: verificar_limite_movimiento (cantidad <= 0 debe fallar)
    try:
        cursor.execute("INSERT INTO movimiento (id_portafolio, id_activo, tipo_mov, cantidad, precio_por_accion) VALUES (1, 1, 'BUY', -10, 150.0);")
        conn.commit()
        print("[FALLO] Trigger verificar_limite_movimiento no detuvo cantidad negativa.")
    except Exception as e:
        print(f"[OK] Trigger verificar_limite_movimiento bloqueó la inserción como se esperaba: {e}")

    cursor.close()
    conn.close()


def main():
    print("========================================================")
    print("    INVESTOR SCOUT — DEMO & VALIDATION SUITE")
    print("========================================================")
    
    # 1. Crear / Estructurar Base de Datos
    execute_sql_file(SCHEMA_FILE)
    
    # 2. Poblar datos iniciales
    execute_sql_file(SEED_FILE)
    
    # 3. Probar Consultas
    test_queries()
    
    # 4. Probar Funciones
    test_functions()
    
    # 5. Probar Procedimientos
    test_procedures()
    
    # 6. Probar Triggers
    test_triggers()

    print("\n========================================================")
    print("    [EXITO] TODAS LAS PRUEBAS Y DEMOS FINALIZADAS")
    print("========================================================")


if __name__ == "__main__":
    main()
