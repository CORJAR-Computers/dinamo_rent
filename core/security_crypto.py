"""
security_crypto.py — Encriptación transparente para campos de SQLAlchemy
Usa Fernet (AES-128-CBC + HMAC SHA256) de la librería `cryptography`.
"""

import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from sqlalchemy.types import TypeDecorator, String, Text

from core.config import BASE_DIR, _cfg
from core.logger import get_logger

log = get_logger(__name__)

# Intentar obtener o generar clave de encriptación persistente en config.ini
def _get_or_create_crypto_key() -> bytes:
    key_str = _cfg.get("security", "db_encryption_key", fallback="").strip()
    if not key_str:
        # Generar nueva clave Fernet si no existe
        key_bytes = Fernet.generate_key()
        key_str = key_bytes.decode('utf-8')
        _cfg.set("security", "db_encryption_key", key_str)
        try:
            _cfg.save()
            log.info("Nueva clave de encriptación de datos generada y guardada en config.ini")
        except Exception as e:
            log.warning(f"No se pudo guardar db_encryption_key en config.ini: {e}")
        return key_bytes
    else:
        try:
            return key_str.encode('utf-8')
        except Exception:
            return Fernet.generate_key()

_FERNET_INSTANCE: Optional[Fernet] = None

def get_fernet() -> Fernet:
    global _FERNET_INSTANCE
    if _FERNET_INSTANCE is None:
        key = _get_or_create_crypto_key()
        _FERNET_INSTANCE = Fernet(key)
    return _FERNET_INSTANCE


class EncryptedString(TypeDecorator):
    """
    Tipo de columna SQLAlchemy que encripta antes de guardar en BD
    y desencripta transparente al leer.
    """
    impl = String
    cache_ok = True

    def __init__(self, length: int = 255, *args, **kwargs):
        super().__init__(length, *args, **kwargs)

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        if value is None or value == "":
            return value
        try:
            fernet = get_fernet()
            encrypted_bytes = fernet.encrypt(value.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            log.error(f"Error encriptando campo: {e}")
            return value

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        if value is None or value == "":
            return value
        try:
            fernet = get_fernet()
            decrypted_bytes = fernet.decrypt(value.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception:
            # Si el valor no estaba encriptado (ej. migraciones previas), retornar valor original
            return value


class EncryptedText(TypeDecorator):
    """
    Tipo de columna SQLAlchemy para textos largos encriptados.
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        if value is None or value == "":
            return value
        try:
            fernet = get_fernet()
            encrypted_bytes = fernet.encrypt(value.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            log.error(f"Error encriptando campo Text: {e}")
            return value

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        if value is None or value == "":
            return value
        try:
            fernet = get_fernet()
            decrypted_bytes = fernet.decrypt(value.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception:
            return value
