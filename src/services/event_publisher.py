import json
from datetime import datetime
from src.models.database import get_session
from src.models.deuda import OutboxEvento
from src.utils.logger import setup_logger

logger = setup_logger("events")


class EventPublisher:
    def publish(self, aggregate_type: str, aggregate_id: str, event_type: str, payload: dict) -> int | None:
        with get_session() as db:
            try:
                evento = OutboxEvento(
                    aggregate_type=aggregate_type,
                    aggregate_id=aggregate_id,
                    event_type=event_type,
                    payload=json.dumps(payload, ensure_ascii=False, default=str),
                )
                db.add(evento)
                db.commit()
                db.refresh(evento)
                logger.info("Evento outbox registrado: %s para %s/%s", event_type, aggregate_type, aggregate_id)
                return evento.id_outbox
            except Exception as e:
                db.rollback()
                logger.error("Error al registrar evento outbox: %s", e)
                return None

    def get_pending_events(self, limit: int = 100):
        with get_session() as db:
            return db.query(OutboxEvento).filter(OutboxEvento.publicado == False).order_by(OutboxEvento.fecha_creacion.asc()).limit(limit).all()

    def mark_as_published(self, event_id: int):
        with get_session() as db:
            try:
                evento = db.query(OutboxEvento).filter(OutboxEvento.id_outbox == event_id).first()
                if evento:
                    evento.publicado = True
                    evento.fecha_publicacion = datetime.now()
                    db.commit()
                return evento
            except Exception as e:
                db.rollback()
                logger.error("Error al marcar evento como publicado: %s", e)
                return None

    def close(self):
        pass
