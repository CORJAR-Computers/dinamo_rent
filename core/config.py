"""
config.py — Configuración centralizada de Dinamo Rent ERP

Lee TODA la configuración desde config.ini (en la raíz del proyecto).
Ya NO usa python-dotenv ni valores hardcodeados.

Si config.ini no existe, usa valores por defecto y lo genera automáticamente.

Variables de entorno (opcional, sobreescriben al .ini):
    DINAMO_DB_ENGINE   — sobreescribe [database].engine
    DINAMO_DB_HOST     — sobreescribe [database].host
    DINAMO_DB_PORT     — sobreescribe [database].port
    DINAMO_DB_USER     — sobreescribe [database].user
    DINAMO_DB_PASSWORD — sobreescribe [database].password
    DINAMO_DB_NAME     — sobreescribe [database].database
"""

import os
import configparser
from pathlib import Path

# ─── Rutas base ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
INI_PATH = BASE_DIR / "config.ini"


# ═══════════════════════════════════════════════════════════════════════════════
# LECTOR DE config.ini
# ═══════════════════════════════════════════════════════════════════════════════


class _Config:
    """
    Wrapper sobre configparser que provee métodos tipados y
    fallback a valores por defecto si el .ini no existe o falta una clave.
    """

    # Valores por defecto (usados si config.ini no existe o falta la clave)
    _DEFAULTS = {
        "database": {
            "engine": "firebird",
            "host": "localhost",
            "port": "3050",
            "user": "sysdba",
            "password": "masterkey",
            "database": "dinamo_rent",
            "path": "dinamo_rent_v3.fdb",
            "timeout": "10",
            "pool_size": "10",
            "pool_max_overflow": "20",
            "pool_pre_ping": "true",
        },
        "security": {
            "hash_algorithm": "sha256",
            "hash_iterations": "100000",
            "session_timeout": "3600",
            "max_login_attempts": "5",
            "account_lockout_duration": "1800",
            "login_rate_limit_window": "300",
            "max_login_attempts_in_window": "10",
            "db_encryption_key": "",
        },
        "backup": {
            "directory": "Backups",
            "max_copies": "10",
            "schedule_times": "09:00, 13:00, 19:00, 23:00",
            "check_interval_ms": "60000",
            "encryption_enabled": "false",
            "encryption_password": "",
        },
        "logging": {
            "directory": "logs",
            "max_size_mb": "5",
            "backup_count": "5",
            "level": "INFO",
            "error_max_size_mb": "2",
            "error_backup_count": "3",
            "audit_enabled": "true",
            "audit_retention_days": "30",
        },
        "application": {
            "name": "Dinamo Rent ERP",
            "version": "3.2.0",
            "author": "Corjar Computers",
            "language": "es",
            "timezone": "America/Bogota",
            "production_mode": "false",
            "setup_completed": "false",
        },
        "ui": {
            "color_primario": "#2563eb",
            "color_primario_hover": "#1d4ed8",
            "color_primario_focus": "#93c5fd",
            "color_fondo": "#f8fafc",
            "color_exito": "#22c55e",
            "color_success_hover": "#16a34a",
            "color_peligro": "#ef4444",
            "color_danger_hover": "#dc2626",
            "color_alerta": "#f97316",
            "color_surface": "#ffffff",
            "color_border": "#e2e8f0",
            "color_text_primary": "#0f172a",
            "color_text_secondary": "#64748b",
            "color_alt_row": "#f8fafc",
            "color_estado_disponible": "#22c55e",
            "color_estado_rentado": "#2563eb",
            "color_estado_mantenimiento": "#f97316",
            "color_estado_inactivo": "#ef4444",
            "color_estado_activo": "#22c55e",
            "color_estado_vip": "#9333ea",
            "color_estado_lista_negra": "#ef4444",
            "color_cal_disponible": "#bfdbfe",
            "color_cal_rentado": "#a7f3d0",
            "color_cal_reservado": "#fed7aa",
            "font_family": "Segoe UI",
            "font_size": "11",
            "window_width": "1400",
            "window_height": "800",
            "start_maximized": "true",
        },
        "business": {
            "alert_soat_days": "15",
            "alert_tecno_mecanica_days": "15",
            "alert_extintor_days": "15",
            "km_alert_aceite": "500",
            "roles_con_informes": "Administrador, Supervisor",
            "roles_con_usuarios": "Administrador",
            "tipos_auto": "Automóvil, Camioneta, Van, Lujo, Moto",
            "tipos_transmision": "Automática, Mecánica",
            "tipos_combustible": "Gasolina, Diesel, Híbrido, Eléctrico, Gas",
            "estados_auto": "Disponible, Rentado, Mantenimiento, Vendido, Baja",
            "tipos_adquisicion": "Propio, Leasing, Subarrendado",
            "tipos_doc": "Cédula, Pasaporte, Cédula Extranjería, NIT, Licencia USA",
            "estados_cliente": "Activo, Inactivo, Lista Negra, VIP",
            "nivel_tanque": "Lleno, 3/4, 1/2, 1/4, Reserva",
            "tipos_mantenimiento": "Cambio Aceite, Frenos, Llantas, Batería, Tecno-Mecánica, Lavado General, Reparación Mecánica, Otro",
        },
        "email": {
            "enabled": "false",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": "587",
            "use_tls": "true",
            "username": "",
            "password": "",
            "from_email": "",
            "from_name": "Corjar Computers",
        },
        "whatsapp": {
            "enabled": "true",
            "base_url": "https://wa.me/",
        },
        "reports": {
            "pdf_engine": "weasyprint",
            "excel_enabled": "true",
            "currency_symbol": "$",
            "currency_code": "COP",
            "decimal_places": "2",
            "tax_enabled": "true",
            "tax_percentage": "19",
        },
    }

    def __init__(self):
        self._parser = configparser.ConfigParser(
            interpolation=None,
            comment_prefixes=(";", "#"),
        )
        # Cargar defaults como sección DEFAULT (siempre disponibles)
        for section, values in self._DEFAULTS.items():
            if not self._parser.has_section(section):
                self._parser.add_section(section)
            for key, val in values.items():
                self._parser.set(section, key, val)

        # Leer config.ini si existe (sobreescribe defaults)
        if INI_PATH.exists():
            self._parser.read(str(INI_PATH), encoding="utf-8")

    # ── Métodos tipados ────────────────────────────────────────

    def get(self, section: str, key: str, fallback: str = None) -> str:
        """Retorna un valor como string."""
        try:
            val = self._parser.get(section, key)
            return val
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback if fallback is not None else ""

    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """Retorna un valor como int."""
        try:
            return self._parser.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def getfloat(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Retorna un valor como float."""
        try:
            return self._parser.getfloat(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def getbool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Retorna un valor como bool (true/1/yes = True)."""
        try:
            return self._parser.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def getlist(self, section: str, key: str, fallback: list = None) -> list:
        """Retorna un valor como lista (separado por comas, strip automático)."""
        raw = self.get(section, key, fallback="")
        if not raw:
            return fallback or []
        return [item.strip() for item in raw.split(",") if item.strip()]

    def getset(self, section: str, key: str, fallback: set = None) -> set:
        """Retorna un valor como set (separado por comas, strip automático)."""
        return set(self.getlist(section, key, fallback=list(fallback or [])))

    def set(self, section: str, key: str, value: str):
        """Asigna un valor en el parser (en memoria)."""
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        self._parser.set(section, key, str(value))

    def save(self):
        """Guarda los cambios del parser físico en el archivo config.ini."""
        with open(INI_PATH, "w", encoding="utf-8") as configfile:
            self._parser.write(configfile)


def guardar_configuracion(seccion: str, valores: dict):
    """Actualiza y guarda múltiples valores en una sección específica."""
    for k, v in valores.items():
        _cfg.set(seccion, k, v)
    _cfg.save()


# Instancia global (se crea una sola vez al importar)
_cfg = _Config()


# ═══════════════════════════════════════════════════════════════════════════════
# VARIABLES PÚBLICAS — Interface compatible con el resto de la app
# ═══════════════════════════════════════════════════════════════════════════════

# ─── Directorios ──────────────────────────────────────────────────────────────
LOGS_DIR = BASE_DIR / _cfg.get("logging", "directory", "logs")
BACKUP_DIR = BASE_DIR / _cfg.get("backup", "directory", "Backups")

LOGS_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

# ─── Base de datos ────────────────────────────────────────────────────────────
# Variables de entorno tienen prioridad absoluta (para Docker/VPS)
DB_ENGINE = os.getenv("DINAMO_DB_ENGINE", _cfg.get("database", "engine", "firebird"))

DB_NAME = _cfg.get("database", "path", "dinamo_rent_v3.fdb")
DB_PATH = str(BASE_DIR / DB_NAME)
DB_TIMEOUT = _cfg.getint("database", "timeout", 10)

DB_MYSQL = {
    "host": os.getenv("DINAMO_DB_HOST", _cfg.get("database", "host", "localhost")),
    "port": int(os.getenv("DINAMO_DB_PORT", _cfg.get("database", "port", "3306"))),
    "user": os.getenv("DINAMO_DB_USER", _cfg.get("database", "user", "root")),
    "password": os.getenv("DINAMO_DB_PASSWORD", _cfg.get("database", "password", "")),
    "database": os.getenv("DINAMO_DB_NAME", _cfg.get("database", "database", "dinamo_rent")),
}

DB_POOL_SIZE = _cfg.getint("database", "pool_size", 10)
DB_POOL_MAX_OVERFLOW = _cfg.getint("database", "pool_max_overflow", 20)
DB_POOL_PRE_PING = _cfg.getbool("database", "pool_pre_ping", True)

# ─── Seguridad ────────────────────────────────────────────────────────────────
HASH_ALGORITHM = _cfg.get("security", "hash_algorithm", "sha256")
HASH_ITERATIONS = _cfg.getint("security", "hash_iterations", 100000)
SESSION_TIMEOUT = _cfg.getint("security", "session_timeout", 3600)
MAX_LOGIN_ATTEMPTS = _cfg.getint("security", "max_login_attempts", 5)
ACCOUNT_LOCKOUT_DURATION = _cfg.getint("security", "account_lockout_duration", 1800)
LOGIN_RATE_LIMIT_WINDOW = _cfg.getint("security", "login_rate_limit_window", 300)
MAX_LOGIN_ATTEMPTS_IN_WINDOW = _cfg.getint("security", "max_login_attempts_in_window", 10)

# ─── Backup ───────────────────────────────────────────────────────────────────
BACKUP_HOURS = _cfg.getlist("backup", "schedule_times", ["09:00", "13:00", "19:00", "23:00"])
BACKUP_MAX_COPIES = _cfg.getint("backup", "max_copies", 10)
BACKUP_INTERVAL_MS = _cfg.getint("backup", "check_interval_ms", 60000)
BACKUP_ENCRYPTION = _cfg.getbool("backup", "encryption_enabled", False)
BACKUP_ENC_PASSWORD = _cfg.get("backup", "encryption_password", "")

# ─── UI ───────────────────────────────────────────────────────────────────────
COLOR_PRIMARIO = _cfg.get("ui", "color_primario", "#1e40af")
COLOR_PRIMARIO_HOVER = _cfg.get("ui", "color_primario_hover", "#1d4ed8")
COLOR_PRIMARIO_FOCUS = _cfg.get("ui", "color_primario_focus", "#3b82f6")
COLOR_FONDO = _cfg.get("ui", "color_fondo", "#f8fafc")
COLOR_EXITO = _cfg.get("ui", "color_exito", "#2e7d32")
COLOR_SUCCESS_HOVER = _cfg.get("ui", "color_success_hover", "#1b5e20")
COLOR_PELIGRO = _cfg.get("ui", "color_peligro", "#c62828")
COLOR_DANGER_HOVER = _cfg.get("ui", "color_danger_hover", "#b71c1c")
COLOR_ALERTA = _cfg.get("ui", "color_alerta", "#ef6c00")
COLOR_SURFACE = _cfg.get("ui", "color_surface", "#ffffff")
COLOR_BORDER = _cfg.get("ui", "color_border", "#e0e0e0")
COLOR_TEXT_PRIMARY = _cfg.get("ui", "color_text_primary", "#1a1a2e")
COLOR_TEXT_SECONDARY = _cfg.get("ui", "color_text_secondary", "#666666")
COLOR_ALT_ROW = _cfg.get("ui", "color_alt_row", "#f5f7fa")

COLOR_ESTADO_DISPONIBLE = _cfg.get("ui", "color_estado_disponible", "#2e7d32")
COLOR_ESTADO_RENTADO = _cfg.get("ui", "color_estado_rentado", "#1565c0")
COLOR_ESTADO_MANTENIMIENTO = _cfg.get("ui", "color_estado_mantenimiento", "#ef6c00")
COLOR_ESTADO_INACTIVO = _cfg.get("ui", "color_estado_inactivo", "#c62828")
COLOR_ESTADO_ACTIVO = _cfg.get("ui", "color_estado_activo", "#2e7d32")
COLOR_ESTADO_VIP = _cfg.get("ui", "color_estado_vip", "#7b1fa2")
COLOR_ESTADO_LISTA_NEGRA = _cfg.get("ui", "color_estado_lista_negra", "#c62828")

COLOR_CAL_DISPONIBLE = _cfg.get("ui", "color_cal_disponible", "#bbdefb")
COLOR_CAL_RENTADO = _cfg.get("ui", "color_cal_rentado", "#81c784")
COLOR_CAL_RESERVADO = _cfg.get("ui", "color_cal_reservado", "#ffd54f")

FONT_FAMILY = _cfg.get("ui", "font_family", "Segoe UI")
FONT_SIZE = _cfg.getint("ui", "font_size", 10)

# ─── Alertas ──────────────────────────────────────────────────────────────────
DIAS_ALERTA_SOAT = _cfg.getint("business", "alert_soat_days", 15)
DIAS_ALERTA_TECNICO = _cfg.getint("business", "alert_tecno_mecanica_days", 15)
DIAS_ALERTA_EXTINTOR = _cfg.getint("business", "alert_extintor_days", 15)
KM_ALERTA_ACEITE_PREV = _cfg.getint("business", "km_alert_aceite", 500)

# ─── App ──────────────────────────────────────────────────────────────────────
APP_NAME = _cfg.get("application", "name", "Dinamo Rent ERP")
APP_VERSION = _cfg.get("application", "version", "3.2.0")
APP_AUTHOR = _cfg.get("application", "author", "Corjar Computers")
APP_LANGUAGE = _cfg.get("application", "language", "es")
APP_TIMEZONE = _cfg.get("application", "timezone", "America/Bogota")
PRODUCTION_MODE = _cfg.getbool("application", "production_mode", False)
SETUP_COMPLETED = _cfg.getbool("application", "setup_completed", False)

# ─── Roles ────────────────────────────────────────────────────────────────────
ROLES = ["Administrador", "Operador", "Supervisor", "Mecánico"]
ROLES_CON_INFORMES = _cfg.getset("business", "roles_con_informes", {"Administrador", "Supervisor"})
ROLES_CON_USUARIOS = _cfg.getset("business", "roles_con_usuarios", {"Administrador"})

# ─── Combos estáticos ────────────────────────────────────────────────────────
TIPOS_AUTO = _cfg.getlist(
    "business", "tipos_auto", ["Automóvil", "Camioneta", "Van", "Lujo", "Moto"]
)
TIPOS_TRANSMISION = _cfg.getlist("business", "tipos_transmision", ["Automática", "Mecánica"])
TIPOS_COMBUSTIBLE = _cfg.getlist(
    "business", "tipos_combustible", ["Gasolina", "Diesel", "Híbrido", "Eléctrico", "Gas"]
)
ESTADOS_AUTO = _cfg.getlist(
    "business", "estados_auto", ["Disponible", "Rentado", "Mantenimiento", "Vendido", "Baja"]
)
TIPOS_ADQUISICION = _cfg.getlist(
    "business", "tipos_adquisicion", ["Propio", "Leasing", "Subarrendado"]
)
TIPOS_DOC = _cfg.getlist(
    "business", "tipos_doc", ["Cédula", "Pasaporte", "Cédula Extranjería", "NIT", "Licencia USA"]
)
ESTADOS_CLIENTE = _cfg.getlist(
    "business", "estados_cliente", ["Activo", "Inactivo", "Lista Negra", "VIP"]
)
NIVEL_TANQUE = _cfg.getlist("business", "nivel_tanque", ["Lleno", "3/4", "1/2", "1/4", "Reserva"])
TIPOS_MANTENIMIENTO = _cfg.getlist(
    "business",
    "tipos_mantenimiento",
    [
        "Cambio Aceite",
        "Frenos",
        "Llantas",
        "Batería",
        "Tecno-Mecánica",
        "Lavado General",
        "Reparación Mecánica",
        "Otro",
    ],
)
PAISES_DEFECTO = _cfg.getlist(
    "business",
    "paises_defecto",
    [
        "Colombia",
        "México",
        "Estados Unidos",
        "España",
        "Perú",
        "Argentina",
        "Chile",
        "Ecuador",
        "Panamá",
        "Costa Rica",
    ],
)

# ─── Email ────────────────────────────────────────────────────────────────────
EMAIL_ENABLED = _cfg.getbool("email", "enabled", False)
EMAIL_SMTP = _cfg.get("email", "smtp_server", "smtp.gmail.com")
EMAIL_PORT = _cfg.getint("email", "smtp_port", 587)
EMAIL_USE_TLS = _cfg.getbool("email", "use_tls", True)
EMAIL_USER = _cfg.get("email", "username", "")
EMAIL_PASSWORD = _cfg.get("email", "password", "")
EMAIL_FROM = _cfg.get("email", "from_email", "")
EMAIL_FROM_NAME = _cfg.get("email", "from_name", "Corjar Computers")

# ─── WhatsApp ─────────────────────────────────────────────────────────────────
WHATSAPP_ENABLED = _cfg.getbool("whatsapp", "enabled", True)
WHATSAPP_URL = _cfg.get("whatsapp", "base_url", "https://wa.me/")

# ─── Reportes ─────────────────────────────────────────────────────────────────
REPORTS_PDF_ENGINE = _cfg.get("reports", "pdf_engine", "weasyprint")
REPORTS_EXCEL = _cfg.getbool("reports", "excel_enabled", True)
CURRENCY_SYMBOL = _cfg.get("reports", "currency_symbol", "$")
CURRENCY_CODE = _cfg.get("reports", "currency_code", "COP")
CURRENCY_DECIMALS = _cfg.getint("reports", "decimal_places", 2)
TAX_ENABLED = _cfg.getbool("reports", "tax_enabled", True)
TAX_PERCENTAGE = _cfg.getfloat("reports", "tax_percentage", 19.0)

# ─── Logging ──────────────────────────────────────────────────────────────────
LOG_MAX_SIZE_MB = _cfg.getint("logging", "max_size_mb", 5)
LOG_BACKUP_COUNT = _cfg.getint("logging", "backup_count", 5)
LOG_LEVEL = _cfg.get("logging", "level", "INFO")
LOG_ERROR_MAX_SIZE = _cfg.getint("logging", "error_max_size_mb", 2)
LOG_ERROR_BACKUP = _cfg.getint("logging", "error_backup_count", 3)
AUDIT_ENABLED = _cfg.getbool("logging", "audit_enabled", True)
AUDIT_RETENTION_DAYS = _cfg.getint("logging", "audit_retention_days", 30)
