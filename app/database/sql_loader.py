"""
Lee archivos .sql de la carpeta info/sql/ y los ejecuta.

Sirve tanto para SELECT (te devuelve las filas) como para
INSERT/DELETE/CALL (hace commit solo y devuelve una lista vacia,
o las filas si el CALL trae un SELECT adentro).
"""
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = os.path.join(PROJECT_ROOT, "info", "sql")


def _es_call(consulta):
    """
    Revisa la primera linea con codigo real (saltando comentarios y
    lineas vacias) para saber si la sentencia es un CALL a procedimiento.
    """
    for linea in consulta.splitlines():
        limpio = linea.strip()
        if not limpio or limpio.startswith("--"):
            continue
        return limpio.upper().startswith("CALL")
    return False


def ejecutar_sql(conexion, archivo, parametros=None):
    """
    archivo: ruta relativa dentro de info/sql, ej: "portfolio/positions.sql"
    parametros: tupla con los valores para los %s del archivo, en orden.
    """
    ruta = os.path.join(BASE_DIR, archivo)
    with open(ruta, "r", encoding="utf-8") as f:
        consulta = f.read()

    cursor = conexion.cursor(dictionary=True)
    filas = []
    try:
        print("=" * 60)
        print("SQL que se ejecutara")
        print(consulta)
        print()
        print("PARAMETROS")
        print(parametros)
        print("=" * 60)

        if _es_call(consulta):
            # Para CALL, usamos execute() normal y iteramos sobre los result sets con stored_results()
            cursor.execute(consulta, parametros or ())
            for result in cursor.stored_results():
                filas.extend(result.fetchall())
        else:
            # Para SELECT/INSERT/DELETE/UPDATE normales
            cursor.execute(consulta, parametros or ())
            if cursor.with_rows:
                filas = cursor.fetchall()

        conexion.commit()
        print("COMMIT REALIZADO")

    finally:
        cursor.close()
        print("FILAS DEVUELTAS")
        print(filas)

    return filas


def ejecutar_insert_y_devolver_id(conexion, archivo, parametros=None):
    """
    Ejecuta un INSERT desde un archivo .sql y devuelve el ID generado (lastrowid).
    
    archivo: ruta relativa dentro de info/sql, ej: "bond/create_bond_asset.sql"
    parametros: tupla con los valores para los %s del archivo.
    """
    ruta = os.path.join(BASE_DIR, archivo)
    with open(ruta, "r", encoding="utf-8") as f:
        consulta = f.read()

    cursor = conexion.cursor()
    last_id = None
    try:
        print("=" * 60)
        print("SQL INSERT (Devolviendo ID)")
        print(consulta)
        print()
        print("PARAMETROS")
        print(parametros)
        print("=" * 60)

        cursor.execute(consulta, parametros or ())
        last_id = cursor.lastrowid

        conexion.commit()
        print(f"COMMIT REALIZADO - ID generado: {last_id}")

    finally:
        cursor.close()

    return last_id