"""Dialogo base con LoadingOverlay + QTimer.singleShot + guardia RuntimeError.

Provee:
    - _init_overlay(message) — crea y muestra el LoadingOverlay
    - _deferred_load() — hook para inicialización diferida (override)
    - _deferred_call(fn) — guardia RuntimeError + ciclo overlay show/hide
    - _callback_ex — inyección de excepciones para tests
    - Animación fade-in al mostrar, fade-out al cerrar con Escape
    - Enter → click botón aceptar / acept()
    - Escape → reject() con fade-out

Uso:
    class MiDialogo(BaseDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._setup_ui()
            self._init_overlay("Cargando...")
            QTimer.singleShot(0, self._deferred_load)

        def _deferred_load(self):
            self.cargar_datos()
"""

from typing import Any, Optional

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGraphicsOpacityEffect,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
)

from views.components.loading_spinner import LoadingOverlay


class BaseDialog(QDialog):
    """Dialogo base con LoadingOverlay, carga diferida y guardia RuntimeError.

    Subclases:
    1. Llamar ``self._init_overlay(mensaje)`` en __init__ si usan overlay
    2. Sobrescribir ``_deferred_load()`` para inicialización diferida
    3. O llamar ``self._deferred_call(fn)`` desde QTimer.singleShot

    Para tests, pasar ``callback_ex=<Exception>()`` para simular errores
    en el callback diferido.

    Características:
    - Animación fade-in al mostrar (showEvent)
    - Animación fade-out al presionar Escape
    - Enter → intenta hacer click en botón Guardar/Aceptar/Save, o accept()
    - Escape → reject() con fade-out
    - Hereda todo el manejo de LoadingOverlay de la versión anterior
    """

    LOADING_MESSAGE: str = "Cargando..."
    ENABLE_ANIMATIONS: bool = True
    ANIMATION_DURATION_MS: int = 200

    def __init__(
        self,
        parent: QDialog | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent)
        # callback_ex es consumido por BaseDialog; no pasa a QDialog
        self._callback_ex: BaseException | None = kwargs.pop("callback_ex", None)
        self._loading_overlay: Optional[LoadingOverlay] = None
        self._fade_out_pending: bool = False

        if self.ENABLE_ANIMATIONS:
            self._setup_animation()

    # ── Animación ──────────────────────────────────────────────────────────

    def _setup_animation(self) -> None:
        """Configura QGraphicsOpacityEffect + QPropertyAnimation para fade."""
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)

        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(self.ANIMATION_DURATION_MS)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ── API pública ────────────────────────────────────────────────────────

    def _init_overlay(self, message: str | None = None) -> None:
        """Crea y muestra el LoadingOverlay.

        Llamar desde __init__ de la subclase. Es seguro llamarlo
        múltiples veces (solo crea si es None).
        """
        if self._loading_overlay is None:
            self._loading_overlay = LoadingOverlay(self, message or self.LOADING_MESSAGE)
        elif message:
            self._loading_overlay.set_message(message)
        self._loading_overlay.show()

    def _deferred_load(self) -> None:
        """Hook para inicialización diferida.

        Sobrescribir en subclases. Por defecto no hace nada.
        """
        pass

    def _deferred_call(self, func: Any) -> None:
        """Ejecuta func() con guardia RuntimeError + ciclo overlay.

        - Guardia: si el objeto C++ fue destruido, retorna silenciosamente
        - RuntimeError se suprime (widget destruido entre timer y callback)
        - Otras excepciones se relanzan
        - Overlay se oculta en ``finally``
        """
        # Guard: C++ object may have been deleted
        try:
            _ = self.isWidgetType()
        except RuntimeError:
            self._loading_overlay = None
            return

        self._show_overlay_safe()
        if self._loading_overlay is not None:
            try:
                self._loading_overlay.repaint()
            except RuntimeError:
                self._loading_overlay = None

        try:
            if self._callback_ex:
                raise self._callback_ex
            func()
        except RuntimeError:
            pass
        except Exception:
            raise
        finally:
            self._hide_overlay_safe()

    # ── Teclado ────────────────────────────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event is None:
            super().keyPressEvent(event)
            return

        key = event.key()

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._handle_enter(event)
            return

        if key == Qt.Key.Key_Escape:
            self._close_with_fade()
            return

        super().keyPressEvent(event)

    def _handle_enter(self, event: QKeyEvent) -> None:
        """Enter: intenta hacer click en btn Guardar/Aceptar/Save, o accept()."""
        widget = self.focusWidget()

        # Botones y combos manejan su propio Enter
        if isinstance(widget, (QPushButton, QComboBox)):
            super().keyPressEvent(event)
            return

        # Texto multilínea no debe cerrar el diálogo con Enter
        if isinstance(widget, (QTextEdit, QPlainTextEdit)):
            super().keyPressEvent(event)
            return

        # Buscar botón principal de acción
        if self._click_accept_button():
            return

        # Fallback: accept directo
        self.accept()

    def _click_accept_button(self) -> bool:
        """Busca y hace click en el botón aceptar principal.

        Busca por objectName: guardar, aceptar, save, ok. Si lo encuentra
        y está habilitado, hace click() y retorna True.
        Si encuentra botones aceptar pero todos están deshabilitados,
        retorna True igualmente para evitar el fallback a accept().
        """
        names = ("guardar", "aceptar", "save", "ok")
        found_disabled = False
        for btn in self.findChildren(QPushButton):
            obj_name = btn.objectName().lower()
            if any(n in obj_name for n in names):
                if btn.isEnabled() and btn.isVisible():
                    btn.click()
                    return True
                found_disabled = True
        return found_disabled

    def _close_with_fade(self) -> None:
        """Escape: anima fade-out y luego reject().

        La animación se ejecuta completa antes de llamar a reject()
        para evitar complicaciones con closeEvent / done / señales
        duplicadas. Durante la animación se deshabilita el diálogo.
        """
        if self.ENABLE_ANIMATIONS:
            self._fade_out_pending = True
            self._fade_anim.finished.connect(self._complete_fade_close)
            self._fade_anim.setStartValue(self._opacity_effect.opacity())
            self._fade_anim.setEndValue(0.0)
            self._fade_anim.start()
            self.setEnabled(False)
        else:
            self.reject()

    def _complete_fade_close(self) -> None:
        """Callback: animación terminada → reject() real."""
        try:
            self._fade_anim.finished.disconnect(self._complete_fade_close)
        except (RuntimeError, TypeError):
            pass
        self._fade_out_pending = False
        self.setEnabled(True)
        self.reject()

    # ── Eventos de ciclo de vida ───────────────────────────────────────────

    def showEvent(self, event: Any) -> None:
        """Anima fade-in al mostrar el diálogo."""
        if self.ENABLE_ANIMATIONS:
            self._opacity_effect.setOpacity(0.0)
            self._fade_anim.stop()
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.start()
        super().showEvent(event)

    def closeEvent(self, event: Any) -> None:
        """Limpieza simple sin interceptación de animación.

        La animación de salida se maneja en _close_with_fade antes
        de llamar a reject(), no aquí.
        """
        self._loading_overlay = None
        super().closeEvent(event)

    def accept(self) -> None:
        """Accept inmediato (sin fade-out)."""
        self._fade_out_pending = False
        super().accept()

    def reject(self) -> None:
        """Reject inmediato (sin fade-out)."""
        self._fade_out_pending = False
        super().reject()

    # ── Helpers internos ────────────────────────────────────────────────────

    def _show_overlay_safe(self) -> None:
        if self._loading_overlay is None:
            return
        try:
            self._loading_overlay.show()
        except RuntimeError:
            self._loading_overlay = None

    def _hide_overlay_safe(self) -> None:
        if self._loading_overlay is None:
            return
        try:
            self._loading_overlay.hide()
        except RuntimeError:
            self._loading_overlay = None
