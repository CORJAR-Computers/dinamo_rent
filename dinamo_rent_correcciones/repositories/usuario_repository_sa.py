"""
usuario_repository_sa.py — Repositorio de Usuarios

"""

from typing import List, Dict, Optional
from datetime import datetime

from core.database_sa import get_session
from core.models import Usuario
from core.schemas import UsuarioCreate, UsuarioUpdate
from core.exceptions import RegistroNoEncontrado
from core.security import SecurityManager
from core.logger import get_logger

log = get_logger(__name__)

class UsuarioRepositorySA:
    @staticmethod
    def obtener_todos() -> List[Dict]:
        """Obtiene todos los usuarios del sistema."""
        with get_session() as session:
            usuarios = session.query(Usuario).order_by(Usuario.username).all()
            return [UsuarioRepositorySA._to_dict(u) for u in usuarios]

    @staticmethod
    def obtener_por_username(username: str) -> Optional[Dict]:
        """Obtiene un usuario por su nombre de usuario."""
        with get_session() as session:
            usuario = session.query(Usuario).filter(Usuario.username == username.strip()).first()
            return UsuarioRepositorySA._to_dict(usuario) if usuario else None

    @staticmethod
    def insertar(datos: UsuarioCreate) -> int:
        """Inserta un nuevo usuario con contraseña hasheada."""
        with get_session() as session:
            hashed_pwd = SecurityManager.hash_password(datos.password_raw)
            nuevo_usuario = Usuario(
                username=datos.username.strip(),
                password=hashed_pwd,
                nombre=datos.nombre,
                rol=datos.rol,
                email=datos.email,
                activo=1 if datos.activo else 0,
            )
            session.add(nuevo_usuario)
            session.flush()
            log.info("Usuario creado: %s (rol=%s)", datos.username, datos.rol)
            return nuevo_usuario.id

    @staticmethod
    def actualizar(datos: UsuarioUpdate) -> None:
        """
        Actualiza un usuario existente. Si password_raw viene, cambia la contraseña.

        F1C: UsuarioUpdate ahora incluye username como campo requerido
        para identificar el registro a actualizar.
        """
        with get_session() as session:
            usuario = session.query(Usuario).filter(Usuario.username == datos.username).first()

            if not usuario:
                raise RegistroNoEncontrado(f"Usuario '{datos.username}' no encontrado.")

            update_fields = datos.model_dump(
                exclude_unset=True, exclude={"password_raw", "username"}
            )

            # Hash de nueva contraseña si viene
            if datos.password_raw:
                usuario.password = SecurityManager.hash_password(datos.password_raw)

            for campo, valor in update_fields.items():
                if hasattr(usuario, campo):
                    # Convertir bool a int para activo
                    if campo == "activo" and isinstance(valor, bool):
                        valor = 1 if valor else 0
                    setattr(usuario, campo, valor)

            log.info("Usuario actualizado: %s", datos.username)

    @staticmethod
    def eliminar(username: str) -> None:
        """Elimina un usuario por username."""
        with get_session() as session:
            usuario = session.query(Usuario).filter(Usuario.username == username).first()
            if not usuario:
                raise RegistroNoEncontrado(f"Usuario '{username}' no encontrado.")
            session.delete(usuario)
            log.info("Usuario eliminado: %s", username)

    @staticmethod
    def registrar_acceso(username: str) -> None:
        """Registra la fecha/hora del último acceso de un usuario."""
        with get_session() as session:
            usuario = session.query(Usuario).filter(Usuario.username == username).first()
            if usuario:
                usuario.ultimo_acceso = datetime.now()
                usuario.intentos_fallidos = 0

    @staticmethod
    def _to_dict(usuario: Usuario) -> Dict:
        if not usuario:
            return None
        return {
            "id": usuario.id,
            "username": usuario.username,
            "password": usuario.password,
            "nombre": usuario.nombre,
            "rol": usuario.rol,
            "email": usuario.email,
            "activo": bool(usuario.activo),
            "debe_cambiar_password": bool(usuario.debe_cambiar_password),
            "intentos_fallidos": usuario.intentos_fallidos,
            "ultimo_acceso": usuario.ultimo_acceso,
            "created_at": usuario.created_at,
            "updated_at": usuario.updated_at,
        }
