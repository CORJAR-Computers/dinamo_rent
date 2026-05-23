"""User management service with RBAC protection."""

from typing import List, Dict

from core.exceptions import NegocioError, ValidacionError
from core.logger import get_logger, get_audit_logger
from core.validators import requerir
from core.schemas import UsuarioCreate, UsuarioUpdate
from core.rbac import require_role
from core.config import ROLES_CON_USUARIOS
from core.security import SecurityManager
from repositories.repositories_sa import UsuarioRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class UsuarioService:

    @staticmethod
    @require_role(*ROLES_CON_USUARIOS)
    def listar(session_id: str = None) -> List[Dict]:
        return UsuarioRepositorySA.obtener_todos()

    @staticmethod
    @require_role(*ROLES_CON_USUARIOS)
    def crear(datos: dict, session_id: str = None) -> None:
        """Create a new user with hashed password."""
        requerir(datos.get("username"), "Nombre de usuario")
        requerir(datos.get("nombre"), "Nombre completo")
        pwd = datos.get("password_raw", "")
        if not pwd:
            raise ValidacionError(mensaje_usuario="La contraseña es obligatoria para nuevos usuarios.")

        # Validar fortaleza de contraseña
        password_errors = SecurityManager.validate_password_strength(pwd)
        if password_errors:
            error_msg = "; ".join(password_errors)
            raise ValidacionError(
                detalle=f"Contraseña débil: {error_msg}",
                mensaje_usuario=f"La contraseña no cumple los requisitos: {error_msg}"
            )

        if UsuarioRepositorySA.obtener_por_username(datos["username"]):
            raise NegocioError(mensaje_usuario="El nombre de usuario ya está en uso.")

        try:
            usuario_validado = UsuarioCreate(
                username=datos["username"].strip(),
                password_raw=pwd,
                nombre=datos["nombre"].strip(),
                rol=datos.get("rol", "Operador"),
                email=datos.get("email", "").strip(),
                activo=True,
            )
        except Exception as e:
            raise ValidacionError(f"Datos de usuario inválidos: {str(e)}")

        UsuarioRepositorySA.insertar(usuario_validado)
        audit.info("Usuario creado: %s (rol=%s)", datos["username"], datos.get("rol"))

    @staticmethod
    @require_role(*ROLES_CON_USUARIOS)
    def actualizar(datos: dict, session_id: str = None) -> None:
        """Update a user. If 'password_raw' is present, the password changes."""
        requerir(datos.get("username"), "Nombre de usuario")
        requerir(datos.get("nombre"), "Nombre completo")

        # Si se está cambiando la contraseña, validar fortaleza
        if datos.get("password_raw"):
            password_errors = SecurityManager.validate_password_strength(datos["password_raw"])
            if password_errors:
                error_msg = "; ".join(password_errors)
                raise ValidacionError(
                    detalle=f"Contraseña débil: {error_msg}",
                    mensaje_usuario=f"La contraseña no cumple los requisitos: {error_msg}"
                )

        update_data = UsuarioUpdate(
            username=datos["username"],
            nombre=datos.get("nombre", "").strip(),
            rol=datos.get("rol"),
            email=datos.get("email", "").strip(),
            activo=bool(int(datos.get("activo", 1))) if datos.get("activo") is not None else None,
            password_raw=datos.get("password_raw", "") or None,
        )

        UsuarioRepositorySA.actualizar(update_data)
        audit.info("Usuario actualizado: %s", datos["username"])

    @staticmethod
    @require_role(*ROLES_CON_USUARIOS)
    def eliminar(username: str, session_id: str = None) -> None:
        if username == "admin":
            raise NegocioError(mensaje_usuario="No se puede eliminar el Administrador Principal.")
        UsuarioRepositorySA.eliminar(username)
        audit.info("Usuario eliminado: %s", username)
