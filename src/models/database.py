from contextlib import contextmanager
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from src.utils.config import db_settings

engine = create_engine(
    db_settings.get_connection_url(),
    pool_size=20,
    max_overflow=50,
    pool_recycle=1800,
    pool_pre_ping=True,
    pool_timeout=30,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
Base = declarative_base()


@contextmanager
def get_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
