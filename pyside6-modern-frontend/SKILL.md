---
name: pyside6-modern-frontend
description: >
  Especialista en crear y refactorizar interfaces gráficas de escritorio modernas con PySide6 (prioridad),
  PyQt6 o PyQt5. Usar este skill SIEMPRE que el usuario mencione: PySide6, PyQt, Qt, GUI de escritorio,
  interfaz gráfica en Python, ventana de aplicación, widgets, QMainWindow, QDialog, QWidget, dashboard
  de escritorio, app de escritorio Python, refactorizar vista Qt, modernizar UI Python, o cualquier tarea
  de diseño visual para aplicaciones de escritorio con Python. También activar cuando el usuario suba un
  archivo .py que contenga imports de PySide6/PyQt y pida mejoras visuales. El skill cubre: creación desde
  cero, refactorización de vistas existentes, sistema de temas por tipo de negocio, componentes custom
  reutilizables (ModernMessageBox, CardWidget, etc.), y patrones de layout profesionales.
compatibility:
  python: ">=3.9"
  dependencies:
    - PySide6>=6.5.0  # Prioridad
    - PyQt6>=6.5.0    # Alternativa
    - PyQt5>=5.15.0   # Alternativa legacy
---

# Skill: Frontend Moderno PySide6 / PyQt

## Flujo de Trabajo

Antes de generar código, seguir este flujo:

1. **Identificar tarea**: ¿Crear desde cero o refactorizar existente?
2. **Inferir o preguntar** el tipo de negocio → seleccionar tema de color
3. **Si es refactorización**: leer todo el archivo antes de modificar nada
4. **Generar código** usando los patrones de este skill
5. **Verificar** el Checklist de Entrega (Sección 11) antes de responder

---

## 1. Reglas Fundamentales

### 1.1 Nunca usar widgets "desnudos"
Todo widget visible DEBE tener estilos QSS. Jamás dejes QPushButton, QLabel, QLineEdit, QComboBox,
QTableWidget, QListWidget, QTreeWidget, etc. con apariencia nativa.

### 1.2 QSS como sistema de diseño
- Estructurar el QSS por secciones: `/* === BOTONES === */`, `/* === INPUTS === */`
- `border-radius` consistente: botones `8px`, cards `12px`, dialogs `16px`, inputs `8px`
- Sombras: `box-shadow` para profundidad visual
- Nunca usar `QPalette` para colores → usar QSS exclusivamente
- Nunca usar `setGeometry` → usar layouts siempre

### 1.3 Espaciado consistente
Múltiplos de 4px: `4, 8, 12, 16, 20, 24, 32, 48px`. Sin valores arbitrarios como `7px` o `15px`.

### 1.4 Tipografía jerárquica
| Clase QSS | Tamaño | Peso | Uso |
|-----------|--------|------|-----|
| `title`   | 22px   | 700  | Título de página |
| `subtitle`| 14px   | 400  | Descripción de página |
| `section` | 11px   | 700 + uppercase | Label de campo |
| body (default) | 13px | 400 | Texto general |
| caption   | 12px   | 600  | Badges, tooltips |

---

## 2. Sistema de Temas

Inferir el tema según el tipo de negocio descrito. Si no es claro, preguntar o usar SaaS/Tech.

> **Nota**: Leer la sección de temas en `references/themes.py` si está disponible. Si no, usar los
> diccionarios de abajo directamente.

### Temas disponibles

```python
THEME_SAAS = {
    'primary': '#6366f1', 'primary_hover': '#4f46e5',
    'primary_light': 'rgba(99,102,241,0.12)',
    'bg': '#0f172a', 'bg_card': '#1e293b', 'bg_input': '#334155',
    'fg': '#f1f5f9', 'fg_muted': '#94a3b8', 'border': '#334155',
    'accent': '#22d3ee', 'success': '#34d399', 'warning': '#fbbf24',
    'danger': '#f87171', 'danger_hover': '#ef4444',
}

THEME_CLINICA = {
    'primary': '#0ea5e9', 'primary_hover': '#0284c7',
    'primary_light': 'rgba(14,165,233,0.12)',
    'bg': '#f0f9ff', 'bg_card': '#ffffff', 'bg_input': '#f8fafc',
    'fg': '#0c4a6e', 'fg_muted': '#64748b', 'border': '#e2e8f0',
    'accent': '#06b6d4', 'success': '#10b981', 'warning': '#f59e0b',
    'danger': '#ef4444', 'danger_hover': '#dc2626',
}

THEME_FINTECH = {
    'primary': '#059669', 'primary_hover': '#047857',
    'primary_light': 'rgba(5,150,105,0.12)',
    'bg': '#022c22', 'bg_card': '#064e3b', 'bg_input': '#065f46',
    'fg': '#ecfdf5', 'fg_muted': '#6ee7b7', 'border': '#065f46',
    'accent': '#34d399', 'success': '#34d399', 'warning': '#fbbf24',
    'danger': '#fb7185', 'danger_hover': '#e11d48',
}

THEME_RETAIL = {
    'primary': '#e11d48', 'primary_hover': '#be123c',
    'primary_light': 'rgba(225,29,72,0.10)',
    'bg': '#ffffff', 'bg_card': '#fef2f2', 'bg_input': '#fff1f2',
    'fg': '#1c1917', 'fg_muted': '#78716c', 'border': '#fecdd3',
    'accent': '#f97316', 'success': '#22c55e', 'warning': '#eab308',
    'danger': '#ef4444', 'danger_hover': '#dc2626',
}

THEME_EDUCATIVO = {
    'primary': '#8b5cf6', 'primary_hover': '#7c3aed',
    'primary_light': 'rgba(139,92,246,0.12)',
    'bg': '#faf5ff', 'bg_card': '#ffffff', 'bg_input': '#f5f3ff',
    'fg': '#3b0764', 'fg_muted': '#7c7c8a', 'border': '#e9d5ff',
    'accent': '#a78bfa', 'success': '#34d399', 'warning': '#fbbf24',
    'danger': '#fb7185', 'danger_hover': '#e11d48',
}

THEME_INDUSTRIAL = {
    'primary': '#d97706', 'primary_hover': '#b45309',
    'primary_light': 'rgba(217,119,6,0.12)',
    'bg': '#1c1917', 'bg_card': '#292524', 'bg_input': '#44403c',
    'fg': '#fef3c7', 'fg_muted': '#a8a29e', 'border': '#44403c',
    'accent': '#fbbf24', 'success': '#4ade80', 'warning': '#facc15',
    'danger': '#f87171', 'danger_hover': '#ef4444',
}
```

---

## 3. Sistema de Estilos (`build_stylesheet`)

Siempre generar el stylesheet con esta función. Agrega secciones según los widgets presentes en la vista.

```python
def build_stylesheet(theme: dict) -> str:
    base = """
    /* === BASE === */
    QWidget {
        background-color: {{bg}};
        color: {{fg}};
        font-family: 'Segoe UI', 'Inter', 'SF Pro Display', sans-serif;
        font-size: 13px;
    }
    /* === BOTONES === */
    QPushButton {
        background-color: {{primary}};
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        font-size: 13px;
        min-height: 18px;
    }
    QPushButton:hover { background-color: {{primary_hover}}; }
    QPushButton:pressed { padding-top: 11px; padding-bottom: 9px; }
    QPushButton:disabled { background-color: {{bg_input}}; color: {{fg_muted}}; }

    QPushButton[class="secondary"] {
        background-color: transparent;
        color: {{primary}};
        border: 1.5px solid {{primary}};
    }
    QPushButton[class="secondary"]:hover { background-color: {{primary_light}}; }

    QPushButton[class="ghost"] {
        background-color: transparent;
        color: {{fg_muted}};
        border: none;
    }
    QPushButton[class="ghost"]:hover { background-color: {{primary_light}}; color: {{primary}}; }

    QPushButton[class="danger"] { background-color: {{danger}}; }
    QPushButton[class="danger"]:hover { background-color: {{danger_hover}}; }

    /* === INPUTS === */
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit {
        background-color: {{bg_input}};
        color: {{fg}};
        border: 1.5px solid {{border}};
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 13px;
        selection-background-color: {{primary}};
        selection-color: #ffffff;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
    QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
        border-color: {{primary}};
    }
    QLineEdit::placeholder, QTextEdit::placeholder { color: {{fg_muted}}; }

    /* === COMBOBOX === */
    QComboBox {
        background-color: {{bg_input}};
        color: {{fg}};
        border: 1.5px solid {{border}};
        border-radius: 8px;
        padding: 10px 14px;
        padding-right: 36px;
        min-height: 18px;
    }
    QComboBox:focus { border-color: {{primary}}; }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: right center;
        width: 32px;
        border: none;
        background: transparent;
    }
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {{fg_muted}};
    }
    QComboBox QAbstractItemView {
        background-color: {{bg_card}};
        color: {{fg}};
        border: 1px solid {{border}};
        border-radius: 8px;
        selection-background-color: {{primary_light}};
        selection-color: {{primary}};
        padding: 4px;
        outline: none;
    }

    /* === TABLA === */
    QTableWidget, QTableView {
        background-color: {{bg_card}};
        alternate-background-color: {{bg_input}};
        color: {{fg}};
        border: 1px solid {{border}};
        border-radius: 12px;
        gridline-color: {{border}};
        font-size: 13px;
    }
    QTableWidget::item, QTableView::item {
        padding: 10px 14px;
        border-bottom: 1px solid {{border}};
    }
    QTableWidget::item:selected, QTableView::item:selected {
        background-color: {{primary_light}};
        color: {{primary}};
    }
    QHeaderView::section {
        background-color: {{bg_input}};
        color: {{fg_muted}};
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 12px 14px;
        border: none;
        border-bottom: 2px solid {{border}};
    }
    QHeaderView::section:first { border-top-left-radius: 12px; }
    QHeaderView::section:last { border-top-right-radius: 12px; }

    /* === LISTWIDGET / TREEWIDGET === */
    QListWidget, QTreeWidget {
        background-color: {{bg_card}};
        color: {{fg}};
        border: 1px solid {{border}};
        border-radius: 12px;
        padding: 4px;
        outline: none;
    }
    QListWidget::item, QTreeWidget::item {
        padding: 10px 14px;
        border-radius: 8px;
    }
    QListWidget::item:selected, QTreeWidget::item:selected {
        background-color: {{primary_light}};
        color: {{primary}};
    }
    QListWidget::item:hover, QTreeWidget::item:hover {
        background-color: {{bg_input}};
    }

    /* === SCROLLBAR === */
    QScrollBar:vertical {
        background: transparent;
        width: 8px;
        margin: 0;
    }
    QScrollBar::handle:vertical {
        background: {{border}};
        border-radius: 4px;
        min-height: 40px;
    }
    QScrollBar::handle:vertical:hover { background: {{fg_muted}}; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar:horizontal {
        background: transparent;
        height: 8px;
        margin: 0;
    }
    QScrollBar::handle:horizontal {
        background: {{border}};
        border-radius: 4px;
        min-width: 40px;
    }
    QScrollBar::handle:horizontal:hover { background: {{fg_muted}}; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

    /* === CARDS === */
    QFrame[class="card"] {
        background-color: {{bg_card}};
        border: 1px solid {{border}};
        border-radius: 12px;
        padding: 20px;
    }

    /* === LABELS === */
    QLabel[class="title"] { font-size: 22px; font-weight: 700; color: {{fg}}; }
    QLabel[class="subtitle"] { font-size: 14px; color: {{fg_muted}}; font-weight: 400; }
    QLabel[class="section"] {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: {{fg_muted}};
    }
    QLabel[class="badge-success"] {
        background-color: rgba(52,211,153,0.15);
        color: {{success}};
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }
    QLabel[class="badge-warning"] {
        background-color: rgba(251,191,36,0.15);
        color: {{warning}};
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }
    QLabel[class="badge-danger"] {
        background-color: rgba(248,113,113,0.15);
        color: {{danger}};
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }
    QLabel[class="badge-info"] {
        background-color: rgba(99,102,241,0.15);
        color: {{primary}};
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }

    /* === CHECKBOX === */
    QCheckBox { spacing: 8px; color: {{fg}}; font-size: 13px; }
    QCheckBox::indicator {
        width: 18px; height: 18px;
        border-radius: 4px;
        border: 1.5px solid {{border}};
        background-color: {{bg_input}};
    }
    QCheckBox::indicator:checked { background-color: {{primary}}; border-color: {{primary}}; }

    /* === RADIO BUTTON === */
    QRadioButton { spacing: 8px; color: {{fg}}; font-size: 13px; }
    QRadioButton::indicator {
        width: 18px; height: 18px;
        border-radius: 9px;
        border: 1.5px solid {{border}};
        background-color: {{bg_input}};
    }
    QRadioButton::indicator:checked { background-color: {{primary}}; border-color: {{primary}}; }

    /* === SLIDER === */
    QSlider::groove:horizontal {
        height: 6px;
        background: {{bg_input}};
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: {{primary}};
        border: none;
        width: 18px; height: 18px;
        border-radius: 9px;
        margin: -6px 0;
    }
    QSlider::sub-page:horizontal { background: {{primary}}; border-radius: 3px; }

    /* === TAB WIDGET === */
    QTabWidget::pane {
        border: 1px solid {{border}};
        border-radius: 12px;
        background-color: {{bg_card}};
        padding: 8px;
    }
    QTabBar::tab {
        background: transparent;
        color: {{fg_muted}};
        padding: 10px 20px;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        font-size: 13px;
        margin-right: 2px;
    }
    QTabBar::tab:selected { background-color: {{primary_light}}; color: {{primary}}; font-weight: 600; }
    QTabBar::tab:hover:!selected { background-color: {{bg_input}}; color: {{fg}}; }

    /* === PROGRESS BAR === */
    QProgressBar {
        background-color: {{bg_input}};
        border: none;
        border-radius: 999px;
        min-height: 8px;
        text-align: center;
        color: transparent;
    }
    QProgressBar::chunk { background-color: {{primary}}; border-radius: 999px; }

    /* === TOOLTIP === */
    QToolTip {
        background-color: {{fg}};
        color: {{bg}};
        border: none;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 500;
    }

    /* === SPLITTER === */
    QSplitter::handle { background-color: {{border}}; width: 1px; }

    /* === MENU === */
    QMenu {
        background-color: {{bg_card}};
        border: 1px solid {{border}};
        border-radius: 10px;
        padding: 6px;
    }
    QMenu::item {
        padding: 8px 16px;
        border-radius: 6px;
        color: {{fg}};
        font-size: 13px;
    }
    QMenu::item:selected { background-color: {{primary_light}}; color: {{primary}}; }
    QMenu::separator { height: 1px; background: {{border}}; margin: 4px 8px; }

    /* === STATUS BAR === */
    QStatusBar {
        background-color: {{bg_card}};
        color: {{fg_muted}};
        border-top: 1px solid {{border}};
        font-size: 12px;
        padding: 4px 12px;
    }
    """

    replacements = {
        '{{bg}}': theme.get('bg', '#0f172a'),
        '{{bg_card}}': theme.get('bg_card', '#1e293b'),
        '{{bg_input}}': theme.get('bg_input', '#334155'),
        '{{fg}}': theme.get('fg', '#f1f5f9'),
        '{{fg_muted}}': theme.get('fg_muted', '#94a3b8'),
        '{{primary}}': theme.get('primary', '#6366f1'),
        '{{primary_hover}}': theme.get('primary_hover', '#4f46e5'),
        '{{primary_light}}': theme.get('primary_light', 'rgba(99,102,241,0.12)'),
        '{{border}}': theme.get('border', '#334155'),
        '{{accent}}': theme.get('accent', '#22d3ee'),
        '{{success}}': theme.get('success', '#34d399'),
        '{{warning}}': theme.get('warning', '#fbbf24'),
        '{{danger}}': theme.get('danger', '#f87171'),
        '{{danger_hover}}': theme.get('danger_hover', '#ef4444'),
    }
    for key, val in replacements.items():
        base = base.replace(key, val)
    return base
```

---

## 4. Componentes Custom Obligatorios

### 4.1 ModernMessageBox — reemplaza QMessageBox
> ❌ Nunca usar `QMessageBox` en ninguna forma.

```python
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
            if btn_cfg.get('role') == 'accept':
                btn.clicked.connect(self._on_accept)
            else:
                btn.clicked.connect(self._on_reject)
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
            #msgOuter {{ background-color: #1e293b; border: 1px solid #334155; border-radius: 16px; }}
            #msgTitle {{ font-size: 16px; font-weight: 700; color: #f1f5f9; }}
            #msgBody  {{ font-size: 13px; color: #94a3b8; line-height: 1.5; }}
            #msgSep   {{ background-color: #334155; }}
            QPushButton[class="primary"] {{
                background-color: {c}; color: #ffffff;
                border: none; border-radius: 8px; font-weight: 600;
            }}
            QPushButton[class="secondary"] {{
                background-color: transparent; color: #94a3b8;
                border: 1.5px solid #334155; border-radius: 8px; font-weight: 600;
            }}
            QPushButton[class="secondary"]:hover {{ background-color: rgba(255,255,255,0.05); }}
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
```

### 4.2 CardWidget
```python
class CardWidget(QFrame):
    def __init__(self, parent=None, title="", subtitle="", padding=20):
        super().__init__(parent)
        self.setProperty("class", "card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(padding, padding, padding, padding)
        self._layout.setSpacing(12)
        if title:
            t = QLabel(title); t.setProperty("class", "title"); self._layout.addWidget(t)
        if subtitle:
            s = QLabel(subtitle); s.setProperty("class", "subtitle"); self._layout.addWidget(s)
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(10)
        self._layout.addLayout(self.content_layout)
        self._layout.addStretch()

    def add_widget(self, w): self.content_layout.addWidget(w)
    def add_layout(self, l): self.content_layout.addLayout(l)
```

### 4.3 IconButton
```python
class IconButton(QPushButton):
    def __init__(self, icon_str, tooltip="", size=36, parent=None):
        super().__init__(icon_str, parent)
        self.setFixedSize(size, size)
        from PySide6.QtCore import Qt
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setProperty("class", "icon-btn")
        self.setStyleSheet("""
            QPushButton[class="icon-btn"] {
                background-color: transparent; border: none;
                border-radius: 8px; font-size: 16px; color: #94a3b8;
            }
            QPushButton[class="icon-btn"]:hover {
                background-color: rgba(255,255,255,0.08); color: #f1f5f9;
            }
        """)
```

### 4.4 StatusBadge
```python
class StatusBadge(QLabel):
    """status: 'success' | 'warning' | 'danger' | 'info'"""
    def __init__(self, text, status="success", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", f"badge-{status}")
        self.setFixedHeight(28)
        from PySide6.QtCore import Qt
        self.setAlignment(Qt.AlignCenter)
```

### 4.5 AvatarWidget
```python
class AvatarWidget(QLabel):
    def __init__(self, initials="", size=40, color=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        from PySide6.QtCore import Qt
        self.setAlignment(Qt.AlignCenter)
        bg = color or "#6366f1"
        self.setStyleSheet(f"""
            background-color: {bg}; color: #ffffff;
            border-radius: {size//2}px;
            font-weight: 700; font-size: {size//3}px;
        """)
        self.setText(initials.upper()[:2])
```

### 4.6 LoadingSpinner
```python
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QPen

class LoadingSpinner(QWidget):
    def __init__(self, size=40, color="#6366f1", parent=None):
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
```

---

## 5. Patrones de Layout

### 5.1 Sidebar + Content
```python
class MainLayout(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setObjectName("sidebar")

        self.content = QFrame()
        self.content.setObjectName("contentArea")

        layout.addWidget(self.sidebar)
        layout.addWidget(self.content, 1)
        # QSS: #sidebar { border-right: 1px solid {{border}}; }
        # QSS: #contentArea { padding: 24px; }
```

### 5.2 Form Row Moderno
```python
def create_form_row(label_text: str, widget, required=False, hint=""):
    """Retorna QVBoxLayout con label + widget + hint opcional."""
    row = QVBoxLayout()
    row.setSpacing(6)
    text = f"{label_text} *" if required else label_text
    lbl = QLabel(text)
    lbl.setProperty("class", "section")
    row.addWidget(lbl)
    row.addWidget(widget)
    if hint:
        h = QLabel(hint)
        h.setStyleSheet("font-size: 11px; color: #64748b;")
        row.addWidget(h)
    return row
```

### 5.3 Page Header
```python
def create_page_header(title: str, subtitle="", actions=None):
    """Retorna QHBoxLayout con título + subtítulo a la izquierda, botones a la derecha."""
    header = QHBoxLayout()
    left = QVBoxLayout()
    left.setSpacing(4)
    t = QLabel(title); t.setProperty("class", "title"); left.addWidget(t)
    if subtitle:
        s = QLabel(subtitle); s.setProperty("class", "subtitle"); left.addWidget(s)
    header.addLayout(left)
    header.addStretch()
    if actions:
        for btn in actions:
            header.addWidget(btn)
    return header
```

### 5.4 Stats Grid (tarjetas de métricas)
```python
def create_stats_grid(stats: list[dict]) -> QHBoxLayout:
    """
    stats = [{'label': 'Total', 'value': '1,248', 'badge': 'Activo', 'status': 'success'}, ...]
    """
    row = QHBoxLayout()
    row.setSpacing(16)
    for s in stats:
        card = CardWidget(title=s['value'], subtitle=s['label'], padding=20)
        if s.get('badge'):
            card.add_widget(StatusBadge(s['badge'], s.get('status', 'info')))
        row.addWidget(card)
    return row
```

---

## 6. Reglas de Refactorización

1. **Leer primero**: Leer todo el archivo antes de tocar nada.
2. **Preservar lógica**: NO modificar signals, slots ni lógica de negocio.
3. **Reemplazar QMessageBox**: Buscar todos los `QMessageBox.` y reemplazar por `ModernMessageBox.`.
4. **Aplicar tema**: Inferir tipo de negocio → `build_stylesheet(theme)` en el widget raíz.
5. **Componentizar**: Extraer patrones repetidos a CardWidget, StatusBadge, etc.
6. **Scrollbar**: Toda QScrollArea debe tener scrollbar estilizado.
7. **Verificar estados**: Botones → `:hover :pressed :disabled`. Inputs → `:focus`.
8. **Tipografía**: Asignar `setProperty("class", "title/subtitle/section")` a cada QLabel según jerarquía.
9. **Verificar QMenu y QStatusBar** si la vista los tiene → estilizarlos.

---

## 7. Anti-Patrones Prohibidos

| ❌ Prohibido | ✅ Correcto |
|---|---|
| `QMessageBox.information(...)` | `ModernMessageBox.information(...)` |
| `setGeometry(x, y, w, h)` | Layouts con márgenes y stretch |
| Colores hardcodeados `#333` en widgets | Variables del tema via `build_stylesheet` |
| `QPalette` para colores | QSS exclusivamente |
| Scrollbars sin estilo | Incluir bloque `QScrollBar` en stylesheet |
| Tablas sin header estilizado | Incluir `QHeaderView::section` |
| Fuentes < 12px en contenido | Mínimo 12px; usar jerarquía tipográfica |
| `border-radius` mezclados sin criterio | 8px botones/inputs, 12px cards, 16px dialogs |
| `setFixedSize` en diálogos sin frameless | Frameless + custom header si se necesita tamaño fijo |
| Widgets sin ningún QSS | Todo widget visible debe tener estilo |

---

## 8. Estructura de Archivos Sugerida

```
views/
├── components/
│   ├── __init__.py           # Exporta: ModernMessageBox, CardWidget, IconButton, StatusBadge, AvatarWidget, LoadingSpinner
│   ├── modern_messagebox.py
│   ├── card_widget.py
│   ├── icon_button.py
│   ├── status_badge.py
│   ├── avatar_widget.py
│   └── loading_spinner.py
├── themes/
│   ├── __init__.py           # Exporta: build_stylesheet, THEME_SAAS, THEME_CLINICA, etc.
│   ├── build_stylesheet.py
│   └── themes.py
├── layouts/
│   ├── __init__.py
│   ├── form_helpers.py       # create_form_row, create_page_header
│   └── sidebar_layout.py
└── main_window.py
```

---

## 9. Ejemplo de Vista Completa

```python
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from views.components import ModernMessageBox, CardWidget, StatusBadge
from views.themes import THEME_SAAS, build_stylesheet
from views.layouts.form_helpers import create_page_header, create_stats_grid


class ClienteView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(build_stylesheet(THEME_SAAS))

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(24)

        root.addLayout(create_page_header(
            "Clientes",
            "Gestión de clientes registrados",
            actions=[QPushButton("Nuevo cliente")]
        ))

        root.addLayout(create_stats_grid([
            {'label': 'Total clientes', 'value': '1,248', 'badge': 'Activo', 'status': 'success'},
            {'label': 'Nuevos hoy',     'value': '12',    'badge': '+8%',    'status': 'success'},
            {'label': 'Inactivos',      'value': '43',    'badge': 'Alerta', 'status': 'warning'},
        ]))

        search = QLineEdit()
        search.setPlaceholderText("🔍  Buscar cliente...")
        search.setFixedWidth(300)
        root.addWidget(search)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Nombre", "Email", "Teléfono", "Estado", "Acciones"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_del = QPushButton("Eliminar selección")
        btn_del.setProperty("class", "danger")
        btn_del.clicked.connect(self._on_delete)
        btn_row.addWidget(btn_del)
        root.addLayout(btn_row)

    def _on_delete(self):
        result = ModernMessageBox.question(
            self, "Confirmar eliminación",
            "¿Deseas eliminar los clientes seleccionados? Esta acción no se puede deshacer."
        )
        if result == QDialog.Accepted:
            # lógica de eliminación aquí
            ModernMessageBox.success(self, "Listo", "Clientes eliminados correctamente.")
```

---

## 10. Checklist de Entrega

Antes de responder, verificar que la vista cumpla TODOS estos puntos:

- [ ] Todos los widgets visibles tienen estilos QSS
- [ ] Tema de negocio seleccionado y aplicado vía `build_stylesheet()`
- [ ] Cero instancias de `QMessageBox` (usar `ModernMessageBox`)
- [ ] Botones con `border-radius: 8px` y estados `:hover`, `:pressed`, `:disabled`
- [ ] Inputs con `border-radius: 8px` y efecto `:focus`
- [ ] Tablas con header estilizado (`QHeaderView::section`)
- [ ] Scrollbars personalizados (bloque `QScrollBar` en stylesheet)
- [ ] Tipografía jerárquica (`title`/`subtitle`/`section`/body)
- [ ] Sin colores hardcodeados fuera del sistema de temas
- [ ] Solo layouts, cero `setGeometry`
- [ ] Espaciado en múltiplos de 4px
- [ ] QMenu estilizado (si la vista lo usa)
- [ ] QStatusBar estilizado (si la vista lo usa)
- [ ] LoadingSpinner disponible para operaciones asíncronas (si aplica)
