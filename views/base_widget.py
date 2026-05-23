"""Clase base para widgets: errores UI, toast, validación y utilidades de tabla."""

from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QLabel, QHeaderView,
    QAbstractItemView,
)
from views.components import ModernMessageBox, ToastNotification
from views.components.form_validators import (
    FormValidator, FieldValidator, ValidationRule, make_error_label,
)

from core.exceptions import DinamoBaseError, ValidacionError, NegocioError
from core.logger import get_logger


class BaseWidget(QWidget):
    """Widget base con manejo de errores, toast, validación y diálogos estándar."""

    def __init__(self, parent=None, session_id: str = None):
        super().__init__(parent)
        self._log = get_logger(self.__class__.__name__)
        self._session_id = session_id
        self._form_validator: Optional[FormValidator] = None

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
        """Muestra diálogo de éxito estándar."""
        ModernMessageBox.success(self, titulo, mensaje)

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
