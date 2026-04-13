"""
usuario_service.py — Servicio de Usuarios

Extraido de services_extra.py como parte de F1B (Reestructuración de Services).
"""
from typing import List, Dict

from core.exceptions import NegocioError, ValidacionError
from core.logger import get_logger, get_audit_logger
from core.validators import requerir
from core.schemas import UsuarioCreate, UsuarioUpdate
from repositories.repositories_sa import UsuarioRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class UsuarioService:

    @staticmethod
    def listar() -> List[Dict]:
        return UsuarioRepositorySA.obtener_todos()

    @staticmethod
    def crear(datos: dict) -> None:
        """Crea un nuevo usuario con contraseña hasheada."""
        requerir(datos.get("username"), "Nombre de usuario")
        requerir(datos.get("nombre"), "Nombre completo")
        pwd = datos.get("password_raw", "")
        if not pwd:
            raise ValidacionError(mensaje_usuario="La contraseña es obligatoria para nuevos usuarios.")

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
    def actualizar(datos: dict) -> None:
        """Actualiza un usuario. Si 'password_raw' está presente, cambia la contraseña."""
        requerir(datos.get("username"), "Nombre de usuario")
        requerir(datos.get("nombre"), "Nombre completo")

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
    def eliminar(username: str) -> None:
        if username == "admin":
            raise NegocioError(mensaje_usuario="No se puede eliminar el Administrador Principal.")
        UsuarioRepositorySA.eliminar(username)
        audit.info("Usuario eliminado: %s", username)
