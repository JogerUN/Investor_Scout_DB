"""
Lee archivos .sql de la carpeta info/sql/ y los ejecuta.

Sirve tanto para SELECT (te devuelve las filas) como para
INSERT/DELETE/CALL (hace commit solo y devuelve una lista vacia,
o las filas si el CALL trae un SELECT adentro).
"""
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = os.path.join(PROJECT_ROOT, "info", "sql")

def ejecutar_sql(conexion, archivo, parametros=None):
    """
    archivo: ruta relativa dentro de info/sql, ej: "portfolio/positions.sql"
    parametros: tupla con los valores para los %s del archivo, en orden.
    """
    ruta = os.path.join(BASE_DIR, archivo)
    with open(ruta, "r", encoding="utf-8") as f:
        consulta = f.read().strip()

    cursor = conexion.cursor(dictionary=True)
    filas = []
    try:
        cursor.execute(consulta, parametros)
        if cursor.with_rows:
            filas.extend(cursor.fetchall())
        
        # Si la consulta devuelve multiples result sets (ej: CALL procedimieto)
        if hasattr(cursor, 'stored_results'):
            for res in cursor.stored_results():
                if res.with_rows:
                    filas.extend(res.fetchall())

        conexion.commit()
    finally:
        cursor.close()

    return filas