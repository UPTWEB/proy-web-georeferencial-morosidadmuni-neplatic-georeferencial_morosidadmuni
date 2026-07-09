from sqlalchemy import Column, Integer, String, Boolean, Date, Numeric, SmallInteger, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import INET
from src.models.database import Base


class EstadoCobranza(Base):
    __tablename__ = "estado_cobranza"
    __table_args__ = {"schema": "neplatic"}

    id_estado = Column(SmallInteger, primary_key=True)
    codigo = Column(String(20), nullable=False, unique=True)
    nombre = Column(String(50), nullable=False)
    color_hex = Column(String(7), nullable=False)
    prioridad = Column(SmallInteger, nullable=False, default=0)
    descripcion = Column(String)
    activo = Column(Boolean, default=True)


class TipoTributo(Base):
    __tablename__ = "tipo_tributo"
    __table_args__ = {"schema": "neplatic"}

    id_tipo_tributo = Column(SmallInteger, primary_key=True)
    codigo = Column(String(10), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String)
    activo = Column(Boolean, default=True)


class RolUsuario(Base):
    __tablename__ = "rol_usuario"
    __table_args__ = {"schema": "neplatic"}

    id_rol = Column(SmallInteger, primary_key=True)
    codigo = Column(String(20), nullable=False, unique=True)
    nombre = Column(String(50), nullable=False)
    descripcion = Column(String)
    activo = Column(Boolean, default=True)


class Permiso(Base):
    __tablename__ = "permiso"
    __table_args__ = {"schema": "neplatic"}

    id_permiso = Column(SmallInteger, primary_key=True)
    codigo = Column(String(50), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String)
    modulo = Column(String(50), nullable=False)


class RolPermiso(Base):
    __tablename__ = "rol_permiso"
    __table_args__ = {"schema": "neplatic"}

    id_rol = Column(SmallInteger, ForeignKey("neplatic.rol_usuario.id_rol"), primary_key=True)
    id_permiso = Column(SmallInteger, ForeignKey("neplatic.permiso.id_permiso"), primary_key=True)


class EstadoNotificacion(Base):
    __tablename__ = "estado_notificacion"
    __table_args__ = {"schema": "neplatic"}

    id_estado_notif = Column(SmallInteger, primary_key=True)
    codigo = Column(String(20), nullable=False, unique=True)
    nombre = Column(String(50), nullable=False)
    color_hex = Column(String(7))
    descripcion = Column(String)


class TipoDocumento(Base):
    __tablename__ = "tipo_documento"
    __table_args__ = {"schema": "neplatic"}

    id_tipo_doc = Column(SmallInteger, primary_key=True)
    codigo = Column(String(1), nullable=False, unique=True)
    nombre = Column(String(50), nullable=False)
    activo = Column(Boolean, default=True)


class Sector(Base):
    __tablename__ = "sector"
    __table_args__ = {"schema": "neplatic"}

    id_sector = Column(SmallInteger, primary_key=True)
    codigo = Column(String(10), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    area_m2 = Column(Numeric(12, 2))
    perimetro_m = Column(Numeric(12, 2))
    geom = Column(String)
    activo = Column(Boolean, default=True)


class Manzana(Base):
    __tablename__ = "manzana"
    __table_args__ = {"schema": "neplatic"}

    id_manzana = Column(Integer, primary_key=True)
    id_sector = Column(SmallInteger, ForeignKey("neplatic.sector.id_sector"), nullable=False)
    codigo = Column(String(15), nullable=False, unique=True)
    area_m2 = Column(Numeric(12, 2))
    perimetro_m = Column(Numeric(12, 2))
    geom = Column(String)
    activo = Column(Boolean, default=True)


class Via(Base):
    __tablename__ = "via"
    __table_args__ = {"schema": "neplatic"}

    id_via = Column(Integer, primary_key=True)
    codigo = Column(String(10), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    tipo = Column(String(20))
    longitud_m = Column(Numeric(10, 2))
    geom = Column(String)


class Lote(Base):
    __tablename__ = "lote"
    __table_args__ = {"schema": "neplatic"}

    id_lote = Column(Integer, primary_key=True)
    id_manzana = Column(Integer, ForeignKey("neplatic.manzana.id_manzana"), nullable=False)
    id_via = Column(SmallInteger, ForeignKey("neplatic.via.id_via"))
    codigo = Column(String(20), nullable=False, unique=True)
    numero_municipal = Column(String(10))
    direccion = Column(String(200))
    area_terreno_m2 = Column(Numeric(10, 2))
    area_construida_m2 = Column(Numeric(10, 2))
    pisos = Column(SmallInteger, default=1)
    uso = Column(String(30))
    geom = Column(String)
    latitud = Column(Numeric(10, 7))
    longitud = Column(Numeric(10, 7))
    activo = Column(Boolean, default=True)