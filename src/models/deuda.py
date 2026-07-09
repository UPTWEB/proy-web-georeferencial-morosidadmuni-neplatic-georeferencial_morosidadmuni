from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Numeric, SmallInteger, ForeignKey, func
from sqlalchemy.dialects.postgresql import INET
from src.models.database import Base


class Deuda(Base):
    __tablename__ = "deuda"
    __table_args__ = {"schema": "neplatic"}

    id_deuda = Column(Integer, primary_key=True)
    id_contribuyente = Column(Integer, ForeignKey("neplatic.contribuyente.id_contribuyente"), nullable=False)
    id_lote = Column(Integer, ForeignKey("neplatic.lote.id_lote"))
    id_tipo_tributo = Column(SmallInteger, ForeignKey("neplatic.tipo_tributo.id_tipo_tributo"), nullable=False)
    id_estado_cobranza = Column(SmallInteger, ForeignKey("neplatic.estado_cobranza.id_estado"), nullable=False)
    numero_resolucion = Column(String(50))
    anio_tributo = Column(SmallInteger, nullable=False)
    periodo = Column(String(6))
    monto_original = Column(Numeric(12, 2), nullable=False)
    saldo_pendiente = Column(Numeric(12, 2), nullable=False)
    monto_pagado = Column(Numeric(12, 2), default=0.00)
    fecha_emision = Column(Date)
    fecha_vencimiento = Column(Date)
    fecha_ultimo_pago = Column(Date)
    fecha_prescripcion = Column(Date)
    tiene_fraccionamiento = Column(Boolean, default=False)
    id_deuda_origen = Column(Integer, ForeignKey("neplatic.deuda.id_deuda"))
    fecha_ingreso_coactiva = Column(Date)
    fecha_ultima_actualizacion = Column(DateTime, server_default=func.now())
    origen_dato = Column(String(20), default="ORACLE")
    lote_etl = Column(String(20))
    observaciones = Column(String)
    activo = Column(Boolean, default=True)


class HistorialEstadoDeuda(Base):
    __tablename__ = "historial_estado_deuda"
    __table_args__ = {"schema": "neplatic"}

    id_historial = Column(Integer, primary_key=True)
    id_deuda = Column(Integer, ForeignKey("neplatic.deuda.id_deuda"), nullable=False)
    id_estado_anterior = Column(SmallInteger, ForeignKey("neplatic.estado_cobranza.id_estado"))
    id_estado_nuevo = Column(SmallInteger, ForeignKey("neplatic.estado_cobranza.id_estado"), nullable=False)
    fecha_cambio = Column(DateTime, server_default=func.now())
    usuario = Column(String(50))
    origen_cambio = Column(String(30))
    justificacion = Column(String)
    ip_origen = Column(INET)


class ContribuyenteLote(Base):
    __tablename__ = "contribuyente_lote"
    __table_args__ = {"schema": "neplatic"}

    id_contribuyente = Column(Integer, ForeignKey("neplatic.contribuyente.id_contribuyente"), primary_key=True)
    id_lote = Column(Integer, ForeignKey("neplatic.lote.id_lote"), primary_key=True)
    tipo_relacion = Column(String(20), primary_key=True, default="PROPIETARIO")
    porcentaje_propiedad = Column(Numeric(5, 2), default=100.00)
    fecha_adquisicion = Column(Date)
    fecha_registro = Column(Date, server_default=func.now())
    activo = Column(Boolean, default=True)


class Notificacion(Base):
    __tablename__ = "notificacion"
    __table_args__ = {"schema": "neplatic"}

    id_notificacion = Column(Integer, primary_key=True)
    id_deuda = Column(Integer, ForeignKey("neplatic.deuda.id_deuda"), nullable=False)
    id_usuario = Column(Integer, ForeignKey("neplatic.usuario.id_usuario"), nullable=False)
    id_estado_notif = Column(SmallInteger, ForeignKey("neplatic.estado_notificacion.id_estado_notif"), nullable=False)
    fecha_notificacion = Column(Date, nullable=False, server_default=func.now())
    hora_notificacion = Column(String(8), nullable=False)
    latitud = Column(Numeric(10, 7))
    longitud = Column(Numeric(10, 7))
    precision_gps_m = Column(Numeric(6, 2))
    punto_ubicacion = Column(String)
    direccion_visitada = Column(String(200))
    persona_contactada = Column(String(150))
    parentesco = Column(String(30))
    tipo_evidencia = Column(String(20))
    evidencia_url = Column(String(500))
    comentario = Column(String)
    fecha_registro = Column(DateTime, server_default=func.now())


class RutaNotificacion(Base):
    __tablename__ = "ruta_notificacion"
    __table_args__ = {"schema": "neplatic"}

    id_ruta = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey("neplatic.usuario.id_usuario"), nullable=False)
    fecha_ruta = Column(Date, nullable=False, server_default=func.now())
    estado_ruta = Column(String(20), default="PLANIFICADA")
    total_deudas = Column(Integer, default=0)
    deudas_atendidas = Column(Integer, default=0)
    deudas_efectivas = Column(Integer, default=0)
    distancia_estimada_km = Column(Numeric(8, 2))
    hora_inicio = Column(String(8))
    hora_fin = Column(String(8))
    comentario = Column(String)


class RutaDetalle(Base):
    __tablename__ = "ruta_detalle"
    __table_args__ = {"schema": "neplatic"}

    id_ruta_detalle = Column(Integer, primary_key=True)
    id_ruta = Column(Integer, ForeignKey("neplatic.ruta_notificacion.id_ruta"), nullable=False)
    id_deuda = Column(Integer, ForeignKey("neplatic.deuda.id_deuda"), nullable=False)
    orden_visita = Column(SmallInteger, nullable=False)
    visitado = Column(Boolean, default=False)
    id_notificacion = Column(Integer, ForeignKey("neplatic.notificacion.id_notificacion"))


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


class Parametro(Base):
    __tablename__ = "parametro"
    __table_args__ = {"schema": "neplatic"}

    clave = Column(String(50), primary_key=True)
    valor = Column(String)
    tipo = Column(String(20), default="STRING")
    descripcion = Column(String)
    editable = Column(Boolean, default=True)


class LogSincronizacion(Base):
    __tablename__ = "log_sincronizacion"
    __table_args__ = {"schema": "neplatic"}

    id_log = Column(Integer, primary_key=True)
    sync_batch_id = Column(String(50), nullable=False)
    device_uuid = Column(String(100), nullable=False)
    tabla_sincronizada = Column(String(50), nullable=False)
    registros_afectados = Column(Integer, default=0)
    estado = Column(String(20), default="EXITOSO")
    error_detalle = Column(String)
    fecha_sincronizacion = Column(DateTime, server_default=func.now())