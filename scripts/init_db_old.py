import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import DBConnectionManager

logger = logging.getLogger(__name__)

SQL_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "info",
    "InvestorScout_FINAL_v4.sql",
)


def _read_statements(skip_database_statements: bool = True):
    """
    Lee el archivo .sql y lo separa en sentencias individuales.
    Elimina comentarios de línea (--, #) antes de partir por ';', en vez de
    depender de que cada sentencia termine exactamente al final de una línea
    (el parser anterior fallaba con sentencias mal formateadas o con texto
    extra después del ';').
    """
    if not os.path.exists(SQL_FILE_PATH):
        raise FileNotFoundError(f"No se encontró el archivo de esquema: {SQL_FILE_PATH}")

    with open(SQL_FILE_PATH, "r", encoding="utf-8") as f:
        raw = f.read()

    cleaned_lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--") or stripped.startswith("#"):
            continue
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    statements = [s.strip() for s in cleaned.split(";") if s.strip()]

    if skip_database_statements:
        # La creación/selección de la base de datos ya la maneja
        # DBConnectionManager a partir de config/db_config.json.
        # Omitimos aquí DROP DATABASE / CREATE DATABASE / USE para que
        # inicializar la app en cada arranque NUNCA borre datos existentes.
        statements = [
            s for s in statements
            if not s.upper().startswith("DROP DATABASE")
            and not s.upper().startswith("CREATE DATABASE")
            and not s.upper().startswith("USE ")
        ]

    return statements


def initialize_database() -> bool:
    """
    Crea la base de datos (si no existe) y todas las tablas del esquema
    (CREATE TABLE IF NOT EXISTS). Es seguro llamarla en cada arranque:
    nunca elimina datos ya guardados.
    """
    print("--- Investor Scout: verificando base de datos y tablas ---")
    conn = None
    cursor = None
    try:
        statements = _read_statements(skip_database_statements=True)

        conn = DBConnectionManager.get_connection()
        cursor = conn.cursor()

        count = 0
        for stmt in statements:
            cursor.execute(stmt)
            count += 1

        conn.commit()
        print(f"[OK] {count} sentencias ejecutadas. Tablas listas.")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar la base de datos: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def reset_database() -> bool:
    """
    PELIGRO: ejecuta el script completo, incluyendo DROP DATABASE / CREATE DATABASE.
    Borra todos los datos existentes y vuelve a crear el esquema desde cero.
    Solo debe invocarse explícitamente (nunca automáticamente al arrancar).
    """
    import mysql.connector

    print("--- Investor Scout: REINICIO COMPLETO de la base de datos ---")
    try:
        with open(SQL_FILE_PATH, "r", encoding="utf-8") as f:
            raw = f.read()

        # Para el reinicio completo sí necesitamos ejecutar DROP/CREATE DATABASE,
        # por lo que usamos una conexión sin base de datos preseleccionada.
        import json
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "db_config.json",
        )
        with open(config_path, "r") as f:
            config = json.load(f)

        conn = mysql.connector.connect(
            host=config.get("host", "127.0.0.1"),
            port=int(config.get("port", 3306)),
            user=config.get("user", "root"),
            password=config.get("password", ""),
        )
        cursor = conn.cursor()

        cleaned_lines = []
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("--") or stripped.startswith("#"):
                continue
            cleaned_lines.append(line)
        cleaned = "\n".join(cleaned_lines)
        statements = [s.strip() for s in cleaned.split(";") if s.strip()]

        count = 0
        for stmt in statements:
            cursor.execute(stmt)
            count += 1

        conn.commit()
        cursor.close()
        conn.close()
        print(f"[OK] Base de datos reiniciada. {count} sentencias ejecutadas.")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo reiniciar la base de datos: {e}")
        return False


if __name__ == "__main__":
    initialize_database()
