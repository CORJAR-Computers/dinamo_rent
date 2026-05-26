from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from views.components import CardWidget, StatusBadge


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
        h.setProperty("class", "hint")
        row.addWidget(h)
    return row


def create_page_header(title: str, subtitle="", actions=None):
    """Retorna QHBoxLayout con título + subtítulo a la izquierda, botones a la derecha."""
    header = QHBoxLayout()
    left = QVBoxLayout()
    left.setSpacing(4)
    t = QLabel(title)
    t.setProperty("class", "title")
    left.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setProperty("class", "subtitle")
        left.addWidget(s)
    header.addLayout(left)
    header.addStretch()
    if actions:
        for btn in actions:
            header.addWidget(btn)
    return header


def create_stats_grid(stats: list[dict]) -> QHBoxLayout:
    """
    stats = [{'label': 'Total', 'value': '1,248', 'badge': 'Activo', 'status': 'success'}, ...]
    """
    row = QHBoxLayout()
    row.setSpacing(16)
    for s in stats:
        card = CardWidget(title=s["value"], subtitle=s["label"], padding=20)
        if s.get("badge"):
            card.add_widget(StatusBadge(s["badge"], s.get("status", "info")))
        row.addWidget(card)
    return row


def build_dialog_header(icon_str: str, title: str, subtitle: str) -> QWidget:
    """Crea el banner gradiente para diálogos (78px height, icono 48px).

    Sigue el patrón establecido por AutoFormDialog y ClienteFormDialog.
    """
    from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
    from PySide6.QtCore import Qt

    header = QWidget()
    header.setObjectName("dlg_header")
    header.setFixedHeight(78)

    lay = QHBoxLayout(header)
    lay.setContentsMargins(22, 0, 22, 0)
    lay.setSpacing(16)

    avatar = QLabel(icon_str)
    avatar.setFixedSize(48, 48)
    avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
    avatar.setProperty("class", "dialog-header-icon")
    lay.addWidget(avatar)

    txt_col = QVBoxLayout()
    txt_col.setSpacing(3)
    txt_col.addStretch()

    lbl_t = QLabel(title)
    lbl_t.setProperty("class", "banner-title")
    lbl_s = QLabel(subtitle)
    lbl_s.setProperty("class", "banner-subtitle")
    txt_col.addWidget(lbl_t)
    txt_col.addWidget(lbl_s)
    txt_col.addStretch()

    lay.addLayout(txt_col)
    lay.addStretch()

    return header


def create_banner(icon_str: str, title_str: str, subtitle_str: str, refresh_callback=None):
    from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
    from PySide6.QtCore import Qt

    banner = QWidget()
    banner.setFixedHeight(64)
    banner.setProperty("class", "banner")
    b_lay = QHBoxLayout(banner)
    b_lay.setContentsMargins(22, 0, 22, 0)
    b_lay.setSpacing(14)

    ico = QLabel(icon_str)
    ico.setFixedSize(40, 40)
    ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
    ico.setProperty("class", "banner-icon")
    b_lay.addWidget(ico)

    t_col = QVBoxLayout()
    t_col.setSpacing(1)
    t_col.addStretch()
    lbl_t = QLabel(title_str)
    lbl_t.setProperty("class", "banner-title")
    lbl_s = QLabel(subtitle_str)
    lbl_s.setProperty("class", "banner-subtitle")
    t_col.addWidget(lbl_t)
    t_col.addWidget(lbl_s)
    t_col.addStretch()
    b_lay.addLayout(t_col)
    b_lay.addStretch()

    if refresh_callback:
        btn_ref = QPushButton("↻  Actualizar")
        btn_ref.setProperty("class", "banner-btn")
        btn_ref.clicked.connect(refresh_callback)
        b_lay.addWidget(btn_ref)

    return banner
