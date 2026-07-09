import oracledb
from typing import List, Dict
from src.utils.logger import setup_logger

logger = setup_logger("etl-oracle")


class OracleExtractor:
    def __init__(self, dsn: str, user: str, password: str):
        self.dsn = dsn
        self.user = user
        self.password = password
        self.connection = None

    def connect(self):
        self.connection = oracledb.connect(user=self.user, password=self.password, dsn=self.dsn)

    def extract_deudas(self, limit: int = 10000) -> List[Dict]:
        cursor = self.connection.cursor()
        cursor.execute(f"""
            SELECT id_deuda, id_contribuyente, id_lote, id_tipo_tributo, 
                   numero_resolucion, anio_tributo, periodo, monto_original,
                   saldo_pendiente, monto_pagado, fecha_emision, fecha_vencimiento
            FROM deudas_oracle WHERE ROWNUM <= :limit
        """, {"limit": limit})
        columns = [col[0].lower() for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def close(self):
        if self.connection:
            self.connection.close()