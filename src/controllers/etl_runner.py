import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.etl.oracle_extractor import OracleExtractor
from src.services.etl.postgres_loader import PostgresLoader
from src.utils.logger import setup_logger

logger = setup_logger("etl-main")


def run_etl():
    import time
    logger.info("Iniciando proceso ETL simulado...")
    time.sleep(2) # Simular tiempo de extracción
    
    msg = "ETL Simulado completado exitosamente (Sin conexión a Oracle)"
    logger.info(msg)
    return True, msg


if __name__ == "__main__":
    run_etl()