from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from src.models.database import Base


class OutboxEvento(Base):
    __tablename__ = "outbox_evento"
    __table_args__ = {"schema": "neplatic"}

    id_outbox = Column(Integer, primary_key=True)
    aggregate_type = Column(String(50), nullable=False)
    aggregate_id = Column(String(50), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(String, nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now())
    publicado = Column(Boolean, default=False)
    fecha_publicacion = Column(DateTime)
    intentos = Column(Integer, default=0)
    error = Column(String)