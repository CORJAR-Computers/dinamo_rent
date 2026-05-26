"""
app_config.py — Configuración centralizada desde archivo .ini

Este módulo lee y valida el archivo config.ini, proporcionando
una interfaz tipo-dict para acceder a todas las configuraciones.
"""

import os
import configparser
from pathlib import Path
from typing import Any, List


class AppConfig:
    """
    Gestor de configuración centralizado desde config.ini.

    Uso:
        from core.app_config import config

        # Acceder a valores
        db_host = config.get('database', 'host')
        db_port = config.getint('database', 'port')

        # Accesos directos
        db_config = config.get_database_config()
    """

    def __init__(self, config_path: str = None):
        """
        Inicializa el gestor de configuración.

        Args:
            config_path: Ruta al archivo .ini (None = buscar automáticamente)
        """
        self._config = configparser.ConfigParser(
            interpolation=None,  # No interpolar variables
            comment_prefixes=("#", ";"),
            inline_comment_prefixes=(";",),  # Solo ';' como inline; '#' permite colores hex
        )
        self._config_path = self._find_config_file(config_path)
        self._load_config()

    def _find_config_file(self, config_path: str = None) -> str:
        """Busca el archivo de configuración."""
        if config_path and os.path.exists(config_path):
            return config_path

        # Buscar en el directorio base
        base_dir = Path(__file__).resolve().parent.parent
        possible_paths = [
            base_dir / "config.ini",
            base_dir / "config.ini.example",
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        raise FileNotFoundError(
            "No se encontró config.ini. Copiar config.ini.example a config.ini y configurar."
        )

    def _load_config(self) -> None:
        """Carga el archivo de configuración."""
        self._config.read(self._config_path, encoding="utf-8")
        self._validate_config()

    def _validate_config(self) -> None:
        """Valida que existan las secciones requeridas."""
        required_sections = ["database", "security", "application"]

        for section in required_sections:
            if not self._config.has_section(section):
                raise ValueError(f"Sección requerida no encontrada en config.ini: [{section}]")

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """
        Obtiene un valor de configuración como string.

        Args:
            section: Sección del .ini
            key: Clave a obtener
            fallback: Valor por defecto si no existe

        Returns:
            Valor como string
        """
        if self._config.has_section(section):
            return self._config.get(section, key, fallback=fallback)
        return fallback

    def getint(self, section: str, key: str, fallback: int = None) -> int:
        """Obtiene un valor entero."""
        if self._config.has_section(section):
            return self._config.getint(section, key, fallback=fallback)
        return fallback

    def getfloat(self, section: str, key: str, fallback: float = None) -> float:
        """Obtiene un valor flotante."""
        if self._config.has_section(section):
            return self._config.getfloat(section, key, fallback=fallback)
        return fallback

    def getboolean(self, section: str, key: str, fallback: bool = None) -> bool:
        """Obtiene un valor booleano."""
        if self._config.has_section(section):
            return self._config.getboolean(section, key, fallback=fallback)
        return fallback

    def getlist(self, section: str, key: str, fallback: List = None) -> List[str]:
        """
        Obtiene una lista de valores separados por comas.

        Returns:
            Lista de strings limpios
        """
        if self._config.has_section(section):
            value = self._config.get(section, key, fallback="")
            if not value:
                return fallback or []
            return [item.strip() for item in value.split(",")]
        return fallback or []

    def has_section(self, section: str) -> bool:
        """Verifica si existe una sección."""
        return self._config.has_section(section)

    def sections(self) -> List[str]:
        """Retorna todas las secciones."""
        return self._config.sections()

    # ─── Métodos de acceso directo ─────────────────────────────────────────

    def get_database_config(self) -> dict:
        """Retorna configuración completa de base de datos."""
        return {
            "engine": self.get("database", "engine", "mysql"),
            "host": self.get("database", "host", "localhost"),
            "port": self.getint("database", "port", 3306),
            "user": self.get("database", "user", "root"),
            "password": self.get("database", "password", ""),
            "database": self.get("database", "database", "dinamo_rent"),
            "pool_size": self.getint("database", "pool_size", 10),
            "pool_max_overflow": self.getint("database", "pool_max_overflow", 20),
            "pool_pre_ping": self.getboolean("database", "pool_pre_ping", True),
        }

    def get_sqlite_config(self) -> dict:
        """Retorna configuración de SQLite."""
        base_dir = Path(__file__).resolve().parent.parent
        return {
            "path": self.get("database", "path", "dinamo_rent_v3.db"),
            "timeout": self.getint("database", "timeout", 10),
            "full_path": str(base_dir / self.get("database", "path", "dinamo_rent_v3.db")),
        }

    def get_security_config(self) -> dict:
        """Retorna configuración de seguridad."""
        return {
            "hash_algorithm": self.get("security", "hash_algorithm", "sha256"),
            "hash_iterations": self.getint("security", "hash_iterations", 100000),
            "session_timeout": self.getint("security", "session_timeout", 3600),
            "max_login_attempts": self.getint("security", "max_login_attempts", 5),
            "account_lockout_duration": self.getint("security", "account_lockout_duration", 1800),
            "login_rate_limit_window": self.getint("security", "login_rate_limit_window", 300),
            "max_login_attempts_in_window": self.getint(
                "security", "max_login_attempts_in_window", 10
            ),
        }

    def get_backup_config(self) -> dict:
        """Retorna configuración de backups."""
        base_dir = Path(__file__).resolve().parent.parent
        return {
            "directory": str(base_dir / self.get("backup", "directory", "Backups")),
            "max_copies": self.getint("backup", "max_copies", 10),
            "schedule_times": self.getlist("backup", "schedule_times"),
            "check_interval_ms": self.getint("backup", "check_interval_ms", 60000),
            "encryption_enabled": self.getboolean("backup", "encryption_enabled", True),
            "encryption_password": self.get("backup", "encryption_password", ""),
        }

    def get_logging_config(self) -> dict:
        """Retorna configuración de logs."""
        base_dir = Path(__file__).resolve().parent.parent
        return {
            "directory": str(base_dir / self.get("logging", "directory", "logs")),
            "max_size_mb": self.getint("logging", "max_size_mb", 5),
            "backup_count": self.getint("logging", "backup_count", 5),
            "level": self.get("logging", "level", "INFO"),
            "error_max_size_mb": self.getint("logging", "error_max_size_mb", 2),
            "error_backup_count": self.getint("logging", "error_backup_count", 3),
            "audit_enabled": self.getboolean("logging", "audit_enabled", True),
            "audit_retention_days": self.getint("logging", "audit_retention_days", 30),
        }

    def get_application_config(self) -> dict:
        """Retorna configuración general de la aplicación."""
        return {
            "name": self.get("application", "name", "Dinamo Rent ERP"),
            "version": self.get("application", "version", "3.2.0"),
            "author": self.get("application", "author", "Corjar Computers"),
            "language": self.get("application", "language", "es"),
            "timezone": self.get("application", "timezone", "America/Bogota"),
        }

    def get_ui_config(self) -> dict:
        """Retorna configuración de interfaz de usuario."""
        return {
            "color_primario": self.get("ui", "color_primario", "#004aad"),
            "color_primario_hover": self.get("ui", "color_primario_hover", "#003d8f"),
            "color_fondo": self.get("ui", "color_fondo", "#f0f2f5"),
            "color_exito": self.get("ui", "color_exito", "#2e7d32"),
            "color_success_hover": self.get("ui", "color_success_hover", "#1b5e20"),
            "color_peligro": self.get("ui", "color_peligro", "#c62828"),
            "color_danger_hover": self.get("ui", "color_danger_hover", "#b71c1c"),
            "color_alerta": self.get("ui", "color_alerta", "#ef6c00"),
            "color_surface": self.get("ui", "color_surface", "#ffffff"),
            "color_border": self.get("ui", "color_border", "#e0e0e0"),
            "color_text_primary": self.get("ui", "color_text_primary", "#1a1a2e"),
            "color_text_secondary": self.get("ui", "color_text_secondary", "#666666"),
            "color_alt_row": self.get("ui", "color_alt_row", "#f5f7fa"),
            "font_family": self.get("ui", "font_family", "Segoe UI"),
            "font_size": self.getint("ui", "font_size", 10),
            "window_width": self.getint("ui", "window_width", 1366),
            "window_height": self.getint("ui", "window_height", 768),
            "start_maximized": self.getboolean("ui", "start_maximized", True),
        }

    def get_business_config(self) -> dict:
        """Retorna configuración de reglas de negocio."""
        return {
            "alert_soat_days": self.getint("business", "alert_soat_days", 15),
            "alert_tecno_mecanica_days": self.getint("business", "alert_tecno_mecanica_days", 15),
            "alert_extintor_days": self.getint("business", "alert_extintor_days", 15),
            "km_alert_aceite": self.getint("business", "km_alert_aceite", 500),
            "roles_con_informes": set(self.getlist("business", "roles_con_informes")),
            "roles_con_usuarios": set(self.getlist("business", "roles_con_usuarios")),
            "tipos_auto": self.getlist("business", "tipos_auto"),
            "tipos_transmision": self.getlist("business", "tipos_transmision"),
            "tipos_combustible": self.getlist("business", "tipos_combustible"),
            "estados_auto": self.getlist("business", "estados_auto"),
            "tipos_adquisicion": self.getlist("business", "tipos_adquisicion"),
            "tipos_doc": self.getlist("business", "tipos_doc"),
            "estados_cliente": self.getlist("business", "estados_cliente"),
            "nivel_tanque": self.getlist("business", "nivel_tanque"),
            "tipos_mantenimiento": self.getlist("business", "tipos_mantenimiento"),
        }

    def get_email_config(self) -> dict:
        """Retorna configuración de email."""
        return {
            "enabled": self.getboolean("email", "enabled", False),
            "smtp_server": self.get("email", "smtp_server", "smtp.gmail.com"),
            "smtp_port": self.getint("email", "smtp_port", 587),
            "use_tls": self.getboolean("email", "use_tls", True),
            "username": self.get("email", "username", ""),
            "password": self.get("email", "password", ""),
            "from_email": self.get("email", "from_email", ""),
            "from_name": self.get("email", "from_name", "Corjar Computers"),
        }

    def get_reports_config(self) -> dict:
        """Retorna configuración de reportes."""
        return {
            "pdf_engine": self.get("reports", "pdf_engine", "weasyprint"),
            "excel_enabled": self.getboolean("reports", "excel_enabled", True),
            "currency_symbol": self.get("reports", "currency_symbol", "$"),
            "currency_code": self.get("reports", "currency_code", "COP"),
            "decimal_places": self.getint("reports", "decimal_places", 2),
            "tax_enabled": self.getboolean("reports", "tax_enabled", True),
            "tax_percentage": self.getfloat("reports", "tax_percentage", 19.0),
        }

    def reload(self) -> None:
        """Recarga la configuración desde el archivo."""
        self._load_config()

    def save(self, config_path: str = None) -> None:
        """
        Guarda la configuración actual al archivo.

        Args:
            config_path: Ruta de salida (None = sobrescribir actual)
        """
        path = config_path or self._config_path
        with open(path, "w", encoding="utf-8") as f:
            self._config.write(f)

    def set(self, section: str, key: str, value: Any) -> None:
        """
        Establece un valor de configuración.

        Args:
            section: Sección del .ini
            key: Clave a establecer
            value: Valor (se convertirá a string)
        """
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, key, str(value))

    def __repr__(self) -> str:
        return f"<AppConfig loaded from {self._config_path}>"


# ─── Instancia global ────────────────────────────────────────────────────────

# Singleton para acceso fácil desde toda la aplicación
config = AppConfig()


# ─── Funciones helper para compatibilidad con sistema antiguo ────────────────


def get_config() -> AppConfig:
    """Retorna la instancia global de configuración."""
    return config


def reload_config() -> None:
    """Recarga la configuración global."""
    config.reload()
