"""
security.py — Gestión de contraseñas, sesiones y seguridad mejorada

Separado de database.py para poder usarlo sin importar la BD
(por ejemplo, desde los tests).
"""
import hashlib
import secrets
import time
import re
from typing import Optional, Dict, List
from collections import defaultdict

from core.config import HASH_ALGORITHM, HASH_ITERATIONS, SESSION_TIMEOUT
from core.exceptions import SesionExpirada


# ─── Configuración de seguridad ───────────────────────────────────────────────

MAX_LOGIN_ATTEMPTS = 5  # Intentos antes de bloqueo
ACCOUNT_LOCKOUT_DURATION = 1800  # 30 minutos de bloqueo
LOGIN_RATE_LIMIT_WINDOW = 300  # 5 minutos ventana de rate limiting
MAX_LOGIN_ATTEMPTS_IN_WINDOW = 10  # Máx intentos en la ventana

# Rate limiting por IP
IP_RATE_LIMIT_WINDOW = 60  # 1 minuto ventana para IP
IP_MAX_ATTEMPTS_IN_WINDOW = 20  # Máx 20 intentos por IP por minuto


class IPRateLimiter:
    """Rate limiting por dirección IP."""

    def __init__(self):
        self._ip_timestamps: Dict[str, List[float]] = defaultdict(list)
        self._blocked_ips: Dict[str, float] = {}

    def record_request(self, ip: str) -> int:
        """Registra un intento y retorna cantidad en ventana."""
        now = time.time()
        self._ip_timestamps[ip].append(now)
        self._clean_old_timestamps(ip, now)
        return len(self._ip_timestamps[ip])

    def is_rate_limited(self, ip: str) -> bool:
        """Verifica si IP excedió el límite."""
        if ip in self._blocked_ips:
            if time.time() < self._blocked_ips[ip]:
                return True
            else:
                del self._blocked_ips[ip]
        return False

    def block_ip(self, ip: str, duration: int = 300) -> None:
        """Bloquea IP por periodo."""
        self._blocked_ips[ip] = time.time() + duration

    def get_remaining_attempts(self, ip: str) -> int:
        """Intentos restantes para IP."""
        return max(0, IP_MAX_ATTEMPTS_IN_WINDOW - len(self._ip_timestamps.get(ip, [])))

    def _clean_old_timestamps(self, ip: str, now: float) -> None:
        """Elimina timestamps antiguos."""
        cutoff = now - IP_RATE_LIMIT_WINDOW
        self._ip_timestamps[ip] = [ts for ts in self._ip_timestamps[ip] if ts > cutoff]


class LoginAttemptTracker:
    """Rastrea intentos fallidos de login por username/IP."""

    def __init__(self):
        self._failed_attempts: Dict[str, int] = defaultdict(int)
        self._lockout_until: Dict[str, float] = {}
        self._login_timestamps: Dict[str, List[float]] = defaultdict(list)
        self._ip_tracker = IPRateLimiter()

    def record_failed_attempt(self, identifier: str, ip: str = None) -> int:
        """Registra un intento fallido y retorna el total de intentos."""
        now = time.time()
        self._failed_attempts[identifier] += 1

        # Registrar timestamp para rate limiting
        self._login_timestamps[identifier].append(now)

        # Limpiar timestamps antiguos
        self._clean_old_timestamps(identifier, now)

        # Registrar también por IP si se proporciona
        if ip:
            self._ip_tracker.record_request(ip)

        return self._failed_attempts[identifier]

    def is_locked(self, identifier: str) -> bool:
        """Verifica si la cuenta está bloqueada."""
        if identifier not in self._lockout_until:
            return False

        if time.time() < self._lockout_until[identifier]:
            return True

        # Desbloquear automáticamente
        del self._lockout_until[identifier]
        self._failed_attempts[identifier] = 0
        return False

    def lock_account(self, identifier: str) -> None:
        """Bloquea la cuenta por el período configurado."""
        self._lockout_until[identifier] = time.time() + ACCOUNT_LOCKOUT_DURATION

    def reset_attempts(self, identifier: str) -> None:
        """Reinicia los intentos tras login exitoso."""
        self._failed_attempts[identifier] = 0
        self._login_timestamps[identifier] = []

    def check_rate_limit(self, identifier: str, ip: str = None) -> bool:
        """Verifica si se excedió el límite de rate. True = excedido."""
        now = time.time()
        self._clean_old_timestamps(identifier, now)

        # Verificar rate limiting de usuario
        if len(self._login_timestamps[identifier]) > MAX_LOGIN_ATTEMPTS_IN_WINDOW:
            return True

        # Verificar rate limiting de IP
        if ip and self._ip_tracker.is_rate_limited(ip):
            return True

        return False

    def check_ip_rate_limit(self, ip: str) -> tuple:
        """Verifica rate limit por IP. Retorna (bloqueado, intentos_usados)."""
        if ip:
            attempts = self._ip_tracker.record_request(ip)
            return attempts >= IP_MAX_ATTEMPTS_IN_WINDOW, attempts
        return False, 0

    def _clean_old_timestamps(self, identifier: str, now: float) -> None:
        """Elimina timestamps fuera de la ventana."""
        cutoff = now - LOGIN_RATE_LIMIT_WINDOW
        self._login_timestamps[identifier] = [
            ts for ts in self._login_timestamps[identifier]
            if ts > cutoff
        ]

    def get_remaining_attempts(self, identifier: str) -> int:
        """Retorna intentos restantes antes del bloqueo."""
        return max(0, MAX_LOGIN_ATTEMPTS - self._failed_attempts.get(identifier, 0))

    def get_lockout_remaining_time(self, identifier: str) -> int:
        """Retorna segundos restantes de bloqueo, o 0 si no está bloqueado."""
        if identifier not in self._lockout_until:
            return 0
        remaining = int(self._lockout_until[identifier] - time.time())
        return max(0, remaining)


# Tracker global de intentos
login_tracker = LoginAttemptTracker()


class SecurityManager:
    """Utilidades de criptografía para contraseñas."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Genera hash PBKDF2 con salt aleatorio."""
        if not password:
            return ""
        salt = secrets.token_hex(16)
        h = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            password.encode(),
            salt.encode(),
            HASH_ITERATIONS,
        )
        return f"{h.hex()}:{salt}"

    @staticmethod
    def verify_password(stored: str, provided: str) -> bool:
        """Compara en tiempo constante para prevenir timing attacks."""
        try:
            if not stored or ":" not in stored:
                return False
            hash_val, salt = stored.split(":", 1)
            new_hash = hashlib.pbkdf2_hmac(
                HASH_ALGORITHM,
                provided.encode(),
                salt.encode(),
                HASH_ITERATIONS,
            )
            return secrets.compare_digest(new_hash.hex(), hash_val)
        except Exception:
            return False

    @staticmethod
    def validate_password_strength(password: str) -> List[str]:
        """
        Valida la fortaleza de la contraseña.
        Retorna lista de errores (vacía = válida).
        """
        errors = []
        if len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres")
        if len(password) > 128:
            errors.append("La contraseña no puede tener más de 128 caracteres")
        if not re.search(r'[A-Z]', password):
            errors.append("Debe contener al menos una letra mayúscula")
        if not re.search(r'[a-z]', password):
            errors.append("Debe contener al menos una letra minúscula")
        if not re.search(r'\d', password):
            errors.append("Debe contener al menos un número")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Debe contener al menos un carácter especial (!@#$%^&*(),.?\"':{}|<>)")
        return errors

    @staticmethod
    def sanitize_input(value: str, max_length: int = 500, allow_html: bool = False) -> str:
        """
        Sanitiza entradas de usuario para prevenir inyección.

        Args:
            value: Valor de entrada
            max_length: Longitud máxima permitida
            allow_html: Si se permite HTML (default False)

        Returns:
            Valor sanitizado

        Raises:
            InputSanitizationError: Si el input es malicioso
        """
        if not value:
            return ""

        # Limitar longitud
        if len(value) > max_length:
            value = value[:max_length]

        if not allow_html:
            # Eliminar caracteres potencialmente peligrosos
            # Mantener caracteres básicos para nombres, direcciones, etc.
            dangerous_patterns = [
                r'<script',
                r'javascript:',
                r'on\w+\s*=',  # event handlers como onclick=
                r'<iframe',
                r'<object',
                r'<embed',
                r'<form',
                r'union\s+select',  # SQL injection
                r'drop\s+table',    # SQL injection
                r';\s*--',          # SQL comment injection
            ]

            value_lower = value.lower()
            for pattern in dangerous_patterns:
                if re.search(pattern, value_lower, re.IGNORECASE):
                    from core.exceptions import InputSanitizationError
                    raise InputSanitizationError(
                        detalle=f"Patrón peligroso detectado: {pattern}",
                        mensaje_usuario="El texto contiene caracteres no permitidos."
                    )

        # Eliminar null bytes
        value = value.replace('\x00', '')

        return value.strip()

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Genera un token criptográficamente seguro."""
        return secrets.token_urlsafe(length)


class SessionManager:
    """Gestión de sesiones en memoria (proceso único)."""

    _sessions: Dict[str, dict] = {}

    @classmethod
    def create(cls, user_id: int, username: str, role: str, nombre: str) -> str:
        session_id = secrets.token_urlsafe(32)
        cls._sessions[session_id] = {
            "user_id":      user_id,
            "username":     username,
            "role":         role,
            "nombre":       nombre,
            "last_activity": time.time(),
        }
        return session_id

    @classmethod
    def get(cls, session_id: str) -> Optional[dict]:
        data = cls._sessions.get(session_id)
        if data is None:
            return None
        if time.time() - data["last_activity"] > SESSION_TIMEOUT:
            cls.destroy(session_id)
            raise SesionExpirada()
        data["last_activity"] = time.time()
        return data

    @classmethod
    def destroy(cls, session_id: str) -> None:
        cls._sessions.pop(session_id, None)

    @classmethod
    def purge_expired(cls) -> int:
        """Elimina sesiones expiradas. Retorna la cantidad eliminada."""
        ahora = time.time()
        expiradas = [
            sid for sid, data in cls._sessions.items()
            if ahora - data["last_activity"] > SESSION_TIMEOUT
        ]
        for sid in expiradas:
            del cls._sessions[sid]
        return len(expiradas)
