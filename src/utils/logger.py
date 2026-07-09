import logging
import sys
from datetime import datetime
from sqlalchemy import text

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    return logger


def log_sistema(db_session, nivel: str, modulo: str, mensaje: str, usuario: str = None, ip_origen: str = None):
    from src.models.deuda import OutboxEvento
    db_session.execute(
        text("INSERT INTO neplatic.log_sistema (nivel, modulo, mensaje, usuario, ip_origen, fecha) VALUES (:nivel, :modulo, :mensaje, :usuario, :ip, :fecha)"),
        {"nivel": nivel, "modulo": modulo, "mensaje": mensaje, "usuario": usuario, "ip": ip_origen, "fecha": datetime.now()}
    )
    db_session.commit()