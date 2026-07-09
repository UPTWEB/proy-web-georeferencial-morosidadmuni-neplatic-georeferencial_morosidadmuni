import json
import redis
from src.utils.config import redis_settings
from src.utils.logger import setup_logger

logger = setup_logger("redis_publisher")


class RedisPublisher:
    def __init__(self):
        self._client = None
        self._config = redis_settings

    @property
    def client(self):
        if self._client is None:
            try:
                self._client = redis.Redis(**self._config.get_connection_kwargs())
                self._client.ping()
                logger.info("Conexion a Redis establecida en %s:%s", self._config.host, self._config.port)
            except Exception as e:
                logger.error("No se pudo conectar a Redis: %s", e)
                self._client = None
        return self._client

    def publish(self, event_type: str, aggregate_id: str, payload: dict) -> bool:
        try:
            if not self.client:
                logger.warning("Redis no disponible. El evento quedara en el outbox.")
                return False
            message = {
                "event_type": event_type,
                "aggregate_id": aggregate_id,
                "payload": payload,
            }
            self.client.publish(self._config.channel, json.dumps(message, ensure_ascii=False, default=str))
            logger.info("Evento publicado en Redis [%s]: %s / %s", self._config.channel, event_type, aggregate_id)
            return True
        except Exception as e:
            logger.error("Error al publicar en Redis: %s", e)
            self._client = None
            return False

    def close(self):
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
