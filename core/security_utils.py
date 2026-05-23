"""
security_utils.py - Utilidades de seguridad para protección de archivos y datos sensibles

Proporciona funciones para:
- Encriptar/desencriptar archivos .env y configuraciones
- Gestión segura de credenciales
- Limpieza segura de archivos
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class FileEncryptor:
    """Encriptación de archivos sensibles con AES-256."""

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        """Deriva una clave de 32 bytes desde una contraseña."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    @staticmethod
    def encrypt_file(file_path: str, password: str, output_path: str = None) -> str:
        """
        Encripta un archivo con AES-256.

        Args:
            file_path: Ruta del archivo a encriptar
            password: Contraseña para encriptar
            output_path: Ruta de salida (opcional, default: .enc)

        Returns:
            Ruta del archivo encriptado
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        if output_path is None:
            output_path = file_path + ".enc"

        # Generar salt y derivar clave
        salt = os.urandom(16)
        key = FileEncryptor._derive_key(password, salt)
        fernet = Fernet(key)

        # Leer y encriptar
        with open(file_path, 'rb') as f:
            file_data = f.read()

        encrypted_data = fernet.encrypt(file_data)

        # Guardar con salt al inicio
        with open(output_path, 'wb') as f:
            f.write(salt)
            f.write(encrypted_data)

        return output_path

    @staticmethod
    def decrypt_file(encrypted_path: str, password: str, output_path: str = None) -> str:
        """
        Desencripta un archivo.

        Args:
            encrypted_path: Ruta del archivo encriptado
            password: Contraseña utilizada
            output_path: Ruta de salida (opcional, default: sin .enc)

        Returns:
            Ruta del archivo desencriptado
        """
        if not os.path.exists(encrypted_path):
            raise FileNotFoundError(f"Archivo no encontrado: {encrypted_path}")

        if output_path is None:
            if encrypted_path.endswith('.enc'):
                output_path = encrypted_path[:-4]
            else:
                output_path = encrypted_path + ".decrypted"

        # Leer archivo
        with open(encrypted_path, 'rb') as f:
            salt = f.read(16)
            encrypted_data = f.read()

        # Derivar clave y desencriptar
        key = FileEncryptor._derive_key(password, salt)
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)

        # Guardar
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)

        return output_path


class SecureEnvManager:
    """Gestión segura de archivos .env."""

    @staticmethod
    def mask_sensitive_value(key: str, value: str) -> str:
        """
        Enmascara valores sensibles para logging/display.

        Ejemplo: 'my_secret_password' -> 'my_******rd'
        """
        if not value or len(value) < 4:
            return "****"

        sensitive_keys = ['password', 'secret', 'key', 'token', 'pass']
        is_sensitive = any(s in key.lower() for s in sensitive_keys)

        if not is_sensitive:
            return value

        # Mostrar primeros y últimos 2 caracteres
        return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"

    @staticmethod
    def validate_env_security(env_path: str = None) -> list:
        """
        Valida la seguridad de un archivo .env.

        Returns:
            Lista de problemas encontrados
        """
        if env_path is None:
            from core.config import BASE_DIR
            env_path = BASE_DIR / ".env"

        issues = []

        if not os.path.exists(env_path):
            issues.append(f"Archivo .env no encontrado: {env_path}")
            return issues

        # Verificar permisos del archivo (Windows)
        # En Windows los permisos son más limitados, pero podemos verificar si es de solo lectura

        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Verificar contraseñas vacías
                    if 'password' in key.lower() and not value:
                        issues.append(f"Contraseña vacía para: {key}")

                    # Verificar contraseñas débiles
                    if 'password' in key.lower() and value:
                        if len(value) < 8:
                            issues.append(f"Contraseña muy corta para {key} (< 8 caracteres)")
                        if value in ['password', '123456', 'admin', 'root', '']:
                            issues.append(f"Contraseña por defecto o débil para {key}")

        return issues

    @staticmethod
    def secure_delete_file(file_path: str, passes: int = 3) -> bool:
        """
        Elimina un archivo de forma segura (sobrescritura múltiple).

        Args:
            file_path: Archivo a eliminar
            passes: Número de pasadas de sobrescritura

        Returns:
            True si se eliminó exitosamente
        """
        if not os.path.exists(file_path):
            return False

        try:
            file_size = os.path.getsize(file_path)

            # Sobrescribir múltiples veces
            for i in range(passes):
                with open(file_path, 'wb') as f:
                    # Escribir bytes aleatorios
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())

            # Eliminar archivo
            os.remove(file_path)
            return True
        except Exception as e:
            from core.logger import get_logger
            log = get_logger(__name__)
            log.error("Error elimin archivo seguro %s: %s", file_path, e)
            return False


class CredentialManager:
    """Gestión segura de credenciales en memoria."""

    _credentials = {}
    _fernet = Fernet(Fernet.generate_key())

    @classmethod
    def store(cls, service: str, username: str, password: str) -> None:
        """Almacena credenciales en memoria (no persistente) usando cifrado en memoria."""
        encrypted = cls._fernet.encrypt(password.encode()).decode()
        cls._credentials[service] = {
            'username': username,
            'password': encrypted,
            '_encrypted': True,
        }

    @classmethod
    def get(cls, service: str) -> dict:
        """Obtiene credenciales."""
        cred = cls._credentials.get(service)
        if not cred:
            return None
        if cred.get('_encrypted'):
            try:
                decoded = cls._fernet.decrypt(cred['password'].encode())
                return {
                    'username': cred['username'],
                    'password': decoded.decode(),
                }
            except Exception:
                return None
        return cred

    @classmethod
    def clear(cls, service: str = None) -> None:
        """Limpia credenciales de memoria."""
        if service:
            cls._credentials.pop(service, None)
        else:
            cls._credentials.clear()

    @classmethod
    def list_services(cls) -> list:
        """Lista servicios con credenciales almacenadas."""
        return list(cls._credentials.keys())
