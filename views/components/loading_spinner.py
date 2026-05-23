from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QPen

class LoadingSpinner(QWidget):
    def __init__(self, size=40, color="#004aad", parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._color = QColor(color)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(16)

    def _rotate(self):
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.translate(self.width()/2, self.height()/2)
        p.rotate(self._angle)
        pen = QPen(self._color, 3, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        r = self.width()/2 - 4
        p.drawArc(QRectF(-r, -r, r*2, r*2), 0*16, 270*16)
        p.end()

    def stop(self): self._timer.stop(); self.hide()
    def start(self): self._timer.start(16); self.show()
