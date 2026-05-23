"""Estilos centralizados para widgets (Tema: Dinamo Pro)"""
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from core.config import (
    COLOR_PRIMARIO, COLOR_PRIMARIO_HOVER, COLOR_PRIMARIO_FOCUS,
    COLOR_EXITO, COLOR_SUCCESS_HOVER,
    COLOR_PELIGRO, COLOR_DANGER_HOVER,
    COLOR_ALERTA,
    COLOR_CAL_DISPONIBLE, COLOR_CAL_RENTADO, COLOR_CAL_RESERVADO,
    COLOR_ESTADO_VIP,
    COLOR_SURFACE, COLOR_BORDER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_FONDO
)

_WHITE = "#ffffff"
_DARK = COLOR_TEXT_PRIMARY
_MUTED = COLOR_TEXT_SECONDARY

# --- Base Button Styles ---
_BASE_BTN = (
    "QPushButton {{"
    "color: {fg};"
    "background-color: {bg};"
    "font-weight: 600;"
    "padding: {pad};"
    "border: none;"
    "border-radius: 8px;"
    "font-size: 11pt;"
    "}}"
)

_BASE_BTN_HOVER = (
    _BASE_BTN +
    "QPushButton:hover{{ background-color: {bg_hover}; }}"
    "QPushButton:pressed{{ background-color: {bg_pressed}; }}"
    "QPushButton:focus{{ border: 2px solid {focus_outline}; }}"
)

_BTN_NORMAL_PAD = "10px 24px"
_BTN_LARGE_PAD = "12px 32px"


def apply_shadow(widget, blur_radius=15, y_offset=2):
    """Aplica un efecto de sombra sutil a un widget."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur_radius)
    shadow.setColor(QColor(0, 0, 0, 30))
    shadow.setOffset(0, y_offset)
    widget.setGraphicsEffect(shadow)


def btn_primary(btn, large=False):
    """Botón primario (Guardar, Aceptar, Buscar)."""
    pad = _BTN_LARGE_PAD if large else _BTN_NORMAL_PAD
    btn.setStyleSheet(
        _BASE_BTN_HOVER.format(
            fg=_WHITE,
            pad=pad,
            bg=COLOR_PRIMARIO,
            bg_hover=COLOR_PRIMARIO_HOVER,
            bg_pressed=COLOR_PRIMARIO,
            focus_outline=COLOR_PRIMARIO_FOCUS,
        )
    )

def btn_default(btn, large=False):
    """Botón por defecto (Cancelar, Volver)."""
    pad = _BTN_LARGE_PAD if large else _BTN_NORMAL_PAD
    btn.setStyleSheet(
        _BASE_BTN_HOVER.format(
            fg=COLOR_TEXT_PRIMARY,
            pad=pad,
            bg="#f1f5f9",
            bg_hover="#e2e8f0",
            bg_pressed="#cbd5e1",
            focus_outline=COLOR_PRIMARIO_FOCUS,
        )
    )

def btn_success(btn, large=False):
    """Botón de acción exitosa (Nuevo, Crear, Registrar)."""
    pad = _BTN_LARGE_PAD if large else _BTN_NORMAL_PAD
    btn.setStyleSheet(
        _BASE_BTN_HOVER.format(
            fg=_WHITE,
            pad=pad,
            bg=COLOR_EXITO,
            bg_hover=COLOR_SUCCESS_HOVER,
            bg_pressed=COLOR_EXITO,
            focus_outline=COLOR_PRIMARIO_FOCUS,
        )
    )

def btn_danger(btn):
    """Botón de peligro (Eliminar, Cancelar)."""
    btn.setStyleSheet(
        _BASE_BTN_HOVER.format(
            fg=_WHITE,
            pad=_BTN_NORMAL_PAD,
            bg=COLOR_PELIGRO,
            bg_hover=COLOR_DANGER_HOVER,
            bg_pressed=COLOR_PELIGRO,
            focus_outline=COLOR_PRIMARIO_FOCUS,
        )
    )

def btn_warning(btn):
    """Botón de advertencia."""
    btn.setStyleSheet(
        _BASE_BTN_HOVER.format(
            fg=_WHITE,
            pad=_BTN_NORMAL_PAD,
            bg=COLOR_ALERTA,
            bg_hover="#fb923c", # orange-400
            bg_pressed=COLOR_ALERTA,
            focus_outline=COLOR_PRIMARIO_FOCUS,
        )
    )

def btn_secondary(btn):
    """Botón secundario (Actualizar, Recargar)."""
    btn.setStyleSheet(
        _BASE_BTN_HOVER.format(
            fg=COLOR_TEXT_PRIMARY,
            pad=_BTN_NORMAL_PAD,
            bg="#e2e8f0", # slate-200
            bg_hover="#cbd5e1", # slate-300
            bg_pressed="#e2e8f0",
            focus_outline=COLOR_PRIMARIO_FOCUS,
        )
    )

def btn_icon(btn):
    """Botón con borde sutil para acciones en tablas y barras de herramientas."""
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: #f8fafc;
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
            padding: 6px 12px;
            color: {COLOR_TEXT_PRIMARY};
            font-weight: 600;
            font-size: 9pt;
        }}
        QPushButton:hover {{
            background-color: #eff6ff;
            border-color: {COLOR_PRIMARIO};
            color: {COLOR_PRIMARIO};
        }}
        QPushButton:pressed {{
            background-color: #dbeafe;
        }}
        QPushButton:focus {{
            border: 2px solid {COLOR_PRIMARIO_FOCUS};
        }}
    """)

# --- Labels ---
def lbl_title(lbl):
    """Título principal de vista (20pt bold)."""
    lbl.setStyleSheet(f"QLabel {{ font-size:22pt; font-weight:700; color:{_DARK}; }}")

def lbl_subtitle(lbl):
    """Subtítulo (14pt semibold azul)."""
    lbl.setStyleSheet(f"QLabel {{ font-size:15pt; font-weight:600; color:{COLOR_PRIMARIO}; }}")

def lbl_section(lbl):
    """Título de sección (12pt bold)."""
    lbl.setStyleSheet(f"QLabel {{ font-size:12pt; font-weight:600; color:{_DARK}; padding:8px 0; }}")

def lbl_total_renta(lbl):
    """Estilo para el total a pagar en NuevaRentaDialog."""
    lbl.setStyleSheet("QLabel { font-size: 24px; color: #004aad; font-weight: bold; }")

def lbl_extra_info(lbl):
    """Estilo para información extra como horas o días adicionales."""
    lbl.setStyleSheet(f"QLabel {{ color: {COLOR_PELIGRO}; font-weight: bold; }}")

def lbl_new_total_extension(lbl):
    """Estilo para el nuevo total en el diálogo de extensión de renta."""
    lbl.setStyleSheet(f"QLabel {{ color: {COLOR_EXITO}; font-size: 16px; font-weight: bold; }}")

# --- Frames & Cards ---
def frame_card(frame):
    """Frame tipo tarjeta con sombra."""
    frame.setStyleSheet(f"""
        QFrame {{
            background-color: {COLOR_SURFACE};
            border: none;
            border-radius: 12px;
        }}
    """)
    apply_shadow(frame)

def frame_summary(frame):
    """Frame resumen financiero (azul claro)."""
    frame.setStyleSheet("""
        QFrame {
            background-color: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 12px;
            padding: 16px;
        }
    """)

# --- Badges ---
def badge_success(badge):
    badge.setStyleSheet(
        "QLabel {background-color:#dcfce7;color:#166534;padding:4px 12px;"
        "border-radius:14px;font-weight:600;font-size:10pt;border:1px solid #bbf7d0;}"
    )

def badge_warning(badge):
    badge.setStyleSheet(
        "QLabel {background-color:#ffedd5;color:#9a3412;padding:4px 12px;"
        "border-radius:14px;font-weight:600;font-size:10pt;border:1px solid #fdba74;}"
    )

def badge_danger(badge):
    badge.setStyleSheet(
        "QLabel {background-color:#fee2e2;color:#991b1b;padding:4px 12px;"
        "border-radius:14px;font-weight:600;font-size:10pt;border:1px solid #fca5a5;}"
    )

def badge_info(badge):
    badge.setStyleSheet(
        "QLabel {background-color:#dbeafe;color:#1e40af;padding:4px 12px;"
        "border-radius:14px;font-weight:600;font-size:10pt;border:1px solid #93c5fd;}"
    )

# --- Inputs & Validation ---
def edit_search(edit):
    edit.setStyleSheet(f"""
        QLineEdit {{
            padding: 8px 16px 8px 16px;
            border: 1px solid {COLOR_BORDER};
            border-radius: 18px;
            background-color: #ffffff;
            font-size: 11pt;
            color: #1e293b;
        }}
        QLineEdit:focus {{
            border-color: {COLOR_PRIMARIO};
            background-color: #eff6ff;
        }}
    """)

def input_error(edit):
    edit.setStyleSheet(f"""
        QLineEdit {{
            border: 1px solid {COLOR_PELIGRO};
            border-radius: 8px;
            background-color: #fee2e2;
            padding: 8px 12px;
            color: #991b1b;
        }}
    """)

def input_success(edit):
    edit.setStyleSheet(f"""
        QLineEdit {{
            border: 1px solid {COLOR_EXITO};
            border-radius: 8px;
            background-color: #f0fdf4;
            padding: 8px 12px;
            color: #166534;
        }}
    """)

def edit_readonly_info(edit):
    edit.setStyleSheet(
        "QLineEdit {"
        "background-color:#eff6ff;color:#1e40af;"
        "font-weight:600;padding:8px 12px;border:1px solid #dbeafe;"
        "border-radius:8px;"
        "}"
    )

# --- Other UI Elements ---
def divider(line):
    line.setStyleSheet(f"QFrame {{ background-color: {COLOR_BORDER}; max-height: 1px; }}")

def legend_available(lbl):
    lbl.setStyleSheet(f"QLabel {{ background-color:{COLOR_CAL_DISPONIBLE}; border-radius:4px; padding:4px 8px; font-weight:600; color:#1e40af; }}")

def legend_rented(lbl):
    lbl.setStyleSheet(f"QLabel {{ background-color:{COLOR_CAL_RENTADO}; border-radius:4px; padding:4px 8px; font-weight:600; color:#15803d; }}")

def legend_reserved(lbl):
    lbl.setStyleSheet(f"QLabel {{ background-color:{COLOR_CAL_RESERVADO}; border-radius:4px; padding:4px 8px; font-weight:600; color:#c2410c; }}")

def status_active(lbl):
    lbl.setStyleSheet(f"QLabel {{ color:{COLOR_EXITO}; font-weight:600; font-size:11pt; }}")

def status_inactive(lbl):
    lbl.setStyleSheet(f"QLabel {{ color:{COLOR_PELIGRO}; font-weight:600; font-size:11pt; }}")

def status_warning(lbl):
    lbl.setStyleSheet(f"QLabel {{ color:{COLOR_ALERTA}; font-weight:600; font-size:11pt; }}")

def status_vip(lbl):
    lbl.setStyleSheet(f"QLabel {{ color:{COLOR_ESTADO_VIP}; font-weight:600; font-size:11pt; }}")

def table_widget(table):
    """Estilo para tablas con mejor contraste y aspecto moderno."""
    table.setStyleSheet(f"""
        QTableWidget {{
            background-color: {COLOR_SURFACE};
            border: 1px solid {COLOR_BORDER};
            border-radius: 12px;
            gridline-color: #f1f5f9;
        }}
        QTableWidget::item {{
            padding: 12px 10px;
            border-bottom: 1px solid #f1f5f9;
        }}
        QTableWidget::item:selected {{
            background-color: #dbeafe;
            color: #1e40af;
        }}
        QHeaderView::section {{
            background-color: #f8fafc;
            color: {COLOR_TEXT_SECONDARY};
            padding: 12px 10px;
            border: none;
            border-bottom: 1px solid {COLOR_BORDER};
            font-weight: 600;
            font-size: 10pt;
            text-transform: uppercase;
        }}
    """)
    apply_shadow(table)


# --- Dialog Inputs ---
def input_field(edit):
    """Estilo profesional para QLineEdit en diálogos."""
    edit.setStyleSheet("""
        QLineEdit {
            padding: 6px 10px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            background-color: #ffffff;
            font-size: 11pt;
            color: #1e293b;
        }
        QLineEdit:focus {
            border-color: #3b82f6;
            background-color: #eff6ff;
        }
        QLineEdit:disabled {
            background-color: #f1f5f9;
            color: #94a3b8;
            border-color: #e2e8f0;
        }
    """)


def input_combo(combo):
    """Estilo profesional para QComboBox en diálogos."""
    combo.setStyleSheet("""
        QComboBox {
            padding: 6px 10px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            background-color: #ffffff;
            font-size: 11pt;
            color: #1e293b;
        }
        QComboBox:hover {
            border-color: #94a3b8;
        }
        QComboBox:focus {
            border-color: #3b82f6;
            background-color: #eff6ff;
        }
        QComboBox::drop-down {
            border: none;
            width: 30px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #64748b;
            margin-right: 10px;
        }
        QComboBox QAbstractItemView {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            background-color: #ffffff;
            selection-background-color: #dbeafe;
            selection-color: #1e40af;
            padding: 4px;
        }
    """)


def input_spinbox(spin):
    """Estilo profesional para QSpinBox/QDoubleSpinBox en diálogos."""
    spin.setStyleSheet("""
        QSpinBox, QDoubleSpinBox {
            padding: 6px 10px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            background-color: #ffffff;
            font-size: 11pt;
            color: #1e293b;
        }
        QSpinBox:focus, QDoubleSpinBox:focus {
            border-color: #3b82f6;
            background-color: #eff6ff;
        }
        QSpinBox::up-button, QDoubleSpinBox::up-button {
            border: none;
            width: 20px;
            background-color: transparent;
        }
        QSpinBox::down-button, QDoubleSpinBox::down-button {
            border: none;
            width: 20px;
            background-color: transparent;
        }
    """)


def input_date(date_edit):
    """Estilo profesional para QDateEdit en diálogos."""
    date_edit.setStyleSheet("""
        QDateEdit {
            padding: 6px 10px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            background-color: #ffffff;
            font-size: 11pt;
            color: #1e293b;
        }
        QDateEdit:hover {
            border-color: #94a3b8;
        }
        QDateEdit:focus {
            border-color: #3b82f6;
            background-color: #eff6ff;
        }
        QDateEdit::drop-down {
            border: none;
            width: 30px;
        }
        QDateEdit::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #64748b;
            margin-right: 10px;
        }
        QCalendarWidget QWidget {
            background-color: #ffffff;
        }
        QCalendarWidget QAbstractItemView {
            selection-background-color: #3b82f6;
            selection-color: #ffffff;
        }
    """)

def input_time(time_edit):
    """Estilo profesional para QTimeEdit en diálogos."""
    time_edit.setStyleSheet("""
        QTimeEdit {
            padding: 6px 10px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            background-color: #ffffff;
            font-size: 11pt;
            color: #1e293b;
        }
        QTimeEdit:hover {
            border-color: #94a3b8;
        }
        QTimeEdit:focus {
            border-color: #3b82f6;
            background-color: #eff6ff;
        }
        QTimeEdit::up-button, QTimeEdit::down-button {
            background-color: transparent;
            border: none;
        }
        QTimeEdit::section {
            padding: 0 4px;
        }
    """)


def input_textedit(textedit):
    """Estilo profesional para QPlainTextEdit/QTextEdit en diálogos."""
    textedit.setStyleSheet("""
        QPlainTextEdit, QTextEdit {
            padding: 6px 10px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            background-color: #ffffff;
            font-size: 11pt;
            color: #1e293b;
        }
        QPlainTextEdit:focus, QTextEdit:focus {
            border-color: #3b82f6;
            background-color: #eff6ff;
        }
    """)


def dialog_container(frame):
    """Estilo profesional para frames contenedores de diálogos."""
    frame.setStyleSheet("""
        QFrame {
            background-color: #ffffff;
            border-radius: 12px;
        }
    """)
    apply_shadow(frame, blur_radius=20, y_offset=4)


def dialog_title(lbl):
    """Título principal de diálogo."""
    lbl.setStyleSheet(f"QLabel {{ font-size:20pt; font-weight:700; color:{COLOR_TEXT_PRIMARY}; }}")


def dialog_description(lbl):
    """Descripción de texto para diálogos."""
    lbl.setStyleSheet(f"QLabel {{ font-size:11pt; color:{COLOR_TEXT_SECONDARY}; padding-bottom:10px; }}")


def dialog_background(widget):
    """Aplica fondo y texto base para diálogos de la aplicación."""
    widget.setStyleSheet(
        "QDialog { background-color: #f8fafc; }"
        "QLabel { color: #334155; font-size: 10pt; }"
    )


def view_background(widget):
    """Aplica fondo y texto base para widgets de página."""
    widget.setStyleSheet(
        "QWidget { background-color: #f8fafc; }"
        "QLabel { color: #334155; font-size: 10pt; }"
    )

def banner_gradient_background(widget):
    """Estilo para el banner superior con gradiente."""
    widget.setStyleSheet("""
        QWidget {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #1a3558, stop:1 #2563eb);
        }
    """)

def banner_icon_style(lbl):
    """Estilo para el icono en el banner."""
    lbl.setStyleSheet("""
        QLabel {
            background: rgba(255,255,255,0.15);
            border-radius: 20px;
            font-size: 18px;
        }
    """)

def banner_title_style(lbl):
    """Estilo para el título principal en el banner."""
    lbl.setStyleSheet("QLabel { color:#fff; font-size:14pt; font-weight:700; background:transparent; }")

def banner_subtitle_style(lbl):
    """Estilo para el subtítulo en el banner."""
    lbl.setStyleSheet("QLabel { color:rgba(255,255,255,0.72); font-size:9pt; background:transparent; }")

def btn_refresh_style(btn):
    """Estilo para el botón de actualizar en el banner."""
    btn.setStyleSheet("""
        QPushButton {
            background: rgba(255,255,255,0.15);
            color: #ffffff;
            border: 1px solid rgba(255,255,255,0.35);
            border-radius: 7px;
            padding: 7px 18px;
            font-size: 9.5pt;
            font-weight: 600;
        }
        QPushButton:hover { background: rgba(255,255,255,0.25); }
        QPushButton:pressed { background: rgba(255,255,255,0.10); }
    """)

def dialog_header_style(widget):
    """Estilo para el encabezado de los diálogos."""
    widget.setStyleSheet(f"""
        QWidget#dlg_header {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLOR_PRIMARIO},
                stop:1 {COLOR_PRIMARIO_FOCUS}
            );
        }}
    """)

def dialog_body_style(widget):
    """Estilo para el cuerpo de los diálogos."""
    widget.setStyleSheet(f"""
        QWidget#dlg_body {{
            background-color: {COLOR_FONDO};
        }}
    """)

def tab_widget_pane_style(tab_widget):
    """Estilo para el panel del QTabWidget."""
    tab_widget.setStyleSheet(f"""
        QTabWidget::pane {{
            border: 1px solid {COLOR_BORDER};
            border-radius: 10px;
            background: {COLOR_SURFACE};
            padding: 10px;
        }}
    """)

def tab_bar_style(tab_bar):
    """Estilo para las pestañas del QTabBar."""
    tab_bar.setStyleSheet(f"""
        QTabBar::tab {{
            padding: 11px 26px;
            font-size: 10pt;
            font-weight: 600;
            color: {_MUTED};
            background: transparent;
            border: none;
            border-bottom: 3px solid transparent;
            margin-right: 6px;
        }}
        QTabBar::tab:selected {{
            color: {COLOR_PRIMARIO_FOCUS};
            border-bottom: 3px solid {COLOR_PRIMARIO_FOCUS};
        }}
        QTabBar::tab:hover:!selected {{
            color: {COLOR_TEXT_PRIMARY};
            border-bottom: 3px solid #94a3b8;
        }}
    """)

def dialog_label_style(lbl):
    """Estilo general para QLabel dentro de diálogos."""
    lbl.setStyleSheet(f"""
        QLabel {{
            color: {COLOR_TEXT_PRIMARY};
            font-size: 10pt;
            background: transparent;
        }}
    """)


def group_box(widget):
    """
    Aplica estilo moderno a un QGroupBox.
    """
    widget.setStyleSheet("""
        QGroupBox {
            font-weight: 700;
            font-size: 10pt;
            color: #1e293b;
            border: 1.5px solid #cbd5e1;
            border-radius: 8px;
            margin-top: 20px;
            padding-top: 8px;
        }
        QGroupBox::title {
            /* Posiciona el texto ENCIMA del borde, no dentro del padding */
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            /* top negativo lo sube justo sobre la línea del borde */
            top: -1px;
            padding: 2px 8px;
            background-color: #ffffff;
            border-radius: 4px;
            color: #1a3558;
        }
    """)
