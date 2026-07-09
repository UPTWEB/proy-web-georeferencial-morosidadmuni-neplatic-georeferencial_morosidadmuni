import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class DatabaseConfig:
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    database: str = os.getenv("DB_NAME", "neplatic")
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "")
    schema: str = os.getenv("DB_SCHEMA", "neplatic")

    def get_connection_url(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    password: str = os.getenv("REDIS_PASSWORD", "")
    channel: str = os.getenv("REDIS_CHANNEL", "neplatic.rutas")

    def get_connection_kwargs(self) -> dict:
        kwargs = {
            "host": self.host,
            "port": self.port,
            "decode_responses": True,
        }
        if self.password:
            kwargs["password"] = self.password
        return kwargs


db_settings = DatabaseConfig()
redis_settings = RedisConfig()