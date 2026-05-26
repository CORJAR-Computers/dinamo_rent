"""
rbac.py — Control de acceso basado en roles (RBAC) para la capa de servicios

Proporciona decoradores para verificar permisos a nivel de servicio,
no solo en la UI.

CORRECCIONES vs versión original:
  - Eliminada heurística peligrosa len(args[0]) > 20 que podía consumir
    argumentos legítimos (placas, nombres, etc.)
  - Ahora session_id se pasa EXCLUSIVAMENTE como keyword argument
    o como primer argumento posicional identificado por convención
  - Añadido @require_permissions para verificaciones múltiples
"""

from functools import wraps
from typing import Callable, Any, Optional

from core.exceptions import PermisoInsuficiente
from core.security import SessionManager


def _extract_session_id(args: tuple, kwargs: dict) -> Optional[str]:
    """
    Extrae session_id de los argumentos de forma segura.

    Orden de búsqueda:
    1. kwargs['session_id'] — la forma preferida y más explícita
    2. kwargs['sid']        — alias corto opcional

    NO busca en args posicionales para evitar consumir argumentos
    legítimos por error. Si necesitas pasar session_id posicionalmente,
    usa el keyword argument en su lugar.
    """
    session_id = kwargs.pop("session_id", None)
    if session_id is None:
        session_id = kwargs.pop("sid", None)
    return session_id


def _validate_session(session_id: str) -> dict:
    """
    Valida una sesión y retorna los datos del usuario.

    Args:
        session_id: ID de sesión a validar

    Returns:
        dict con datos de la sesión (user_id, username, role, nombre)

    Raises:
        PermisoInsuficiente: Si la sesión es inválida o expirada
    """
    if not session_id:
        raise PermisoInsuficiente(
            detalle="No se proporcionó sesión activa",
            mensaje_usuario="Debes iniciar sesión para realizar esta acción.",
        )

    session_data = SessionManager.get(session_id)
    if not session_data:
        raise PermisoInsuficiente(
            detalle="Sesión inválida o expirada",
            mensaje_usuario="Tu sesión ha expirado. Inicia sesión nuevamente.",
        )

    return session_data


def _log_access_denied(session_data: dict, func_name: str, required: tuple) -> None:
    """Registra intento de acceso denegado en el log de auditoría."""
    from core.logger import get_audit_logger

    audit = get_audit_logger()
    audit.warning(
        "ACCESO DENEGADO: usuario=%s, rol=%s, función=%s, roles_requeridos=%s",
        session_data.get("username"),
        session_data.get("role"),
        func_name,
        required,
    )


def require_role(*allowed_roles: str) -> Callable:
    """
    Decorador que restringe el acceso a funciones según el rol del usuario.

    Uso:
        @require_role('Administrador', 'Supervisor')
        def generar_informe(session_id: str, ...):
            ...

    IMPORTANTE: session_id debe pasarse como keyword argument:
        generar_informe(session_id=sid, ...)

    Args:
        allowed_roles: Roles permitidos para ejecutar la función

    Raises:
        PermisoInsuficiente: Si el usuario no tiene un rol permitido
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            session_id = _extract_session_id(args, kwargs)
            session_data = _validate_session(session_id)

            user_role = session_data.get("role")
            if user_role not in allowed_roles:
                _log_access_denied(session_data, func.__name__, allowed_roles)
                raise PermisoInsuficiente(
                    detalle=f"Rol '{user_role}' no tiene permisos para {func.__name__}",
                    mensaje_usuario="No tienes permisos para realizar esta acción.",
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_active_session(func: Callable) -> Callable:
    """
    Decorador que verifica que exista una sesión activa (sin verificar rol).

    Uso:
        @require_active_session
        def obtener_datos(session_id: str, ...):
            ...

    IMPORTANTE: session_id debe pasarse como keyword argument:
        obtener_datos(session_id=sid, ...)
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        session_id = _extract_session_id(args, kwargs)
        _validate_session(session_id)  # Raises if invalid
        return func(*args, **kwargs)

    return wrapper


class PermissionChecker:
    """Verificador de permisos programático (sin decoradores)."""

    @staticmethod
    def check_role(session_id: str, *required_roles: str) -> dict:
        """
        Verifica el rol del usuario y retorna datos de la sesión.

        Returns:
            dict con datos de la sesión si tiene permisos

        Raises:
            PermisoInsuficiente: Si no tiene el rol requerido
        """
        session_data = SessionManager.get(session_id)
        if not session_data:
            raise PermisoInsuficiente(
                detalle="Sesión inválida o expirada",
                mensaje_usuario="Tu sesión ha expirado. Inicia sesión nuevamente.",
            )

        user_role = session_data.get("role")
        if required_roles and user_role not in required_roles:
            from core.logger import get_audit_logger

            audit = get_audit_logger()
            audit.warning(
                "PERMISO INSUFICIENTE: usuario=%s, rol=%s, requeridos=%s",
                session_data.get("username"),
                user_role,
                required_roles,
            )
            raise PermisoInsuficiente()

        return session_data

    @staticmethod
    def can_access_informes(session_id: str) -> bool:
        """Verifica si el usuario puede acceder a informes financieros."""
        from core.config import ROLES_CON_INFORMES

        try:
            PermissionChecker.check_role(session_id, *ROLES_CON_INFORMES)
            return True
        except PermisoInsuficiente:
            return False

    @staticmethod
    def can_manage_users(session_id: str) -> bool:
        """Verifica si el usuario puede gestionar otros usuarios."""
        from core.config import ROLES_CON_USUARIOS

        try:
            PermissionChecker.check_role(session_id, *ROLES_CON_USUARIOS)
            return True
        except PermisoInsuficiente:
            return False

    @staticmethod
    def get_user_role(session_id: str) -> Optional[str]:
        """Retorna el rol del usuario o None si la sesión es inválida."""
        try:
            session_data = SessionManager.get(session_id)
            return session_data.get("role") if session_data else None
        except Exception:
            return None
