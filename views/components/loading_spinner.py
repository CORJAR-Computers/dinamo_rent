"""Loading spinner animation and overlay for deferred data loading."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QPen


class LoadingSpinner(QWidget):
    """Animated circular arc spinner — 16ms refresh rate."""

    def __init__(self, size=40, color="#2563eb", parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._color = QColor(color)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.setInterval(16)

    def _rotate(self):
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(self.width() / 2, self.height() / 2)
        p.rotate(self._angle)
        pen = QPen(self._color, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        r = self.width() / 2 - 4
        p.drawArc(QRectF(-r, -r, r * 2, r * 2), 0 * 16, 270 * 16)
        p.end()

    def stop(self):
        self._timer.stop()
        self.hide()

    def start(self):
        self._timer.start()
        self.show()


class LoadingOverlay(QWidget):
    """Semi-transparent overlay with centered spinner for deferred loads.

    Covers the entire parent widget, blocks mouse interaction, and
    displays a spinning indicator while data is loading.
    """

    _OVERLAY_COLOR = QColor(255, 255, 255, 210)

    def __init__(self, parent=None, message="Cargando...",
                 spinner_size=42, spinner_color="#2563eb"):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        self.setStyleSheet("background: transparent;")

        # ── Layout: centered spinner + message ──────────────────────────
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(14)

        self.spinner = LoadingSpinner(size=spinner_size, color=spinner_color,
                                      parent=self)
        layout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignCenter)

        self.lbl_msg = QLabel(message, self)
        self.lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_msg.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 10.5pt;
                font-weight: 600;
                background: transparent;
                padding-top: 2px;
            }
        """)
        layout.addWidget(self.lbl_msg, alignment=Qt.AlignmentFlag.AlignCenter)

        self.hide()

    def showEvent(self, event):
        """Ensure overlay covers parent and spinner is running."""
        super().showEvent(event)
        self.raise_()
        self._resize_to_parent()
        self.spinner.start()

    def hideEvent(self, event):
        """Stop spinner when hiding."""
        super().hideEvent(event)
        self.spinner.stop()

    def resizeEvent(self, event):
        """Re-cover parent when resized."""
        super().resizeEvent(event)
        self._resize_to_parent()

    def _resize_to_parent(self):
        p = self.parent()
        if p:
            self.setGeometry(0, 0, p.width(), p.height())

    def paintEvent(self, event):
        """Draw semi-transparent background."""
        p = QPainter(self)
        p.fillRect(self.rect(), self._OVERLAY_COLOR)
        p.end()

    def set_message(self, text: str):
        """Update the loading message text."""
        self.lbl_msg.setText(text)
