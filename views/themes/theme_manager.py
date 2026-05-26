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
    return config.get("ui", "theme", fallback="dinamo")


def set_theme_name(name: str) -> None:
    """Persiste el nombre del tema en config.ini."""
    config.set("ui", "theme", name)
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


def animated_toggle_theme(parent_widget) -> str:
    """Cambia de tema con transición suave fade-out → cambio → fade-in.

    Aplica un efecto de opacidad animado sobre *parent_widget* (ej. el
    ``centralWidget`` de MainWindow), cambia el tema en el punto más
    tenue del fade, y luego restaura la opacidad.

    Incluye guarda anti-re-entrada: si ya hay una animación en curso
    (detectada por un ``_theme_animating`` flag en el widget), la
    llamada se descarta silenciosamente.

    Returns:
        Nombre del nuevo tema aplicado, o ``None`` si se descartó.
    """
    from PySide6.QtWidgets import QGraphicsOpacityEffect
    from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QAbstractAnimation

    # ── Guarda anti-re-entrada ──────────────────────────────────────────
    if getattr(parent_widget, "_theme_animating", False):
        return None

    current = get_current_theme_name()
    new = "saas" if current == "dinamo" else "dinamo"

    parent_widget._theme_animating = True

    # ── Efecto de opacidad sobre el widget padre ────────────────────────
    effect = QGraphicsOpacityEffect(parent_widget)
    parent_widget.setGraphicsEffect(effect)

    # ── Fade out: 1.0 → 0.15 ────────────────────────────────────────────
    anim_out = QPropertyAnimation(effect, b"opacity")
    anim_out.setParent(effect)  # ← evita GC prematuro
    anim_out.setDuration(130)
    anim_out.setStartValue(1.0)
    anim_out.setEndValue(0.15)
    anim_out.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _on_fade_out_finished():
        # Aplicar nuevo tema en el punto más tenue
        set_theme_name(new)
        apply_theme(new)

        # ── Fade in: 0.15 → 1.0 ────────────────────────────────────────
        anim_in = QPropertyAnimation(effect, b"opacity")
        anim_in.setParent(effect)  # ← evita GC prematuro
        anim_in.setDuration(130)
        anim_in.setStartValue(0.15)
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_fade_in_finished():
            # Limpiar flag y remover el efecto
            parent_widget._theme_animating = False
            parent_widget.setGraphicsEffect(None)

        anim_in.finished.connect(_on_fade_in_finished)
        anim_in.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    anim_out.finished.connect(_on_fade_out_finished)
    anim_out.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
