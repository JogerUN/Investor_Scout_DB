from typing import Optional

from app.models.domain import EquityDetails
from app.repositories.base_repository import BaseRepository


class EquityRepository(BaseRepository):
    """
    Repository for the 'equity' table.

    NOTA IMPORTANTE: la tabla 'equity' del esquema tiene una llave primaria
    compuesta (id_activo, id_equity) y 'id_equity' es NOT NULL sin valor por
    defecto ni AUTO_INCREMENT. Como cada activo EQUITY tiene una única fila
    de detalles (relación 1:1 con 'activo'), reutilizamos el mismo valor de
    id_activo también como id_equity. Esto evita el error de MySQL
    "Field 'id_equity' doesn't have a default value".
    """
    def save(self, details: EquityDetails):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO equity (id_equity, id_activo, sector, industria, earnings_date)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    sector = VALUES(sector),
                    industria = VALUES(industria),
                    earnings_date = VALUES(earnings_date)
            """
            cursor.execute(query, (
                details.id_activo, # id_equity = id_activo (relación 1:1)
                details.id_activo,  
                details.sector,
                details.industria,
                details.earnings_date
            ))
            conn.commit()
        finally:
            cursor.close()
            self.close_connection(conn)

    def get_by_id(self, id_activo: int) -> Optional[EquityDetails]:
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id_activo, sector, industria, earnings_date FROM equity WHERE id_activo = %s"
            cursor.execute(query, (id_activo,))
            row = cursor.fetchone()
            if row:
                return EquityDetails(
                    id_activo=row["id_activo"],
                    sector=row["sector"],
                    industria=row["industria"],
                    earnings_date=row["earnings_date"]
                )
            return None
        finally:
            cursor.close()
            self.close_connection(conn)
