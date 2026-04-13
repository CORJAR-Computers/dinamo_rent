"""
auth_service.py — Servicio de Autenticación

Extraido de services.py como parte de F1B (Reestructuración de Services).
"""
from core.exceptions import CredencialesInvalidas
from core.logger import get_logger, get_audit_logger
from core.security import SecurityManager, SessionManager
from repositories.repositories_sa import UsuarioRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class AuthService:

    @staticmethod
    def login(username: str, password: str) -> dict:
        if not username or not password:
            raise CredencialesInvalidas()

        usuario = UsuarioRepositorySA.obtener_por_username(username)

        if not usuario or not SecurityManager.verify_password(usuario["password"], password):
            log.warning("Intento de login fallido: %s", username)
            audit.info("LOGIN FALLIDO: usuario=%s", username)
            raise CredencialesInvalidas()

        UsuarioRepositorySA.registrar_acceso(username)

        sid = SessionManager.create(
            usuario["id"], usuario["username"], usuario["rol"], usuario["nombre"]
        )

        log.info("Login exitoso: %s (rol=%s)", username, usuario["rol"])
        audit.info("LOGIN OK: usuario=%s, rol=%s", username, usuario["rol"])

        return {
            "success": True,
            "session_id": sid,
            "username": usuario["username"],
            "nombre": usuario["nombre"],
            "rol": usuario["rol"],
        }
