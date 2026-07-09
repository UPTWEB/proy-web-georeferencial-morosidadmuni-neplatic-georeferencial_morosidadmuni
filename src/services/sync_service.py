import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime

import requests
from sqlalchemy import text

from src.models.database import SessionLocal
from src.models.deuda import LogSincronizacion, RutaDetalle, RutaNotificacion
from src.utils.logger import setup_logger

logger = setup_logger("sync_service")


class SyncService:
    CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scratch")
    CACHE_FILE = os.path.join(CACHE_DIR, "sync_queue.json")
    HMAC_SECRET = b"neplatic-desktop-secret-sync-key-2026"

    def __init__(self):
        self.api_base_url = os.getenv("WEB_API_BASE_URL", "").rstrip("/")
        self.api_token = os.getenv("WEB_API_TOKEN", "")
        self.device_id = os.getenv("DEVICE_ID", "DESKTOP-NEPLATIC-01")
        self.session = requests.Session()
        if self.api_token:
            self.session.headers.update({"Authorization": f"Bearer {self.api_token}"})
        self.session.headers.update({"Content-Type": "application/json"})

        if not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR)
        if not os.path.exists(self.CACHE_FILE):
            self._write_cache({"pending": []})

    def _read_cache(self) -> dict:
        try:
            with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "pending" not in data:
                data = {"pending": []}
            return data
        except Exception:
            return {"pending": []}

    def _write_cache(self, data: dict):
        with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def check_online_status(self) -> bool:
        if self.api_base_url:
            try:
                url = f"{self.api_base_url}/health"
                response = self.session.get(url, timeout=5)
                return response.status_code < 500
            except Exception as e:
                logger.warning(f"Estado offline hacia API detectado: {e}")
                return False

        db = None
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.warning(f"Estado offline detectado: {e}")
            return False
        finally:
            if db:
                db.close()

    def firmar_payload(self, payload: str) -> str:
        return hmac.new(self.HMAC_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    def _append_pending(self, record: dict):
        cache = self._read_cache()
        cache["pending"].append(record)
        self._write_cache(cache)

    def _replace_pending(self, pending: list[dict]):
        self._write_cache({"pending": pending})

    def _payload_for_ruta(self, id_usuario: int, total_deudas: int, deudas: list, distancia_km: float) -> dict:
        return {
            "entity_type": "ruta",
            "action": "create",
            "device_id": self.device_id,
            "payload": {
                "id_usuario": id_usuario,
                "total_deudas": total_deudas,
                "deudas": deudas,
                "distancia_km": distancia_km,
                "fecha": datetime.now().strftime("%Y-%m-%d"),
            },
        }

    def _payload_for_notificacion(self, notif: dict) -> dict:
        return {
            "entity_type": "notificacion",
            "action": "create",
            "device_id": self.device_id,
            "payload": {
                "id_notificacion": notif.get("id_notificacion"),
                "id_deuda": notif.get("id_deuda"),
                "id_usuario": notif.get("id_usuario"),
                "id_estado_notif": notif.get("id_estado_notif"),
                "direccion_visitada": notif.get("direccion_visitada", ""),
                "persona_contactada": notif.get("persona_contactada", ""),
                "parentesco": notif.get("parentesco", ""),
                "fecha_registro": notif.get("fecha_registro") or datetime.now().isoformat(),
            },
        }

    def _api_endpoint_for_record(self, record: dict) -> str:
        entity = record.get("entity_type")
        action = record.get("action", "create")
        if entity == "ruta":
            return f"/api/v1/rutas"
        if entity == "notificacion":
            return f"/api/v1/notificaciones"
        if entity == "sector":
            return "/api/v1/sectores"
        if entity == "zona":
            return "/api/v1/zonas"
        if entity == "asignacion":
            return "/api/v1/asignaciones"
        return f"/api/v1/sync/{entity}/{action}"

    def _send_record_to_api(self, record: dict) -> tuple[bool, str]:
        if not self.api_base_url:
            return False, "No se configuró WEB_API_BASE_URL"
        try:
            endpoint = self._api_endpoint_for_record(record)
            payload = {
                "device_id": self.device_id,
                "entity_type": record["entity_type"],
                "action": record.get("action", "create"),
                "payload": record["payload"],
                "signature": self.firmar_payload(json.dumps(record["payload"], ensure_ascii=False, sort_keys=True)),
                "client_timestamp": record.get("client_timestamp") or datetime.now().isoformat(),
            }
            response = self.session.post(f"{self.api_base_url}{endpoint}", data=json.dumps(payload), timeout=12)
            if response.status_code >= 400:
                return False, f"HTTP {response.status_code}: {response.text[:240]}"
            return True, response.text
        except Exception as e:
            return False, str(e)

    def _log_sync(self, batch_id: str, tabla: str, estado: str, registros: int = 0, error: str | None = None):
        db = SessionLocal()
        try:
            log = LogSincronizacion(
                sync_batch_id=batch_id,
                device_uuid=self.device_id,
                tabla_sincronizada=tabla,
                registros_afectados=registros,
                estado=estado,
                error_detalle=error,
            )
            db.add(log)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"No fue posible registrar el log de sincronización: {e}")
        finally:
            db.close()

    def sincronizar_ruta(self, id_usuario: int, total_deudas: int, deudas: list, distancia_km: float) -> dict:
        batch_id = f"sync_{uuid.uuid4().hex[:10]}"
        record = self._payload_for_ruta(id_usuario, total_deudas, deudas, distancia_km)
        record.update({"batch_id": batch_id, "client_timestamp": datetime.now().isoformat()})

        if self.api_base_url and self.check_online_status():
            ok, message = self._send_record_to_api(record)
            if ok:
                self._log_sync(batch_id, "ruta_notificacion", "EXITOSO", registros=1 + len(deudas))
                return {"status": "online", "message": "Ruta sincronizada con el sistema web.", "batch_id": batch_id}
            self._append_pending(record)
            self._log_sync(batch_id, "ruta_notificacion", "ERROR", registros=0, error=message)
            return {"status": "offline_retry", "message": "No se pudo enviar al web. Guardado en cola local.", "batch_id": batch_id}

        # Fallback directo a base central
        db = SessionLocal()
        try:
            nueva_ruta = RutaNotificacion(
                id_usuario=id_usuario,
                fecha_ruta=datetime.now().date(),
                estado_ruta="PLANIFICADA",
                total_deudas=total_deudas,
                deudas_atendidas=0,
                distancia_estimada_km=distancia_km,
            )
            db.add(nueva_ruta)
            db.commit()
            db.refresh(nueva_ruta)

            for orden, id_deuda in enumerate(deudas, start=1):
                db.add(RutaDetalle(id_ruta=nueva_ruta.id_ruta, id_deuda=id_deuda, orden_visita=orden, visitado=False))
            db.commit()
            self._log_sync(batch_id, "ruta_notificacion", "EXITOSO", registros=1 + len(deudas))
            return {
                "status": "online",
                "message": "Ruta guardada en la base central.",
                "batch_id": batch_id,
                "id_ruta": nueva_ruta.id_ruta,
            }
        except Exception as e:
            db.rollback()
            self._append_pending(record)
            self._log_sync(batch_id, "ruta_notificacion", "ERROR", registros=0, error=str(e))
            return {"status": "offline_retry", "message": "Se guardó en cola local para reintento.", "batch_id": batch_id}
        finally:
            db.close()

    def sincronizar_notificacion(self, notif: dict) -> dict:
        batch_id = f"notif_{uuid.uuid4().hex[:10]}"
        record = self._payload_for_notificacion(notif)
        record.update({"batch_id": batch_id, "client_timestamp": datetime.now().isoformat()})

        if self.api_base_url and self.check_online_status():
            ok, message = self._send_record_to_api(record)
            if ok:
                self._log_sync(batch_id, "notificacion", "EXITOSO", registros=1)
                return {"status": "online", "message": "Notificacion sincronizada con el sistema web.", "batch_id": batch_id}
            self._append_pending(record)
            self._log_sync(batch_id, "notificacion", "ERROR", registros=0, error=message)
            return {"status": "offline_retry", "message": "No se pudo enviar al web. Guardado en cola local.", "batch_id": batch_id}

        self._append_pending(record)
        return {"status": "offline_retry", "message": "Sin conexion. Queda en cola local para reintento.", "batch_id": batch_id}

    def encolar_localmente(self, tipo: str, datos: dict):
        record = {
            "entity_type": tipo,
            "action": "create",
            "device_id": self.device_id,
            "payload": datos,
            "batch_id": f"queued_{uuid.uuid4().hex[:10]}",
            "client_timestamp": datetime.now().isoformat(),
        }
        self._append_pending(record)

    def obtener_cola_local(self) -> dict:
        return self._read_cache()

    def limpiar_cola_local(self):
        self._replace_pending([])

    def procesar_cola_pendiente(self) -> dict:
        cache = self._read_cache()
        pending = cache.get("pending", [])
        if not pending:
            return {"status": "empty", "message": "No hay datos pendientes por sincronizar."}

        if not self.check_online_status():
            return {"status": "offline", "message": f"Continúa offline. {len(pending)} registros pendientes."}

        remaining = []
        success_count = 0
        for record in pending:
            ok, message = self._send_record_to_api(record) if self.api_base_url else (False, "API no configurada")
            if ok:
                success_count += 1
                self._log_sync(record.get("batch_id", "local"), record.get("entity_type", "unknown"), "EXITOSO", registros=1)
            else:
                remaining.append(record)
                self._log_sync(record.get("batch_id", "local"), record.get("entity_type", "unknown"), "ERROR", registros=0, error=message)

        self._replace_pending(remaining)
        if not remaining:
            return {"status": "success", "message": f"Sincronización exitosa: {success_count} registros enviados al sistema web."}
        return {"status": "partial", "message": f"Sincronización parcial: {success_count} enviados, {len(remaining)} siguen en cola."}

