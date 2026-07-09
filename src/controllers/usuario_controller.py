import bcrypt
from datetime import datetime
from src.models.database import get_session
from src.models.usuario import Usuario
from src.models.contribuyente import RolUsuario, Permiso, RolPermiso
from src.utils.logger import setup_logger

logger = setup_logger("usuario_controller")


class UsuarioController:
    def __init__(self):
        pass

    def obtener_perfil(self, id_usuario: int):
        with get_session() as db:
            try:
                resultado = db.query(
                    Usuario,
                    RolUsuario.nombre.label("rol_nombre")
                ).join(
                    RolUsuario,
                    Usuario.id_rol == RolUsuario.id_rol
                ).filter(
                    Usuario.id_usuario == id_usuario
                ).first()
                return resultado
            except Exception as e:
                logger.error(f"Error al obtener perfil para usuario {id_usuario}: {e}")
                return None

    def obtener_usuario_por_id(self, id_usuario: int):
        with get_session() as db:
            try:
                return db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
            except Exception as e:
                logger.error(f"Error al obtener usuario {id_usuario}: {e}")
                return None

    def listar_usuarios(self) -> list[dict]:
        with get_session() as db:
            try:
                rows = db.query(
                    Usuario.id_usuario,
                    Usuario.username,
                    Usuario.nombres,
                    Usuario.apellidos,
                    Usuario.email,
                    Usuario.telefono,
                    Usuario.fecha_creacion,
                    Usuario.ultimo_acceso,
                    Usuario.activo,
                    Usuario.bloqueado,
                    RolUsuario.nombre.label("rol_nombre"),
                ).join(
                    RolUsuario,
                    Usuario.id_rol == RolUsuario.id_rol
                ).order_by(Usuario.id_usuario.asc()).all()

                return [
                    {
                        "id_usuario": r.id_usuario,
                        "username": r.username,
                        "nombres": r.nombres,
                        "apellidos": r.apellidos,
                        "email": r.email,
                        "telefono": r.telefono,
                        "fecha_creacion": r.fecha_creacion,
                        "ultimo_acceso": r.ultimo_acceso,
                        "activo": r.activo,
                        "bloqueado": r.bloqueado,
                        "rol_nombre": r.rol_nombre,
                    }
                    for r in rows
                ]
            except Exception as e:
                logger.error(f"Error al listar usuarios: {e}")
                return []

    def listar_roles(self) -> list[dict]:
        with get_session() as db:
            try:
                rows = db.query(RolUsuario).order_by(RolUsuario.nombre.asc()).all()
                return [{"id_rol": r.id_rol, "nombre": r.nombre, "codigo": r.codigo, "activo": r.activo} for r in rows]
            except Exception as e:
                logger.error(f"Error al listar roles: {e}")
                return []

    def restablecer_contrasena(self, id_usuario: int, nueva_contrasena: str) -> tuple[bool, str]:
        with get_session() as db:
            try:
                user = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
                if not user:
                    return False, "Usuario no encontrado."

                if len(nueva_contrasena) < 8:
                    return False, "La contraseña debe tener al menos 8 caracteres."

                has_upper = any(char.isupper() for char in nueva_contrasena)
                has_digit = any(char.isdigit() for char in nueva_contrasena)
                if not (has_upper and has_digit):
                    return False, "La contraseña debe contener al menos una mayúscula y un número."

                salt = bcrypt.gensalt()
                hashed = bcrypt.hashpw(nueva_contrasena.encode("utf-8"), salt).decode("utf-8")
                user.password_hash = hashed
                user.bloqueado = False
                user.intentos_fallidos = 0
                db.commit()
                logger.info(f"Contraseña de usuario {id_usuario} restablecida por administrador.")
                return True, "Contraseña restablecida correctamente."
            except Exception as e:
                db.rollback()
                logger.error(f"Error al restablecer contraseña de usuario {id_usuario}: {e}")
                return False, f"No se pudo restablecer la contraseña: {e}"

    def desbloquear_usuario(self, id_usuario: int) -> tuple[bool, str]:
        with get_session() as db:
            try:
                user = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
                if not user:
                    return False, "Usuario no encontrado."
                user.bloqueado = False
                user.intentos_fallidos = 0
                db.commit()
                return True, "Usuario desbloqueado correctamente."
            except Exception as e:
                db.rollback()
                logger.error(f"Error al desbloquear usuario {id_usuario}: {e}")
                return False, f"No se pudo desbloquear el usuario: {e}"

    def bloquear_usuario(self, id_usuario: int) -> tuple[bool, str]:
        with get_session() as db:
            try:
                user = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
                if not user:
                    return False, "Usuario no encontrado."
                user.bloqueado = True
                db.commit()
                return True, "Usuario bloqueado correctamente."
            except Exception as e:
                db.rollback()
                logger.error(f"Error al bloquear usuario {id_usuario}: {e}")
                return False, f"No se pudo bloquear el usuario: {e}"

    def crear_usuario(self, username: str, password: str, nombres: str, apellidos: str, id_rol: int, email: str = "", telefono: str = "") -> tuple[bool, str]:
        with get_session() as db:
            try:
                exists = db.query(Usuario).filter(Usuario.username == username).first()
                if exists:
                    return False, "El nombre de usuario ya existe."

                if len(password) < 8:
                    return False, "La contraseña debe tener al menos 8 caracteres."

                has_upper = any(char.isupper() for char in password)
                has_digit = any(char.isdigit() for char in password)
                if not (has_upper and has_digit):
                    return False, "La contraseña debe contener al menos una mayúscula y un número."

                salt = bcrypt.gensalt()
                hashed = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
                nuevo = Usuario(
                    username=username.strip(),
                    password_hash=hashed,
                    nombres=nombres.strip(),
                    apellidos=apellidos.strip(),
                    id_rol=id_rol,
                    email=email.strip() or None,
                    telefono=telefono.strip() or None,
                    activo=True,
                    bloqueado=False,
                )
                db.add(nuevo)
                db.commit()
                return True, "Usuario creado correctamente."
            except Exception as e:
                db.rollback()
                logger.error(f"Error al crear usuario: {e}")
                return False, f"No se pudo crear el usuario: {e}"

    def actualizar_usuario(self, id_usuario: int, nombres: str, apellidos: str, id_rol: int, email: str = "", telefono: str = "") -> tuple[bool, str]:
        with get_session() as db:
            try:
                user = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
                if not user:
                    return False, "Usuario no encontrado."

                user.nombres = nombres.strip()
                user.apellidos = apellidos.strip()
                user.id_rol = id_rol
                user.email = email.strip() or None
                user.telefono = telefono.strip() or None
                db.commit()
                return True, "Usuario actualizado correctamente."
            except Exception as e:
                db.rollback()
                logger.error(f"Error al actualizar usuario {id_usuario}: {e}")
                return False, f"No se pudo actualizar el usuario: {e}"

    def cambiar_estado_usuario(self, id_usuario: int, activo: bool) -> tuple[bool, str]:
        with get_session() as db:
            try:
                user = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
                if not user:
                    return False, "Usuario no encontrado."
                user.activo = activo
                db.commit()
                return True, "Estado de usuario actualizado."
            except Exception as e:
                db.rollback()
                logger.error(f"Error cambiando estado de usuario {id_usuario}: {e}")
                return False, f"No se pudo actualizar el estado: {e}"

    def actualizar_perfil(self, id_usuario: int, nombres: str, apellidos: str, email: str, telefono: str) -> bool:
        with get_session() as db:
            try:
                user = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
                if not user:
                    logger.warning(f"Usuario {id_usuario} no encontrado para actualizacion.")
                    return False

                user.nombres = nombres.strip()
                user.apellidos = apellidos.strip()
                user.email = email.strip() or None
                user.telefono = telefono.strip() or None

                db.commit()
                logger.info(f"Perfil de usuario {id_usuario} actualizado exitosamente.")
                return True
            except Exception as e:
                db.rollback()
                logger.error(f"Error al actualizar perfil de usuario {id_usuario}: {e}")
                return False

    def cambiar_contrasena(self, id_usuario: int, contrasena_actual: str, nueva_contrasena: str) -> tuple[bool, str]:
        with get_session() as db:
            try:
                user = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
                if not user:
                    return False, "Usuario no encontrado."

                if not bcrypt.checkpw(contrasena_actual.encode("utf-8"), user.password_hash.encode("utf-8")):
                    logger.warning(f"Intento fallido de cambio de clave para usuario {id_usuario}: clave actual incorrecta.")
                    return False, "La contraseña actual es incorrecta."

                if len(nueva_contrasena) < 8:
                    return False, "La contraseña debe tener al menos 8 caracteres."

                has_upper = any(char.isupper() for char in nueva_contrasena)
                has_digit = any(char.isdigit() for char in nueva_contrasena)

                if not (has_upper and has_digit):
                    return False, "La contraseña debe contener al menos una mayúscula y un número."

                salt = bcrypt.gensalt()
                hashed = bcrypt.hashpw(nueva_contrasena.encode("utf-8"), salt).decode("utf-8")

                user.password_hash = hashed
                db.commit()
                logger.info(f"Contraseña de usuario {id_usuario} cambiada con éxito.")
                return True, "Contraseña cambiada correctamente."

            except Exception as e:
                db.rollback()
                logger.error(f"Error al cambiar contraseña de usuario {id_usuario}: {e}")
                return False, f"Error interno del sistema: {e}"

    def obtener_permisos_usuario(self, id_rol: int) -> list[str]:
        with get_session() as db:
            try:
                permisos = db.query(Permiso.codigo).join(
                    RolPermiso, Permiso.id_permiso == RolPermiso.id_permiso
                ).filter(
                    RolPermiso.id_rol == id_rol
                ).all()
                return [p[0] for p in permisos]
            except Exception as e:
                logger.error(f"Error al obtener permisos para rol {id_rol}: {e}")
                return []

    def close(self):
        pass
