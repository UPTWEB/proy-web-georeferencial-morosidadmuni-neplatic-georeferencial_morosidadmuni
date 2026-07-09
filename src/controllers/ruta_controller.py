from datetime import date, datetime
from src.models.usuario import Usuario
from src.models.deuda import RutaNotificacion, RutaDetalle, Notificacion, Deuda
from src.models.database import get_session
from src.services.event_publisher import EventPublisher
from src.services.redis_publisher import RedisPublisher
from src.services.sync_service import SyncService
from src.utils.logger import setup_logger

logger = setup_logger("ruta")


class RutaController:
    def __init__(self, user: Usuario):
        self.user = user
        self._event_publisher = None
        self._redis_publisher = None
        self._sync_service = None

    @property
    def event_publisher(self):
        if self._event_publisher is None:
            self._event_publisher = EventPublisher()
        return self._event_publisher

    @property
    def redis_publisher(self):
        if self._redis_publisher is None:
            self._redis_publisher = RedisPublisher()
        return self._redis_publisher

    @property
    def sync_service(self):
        if self._sync_service is None:
            self._sync_service = SyncService()
        return self._sync_service

    def listar_rutas_usuario(self):
        with get_session() as db:
            query = db.query(RutaNotificacion).filter(
                RutaNotificacion.fecha_ruta >= date.today()
            )
            if self.user.id_rol == 3:
                query = query.filter(RutaNotificacion.id_usuario == self.user.id_usuario)
            return query.order_by(RutaNotificacion.fecha_ruta.desc()).all()

    def listar_deudas_asignadas(self):
        from src.models.contribuyente import EstadoCobranza, Lote, Manzana, Sector, TipoTributo
        from sqlalchemy import extract

        with get_session() as db:
            current_year = datetime.now().year
            Contribuyente = self._get_contribuyente_model()

            query = db.query(
                RutaDetalle.id_deuda,
                Contribuyente.nombres.label("contribuyente"),
                Contribuyente.numero_documento.label("documento"),
                Contribuyente.direccion_fiscal.label("direccion_fiscal"),
                TipoTributo.nombre.label("tipo_tributo"),
                Lote.codigo.label("codigo_lote"),
                Lote.direccion.label("direccion_predio"),
                Lote.area_terreno_m2.label("area_terreno_m2"),
                Lote.area_construida_m2.label("area_construida_m2"),
                Lote.uso.label("uso_predio"),
                Lote.latitud,
                Lote.longitud,
                Manzana.codigo.label("manzana"),
                Sector.nombre.label("sector"),
                Deuda.anio_tributo,
                Deuda.periodo,
                Deuda.monto_original,
                Deuda.saldo_pendiente.label("saldo"),
                EstadoCobranza.nombre.label("estado_cobranza"),
                Deuda.fecha_vencimiento,
                RutaDetalle.orden_visita,
                RutaDetalle.visitado,
            ).join(
                RutaNotificacion, RutaDetalle.id_ruta == RutaNotificacion.id_ruta
            ).join(
                Deuda, RutaDetalle.id_deuda == Deuda.id_deuda
            ).join(
                Contribuyente, Deuda.id_contribuyente == Contribuyente.id_contribuyente
            ).join(
                TipoTributo, Deuda.id_tipo_tributo == TipoTributo.id_tipo_tributo
            ).join(
                EstadoCobranza, Deuda.id_estado_cobranza == EstadoCobranza.id_estado
            ).outerjoin(
                Lote, Deuda.id_lote == Lote.id_lote
            ).outerjoin(
                Manzana, Lote.id_manzana == Manzana.id_manzana
            ).outerjoin(
                Sector, Manzana.id_sector == Sector.id_sector
            ).filter(
                extract("year", Deuda.fecha_vencimiento) == current_year,
                Deuda.activo == True,
                Deuda.saldo_pendiente > 0,
                RutaNotificacion.estado_ruta != "TERMINADA",
            )

            if self.user.id_rol == 3:
                query = query.filter(RutaNotificacion.id_usuario == self.user.id_usuario)

            return query.order_by(RutaDetalle.orden_visita.asc()).limit(500).all()

    def obtener_detalle_ubicacion_ruta(self, id_ruta: int):
        from src.models.contribuyente import EstadoCobranza, Lote, Manzana, Sector, TipoTributo

        with get_session() as db:
            Contribuyente = self._get_contribuyente_model()
            query = db.query(
                RutaDetalle.orden_visita,
                RutaDetalle.visitado,
                RutaDetalle.id_deuda,
                Contribuyente.nombres.label("contribuyente"),
                Contribuyente.numero_documento.label("documento"),
                TipoTributo.nombre.label("tipo_tributo"),
                Lote.codigo.label("codigo_lote"),
                Lote.direccion.label("direccion_predio"),
                Lote.latitud,
                Lote.longitud,
                Manzana.codigo.label("manzana"),
                Sector.nombre.label("sector"),
                Deuda.saldo_pendiente.label("saldo"),
                EstadoCobranza.nombre.label("estado_cobranza"),
            ).join(
                RutaNotificacion, RutaDetalle.id_ruta == RutaNotificacion.id_ruta
            ).join(
                Deuda, RutaDetalle.id_deuda == Deuda.id_deuda
            ).join(
                Contribuyente, Deuda.id_contribuyente == Contribuyente.id_contribuyente
            ).join(
                TipoTributo, Deuda.id_tipo_tributo == TipoTributo.id_tipo_tributo
            ).join(
                EstadoCobranza, Deuda.id_estado_cobranza == EstadoCobranza.id_estado
            ).outerjoin(
                Lote, Deuda.id_lote == Lote.id_lote
            ).outerjoin(
                Manzana, Lote.id_manzana == Manzana.id_manzana
            ).outerjoin(
                Sector, Manzana.id_sector == Sector.id_sector
            ).filter(
                RutaDetalle.id_ruta == id_ruta
            )
            if self.user.id_rol == 3:
                query = query.filter(RutaNotificacion.id_usuario == self.user.id_usuario)
            return query.order_by(RutaDetalle.orden_visita.asc()).all()

    def listar_deudas_anio_actual(self):
        """Lista TODAS las deudas activas del año actual para la vista del administrador."""
        from src.models.contribuyente import EstadoCobranza, Lote, Manzana, Sector, TipoTributo
        from src.models.deuda import Deuda
        with get_session() as db:
            current_year = datetime.now().year

            Contribuyente = self._get_contribuyente_model()

            results = db.query(
                Deuda.id_deuda,
                Contribuyente.nombres.label("contribuyente"),
                Contribuyente.numero_documento.label("documento"),
                Contribuyente.direccion_fiscal.label("direccion_fiscal"),
                TipoTributo.nombre.label("tipo_tributo"),
                Lote.codigo.label("codigo_lote"),
                Lote.direccion.label("direccion_predio"),
                Lote.area_terreno_m2.label("area_terreno_m2"),
                Lote.area_construida_m2.label("area_construida_m2"),
                Lote.uso.label("uso_predio"),
                Lote.latitud,
                Lote.longitud,
                Manzana.codigo.label("manzana"),
                Sector.nombre.label("sector"),
                Deuda.periodo,
                Deuda.monto_original,
                Deuda.saldo_pendiente.label("saldo"),
                Deuda.anio_tributo,
                EstadoCobranza.nombre.label("estado_cobranza"),
                Deuda.fecha_vencimiento,
            ).join(
                Contribuyente, Deuda.id_contribuyente == Contribuyente.id_contribuyente
            ).join(
                TipoTributo, Deuda.id_tipo_tributo == TipoTributo.id_tipo_tributo
            ).outerjoin(
                Lote, Deuda.id_lote == Lote.id_lote
            ).outerjoin(
                Manzana, Lote.id_manzana == Manzana.id_manzana
            ).outerjoin(
                Sector, Manzana.id_sector == Sector.id_sector
            ).join(
                EstadoCobranza, Deuda.id_estado_cobranza == EstadoCobranza.id_estado
            ).filter(
                Deuda.activo == True,
                Deuda.saldo_pendiente > 0,
                Deuda.anio_tributo == current_year,
            ).order_by(
                Deuda.saldo_pendiente.desc()
            ).limit(500).all()

            return results

    @staticmethod
    def _get_contribuyente_model():
        from sqlalchemy import Column, Integer, String, Boolean, Date, SmallInteger, ForeignKey
        from sqlalchemy.orm import declarative_base
        # Import directly from existing model
        from src.models.database import Base as _B

        class _Contribuyente(_B):
            __tablename__ = "contribuyente"
            __table_args__ = {"schema": "neplatic", "extend_existing": True}

            id_contribuyente = Column(Integer, primary_key=True)
            id_tipo_doc = Column(SmallInteger)
            numero_documento = Column(String(15))
            nombres = Column(String(150))
            apellido_paterno = Column(String(50))
            apellido_materno = Column(String(50))
            razon_social = Column(String(200))
            direccion_fiscal = Column(String(200))
            clasificacion = Column(String(20))
            activo = Column(Boolean, default=True)

        return _Contribuyente

    def obtener_sectores(self):
        from src.models.contribuyente import Sector
        with get_session() as db:
            return db.query(Sector).filter(Sector.activo == True).order_by(Sector.nombre).all()

    def obtener_notificadores(self):
        from src.models.usuario import Usuario
        with get_session() as db:
            # Mostrar únicamente notificadores
            return db.query(Usuario).filter(
                Usuario.activo == True,
                Usuario.id_rol == 3
            ).all()

    def listar_deudas_asignables(self, id_sector: int = None):
        """Lista deudas con coordenadas GPS que no están asignadas a ninguna ruta activa."""
        from src.models.contribuyente import EstadoCobranza, Lote, Manzana, Sector, TipoTributo
        from sqlalchemy import and_, exists

        with get_session() as db:
            Contribuyente = self._get_contribuyente_model()

            # Subquery: deudas que ya están en alguna ruta_detalle de una ruta NO terminada
            already_assigned = db.query(RutaDetalle.id_deuda).join(
                RutaNotificacion, RutaDetalle.id_ruta == RutaNotificacion.id_ruta
            ).filter(
                RutaNotificacion.estado_ruta != 'TERMINADA'
            ).subquery()

            query = db.query(
                Deuda.id_deuda,
                Contribuyente.nombres.label("contribuyente"),
                Contribuyente.numero_documento.label("documento"),
                TipoTributo.nombre.label("tipo_tributo"),
                Lote.codigo.label("codigo_lote"),
                Lote.direccion.label("direccion_predio"),
                Lote.latitud,
                Lote.longitud,
                Manzana.codigo.label("manzana"),
                Sector.nombre.label("sector"),
                Deuda.saldo_pendiente.label("saldo"),
                EstadoCobranza.nombre.label("estado_cobranza"),
            ).join(
                Contribuyente, Deuda.id_contribuyente == Contribuyente.id_contribuyente
            ).join(
                TipoTributo, Deuda.id_tipo_tributo == TipoTributo.id_tipo_tributo
            ).join(
                EstadoCobranza, Deuda.id_estado_cobranza == EstadoCobranza.id_estado
            ).join(
                Lote, Deuda.id_lote == Lote.id_lote
            ).join(
                Manzana, Lote.id_manzana == Manzana.id_manzana
            ).join(
                Sector, Manzana.id_sector == Sector.id_sector
            ).filter(
                Deuda.activo == True,
                Deuda.saldo_pendiente > 0,
                Lote.latitud.isnot(None),
                Lote.longitud.isnot(None),
                ~Deuda.id_deuda.in_(db.query(already_assigned.c.id_deuda)),
            )

            if id_sector:
                query = query.filter(Manzana.id_sector == id_sector)

            return query.order_by(Deuda.saldo_pendiente.desc()).limit(500).all()

    def asignar_deudas_a_ruta(self, id_usuario_notificador: int, fecha_asignacion: date,
                               deuda_ids: list[int], distancia_km: float = 0) -> dict:
        """Crea o reutiliza una ruta y asigna las deudas específicas seleccionadas."""
        from sqlalchemy import func

        if not deuda_ids:
            return {"success": False, "message": "No se seleccionaron deudas para asignar."}

        target_date = fecha_asignacion or date.today()

        with get_session() as db:
            try:
                # Buscar o crear ruta para ese usuario y fecha
                ruta = db.query(RutaNotificacion).filter(
                    RutaNotificacion.id_usuario == id_usuario_notificador,
                    RutaNotificacion.fecha_ruta == target_date
                ).first()

                if not ruta:
                    ruta = RutaNotificacion(
                        id_usuario=id_usuario_notificador,
                        fecha_ruta=target_date,
                        estado_ruta='PLANIFICADA',
                        total_deudas=0,
                        deudas_atendidas=0,
                        distancia_estimada_km=distancia_km,
                    )
                    db.add(ruta)
                    db.flush()
                else:
                    # Actualizar distancia si se proporcionó
                    if distancia_km > 0:
                        ruta.distancia_estimada_km = distancia_km

                # Obtener deudas ya existentes en esta ruta
                deudas_existentes = {d[0] for d in db.query(RutaDetalle.id_deuda).filter(
                    RutaDetalle.id_ruta == ruta.id_ruta
                ).all()}

                # Obtener último orden de visita
                max_orden = db.query(func.max(RutaDetalle.orden_visita)).filter(
                    RutaDetalle.id_ruta == ruta.id_ruta
                ).scalar() or 0
                orden = max_orden + 1

                nuevas_deudas = 0
                for id_deuda in deuda_ids:
                    if id_deuda not in deudas_existentes:
                        detalle = RutaDetalle(
                            id_ruta=ruta.id_ruta,
                            id_deuda=id_deuda,
                            orden_visita=orden,
                            visitado=False
                        )
                        db.add(detalle)
                        orden += 1
                        nuevas_deudas += 1

                if nuevas_deudas == 0:
                    db.rollback()
                    return {"success": False, "message": "Todas las deudas seleccionadas ya estaban asignadas."}

                ruta.total_deudas = (ruta.total_deudas or 0) + nuevas_deudas
                db.commit()

                # Invalidar caché de Redis para la app web
                try:
                    import os
                    redis_prefix = os.getenv("REDIS_PREFIX", "neplatic:")
                    cache_key = f"{redis_prefix}rutas_usuario_{id_usuario_notificador}_{target_date.strftime('%Y-%m-%d')}"
                    if self.redis_publisher.client:
                        self.redis_publisher.client.delete(cache_key)
                        logger.info("Caché invalidada en Redis: %s", cache_key)
                except Exception as cache_error:
                    logger.error("Error al invalidar caché en Redis: %s", cache_error)

                return {
                    "success": True,
                    "message": f"Ruta asignada exitosamente. Se añadieron {nuevas_deudas} deudas a la ruta del {target_date.strftime('%d/%m/%Y')}.",
                    "id_ruta": ruta.id_ruta,
                    "nuevas_deudas": nuevas_deudas,
                }
            except Exception as e:
                db.rollback()
                logger.error("Error al asignar deudas a ruta: %s", e)
                return {"success": False, "message": f"Error: {e}"}

    def asignar_sector(self, id_usuario_notificador: int, id_sector: int, fecha_asignacion: date = None) -> dict:
        from sqlalchemy import func
        from src.models.deuda import RutaNotificacion, RutaDetalle, Deuda
        from src.models.contribuyente import Lote, Manzana
        
        target_date = fecha_asignacion or date.today()
        
        with get_session() as db:
            try:
                # Buscar deudas sin pagar en el sector
                query = db.query(Deuda).join(Lote, Deuda.id_lote == Lote.id_lote).join(Manzana, Lote.id_manzana == Manzana.id_manzana).filter(
                    Manzana.id_sector == id_sector,
                    Deuda.activo == True
                )
                deudas = query.all()
                if not deudas:
                    return {"success": False, "message": "No hay deudas pendientes en este sector."}
                
                # Buscar si ya existe una ruta para este usuario en esa fecha
                ruta = db.query(RutaNotificacion).filter(
                    RutaNotificacion.id_usuario == id_usuario_notificador,
                    RutaNotificacion.fecha_ruta == target_date
                ).first()

                if not ruta:
                    ruta = RutaNotificacion(
                        id_usuario=id_usuario_notificador,
                        fecha_ruta=target_date,
                        estado_ruta='PLANIFICADA',
                        total_deudas=0
                    )
                    db.add(ruta)
                    db.flush()
                
                # Obtener las deudas que ya están en esta ruta para evitar duplicados
                deudas_existentes = {d[0] for d in db.query(RutaDetalle.id_deuda).filter(RutaDetalle.id_ruta == ruta.id_ruta).all()}
                
                # Obtener el último orden de visita
                max_orden = db.query(func.max(RutaDetalle.orden_visita)).filter(RutaDetalle.id_ruta == ruta.id_ruta).scalar() or 0
                orden = max_orden + 1
                
                nuevas_deudas = 0
                for deuda in deudas:
                    if deuda.id_deuda not in deudas_existentes:
                        # Workaround: PostgreSQL SMALLINT limit is 32767.
                        # Cap the max order to 32767 to avoid NumericValueOutOfRange errors when assigning huge sectors
                        safe_orden = min(orden, 32767)
                        detalle = RutaDetalle(
                            id_ruta=ruta.id_ruta,
                            id_deuda=deuda.id_deuda,
                            orden_visita=safe_orden,
                            visitado=False
                        )
                        db.add(detalle)
                        orden += 1
                        nuevas_deudas += 1
                
                if nuevas_deudas == 0:
                    db.rollback()
                    return {"success": False, "message": "Todas las deudas pendientes de este sector ya estaban asignadas a la ruta de hoy."}
                
                ruta.total_deudas += nuevas_deudas
                db.commit()

                # Invalidar caché de Redis para la app web
                try:
                    import os
                    redis_prefix = os.getenv("REDIS_PREFIX", "neplatic:")
                    cache_key = f"{redis_prefix}rutas_usuario_{id_usuario_notificador}_{target_date.strftime('%Y-%m-%d')}"
                    if self.redis_publisher.client:
                        self.redis_publisher.client.delete(cache_key)
                        logger.info("Caché invalidada en Redis: %s", cache_key)
                except Exception as cache_error:
                    logger.error("Error al invalidar caché en Redis: %s", cache_error)

                return {"success": True, "message": f"Sector asignado. Se añadieron {nuevas_deudas} deudas a la ruta del día."}
            except Exception as e:
                db.rollback()
                logger.error("Error al asignar sector: %s", e)
                return {"success": False, "message": f"Error: {e}"}

    def registrar_notificacion(self, id_deuda: int, direccion: str, persona: str, parentesco: str, id_estado: int) -> dict:
        with get_session() as db:
            try:
                deuda_existe = db.query(Deuda).filter(Deuda.id_deuda == id_deuda).first()
                if not deuda_existe:
                    return {"success": False, "message": f"La deuda con ID {id_deuda} no existe en el sistema."}

                notif = Notificacion(
                    id_deuda=id_deuda,
                    id_usuario=self.user.id_usuario,
                    id_estado_notif=id_estado,
                    hora_notificacion=datetime.now().strftime("%H:%M:%S"),
                    direccion_visitada=direccion.strip(),
                    persona_contactada=persona.strip(),
                    parentesco=parentesco.strip(),
                )
                db.add(notif)
                db.commit()
                db.refresh(notif)
                logger.info("Notificacion registrada: deuda %s, estado %s, id=%s", id_deuda, id_estado, notif.id_notificacion)

                payload = {
                    "id_notificacion": notif.id_notificacion,
                    "id_deuda": id_deuda,
                    "id_usuario": self.user.id_usuario,
                    "id_estado_notif": id_estado,
                    "direccion_visitada": direccion.strip(),
                    "persona_contactada": persona.strip(),
                    "parentesco": parentesco.strip(),
                    "fecha_registro": notif.fecha_registro.isoformat() if notif.fecha_registro else datetime.now().isoformat(),
                }

                outbox_id = self.event_publisher.publish(
                    aggregate_type="notificacion",
                    aggregate_id=str(notif.id_notificacion),
                    event_type="VisitaRegistrada",
                    payload=payload,
                )

                redis_ok = self.redis_publisher.publish(
                    event_type="VisitaRegistrada",
                    aggregate_id=str(notif.id_notificacion),
                    payload=payload,
                )

                sync_result = self.sync_service.sincronizar_notificacion(payload)

                detalle = db.query(RutaDetalle).filter(
                    RutaDetalle.id_deuda == id_deuda,
                    RutaDetalle.visitado == False,
                ).first()
                if detalle:
                    detalle.visitado = True
                    detalle.id_notificacion = notif.id_notificacion
                    db.commit()

                logger.info(
                    "Flujo completo: outbox=%s, redis=%s, sync_api=%s",
                    "ok" if outbox_id else "fallo",
                    "ok" if redis_ok else "fallo",
                    sync_result.get("status", "?"),
                )

                return {
                    "success": True,
                    "message": "Visita registrada correctamente.",
                    "id_notificacion": notif.id_notificacion,
                    "outbox_id": outbox_id,
                    "redis_published": redis_ok,
                    "sync_status": sync_result.get("status"),
                    "sync_message": sync_result.get("message"),
                }

            except Exception as e:
                db.rollback()
                logger.error("Error al registrar notificacion: %s", e)
                return {"success": False, "message": f"Error: {e}"}

    def close(self):
        try:
            self.redis_publisher.close()
        except Exception:
            pass
