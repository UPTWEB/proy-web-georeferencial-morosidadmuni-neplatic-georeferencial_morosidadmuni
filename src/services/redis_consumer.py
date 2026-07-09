import threading
import json
import redis
from src.utils.logger import setup_logger
from src.utils.config import redis_settings

logger = setup_logger("redis_consumer")

class RedisConsumer(threading.Thread):
    def __init__(self, callback):
        super().__init__(daemon=True)
        self.callback = callback
        self._config = redis_settings
        self._running = True
        self._client = None
        self._pubsub = None

    def run(self):
        try:
            self._client = redis.Redis(**self._config.get_connection_kwargs())
            self._pubsub = self._client.pubsub()
            self._pubsub.subscribe(self._config.channel)
            logger.info("Suscrito al canal de Redis: %s", self._config.channel)
            
            for message in self._pubsub.listen():
                if not self._running:
                    break
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        self.callback(data)
                    except json.JSONDecodeError:
                        logger.error("Error decodificando mensaje de Redis: %s", message['data'])
                    except Exception as e:
                        logger.error("Error en el callback de Redis: %s", e)
        except Exception as e:
            logger.error("Error conectando Redis Consumer: %s", e)

    def stop(self):
        self._running = False
        if self._pubsub:
            try:
                self._pubsub.unsubscribe()
                self._pubsub.close()
            except:
                pass
        if self._client:
            try:
                self._client.close()
            except:
                pass
