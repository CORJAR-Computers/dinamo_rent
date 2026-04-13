"""
security.py — Gestión de contraseñas y sesiones

Separado de database.py para poder usarlo sin importar la BD
(por ejemplo, desde los tests).
"""
import hashlib
import secrets
import time
from typing import Optional, Dict

from core.config import HASH_ALGORITHM, HASH_ITERATIONS, SESSION_TIMEOUT
from core.exceptions import CredencialesInvalidas, SesionExpirada


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
