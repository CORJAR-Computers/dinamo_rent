from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel
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
        h.setStyleSheet("QLabel { font-size: 11px; color: #64748b; }")
        row.addWidget(h)
    return row

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

def create_banner(icon_str: str, title_str: str, subtitle_str: str, refresh_callback=None):
    from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
    from PySide6.QtCore import Qt
    from views.styles import (
        banner_gradient_background, banner_icon_style, banner_title_style,
        banner_subtitle_style, btn_refresh_style
    )
    banner = QWidget()
    banner.setFixedHeight(64)
    banner_gradient_background(banner)
    b_lay = QHBoxLayout(banner)
    b_lay.setContentsMargins(22, 0, 22, 0)
    b_lay.setSpacing(14)

    ico = QLabel(icon_str)
    ico.setFixedSize(40, 40)
    ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
    banner_icon_style(ico)
    b_lay.addWidget(ico)

    t_col = QVBoxLayout()
    t_col.setSpacing(1)
    t_col.addStretch()
    lbl_t = QLabel(title_str)
    banner_title_style(lbl_t)
    lbl_s = QLabel(subtitle_str)
    banner_subtitle_style(lbl_s)
    t_col.addWidget(lbl_t)
    t_col.addWidget(lbl_s)
    t_col.addStretch()
    b_lay.addLayout(t_col)
    b_lay.addStretch()

    if refresh_callback:
        btn_ref = QPushButton("↻  Actualizar")
        btn_refresh_style(btn_ref)
        btn_ref.clicked.connect(refresh_callback)
        b_lay.addWidget(btn_ref)

    return banner
