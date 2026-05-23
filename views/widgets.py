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


def make_legend_label(text: str, style_func) -> QLabel:
    """Crea un QLabel de leyenda y le aplica la funcion de estilo.

    Uso:
        from views.styles import legend_available
        lbl = make_legend_label("Disponible", legend_available)
    """
    lbl = QLabel(f"  {text}  ")
    if style_func:
        style_func(lbl)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl
