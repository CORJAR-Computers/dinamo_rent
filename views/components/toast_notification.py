"""
ToastNotification — Sistema de notificaciones tipo toast con apilamiento y animaciones.

Niveles: "success", "warning", "error", "info"
Posiciones: "top-right" (defecto), "top-left", "bottom-right", "bottom-left"
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint


_THEMES = {
    "success": {"accent": "#15803d", "bg": "#dcfce7", "icon": "\u2713"},
    "warning": {"accent": "#c2410c", "bg": "#ffedd5", "icon": "\u26a0"},
    "error": {"accent": "#b91c1c", "bg": "#fee2e2", "icon": "\u2717"},
    "info": {"accent": "#1e40af", "bg": "#dbeafe", "icon": "\u2139"},
}


class ToastManager:
    """Gestiona el apilamiento y reposicionamiento de toasts activos."""

    _PADDING = 16
    _SPACING = 8
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._active = []
        return cls._instance

    def register(self, toast: "ToastNotification") -> None:
        """Registra un toast activo y reposiciona la pila."""
        self._active.append(toast)
        toast.destroyed.connect(lambda: self._unregister(toast))
        self._reposition_all()

    def _unregister(self, toast: "ToastNotification") -> None:
        if toast in self._active:
            self._active.remove(toast)
        self._reposition_all()

    def _reposition_all(self) -> None:
        """Reposiciona todos los toasts activos con animación."""
        visible = [t for t in self._active if t.isVisible()]
        if not visible:
            return

        parent = visible[0].parent()
        if not parent:
            return

        parent_width = parent.width()
        parent_height = parent.height()
        position = visible[0]._position

        x, y = self._get_origin(parent_width, parent_height, position)
        y_delta = -1 if position in ("bottom-left", "bottom-right") else 1

        for toast in visible:
            target = QPoint(x, y)
            if toast.pos() != target:
                anim = QPropertyAnimation(toast, b"pos")
                anim.setDuration(180)
                anim.setStartValue(toast.pos())
                anim.setEndValue(target)
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                anim.start()
            y += (toast.height() + self._SPACING) * y_delta

    def _get_origin(self, pw: int, ph: int, position: str):
        p = self._PADDING
        if position == "top-right":
            return pw - p, p
        elif position == "top-left":
            return p, p
        elif position == "bottom-right":
            return pw - p, ph - p
        elif position == "bottom-left":
            return p, ph - p
        return pw - p, p  # default top-right


class ToastNotification(QFrame):
    """Notificación tipo toast con apilamiento, animación y auto-dismiss.

    Args:
        parent: Widget padre (normalmente la ventana principal).
        message: Texto del mensaje.
        level: "success" | "warning" | "error" | "info"
        duration: Milisegundos antes de auto-dismiss (0 = persistente).
        position: "top-right" | "top-left" | "bottom-right" | "bottom-left"
    """

    def __init__(
        self,
        parent,
        message: str,
        level: str = "info",
        duration: int = 3500,
        position: str = "top-right",
    ):
        super().__init__(parent)
        self._position = position
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._animate_dismiss)

        theme = _THEMES.get(level, _THEMES["info"])

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {theme["bg"]};
                border-left: 4px solid {theme["accent"]};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        icon_lbl = QLabel(theme["icon"])
        icon_lbl.setStyleSheet(
            f"QLabel {{ color: {theme['accent']}; font-size: 15px; font-weight: bold; border: none; }}"
        )

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet("QLabel { color: #37474f; font-size: 13px; border: none; }")
        msg_lbl.setWordWrap(True)
        msg_lbl.setMaximumWidth(360)

        close_btn = QPushButton("\u00d7")
        close_btn.setFixedSize(22, 22)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {theme["accent"]};
                border: none; font-size: 15px; font-weight: bold;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: rgba(0,0,0,0.08);
            }}
        """)
        close_btn.clicked.connect(self._animate_dismiss)

        layout.addWidget(icon_lbl)
        layout.addWidget(msg_lbl, stretch=1)
        layout.addWidget(close_btn)

        self.adjustSize()
        w = min(self.sizeHint().width() + 32, parent.width() - 40)
        self.setFixedWidth(max(w, 260))
        self.setFixedHeight(max(self.sizeHint().height(), 44))

        # Registrar en el manager, mostrar y animar
        ToastManager().register(self)
        self.show()
        self._animate_show()

        if duration > 0:
            self._dismiss_timer.start(duration)

    @classmethod
    def show_info(cls, parent, message: str, duration: int = 3500, position: str = "top-right"):
        return cls(parent, message, level="info", duration=duration, position=position)

    @classmethod
    def show_success(cls, parent, message: str, duration: int = 3500, position: str = "top-right"):
        return cls(parent, message, level="success", duration=duration, position=position)

    @classmethod
    def show_warning(cls, parent, message: str, duration: int = 3500, position: str = "top-right"):
        return cls(parent, message, level="warning", duration=duration, position=position)

    @classmethod
    def show_error(cls, parent, message: str, duration: int = 3500, position: str = "top-right"):
        return cls(parent, message, level="error", duration=duration, position=position)

    def _animate_show(self):
        """Aparición con fade-in."""
        self.setWindowOpacity(0)
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._show_anim = anim

    def _animate_dismiss(self):
        """Desaparición con fade-out, luego cierra."""
        self._dismiss_timer.stop()
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(150)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self._cleanup)
        anim.start()
        self._dismiss_anim = anim

    def _cleanup(self):
        self.close()
        self.deleteLater()  # → dispara ToastManager._unregister via destroyed signal
