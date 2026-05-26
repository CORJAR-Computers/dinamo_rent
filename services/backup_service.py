"""Database backup service with encryption support."""

import datetime
import os
import shutil
import subprocess
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.config import BACKUP_DIR, DB_PATH, BACKUP_MAX_COPIES, DB_ENGINE, DB_MYSQL
from core.logger import get_logger

log = get_logger(__name__)

_MYSQLDUMP_PATHS = [
    r"C:\xampp\mysql\bin\mysqldump.exe",
    r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
    r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysqldump.exe",
    "mysqldump",
]


def _find_mysqldump() -> str:
    for p in _MYSQLDUMP_PATHS:
        if os.path.isfile(p):
            return p
    return "mysqldump"


def _get_encryption_key(password: str = None) -> bytes:
    """Genera una clave de encriptación basada en una contraseña."""
    if password is None:
        # Usar una contraseña por defecto basada en la fecha
        password = f"DinamoRent_Backup_{datetime.date.today().strftime('%Y%m')}"
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


import base64


from core.app_config import config


class BackupService:
    @staticmethod
    def _get_backup_config() -> tuple[bool, str]:
        try:
            encrypt = config.getboolean("backup", "encryption_enabled", fallback=False)
            encryption_password = config.get("backup", "encryption_password", fallback=None)
            if encrypt and not encryption_password:
                log.warning(
                    "La encriptación de backups está habilitada pero no se ha proporcionado una contraseña. El backup se creará SIN ENCRIPTAR."
                )
                encrypt = False
            return encrypt, encryption_password
        except Exception as e:
            log.error(f"Error leyendo configuración de backup: {e}")
            return False, None

    @staticmethod
    def _backup_mysql(destino: str) -> tuple[bool, str]:
        cfg = DB_MYSQL
        command = [
            _find_mysqldump(),
            f"--host={cfg['host']}",
            f"--port={cfg['port']}",
            f"--user={cfg['user']}",
            f"--password={cfg['password']}",
            "--default-character-set=utf8mb4",
            "--single-transaction",
            "--routines",
            "--triggers",
            cfg["database"],
        ]
        with open(destino, "w", encoding="utf-8") as f:
            result = subprocess.run(command, stdout=f, stderr=subprocess.PIPE, timeout=120)

        if result.returncode != 0:
            error_msg = result.stderr.decode("utf-8", errors="ignore")
            log.error("Error en mysqldump: %s", error_msg)
            if os.path.exists(destino):
                os.remove(destino)
            return False, f"Error creando backup MySQL: {error_msg}"
        return True, ""

    @staticmethod
    def _backup_sqlite(destino: str) -> tuple[bool, str]:
        if not os.path.exists(DB_PATH):
            return False, "Base de datos SQLite no encontrada."
        shutil.copy2(DB_PATH, destino)
        return True, ""

    @staticmethod
    def _cleanup_old_backups():
        archivos = sorted(
            [
                os.path.join(str(BACKUP_DIR), f)
                for f in os.listdir(str(BACKUP_DIR))
                if f.endswith((".db", ".sql", ".enc"))
            ],
            key=os.path.getmtime,
        )
        while len(archivos) > BACKUP_MAX_COPIES:
            os.remove(archivos.pop(0))

    @staticmethod
    def crear() -> tuple[bool, str]:
        """
        Create a database backup, with encryption handled via config.ini.
        """
        encrypt, encryption_password = BackupService._get_backup_config()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        try:
            if DB_ENGINE == "mysql":
                nombre = f"Backup_Dinamo_{timestamp}.sql"
                destino = os.path.join(str(BACKUP_DIR), nombre)
                success, msg = BackupService._backup_mysql(destino)
            else:
                nombre = f"Backup_Dinamo_{timestamp}.db"
                destino = os.path.join(str(BACKUP_DIR), nombre)
                success, msg = BackupService._backup_sqlite(destino)

            if not success:
                return False, msg

            if encrypt:
                try:
                    encrypted_file = BackupService._encrypt_file(destino, encryption_password)
                    os.remove(destino)
                    nombre = os.path.basename(encrypted_file)
                    destino = encrypted_file
                    log.info("Backup encriptado creado: %s", nombre)
                except Exception as e:
                    log.error("Error encriptando backup: %s", e)
                    return False, f"Error encriptando backup: {str(e)}"

            BackupService._cleanup_old_backups()
            log.info("Backup creado: %s", nombre)
            return True, f"Copia creada: {nombre}"

        except subprocess.TimeoutExpired:
            log.error("Timeout creando backup")
            return False, "Timeout creando backup"
        except Exception as e:
            log.error("Error creando backup: %s", e)
            return False, str(e)

    @staticmethod
    def _encrypt_file(file_path: str, password: str) -> str:
        """Encripta un archivo con AES-256 usando la contraseña proporcionada."""
        if not password:
            raise ValueError("La contraseña de encriptación no puede estar vacía.")

        # Generar salt y derivar clave
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        fernet = Fernet(key)

        # Leer archivo original
        with open(file_path, "rb") as f:
            file_data = f.read()

        # Encriptar
        encrypted_data = fernet.encrypt(file_data)

        # Guardar archivo encriptado con salt al inicio
        encrypted_path = file_path + ".enc"
        with open(encrypted_path, "wb") as f:
            f.write(salt)  # Primeros 16 bytes = salt
            f.write(encrypted_data)

        return encrypted_path

    @staticmethod
    def decrypt_file(encrypted_path: str, output_path: str, password: str) -> tuple[bool, str]:
        """
        Desencripta un archivo de backup. La contraseña es requerida.

        Returns:
            (success, message)
        """
        try:
            if not password:
                return False, "Se requiere una contraseña para desencriptar el backup."

            # Leer archivo encriptado
            with open(encrypted_path, "rb") as f:
                salt = f.read(16)  # Primeros 16 bytes = salt
                encrypted_data = f.read()

            # Derivar clave
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            fernet = Fernet(key)

            # Desencriptar
            decrypted_data = fernet.decrypt(encrypted_data)

            # Guardar archivo desencriptado
            with open(output_path, "wb") as f:
                f.write(decrypted_data)

            log.info("Backup desencriptado: %s", output_path)
            return True, "Backup desencriptado exitosamente"
        except Exception as e:
            log.error("Error desencriptando backup: %s", e)
            return False, f"Error desencriptando: {str(e)}"
