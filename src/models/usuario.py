from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, SmallInteger, ForeignKey, func, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import INET
from src.models.database import Base


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = {"schema": "neplatic"}

    id_usuario = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    id_rol = Column(SmallInteger, ForeignKey("neplatic.rol_usuario.id_rol"), nullable=False)
    id_sector_asignado = Column(SmallInteger, ForeignKey("neplatic.sector.id_sector"))
    email = Column(String(100))
    telefono = Column(String(15))
    fecha_creacion = Column(DateTime, server_default=func.now())
    ultimo_acceso = Column(DateTime)
    intentos_fallidos = Column(Integer, default=0)
    bloqueado = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)


class Contribuyente(Base):
    __tablename__ = "contribuyente"
    __table_args__ = {"schema": "neplatic"}

    id_contribuyente = Column(Integer, primary_key=True)
    id_tipo_doc = Column(SmallInteger, ForeignKey("neplatic.tipo_documento.id_tipo_doc"), nullable=False)
    numero_documento = Column(String(15), nullable=False)
    nombres = Column(String(150), nullable=False)
    apellido_paterno = Column(String(50))
    apellido_materno = Column(String(50))
    razon_social = Column(String(200))
    direccion_fiscal = Column(String(200))
    telefono_fijo = Column(String(15))
    telefono_movil = Column(String(15))
    email = Column(String(100))
    clasificacion = Column(String(20))
    fecha_registro = Column(Date, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
    activo = Column(Boolean, default=True)


class SesionUsuario(Base):
    __tablename__ = "sesion_usuario"
    __table_args__ = {"schema": "neplatic"}

    id_sesion = Column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("neplatic.usuario.id_usuario"), nullable=False)
    token = Column(String(500), nullable=False)
    ip_origen = Column(INET)
    user_agent = Column(String(255))
    fecha_inicio = Column(DateTime, server_default=func.now())
    fecha_fin = Column(DateTime)
    activa = Column(Boolean, default=True)

    usuario = relationship("Usuario", backref="sesiones")