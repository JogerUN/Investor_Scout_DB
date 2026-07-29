import logging
import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import DBConnectionManager

logger = logging.getLogger(__name__)

SQL_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "info",
    "InvestorScout_FINAL_v4.sql",
)


# ----------------------------------------------------------------------
# 1. PARSER CONSCIENTE DE DELIMITER
# ----------------------------------------------------------------------
# El archivo .sql usa `DELIMITER $$` para poder escribir bloques
# BEGIN...END con punto y coma internos (funciones, triggers, procedimientos).
# `DELIMITER` es una instrucción del CLIENTE de MySQL (Workbench, consola),
# el conector de Python NO la entiende — así que la interpretamos nosotros
# mismos aquí y partimos el archivo en sentencias completas y válidas.
def _split_statements(raw_sql: str):
    statements = []
    delimiter = ";"
    buffer = []

    for line in raw_sql.splitlines():
        stripped = line.strip()

        # Comentarios de línea completa: se ignoran
        if not stripped or stripped.startswith("--") or stripped.startswith("#"):
            continue

        # Cambio de delimitador (ej. "DELIMITER $$" o "DELIMITER ;")
        m = re.match(r"^DELIMITER\s+(\S+)\s*$", stripped, re.IGNORECASE)
        if m:
            # Si había algo pendiente en buffer con el delimitador anterior, ciérralo
            pending = "\n".join(buffer).strip()
            if pending:
                statements.append(pending)
            buffer = []
            delimiter = m.group(1)
            continue

        buffer.append(line)

        # ¿La línea actual completa una sentencia con el delimitador vigente?
        joined = "\n".join(buffer)
        if joined.rstrip().endswith(delimiter):
            stmt = joined.rstrip()
            stmt = stmt[: -len(delimiter)].strip()
            if stmt:
                statements.append(stmt)
            buffer = []

    # cualquier resto sin cerrar (no debería pasar en un archivo bien formado)
    remainder = "\n".join(buffer).strip()
    if remainder:
        statements.append(remainder)

    return statements


def _read_statements(skip_database_statements: bool = True):
    if not os.path.exists(SQL_FILE_PATH):
        raise FileNotFoundError(f"No se encontró el archivo de esquema: {SQL_FILE_PATH}")

    with open(SQL_FILE_PATH, "r", encoding="utf-8") as f:
        raw = f.read()

    statements = _split_statements(raw)

    if skip_database_statements:
        # La creación/selección de la base de datos ya la maneja
        # DBConnectionManager a partir de config/db_config.json.
        statements = [
            s for s in statements
            if not s.upper().startswith("DROP DATABASE")
            and not s.upper().startswith("CREATE DATABASE")
            and not s.upper().startswith("USE ")
        ]

    return statements


# ----------------------------------------------------------------------
# 2. IDEMPOTENCIA: DROP ... IF EXISTS antes de cada CREATE FUNCTION/
#    PROCEDURE/TRIGGER, porque MySQL no soporta "CREATE ... IF NOT EXISTS"
#    para estos objetos (solo para tablas). Sin esto, correr el programa
#    una segunda vez truena con "already exists".
# ----------------------------------------------------------------------
_OBJECT_PATTERNS = [
    ("FUNCTION", re.compile(r"^CREATE\s+FUNCTION\s+`?(\w+)`?", re.IGNORECASE)),
    ("PROCEDURE", re.compile(r"^CREATE\s+PROCEDURE\s+`?(\w+)`?", re.IGNORECASE)),
    ("TRIGGER", re.compile(r"^CREATE\s+TRIGGER\s+`?(\w+)`?", re.IGNORECASE)),
]


def _drop_if_exists_statement(stmt: str):
    """Si stmt es un CREATE FUNCTION/PROCEDURE/TRIGGER, devuelve el DROP
    IF EXISTS correspondiente. Si no aplica, devuelve None."""
    for obj_type, pattern in _OBJECT_PATTERNS:
        m = pattern.match(stmt.strip())
        if m:
            name = m.group(1)
            return f"DROP {obj_type} IF EXISTS {name}"
    return None


# ----------------------------------------------------------------------
def initialize_database() -> bool:
    """
    Crea la base de datos (si no existe) y todas las tablas/funciones/
    triggers/procedimientos del esquema. Es seguro llamarla en cada
    arranque: nunca elimina datos ya guardados (tablas usan
    IF NOT EXISTS; funciones/triggers/procedimientos se recrean vía
    DROP IF EXISTS + CREATE, lo cual no afecta datos, solo la definición
    del objeto).
    """
    print("--- Investor Scout: verificando base de datos y esquema completo ---")
    conn = None
    cursor = None
    try:
        statements = _read_statements(skip_database_statements=True)

        conn = DBConnectionManager.get_connection()
        cursor = conn.cursor()

        count = 0
        for stmt in statements:
            drop_stmt = _drop_if_exists_statement(stmt)
            if drop_stmt:
                cursor.execute(drop_stmt)


            cursor.execute(stmt)
            # Si la sentencia fue un SELECT (no debería quedar ninguno tras
            # limpiar el script, pero por seguridad) hay que vaciar el
            # resultado o la siguiente execute() truena con
            # "Unread result found".
            if cursor.with_rows:
                cursor.fetchall()
            count += 1

        conn.commit()
        print(f"[OK] {count} sentencias ejecutadas. Esquema (tablas, funciones, triggers, procedimientos) listo.")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar la base de datos: {e}")
        if conn:
            conn.rollback()
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
    import json
    import mysql.connector

    print("--- Investor Scout: REINICIO COMPLETO de la base de datos ---")
    try:
        with open(SQL_FILE_PATH, "r", encoding="utf-8") as f:
            raw = f.read()

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

        statements = _split_statements(raw)

        count = 0
        for stmt in statements:
            drop_stmt = _drop_if_exists_statement(stmt)
            if drop_stmt:
                cursor.execute(drop_stmt)


            cursor.execute(stmt)
            if cursor.with_rows:
                cursor.fetchall()
            count += 1

        conn.commit()
        cursor.close()
        conn.close()
        print(f"[OK] Base de datos reiniciada desde cero. {count} sentencias ejecutadas.")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo reiniciar la base de datos: {e}")
        return False


if __name__ == "__main__":
    initialize_database()