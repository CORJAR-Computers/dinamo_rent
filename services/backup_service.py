"""
backup_service.py — Servicio de Backups

Extraido de services.py como parte de F1B (Reestructuración de Services).
"""
import datetime
import os
import shutil
import subprocess

from core.config import BACKUP_DIR, DB_PATH, BACKUP_MAX_COPIES, DB_ENGINE, DB_MYSQL
from core.logger import get_logger

log = get_logger(__name__)


class BackupService:

    @staticmethod
    def crear() -> tuple[bool, str]:
        """Crea backup de la base de datos (soporta MySQL y SQLite)."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            if DB_ENGINE == "mysql":
                nombre = f"Backup_Dinamo_{timestamp}.sql"
                destino = os.path.join(str(BACKUP_DIR), nombre)

                cfg = DB_MYSQL
                command = [
                    "mysqldump",
                    f"--host={cfg['host']}",
                    f"--port={cfg['port']}",
                    f"--user={cfg['user']}",
                    f"--password={cfg['password']}",
                    "--default-character-set=utf8mb4",
                    "--single-transaction",
                    "--routines",
                    "--triggers",
                    cfg['database'],
                ]

                with open(destino, 'w', encoding='utf-8') as f:
                    result = subprocess.run(
                        command,
                        stdout=f,
                        stderr=subprocess.PIPE,
                        timeout=120
                    )

                if result.returncode != 0:
                    error_msg = result.stderr.decode('utf-8', errors='ignore')
                    log.error("Error en mysqldump: %s", error_msg)
                    if os.path.exists(destino):
                        os.remove(destino)
                    return False, f"Error creando backup MySQL: {error_msg}"

            else:
                if not os.path.exists(DB_PATH):
                    return False, "Base de datos SQLite no encontrada."

                nombre = f"Backup_Dinamo_{timestamp}.db"
                destino = os.path.join(str(BACKUP_DIR), nombre)
                shutil.copy2(DB_PATH, destino)

            # Limpiar backups antiguos
            archivos = sorted(
                [os.path.join(str(BACKUP_DIR), f) for f in os.listdir(str(BACKUP_DIR))
                 if f.endswith((".db", ".sql"))],
                key=os.path.getmtime,
            )
            while len(archivos) > BACKUP_MAX_COPIES:
                os.remove(archivos.pop(0))

            log.info("Backup creado: %s", nombre)
            return True, f"Copia creada: {nombre}"
        except subprocess.TimeoutExpired:
            log.error("Timeout creando backup")
            return False, "Timeout creando backup"
        except Exception as e:
            log.error("Error creando backup: %s", e)
            return False, str(e)
