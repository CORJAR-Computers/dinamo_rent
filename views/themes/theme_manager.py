"""
theme_manager.py — Gestión de temas con persistencia en config.ini

Permite cambiar entre temas Dinamo (claro) y SaaS (oscuro) con persistencia.
"""

from views.themes import THEME_DINAMO, THEME_SAAS, build_stylesheet
from core.app_config import config
from PySide6.QtWidgets import QApplication

# ── Registro de temas disponibles ────────────────────────────────────────────
THEMES = {
    "dinamo": THEME_DINAMO,
    "saas": THEME_SAAS,
}

THEME_LABELS = {
    "dinamo": "Claro",
    "saas": "Oscuro",
}

THEME_ICONS = {
    "dinamo": "☀️",
    "saas": "🌙",
}


def get_current_theme_name() -> str:
    """Retorna el nombre del tema actual desde config.ini."""
    return config.get('ui', 'theme', fallback='dinamo')


def set_theme_name(name: str) -> None:
    """Persiste el nombre del tema en config.ini."""
    config.set('ui', 'theme', name)
    config.save()


def apply_theme(theme_name: str = None) -> None:
    """Aplica el tema especificado (o el actual) a la QApplication global."""
    if theme_name is None:
        theme_name = get_current_theme_name()
    theme = THEMES.get(theme_name, THEME_DINAMO)
    app = QApplication.instance()
    if app:
        app.setStyleSheet(build_stylesheet(theme))


def toggle_theme() -> str:
    """Cambia al tema opuesto y lo aplica. Retorna el nombre del nuevo tema."""
    current = get_current_theme_name()
    new = "saas" if current == "dinamo" else "dinamo"
    set_theme_name(new)
    apply_theme(new)
    return new
