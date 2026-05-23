from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt

class IconButton(QPushButton):
    def __init__(self, icon_str, tooltip="", size=36, parent=None):
        super().__init__(icon_str, parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setProperty("class", "icon-btn")
        self.setStyleSheet("""
            QPushButton[class="icon-btn"] {
                background-color: transparent; border: none;
                border-radius: 8px; font-size: 16px; color: #94a3b8;
            }
            QPushButton[class="icon-btn"]:hover {
                background-color: rgba(0,0,0,0.08); color: #1e293b;
            }
        """)
