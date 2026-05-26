"""
views/widgets.py — Componentes compartidos entre vistas.

Centraliza widgets personalizados que se usan en múltiples archivos
para evitar duplicación (DRY).
"""

from PySide6.QtWidgets import QLineEdit, QLabel
from PySide6.QtCore import Qt


class UpperLineEdit(QLineEdit):
    """QLineEdit que convierte automáticamente el texto a mayúsculas."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textChanged.connect(self._to_upper)

    def _to_upper(self, text: str):
        if text and not text.isupper():
            self.blockSignals(True)
            self.setText(text.upper())
            self.blockSignals(False)


def make_legend_label(text: str, css_class: str = "badge") -> QLabel:
    """Crea un QLabel de leyenda con clase QSS."""
    lbl = QLabel(f"  {text}  ")
    lbl.setProperty("class", css_class)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl
