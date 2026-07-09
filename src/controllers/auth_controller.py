import bcrypt
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.models.usuario import Usuario, SesionUsuario
from src.utils.logger import setup_logger

logger = setup_logger("auth")


class AuthController:
    SECRET_KEY = "neplatic-desktop-secret-key"
    ALGORITHM = "HS256"
    TOKEN_EXPIRE_HOURS = 8

    def login(self, username: str, password: str) -> Usuario:
        db = self._get_db()
        try:
            user = db.query(Usuario).filter(Usuario.username == username, Usuario.activo == True).first()
            if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                user.ultimo_acceso = datetime.now()
                user.intentos_fallidos = 0
                
                token = self._generate_token(user.id_usuario)
                user.token = token
                
                # Registrar sesión en la base de datos
                sesion = SesionUsuario(
                    id_usuario=user.id_usuario,
                    token=token,
                    ip_origen="127.0.0.1",
                    user_agent="Neplatic Desktop Client",
                    fecha_inicio=datetime.now(),
                    activa=True
                )
                db.add(sesion)
                db.commit()
                
                logger.info(f"Login exitoso y sesion registrada para: {username}")
                return user
            if user:
                user.intentos_fallidos += 1
                db.commit()
                logger.warning(f"Login fallido: {username}")
            return None
        finally:
            db.close()

    def logout(self, token: str) -> bool:
        db = self._get_db()
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            user_id = payload["sub"]
            
            sesion = db.query(SesionUsuario).filter(
                SesionUsuario.token == token,
                SesionUsuario.activa == True
            ).first()
            
            if sesion:
                sesion.activa = False
                sesion.fecha_fin = datetime.now()
                db.commit()
                logger.info(f"Sesion cerrada exitosamente en base de datos para usuario {user_id}")
                return True
            else:
                logger.warning("No se encontro una sesion activa en base de datos para el token.")
                return False
        except jwt.PyJWTError as e:
            logger.warning(f"Error al decodificar token en logout: {e}")
            return False
        finally:
            db.close()

    def _generate_token(self, user_id: int) -> str:
        expire = datetime.now() + timedelta(hours=self.TOKEN_EXPIRE_HOURS)
        return jwt.encode({"sub": str(user_id), "exp": expire}, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def _get_db(self):
        from src.models.database import SessionLocal
        return SessionLocal()

    def verify_token(self, token: str) -> Usuario:
        db = self._get_db()
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            
            # Verificar si la sesión sigue activa en la base de datos
            sesion_activa = db.query(SesionUsuario).filter(
                SesionUsuario.token == token,
                SesionUsuario.activa == True
            ).first()
            if not sesion_activa:
                logger.warning("Token valido pero sesion inactiva en base de datos (revocada).")
                return None
                
            return db.query(Usuario).filter(Usuario.id_usuario == int(payload["sub"])).first()
        except jwt.PyJWTError as e:
            logger.error(f"Error de JWT al verificar token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al verificar token: {e}")
            return None
        finally:
            db.close()