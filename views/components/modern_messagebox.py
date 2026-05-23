from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QPainter, QColor

class ModernMessageBox(QDialog):
    TYPES = {
        'info':     {'color': '#3b82f6', 'bg': 'rgba(59,130,246,0.10)'},
        'success':  {'color': '#22c55e', 'bg': 'rgba(34,197,94,0.10)'},
        'warning':  {'color': '#f59e0b', 'bg': 'rgba(245,158,11,0.10)'},
        'error':    {'color': '#ef4444', 'bg': 'rgba(239,68,68,0.10)'},
        'question': {'color': '#8b5cf6', 'bg': 'rgba(139,92,246,0.10)'},
    }

    def __init__(self, parent=None, title="", message="", msg_type="info",
                 buttons=None, detailed_text=None):
        super().__init__(parent)
        self.msg_type = msg_type
        self.config = self.TYPES.get(msg_type, self.TYPES['info'])
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(440)
        self._result_code = QDialog.Rejected
        self._build_ui(title, message, buttons or [{'text': 'Aceptar', 'role': 'accept', 'class': 'primary'}], detailed_text)
        self._apply_styles()
        self._animate_open()

    def _build_ui(self, title, message, buttons, detailed_text):
        outer = QFrame(self)
        outer.setObjectName("msgOuter")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(outer)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Icono + título
        header = QHBoxLayout()
        header.setSpacing(14)
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(44, 44)
        self._draw_icon(icon_lbl)
        header.addWidget(icon_lbl)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("msgTitle")
        title_lbl.setWordWrap(True)
        header.addWidget(title_lbl, 1)
        layout.addLayout(header)

        # Mensaje
        msg_lbl = QLabel(message)
        msg_lbl.setObjectName("msgBody")
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        # Separador + botones
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setObjectName("msgSep")
        layout.addWidget(sep)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        for btn_cfg in buttons:
            btn = QPushButton(btn_cfg['text'])
            btn.setProperty("class", btn_cfg.get('class', 'secondary'))
            btn.setFixedHeight(38)
            btn.setMinimumWidth(100)
            role = btn_cfg.get('role')
            if role == 'accept':
                btn.clicked.connect(self._on_accept)
            elif role == 'reject':
                btn.clicked.connect(self._on_reject)
            else:
                # Custom role
                def make_handler(r):
                    def handler():
                        self._result_code = r
                        self._animate_close()
                    return handler
                btn.clicked.connect(make_handler(role))
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

    def _draw_icon(self, label):
        c = self.config['color']
        bg_hex = self.config['bg']
        pixmap = QPixmap(44, 44)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(bg_hex))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 40, 40)
        color = QColor(c)
        painter.setBrush(color)
        cx, cy = 22, 22
        if self.msg_type in ('info', 'question'):
            painter.drawEllipse(cx-4, cy-12, 8, 8)
            painter.drawRoundedRect(cx-2, cy-1, 4, 14, 2, 2)
        elif self.msg_type == 'success':
            from PySide6.QtGui import QPen, QPainterPath
            pen = QPen(color, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen); painter.setBrush(Qt.NoBrush)
            path = QPainterPath()
            path.moveTo(10, 23); path.lineTo(18, 31); path.lineTo(34, 15)
            painter.drawPath(path)
        elif self.msg_type == 'warning':
            from PySide6.QtGui import QPen
            pen = QPen(color, 3, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen); painter.setBrush(Qt.NoBrush)
            painter.drawLine(22, 12, 22, 24); painter.drawPoint(22, 30)
        elif self.msg_type == 'error':
            from PySide6.QtGui import QPen
            pen = QPen(color, 3, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen); painter.setBrush(Qt.NoBrush)
            painter.drawLine(14, 14, 30, 30); painter.drawLine(30, 14, 14, 30)
        painter.end()
        label.setPixmap(pixmap)

    def _on_accept(self):
        self._result_code = QDialog.Accepted
        self._animate_close()

    def _on_reject(self):
        self._result_code = QDialog.Rejected
        self._animate_close()

    def _apply_styles(self):
        c = self.config['color']
        self.setStyleSheet(f"""
            #msgOuter {{ background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; }}
            #msgTitle {{ font-size: 16px; font-weight: 700; color: #1e293b; }}
            #msgBody  {{ font-size: 13px; color: #64748b; line-height: 1.5; }}
            #msgSep   {{ background-color: #e2e8f0; }}
            QPushButton[class="primary"] {{
                background-color: {c}; color: #ffffff;
                border: none; border-radius: 8px; font-weight: 600;
            }}
            QPushButton[class="secondary"] {{
                background-color: transparent; color: #64748b;
                border: 1.5px solid #e2e8f0; border-radius: 8px; font-weight: 600;
            }}
            QPushButton[class="secondary"]:hover {{ background-color: rgba(0,0,0,0.05); }}
            QPushButton[class="danger"] {{
                background-color: #ef4444; color: #ffffff;
                border: none; border-radius: 8px; font-weight: 600;
            }}
        """)

    def _animate_open(self):
        self.setWindowOpacity(0)
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(200); anim.setStartValue(0); anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(); self._open_anim = anim

    def _animate_close(self):
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(150); anim.setStartValue(1); anim.setEndValue(0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(lambda: super(ModernMessageBox, self).done(self._result_code))
        anim.start(); self._close_anim = anim

    # API estática (igual a QMessageBox)
    @staticmethod
    def information(parent, title, message):
        d = ModernMessageBox(parent, title, message, 'info'); d.exec(); return d._result_code

    @staticmethod
    def success(parent, title, message):
        d = ModernMessageBox(parent, title, message, 'success'); d.exec(); return d._result_code

    @staticmethod
    def warning(parent, title, message):
        btns = [{'text':'Cancelar','role':'reject','class':'secondary'},
                {'text':'Continuar','role':'accept','class':'primary'}]
        d = ModernMessageBox(parent, title, message, 'warning', btns); d.exec(); return d._result_code

    @staticmethod
    def error(parent, title, message, detailed_text=None):
        btns = [{'text':'Cerrar','role':'reject','class':'secondary'},
                {'text':'Reintentar','role':'accept','class':'primary'}]
        d = ModernMessageBox(parent, title, message, 'error', btns, detailed_text)
        d.exec(); return d._result_code

    @staticmethod
    def question(parent, title, message):
        btns = [{'text':'No','role':'reject','class':'secondary'},
                {'text':'Sí','role':'accept','class':'primary'}]
        d = ModernMessageBox(parent, title, message, 'question', btns); d.exec(); return d._result_code
