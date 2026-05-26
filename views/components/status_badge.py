from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt


class StatusBadge(QLabel):
    """status: 'success' | 'warning' | 'danger' | 'info'"""

    def __init__(self, text, status="success", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", f"badge-{status}")
        self.setFixedHeight(28)
        self.setAlignment(Qt.AlignCenter)
