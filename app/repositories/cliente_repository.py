from typing import List, Optional
from app.repositories.base_repository import BaseRepository
from app.models.domain import Cliente

class ClienteRepository(BaseRepository):
    """
    Repository for the 'cliente' table in MySQL.
    """
    

    def save(self, cliente: Cliente) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO cliente (nombre, apellido, email, password_hash, telefono)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                cliente.nombre,
                cliente.apellido,
                cliente.email,
                cliente.password_hash,
                cliente.telefono
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_by_id(self, id_cliente: int) -> Optional[Cliente]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id_cliente, nombre, apellido, email, password_hash, telefono FROM cliente WHERE id_cliente = %s"
            cursor.execute(query, (id_cliente,))
            row = cursor.fetchone()
            if row:
                return Cliente(
                    id_cliente=row["id_cliente"],
                    nombre=row["nombre"],
                    apellido=row["apellido"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    telefono=row["telefono"]
                )
            return None
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_by_email(self, email: str) -> Optional[Cliente]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id_cliente, nombre, apellido, email, password_hash, telefono FROM cliente WHERE email = %s"
            cursor.execute(query, (email,))
            row = cursor.fetchone()
            if row:
                return Cliente(
                    id_cliente=row["id_cliente"],
                    nombre=row["nombre"],
                    apellido=row["apellido"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    telefono=row["telefono"]
                )
            return None
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_all(self) -> List[Cliente]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id_cliente, nombre, apellido, email, password_hash, telefono FROM cliente"
            cursor.execute(query)
            rows = cursor.fetchall()
            return [
                Cliente(
                    id_cliente=row["id_cliente"],
                    nombre=row["nombre"],
                    apellido=row["apellido"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    telefono=row["telefono"]
                )
                for row in rows
            ]
        finally:
            cursor.close()
            self.close_connection(conn)