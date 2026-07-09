from sqlalchemy.orm import Session
from src.models.deuda import Deuda
from src.models.database import SessionLocal
from src.utils.logger import setup_logger

logger = setup_logger("etl-postgres")


class PostgresLoader:
    def __init__(self):
        self.db: Session = SessionLocal()

    def load_deudas(self, deudas_data: list, lote_etl: str = "MIGRACION"):
        count = 0
        for d in deudas_data:
            deuda = Deuda(
                id_contribuyente=d["id_contribuyente"],
                id_lote=d.get("id_lote"),
                id_tipo_tributo=d["id_tipo_tributo"],
                id_estado_cobranza=1,
                numero_resolucion=d.get("numero_resolucion"),
                anio_tributo=d["anio_tributo"],
                periodo=d.get("periodo"),
                monto_original=d["monto_original"],
                saldo_pendiente=d["saldo_pendiente"],
                monto_pagado=d.get("monto_pagado", 0),
                fecha_emision=d.get("fecha_emision"),
                fecha_vencimiento=d.get("fecha_vencimiento"),
                lote_etl=lote_etl,
                origen_dato="ORACLE"
            )
            self.db.add(deuda)
            count += 1
        self.db.commit()
        logger.info(f"Cargadas {count} deudas al lote {lote_etl}")
        return count

    def close(self):
        self.db.close()