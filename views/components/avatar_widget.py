from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt


class AvatarWidget(QLabel):
    def __init__(self, initials="", size=40, color=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        bg = color or "#004aad"
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg}; color: #ffffff;
                border-radius: {size // 2}px;
                font-weight: 700; font-size: {size // 3}px;
            }}
        """)
        self.setText(initials.upper()[:2])
