"""Authentication service with enhanced security."""

from core.exceptions import (
    CredencialesInvalidas,
    CuentaBloqueadaError,
    RateLimitExceededError,
    ValidacionError,
)
from core.logger import get_logger, get_audit_logger
from core.security import SecurityManager, SessionManager, login_tracker
from repositories.repositories_sa import UsuarioRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class AuthService:
    @staticmethod
    def login(username: str, password: str, ip: str = None) -> dict:
        if not username or not password:
            raise CredencialesInvalidas()

        # Verificar si la cuenta está bloqueada
        if login_tracker.is_locked(username):
            remaining_time = login_tracker.get_lockout_remaining_time(username)
            minutes = remaining_time // 60
            seconds = remaining_time % 60
            log.warning(
                "Intento de login en cuenta bloqueada: %s (restan %dm %ds)",
                username,
                minutes,
                seconds,
            )
            raise CuentaBloqueadaError(
                detalle=f"Cuenta bloqueada por {minutes} minutos y {seconds} segundos",
                mensaje_usuario=f"Tu cuenta está bloqueada. Intenta nuevamente en {minutes} minutos.",
            )

        # Verificar rate limiting por IP
        if ip:
            blocked, attempts = login_tracker.check_ip_rate_limit(ip)
            if blocked:
                log.warning("Rate limit excedido por IP: %s (intentos: %d)", ip, attempts)
                raise RateLimitExceededError(
                    detalle="Demasiados intentos desde esta IP",
                    mensaje_usuario="Demasiados intentos. Espera unos minutos.",
                )

        # Verificar rate limiting por usuario
        if login_tracker.check_rate_limit(username, ip):
            log.warning("Rate limit excedido para usuario: %s", username)
            raise RateLimitExceededError(
                detalle="Demasiados intentos de login en corto tiempo",
                mensaje_usuario="Demasiados intentos. Espera unos minutos antes de intentar nuevamente.",
            )

        # Buscar usuario
        usuario = UsuarioRepositorySA.obtener_por_username(username)

        if not usuario or not SecurityManager.verify_password(usuario["password"], password):
            # Registrar intento fallido (ahora con IP)
            attempts = login_tracker.record_failed_attempt(username, ip)
            remaining = login_tracker.get_remaining_attempts(username)

            log.warning(
                "Intento de login fallido: %s (intentos: %d, restantes: %d, IP: %s)",
                username,
                attempts,
                remaining,
                ip or "desconocida",
            )
            audit.info(
                "LOGIN FALLIDO: usuario=%s, intentos=%d, restantes=%d, IP=%s",
                username,
                attempts,
                remaining,
                ip or "desconocida",
            )

            # Bloquear cuenta si se excedieron los intentos
            if attempts >= 5:
                login_tracker.lock_account(username)
                log.warning("CUENTA BLOQUEADA: %s (demasiados intentos fallidos)", username)
                audit.warning("CUENTA BLOQUEADA: usuario=%s", username)
                raise CuentaBloqueadaError()

            raise CredencialesInvalidas()

        # Login exitoso - resetear intentos
        login_tracker.reset_attempts(username)

        UsuarioRepositorySA.registrar_acceso(username)

        sid = SessionManager.create(
            usuario["id"], usuario["username"], usuario["rol"], usuario["nombre"]
        )

        log.info("Login exitoso: %s (rol=%s, IP=%s)", username, usuario["rol"], ip or "desconocida")
        audit.info(
            "LOGIN OK: usuario=%s, rol=%s, IP=%s", username, usuario["rol"], ip or "desconocida"
        )

        return {
            "success": True,
            "session_id": sid,
            "username": usuario["username"],
            "nombre": usuario["nombre"],
            "rol": usuario["rol"],
            "debe_cambiar_password": usuario["debe_cambiar_password"],
        }

    @staticmethod
    def get_login_status(username: str) -> dict:
        """Obtiene el estado de login de un usuario (intentos, bloqueo, etc.)."""
        return {
            "is_locked": login_tracker.is_locked(username),
            "lockout_remaining_seconds": login_tracker.get_lockout_remaining_time(username),
            "failed_attempts": login_tracker._failed_attempts.get(username, 0),
            "remaining_attempts": login_tracker.get_remaining_attempts(username),
        }

    @staticmethod
    def cambiar_password_obligatorio(
        username: str, current_password: str, new_password: str
    ) -> None:
        """
        Cambio de contraseña obligatorio (debe_cambiar_password = True).

        1. Verifica la contraseña actual
        2. Valida que la nueva no sea igual a la actual
        3. Valida fortaleza de la nueva contraseña
        4. Actualiza hash + limpia flag debe_cambiar_password
        """
        from core.database_sa import get_session
        from core.models import Usuario

        if not username or not current_password or not new_password:
            raise CredencialesInvalidas(mensaje_usuario="Todos los campos son obligatorios.")

        # 1. Obtener usuario con hash actual
        usuario = UsuarioRepositorySA.obtener_por_username(username)
        if not usuario:
            raise CredencialesInvalidas(mensaje_usuario="Usuario no encontrado.")

        # 2. Verificar contraseña actual
        if not SecurityManager.verify_password(usuario["password"], current_password):
            log.warning(
                "Intento de cambio de contraseña con contraseña actual incorrecta: %s", username
            )
            audit.warning(
                "CAMBIO CONTRASEÑA FALLIDO: usuario=%s (contraseña actual incorrecta)", username
            )
            raise CredencialesInvalidas(mensaje_usuario="La contraseña actual no es correcta.")

        # 3. No puede ser igual a la actual
        if current_password == new_password:
            raise ValidacionError(
                mensaje_usuario="La nueva contraseña debe ser diferente a la actual."
            )

        # 4. Validar fortaleza
        errors = SecurityManager.validate_password_strength(new_password)
        if errors:
            error_msg = "; ".join(errors)
            raise ValidacionError(
                detalle=f"Contraseña débil: {error_msg}",
                mensaje_usuario=f"La contraseña no cumple los requisitos: {error_msg}",
            )

        # 5. Actualizar en base de datos
        with get_session() as session:
            user = session.query(Usuario).filter(Usuario.username == username).first()
            if not user:
                raise CredencialesInvalidas(mensaje_usuario="Usuario no encontrado.")
            user.password = SecurityManager.hash_password(new_password)
            user.debe_cambiar_password = 0

        log.info("Contraseña cambiada exitosamente (cambio obligatorio): %s", username)
        audit.info("CAMBIO CONTRASEÑA OBLIGATORIO: usuario=%s", username)

    @staticmethod
    def unlock_account(username: str) -> bool:
        """Desbloquea manualmente una cuenta (solo para administradores)."""
        if login_tracker.is_locked(username):
            login_tracker._lockout_until.pop(username, None)
            login_tracker._failed_attempts[username] = 0
            audit.info("CUENTA DESBLOQUEADA: usuario=%s por administrador", username)
            log.info("Cuenta desbloqueada manualmente: %s", username)
            return True
        return False
