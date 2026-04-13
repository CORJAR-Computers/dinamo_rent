"""
config.py — Configuración centralizada de Dinamo Rent ERP
Soporta SQLite (local/desarrollo) y MySQL (red/producción).

Para cambiar entre bases de datos edita solo la variable DB_ENGINE.
Para producción, usa variables de entorno en lugar de hardcodear credenciales.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (si existe)
load_dotenv()

# ─── Rutas base ───────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
LOGS_DIR   = BASE_DIR / "logs"
BACKUP_DIR = BASE_DIR / "Backups"

LOGS_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

# ─── Motor de base de datos ──────────────────────────────────────────────────
# Cambia a "mysql" cuando tengas MySQL listo
DB_ENGINE = os.getenv("DINAMO_DB_ENGINE", "mysql")   # "sqlite" | "mysql"

# ─── SQLite (para desarrollo local sin servidor) ──────────────────────────────
DB_NAME    = "dinamo_rent_v3.db"
DB_PATH    = str(BASE_DIR / DB_NAME)
DB_TIMEOUT = 10

# ─── MySQL / MariaDB ──────────────────────────────────────────────────────────
# Las variables de entorno tienen prioridad sobre los valores por defecto.
# En producción (VPS / nube) define las variables de entorno en el servidor
# y nunca pongas contraseñas reales en el código.
DB_MYSQL = {
    "host":     os.getenv("DINAMO_DB_HOST",     "localhost"),
    "port":     int(os.getenv("DINAMO_DB_PORT", "3306")),
    "user":     os.getenv("DINAMO_DB_USER",     "root"),          # Usuario por defecto en XAMPP
    "password": os.getenv("DINAMO_DB_PASSWORD", ""),              # Sin contraseña en XAMPP por defecto
    "database": os.getenv("DINAMO_DB_NAME",     "dinamo_rent"),
}

# ─── Seguridad ────────────────────────────────────────────────────────────────
HASH_ALGORITHM     = "sha256"
HASH_ITERATIONS    = 100_000
MAX_LOGIN_ATTEMPTS = 5
SESSION_TIMEOUT    = 3600

# ─── Backup ───────────────────────────────────────────────────────────────────
BACKUP_HOURS       = ["09:00", "13:00", "19:00", "23:00"]
BACKUP_MAX_COPIES  = 10
BACKUP_INTERVAL_MS = 60_000

# ─── UI ───────────────────────────────────────────────────────────────────────
COLOR_PRIMARIO = "#004aad"
COLOR_FONDO    = "#f0f2f5"
COLOR_EXITO    = "#2e7d32"
COLOR_PELIGRO  = "#c62828"
COLOR_ALERTA   = "#ef6c00"
FONT_FAMILY    = "Segoe UI"
FONT_SIZE      = 10

# ─── Alertas ──────────────────────────────────────────────────────────────────
DIAS_ALERTA_SOAT      = 15
DIAS_ALERTA_TECNICO   = 15
DIAS_ALERTA_EXTINTOR  = 15
KM_ALERTA_ACEITE_PREV = 500

# ─── App ──────────────────────────────────────────────────────────────────────
APP_NAME    = "Dinamo Rent ERP"
APP_VERSION = "3.2.0"
APP_AUTHOR  = "Dinamo Rent a Car"

# ─── Roles ───────────────────────────────────────────────────────────────────
ROLES               = ["Administrador", "Operador", "Supervisor", "Mecánico"]
ROLES_CON_INFORMES  = {"Administrador", "Supervisor"}
ROLES_CON_USUARIOS  = {"Administrador"}

# ─── Combos estáticos ────────────────────────────────────────────────────────
TIPOS_AUTO          = ["Automóvil", "Camioneta", "Van", "Lujo", "Moto"]
TIPOS_TRANSMISION   = ["Automática", "Mecánica"]
TIPOS_COMBUSTIBLE   = ["Gasolina", "Diesel", "Híbrido", "Eléctrico", "Gas"]
ESTADOS_AUTO        = ["Disponible", "Rentado", "Mantenimiento", "Vendido", "Baja"]
TIPOS_ADQUISICION   = ["Propio", "Leasing", "Subarrendado"]
TIPOS_DOC           = ["Cédula", "Pasaporte", "Cédula Extranjería", "NIT", "Licencia USA"]
ESTADOS_CLIENTE     = ["Activo", "Inactivo", "Lista Negra", "VIP"]
NIVEL_TANQUE        = ["Lleno", "3/4", "1/2", "1/4", "Reserva"]
TIPOS_MANTENIMIENTO = [
    "Cambio Aceite", "Frenos", "Llantas", "Batería",
    "Tecno-Mecánica", "Lavado General", "Reparación Mecánica", "Otro"
]