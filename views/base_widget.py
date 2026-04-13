"""
base_widget.py — Clase base para todos los widgets de la aplicación

Centraliza el manejo de errores UI, mensajes estándar y
el patrón de carga de datos con logging.
"""
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Qt

from core.exceptions import DinamoBaseError, ValidacionError, NegocioError
from core.logger import get_logger


class BaseWidget(QWidget):
    """
    Widget base con manejo centralizado de errores y utilidades de UI.

    Subclases deben implementar:
        - cargar_datos(): carga/recarga la información de la pantalla
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._log = get_logger(self.__class__.__name__)

    # ─── Manejo de errores ────────────────────────────────────────────────────

    def mostrar_error(self, mensaje: str, titulo: str = "Error") -> None:
        """Muestra un diálogo de error estándar."""
        self._log.warning("Error mostrado al usuario: %s", mensaje)
        QMessageBox.critical(self, titulo, mensaje)

    def mostrar_exito(self, mensaje: str, titulo: str = "Éxito") -> None:
        QMessageBox.information(self, titulo, mensaje)

    def mostrar_advertencia(self, mensaje: str, titulo: str = "Atención") -> None:
        QMessageBox.warning(self, titulo, mensaje)

    def confirmar(self, mensaje: str, titulo: str = "Confirmar") -> bool:
        """Muestra un diálogo de confirmación Sí/No."""
        resp = QMessageBox.question(
            self, titulo, mensaje,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return resp == QMessageBox.StandardButton.Yes

    def ejecutar_seguro(self, func, *args, mensaje_exito: str = "", **kwargs):
        """
        Ejecuta una función manejando excepciones automáticamente.

        - DinamoBaseError → mensaje al usuario con el texto amigable
        - Exception genérica → log + mensaje genérico
        - Retorna el resultado o None si hubo error
        """
        try:
            resultado = func(*args, **kwargs)
            if mensaje_exito:
                self.mostrar_exito(mensaje_exito)
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

    # ─── Utilidades de tabla ──────────────────────────────────────────────────

    @staticmethod
    def ajustar_tabla(tabla, columnas: list[str]) -> None:
        """Configura columnas y comportamiento estándar de una tabla."""
        from PySide6.QtWidgets import QHeaderView, QAbstractItemView, QTableWidget
        tabla.setColumnCount(len(columnas))
        tabla.setHorizontalHeaderLabels(columnas)
        tabla.verticalHeader().setVisible(False)
        tabla.setAlternatingRowColors(True)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        try:
            tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        except Exception:
            pass

    def cargar_datos(self) -> None:
        """Sobrescribir en cada subclase para cargar datos de la pantalla."""
        raise NotImplementedError
