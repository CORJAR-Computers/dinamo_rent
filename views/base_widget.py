"""Clase base para widgets: errores UI, toast, validación y utilidades de tabla."""

from typing import List, Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget, QLabel, QHeaderView,
    QAbstractItemView, QApplication,
)
from PySide6.QtGui import QShowEvent
from views.components import ModernMessageBox, ToastNotification
from views.components.form_validators import (
    FormValidator, FieldValidator, ValidationRule, make_error_label,
)
from views.components.loading_spinner import LoadingOverlay

from core.exceptions import DinamoBaseError, ValidacionError, NegocioError
from core.logger import get_logger


class BaseWidget(QWidget):
    """Widget base con manejo de errores, toast, validación y diálogos estándar."""

    _LOADING_MESSAGE = "Cargando..."

    def __init__(self, parent=None, session_id: str = None):
        super().__init__(parent)
        self._log = get_logger(self.__class__.__name__)
        self._session_id = session_id
        self._form_validator: Optional[FormValidator] = None
        self._loading_overlay: Optional[LoadingOverlay] = None
        self._datos_cargados = False

    def showEvent(self, event: QShowEvent) -> None:
        """Carga datos diferidos en la primera vez que se muestra el widget."""
        if not self._datos_cargados:
            self._datos_cargados = True
            self._on_first_show()
        super().showEvent(event)

    def _on_first_show(self) -> None:
        """Hook para cargar datos en el primer show.
        Subclases pueden sobreescribirlo para usar un método distinto.
        Por defecto llama a self.cargar_datos() con overlay.
        """
        QTimer.singleShot(0, self._deferred_load)

    # ── Toast ────────────────────────────────────────────────────────────────────────

    def mostrar_toast(self, message: str, level: str = "info",
                      duration: int = 3500,
                      position: str = "top-right") -> None:
        """Muestra notificación toast con apilamiento y animación.

        Args:
            message: Texto del mensaje.
            level: "success" | "warning" | "error" | "info"
            duration: Milisegundos (0 = persistente).
            position: "top-right" | "top-left" | "bottom-right" | "bottom-left"
        """
        window = self.window()
        if window:
            ToastNotification(window, message, level, duration, position)

    def mostrar_error(self, mensaje: str, titulo: str = "Error") -> None:
        """Muestra diálogo de error estándar."""
        self._log.warning("Error mostrado al usuario: %s", mensaje)
        ModernMessageBox.error(self, titulo, mensaje)

    def mostrar_exito(self, mensaje: str, titulo: str = "Éxito") -> None:
        """Muestra notificación toast de éxito (no bloqueante)."""
        self.mostrar_toast(mensaje, "success")

    def mostrar_advertencia(self, mensaje: str, titulo: str = "Atención") -> None:
        """Muestra diálogo de advertencia estándar."""
        ModernMessageBox.warning(self, titulo, mensaje)

    def confirmar(self, mensaje: str, titulo: str = "Confirmar") -> bool:
        """Muestra diálogo de confirmación Sí/No."""
        from PySide6.QtWidgets import QDialog
        return ModernMessageBox.question(self, titulo, mensaje) == QDialog.Accepted

    # ── Validación de formularios ───────────────────────────────────────────────────

    @staticmethod
    def make_error_label() -> QLabel:
        """Crea un QLabel para mostrar errores inline debajo de un campo."""
        return make_error_label()

    def crear_validator(self) -> FormValidator:
        """Crea (o resetea) el FormValidator asociado a este widget."""
        self._form_validator = FormValidator()
        return self._form_validator

    def add_field(self, widget, rules, field_name="", error_label=None) -> FieldValidator:
        """Atajo para agregar un campo al FormValidator activo.

        Requiere haber llamado self.crear_validator() primero.
        """
        if self._form_validator is None:
            self._form_validator = FormValidator()
        return self._form_validator.add_field(widget, rules, field_name, error_label)

    def validar_formulario(self) -> bool:
        """Valida todos los campos registrados.

        Si hay errores, enfoca el primer campo inválido.
        Retorna True si todo es válido.
        """
        if self._form_validator is None:
            return True
        if not self._form_validator.validate_all():
            self._form_validator.focus_first_error()
            return False
        return True

    def limpiar_validacion(self) -> None:
        """Limpia los errores visuales de todos los campos validados."""
        if self._form_validator:
            self._form_validator.clear_all()

    def ejecutar_seguro(self, func, *args, mensaje_exito: str = "", **kwargs):
        """Ejecuta función manejando excepciones automáticamente.

        - DinamoBaseError → mensaje al usuario
        - Exception genérica → log + mensaje genérico
        """
        try:
            resultado = func(*args, **kwargs)
            if mensaje_exito:
                self.mostrar_toast(mensaje_exito, "success")
            return resultado
        except ValidacionError as e:
            self.mostrar_advertencia(e.mensaje_usuario, "Dato inválido")
            self._log.warning("Validación fallida: %s", e)
        except NegocioError as e:
            self.mostrar_advertencia(e.mensaje_usuario, "Operación no permitida")
            self._log.warning("Regla de negocio: %s", e)
        except DinamoBaseError as e:
            self.mostrar_error(e.mensaje_usuario)
            self._log.error("Error de aplicación: %s", e, exc_info=True)
        except Exception as e:
            self.mostrar_error(f"Error inesperado: {e}")
            self._log.error("Error inesperado en %s: %s", self.__class__.__name__, e, exc_info=True)
        return None

    def _init_loading_overlay(self, message: str | None = None) -> None:
        """Inicializa el overlay de carga (llamar desde __init__ de subclases
        si se desea spinner mientras carga datos)."""
        if self._loading_overlay is None:
            self._loading_overlay = LoadingOverlay(
                self, message or self._LOADING_MESSAGE
            )
        elif message:
            self._loading_overlay.set_message(message)

    def _deferred_call(self, func) -> None:
        """Ejecuta func() con overlay de carga.

        Muestra el spinner, forza el renderizado SIN procesar eventos
        ajenos (evita cascadas de timers), ejecuta func() y oculta
        el spinner al finalizar. Es seguro llamarlo desde un QTimer
        incluso si el widget C++ ya fue eliminado.
        """
        # Guard: C++ object may have been deleted (e.g., QTimer fired
        # after widget closed in tests). Return silently if so.
        try:
            _ = self.isWidgetType()
        except RuntimeError:
            self._loading_overlay = None
            return

        self._show_overlay_safe()
        # Sync repaint of overlay — no processEvents() to avoid
        # re-entering other deferred timers.
        if self._loading_overlay is not None:
            try:
                self._loading_overlay.repaint()
            except RuntimeError:
                self._loading_overlay = None

        try:
            func()
        except RuntimeError:
            pass  # Widget C++ destroyed before deferred callback fired (tests only)
        except Exception as e:
            self._log.error("Error en carga: %s", e, exc_info=True)
            raise
        finally:
            self._hide_overlay_safe()

    def _show_overlay_safe(self) -> None:
        """Show the loading overlay, safely ignoring deleted C++ objects."""
        if self._loading_overlay is None:
            return
        try:
            self._loading_overlay.show()
        except RuntimeError:
            self._loading_overlay = None

    def _hide_overlay_safe(self) -> None:
        """Hide the loading overlay, safely ignoring deleted C++ objects."""
        if self._loading_overlay is None:
            return
        try:
            self._loading_overlay.hide()
        except RuntimeError:
            self._loading_overlay = None

    def _deferred_load(self) -> None:
        """Conveniencia: ejecuta self.cargar_datos() con overlay de carga."""
        self._deferred_call(self.cargar_datos)

    @staticmethod
    def ajustar_tabla(tabla, columnas: list[str]) -> None:
        """Configura columnas y comportamiento estándar de una tabla."""
        tabla.setColumnCount(len(columnas))
        tabla.setHorizontalHeaderLabels(columnas)
        tabla.verticalHeader().setVisible(False)
        tabla.setAlternatingRowColors(True)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        try:
            tabla.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.Stretch
            )
        except Exception:
            pass

    @staticmethod
    def set_row_color(tabla, row: int, color: str) -> None:
        """Aplica color de texto a toda una fila de la tabla."""
        from PySide6.QtGui import QBrush, QColor
        brush = QBrush(QColor(color))
        for col in range(tabla.columnCount()):
            item = tabla.item(row, col)
            if item:
                item.setForeground(brush)

    @staticmethod
    def set_row_bold(tabla, row: int, bold: bool = True) -> None:
        """Aplica negrita a toda una fila de la tabla."""
        for col in range(tabla.columnCount()):
            item = tabla.item(row, col)
            if item:
                font = item.font()
                font.setBold(bold)
                item.setFont(font)

    def cargar_datos(self) -> None:
        """Sobrescribir en subclases para cargar datos de la pantalla."""
        raise NotImplementedError
