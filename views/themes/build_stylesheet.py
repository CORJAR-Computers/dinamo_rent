def build_stylesheet(theme: dict) -> str:
    base = r"""
/* ═══════════════════════════════════════════════════════════════════════════
   DINAMO RENT QSS — generated from theme tokens
   ═══════════════════════════════════════════════════════════════════════════ */

/* ──────────────── BASE ──────────────── */
QWidget {
    background-color: {{bg}};
    color: {{fg}};
    font-family: 'Segoe UI Variable', 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

/* ──────────────── SELECTION ──────────────── */
QWidget:focus {
    outline: none;
}
QWidget:selected {
    background-color: {{primary_light}};
    color: {{primary}};
}

/* ──────────────── PUSH BUTTON ──────────────── */
/* Default = neutral / ghost-like */
QPushButton {
    background-color: {{bg_input}};
    color: {{fg}};
    border: 1px solid {{border}};
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 13px;
    min-height: 18px;
}
QPushButton:hover {
    background-color: {{primary_light}};
    color: {{primary}};
    border-color: {{primary}};
}
QPushButton:pressed { padding-top: 11px; padding-bottom: 9px; }
QPushButton:disabled { background-color: {{bg_input}}; color: {{fg_muted}}; border-color: {{border}}; }

/* Primary */
QPushButton[class="primary"] {
    background-color: {{primary}};
    color: {{fg_on_primary}};
    border: none;
}
QPushButton[class="primary"]:hover { background-color: {{primary_hover}}; }

/* Secondary — outlined */
QPushButton[class="secondary"] {
    background-color: transparent;
    color: {{primary}};
    border: 1.5px solid {{primary}};
}
QPushButton[class="secondary"]:hover { background-color: {{primary_light}}; }

/* Ghost — subtle bordered */
QPushButton[class="ghost"] {
    background-color: {{bg_input}};
    color: {{fg}};
    border: 1px solid {{border}};
}
QPushButton[class="ghost"]:hover {
    background-color: {{primary_light}};
    color: {{primary}};
    border: 1px solid {{primary}};
}

/* Success */
QPushButton[class="success"] {
    background-color: {{success}};
    color: #ffffff;
}
QPushButton[class="success"]:hover {
    background-color: {{success}};
    opacity: 0.9;
}

/* Danger */
QPushButton[class="danger"] { background-color: {{danger}}; color: #ffffff; }
QPushButton[class="danger"]:hover { background-color: {{danger_hover}}; }

/* Warning */
QPushButton[class="warning"] {
    background-color: {{warning}};
    color: #ffffff;
}
QPushButton[class="warning"]:hover {
    background-color: {{warning}};
}

/* Icon button — small, for tables/toolbars */
QPushButton[class="icon"] {
    background-color: transparent;
    color: {{fg_muted}};
    border: 1px solid {{border}};
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton[class="icon"]:hover {
    background-color: {{primary_light}};
    color: {{primary}};
    border-color: {{primary}};
}

/* ──────────────── INPUTS ──────────────── */
QLineEdit, QTextEdit, QPlainTextEdit,
QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit {
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
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {
    border-color: {{border_focus}};
    background-color: {{bg_input}};
}
QLineEdit:disabled, QTextEdit:disabled {
    background-color: {{table_alt}};
    color: {{fg_muted}};
}

/* Search input */
QLineEdit[class="search"] {
    border-radius: 18px;
    padding: 8px 18px;
    background-color: {{bg_input}};
}
QLineEdit[class="search"]:focus {
    border-color: {{border_focus}};
}

/* Validation states (set dynamically by form_validators) */
QLineEdit[validation_state="error"],
QComboBox[validation_state="error"] {
    border-color: {{danger}};
    background-color: {{danger_light}};
    color: {{danger}};
}
QLineEdit[validation_state="success"],
QComboBox[validation_state="success"] {
    border-color: {{success}};
    background-color: {{success_light}};
    color: {{success}};
}

/* ──────────────── COMBOBOX ──────────────── */
QComboBox {
    background-color: {{bg_input}};
    color: {{fg}};
    border: 1.5px solid {{border}};
    border-radius: 8px;
    padding: 10px 14px;
    padding-right: 36px;
    min-height: 18px;
}
QComboBox:hover { border-color: {{fg_muted}}; }
QComboBox:focus { border-color: {{border_focus}}; }
QComboBox:disabled { background-color: {{table_alt}}; color: {{fg_muted}}; }
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
QComboBox QAbstractItemView::item {
    padding: 8px 12px;
    border-radius: 4px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: {{primary_light}};
}

/* ──────────────── TABLE ──────────────── */
QTableWidget, QTableView {
    background-color: {{bg_card}};
    alternate-background-color: {{table_alt}};
    color: {{fg}};
    border: 1px solid {{border}};
    border-radius: 12px;
    gridline-color: {{table_grid}};
    font-size: 13px;
}
QTableWidget::item, QTableView::item {
    padding: 10px 14px;
    border-bottom: 1px solid {{table_grid}};
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: {{primary_light}};
    color: {{primary}};
}
QTableWidget::item:hover, QTableView::item:hover {
    background-color: {{primary_light}};
}
QHeaderView::section {
    background-color: {{table_header_bg}};
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
QHeaderView::section:hover { color: {{fg}}; }

/* ──────────────── LIST / TREE ──────────────── */
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

/* ──────────────── SCROLLBAR ──────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: {{scrollbar_handle}};
    border-radius: 4px;
    min-height: 40px;
}
QScrollBar::handle:vertical:hover { background: {{scrollbar_hover}}; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: {{scrollbar_handle}};
    border-radius: 4px;
    min-width: 40px;
}
QScrollBar::handle:horizontal:hover { background: {{scrollbar_hover}}; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ──────────────── CALENDAR LEGENDS ──────────────── */
QLabel[class="legend-available"] {
    background-color: {{legend_available_bg}};
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: 600;
    font-size: 12px;
    color: {{fg}};
}
QLabel[class="legend-rented"] {
    background-color: {{legend_rented_bg}};
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: 600;
    font-size: 12px;
    color: {{fg}};
}
QLabel[class="legend-reserved"] {
    background-color: {{legend_reserved_bg}};
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: 600;
    font-size: 12px;
    color: {{fg}};
}

/* ──────────────── STATUS TEXT (without badge bg) ──────────────── */
QLabel[class="status-success"] {
    color: {{success}};
    font-weight: 600;
    font-size: 14px;
}
QLabel[class="status-danger"] {
    color: {{danger}};
    font-weight: 600;
    font-size: 14px;
}
QLabel[class="status-warning"] {
    color: {{warning}};
    font-weight: 600;
    font-size: 14px;
}
QLabel[class="status-vip"] {
    color: {{accent}};
    font-weight: 700;
    font-size: 14px;
}

/* ──────────────── READONLY / INFO INPUT ──────────────── */
QLineEdit[class="readonly-info"] {
    background-color: {{primary_light}};
    color: {{primary}};
    font-weight: 600;
    border: 1px solid {{border}};
}

/* ──────────────── CARDS / FRAMES ──────────────── */
QFrame[class="card"] {
    background-color: {{bg_card}};
    border: 1px solid {{border}};
    border-radius: 12px;
    padding: 20px;
}

QFrame[class="card-raised"] {
    background-color: {{bg_card}};
    border: 1px solid {{border}};
    border-radius: 14px;
    padding: 24px;
}

QFrame[class="login-card"] {
    background-color: {{bg_card}};
    border: 1px solid {{border}};
    border-radius: 25px;
}

QFrame[class="form-card"] {
    background-color: {{bg_card}};
    border-top: 1px solid {{border}};
    border-right: 1px solid {{border}};
    border-bottom: 1px solid {{border}};
    border-left: 4px solid {{primary}};
    border-radius: 8px;
}

QFrame[class="divider"] {
    background-color: {{border}};
    max-height: 1px;
}

QFrame[class="summary-card"] {
    background-color: {{bg_card}};
    border: 1px solid {{border}};
    border-radius: 12px;
    padding: 16px;
}

QFrame[class="summary"] {
    background-color: {{primary_light}};
    border: 1px solid {{primary}};
    border-radius: 12px;
    padding: 16px;
}

QLabel[class="total-amount"] {
    font-size: 24px;
    font-weight: bold;
    color: {{primary}};
}

QLabel[class="extra-info"] {
    color: {{danger}};
    font-weight: bold;
}

QLabel[class="new-total"] {
    color: {{success}};
    font-size: 16px;
    font-weight: bold;
}

/* ──────────────── LABELS ──────────────── */
QLabel[class="title"] {
    font-size: 22px;
    font-weight: 700;
    color: {{fg}};
}
QLabel[class="subtitle"] {
    font-size: 14px;
    color: {{fg_muted}};
    font-weight: 400;
}
QLabel[class="section"] {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: {{fg_muted}};
}
QLabel[class="hint"] {
    font-size: 11px;
    color: {{fg_muted}};
    font-weight: 400;
}

/* ──────────────── BADGES ──────────────── */
QLabel[class="badge"] {
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}
QLabel[class="badge-success"] {
    background-color: {{success_light}};
    color: {{success}};
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}
QLabel[class="badge-warning"] {
    background-color: {{warning_light}};
    color: {{warning}};
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}
QLabel[class="badge-danger"] {
    background-color: {{danger_light}};
    color: {{danger}};
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}
QLabel[class="badge-info"] {
    background-color: {{info_light}};
    color: {{info}};
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}

/* Card icon */
QLabel[class="card-icon"] {
    background-color: {{primary_light}};
    border-radius: 4px;
    font-size: 13px;
    color: {{primary}};
}

/* ──────────────── CHECKBOX ──────────────── */
QCheckBox { spacing: 8px; color: {{fg}}; font-size: 13px; }
QCheckBox::indicator {
    width: 18px; height: 18px;
    border-radius: 4px;
    border: 1.5px solid {{border}};
    background-color: {{bg_input}};
}
QCheckBox::indicator:checked {
    background-color: {{primary}};
    border-color: {{primary}};
}
QCheckBox::indicator:hover {
    border-color: {{primary}};
}

/* ──────────────── RADIO ──────────────── */
QRadioButton { spacing: 8px; color: {{fg}}; font-size: 13px; }
QRadioButton::indicator {
    width: 18px; height: 18px;
    border-radius: 9px;
    border: 1.5px solid {{border}};
    background-color: {{bg_input}};
}
QRadioButton::indicator:checked {
    background-color: {{primary}};
    border-color: {{primary}};
}
QRadioButton::indicator:hover {
    border-color: {{primary}};
}

/* ──────────────── SLIDER ──────────────── */
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
QSlider::handle:horizontal:hover {
    background: {{primary_hover}};
}
QSlider::sub-page:horizontal {
    background: {{primary}};
    border-radius: 3px;
}

/* ──────────────── TAB WIDGET ──────────────── */
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
QTabBar::tab:selected {
    background-color: {{primary_light}};
    color: {{primary}};
    font-weight: 600;
}
QTabBar::tab:hover:!selected {
    background-color: {{bg_input}};
    color: {{fg}};
}

/* ──────────────── PROGRESS BAR ──────────────── */
QProgressBar {
    background-color: {{progress_bg}};
    border: none;
    border-radius: 999px;
    min-height: 8px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: {{progress_chunk}};
    border-radius: 999px;
}

/* ──────────────── TOOLTIP ──────────────── */
QToolTip {
    background-color: {{tooltip_bg}};
    color: {{tooltip_fg}};
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 500;
}

/* ──────────────── SPLITTER ──────────────── */
QSplitter::handle {
    background-color: {{border}};
    width: 1px;
}

/* ──────────────── MENU / CONTEXT ──────────────── */
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

/* ──────────────── STATUS BAR ──────────────── */
QStatusBar {
    background-color: {{bg_card}};
    color: {{fg_muted}};
    border-top: 1px solid {{border}};
    font-size: 12px;
    padding: 4px 12px;
}

/* ──────────────── GROUP BOX ──────────────── */
QGroupBox {
    font-weight: 600;
    font-size: 12px;
    color: {{fg}};
    border: 1.5px solid {{border}};
    border-radius: 8px;
    margin-top: 20px;
    padding-top: 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    top: -1px;
    padding: 2px 8px;
    background-color: {{bg_card}};
    border-radius: 4px;
    color: {{primary}};
}

/* ──────────────── SIDEBAR ──────────────── */
QFrame[class="sidebar-header"] {
    background-color: {{sidebar_bg}};
    border-bottom: 3px solid {{border}};
}

QFrame[class="sidebar-footer"] {
    background-color: {{sidebar_footer_bg}};
    border-top: 1px solid {{border}};
}

QToolButton[class="sidebar-category"] {
    background-color: {{sidebar_category_bg}};
    color: {{fg}};
    border: none;
    border-left: 4px solid {{sidebar_category_border}};
    padding: 0 15px;
    font-size: 13px;
    font-weight: bold;
    text-align: left;
    border-radius: 0;
}
QToolButton[class="sidebar-category"]:hover {
    background-color: {{sidebar_item_hover_bg}};
    border-left: 5px solid {{sidebar_item_active}};
}

QPushButton[class="sidebar-item"] {
    background-color: transparent;
    color: {{sidebar_item}};
    border: none;
    border-left: 5px solid transparent;
    padding: 0 30px;
    font-size: 14px;
    text-align: left;
    border-radius: 4px;
}
QPushButton[class="sidebar-item"]:hover {
    background-color: {{sidebar_item_hover_bg}};
    color: {{fg}};
    border-left: 5px solid {{primary}};
}

QPushButton[class="sidebar-item-active"] {
    background-color: {{sidebar_item_active_bg}};
    color: {{sidebar_item_active}};
    border: none;
    border-left: 5px solid {{sidebar_item_active}};
    padding: 0 30px;
    font-size: 14px;
    font-weight: bold;
    text-align: left;
    border-radius: 4px;
}

/* ──────────────── BANNER ──────────────── */
QWidget[class="banner"] {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {{bg_banner_start}},
        stop:1 {{bg_banner_end}}
    );
}

#dlg_header {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {{primary}},
        stop:1 {{primary_hover}}
    );
}

/* 40×40 icon for page banners (create_banner) */
QLabel[class="banner-icon"] {
    background: rgba(255, 255, 255, 0.18);
    border-radius: 20px;
    font-size: 22px;
    color: white;
}

/* 48×48 icon for dialog headers (build_dialog_header) */
QLabel[class="dialog-header-icon"] {
    background: rgba(255, 255, 255, 0.18);
    border-radius: 24px;
    font-size: 22px;
    color: white;
}

QLabel[class="banner-title"] {
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.3px;
    background: transparent;
}

QLabel[class="banner-subtitle"] {
    color: rgba(255, 255, 255, 0.78);
    font-size: 10px;
    background: transparent;
}

QPushButton[class="banner-btn"] {
    background: rgba(255, 255, 255, 0.15);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: 7px;
    padding: 7px 18px;
    font-size: 9.5px;
    font-weight: 600;
}
QPushButton[class="banner-btn"]:hover {
    background: rgba(255, 255, 255, 0.25);
}
QPushButton[class="banner-btn"]:pressed {
    background: rgba(255, 255, 255, 0.10);
}

/* ──────────────── DIALOG ──────────────── */
QWidget#dlg_body {
    background-color: {{bg}};
}

QWidget#main_tabs QWidget#dlg_body {
    background-color: transparent;
}

QWidget#dlg_header {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {{primary}},
        stop:1 {{primary_hover}}
    );
}

/* ──────────────── DIALOG CONTAINER ──────────────── */
QFrame[class="dialog-container"] {
    background-color: {{bg_card}};
    border-radius: 12px;
}

/* ──────────────── OVERLAY ──────────────── */
QWidget[class="overlay"] {
    background-color: {{overlay_bg}};
}
"""
    replacements = {
        # Backgrounds
        "{{bg}}": theme.get("bg", "#0f172a"),
        "{{bg_card}}": theme.get("bg_card", "#1e293b"),
        "{{bg_input}}": theme.get("bg_input", "#334155"),
        "{{bg_sidebar}}": theme.get("bg_sidebar", "#0f172a"),
        "{{bg_banner_start}}": theme.get("bg_banner_start", "#0f172a"),
        "{{bg_banner_end}}": theme.get("bg_banner_end", "#1e293b"),
        # Text
        "{{fg}}": theme.get("fg", "#f1f5f9"),
        "{{fg_muted}}": theme.get("fg_muted", "#94a3b8"),
        "{{fg_on_primary}}": theme.get("fg_on_primary", "#ffffff"),
        # Primary
        "{{primary}}": theme.get("primary", "#6366f1"),
        "{{primary_hover}}": theme.get("primary_hover", "#4f46e5"),
        "{{primary_light}}": theme.get("primary_light", "rgba(99,102,241,0.12)"),
        "{{primary_dark}}": theme.get("primary_dark", "#4f46e5"),
        # Borders
        "{{border}}": theme.get("border", "#334155"),
        "{{border_focus}}": theme.get("border_focus", "#6366f1"),
        # Accent
        "{{accent}}": theme.get("accent", "#22d3ee"),
        # Semantic
        "{{success}}": theme.get("success", "#34d399"),
        "{{success_light}}": theme.get("success_light", "rgba(52,211,153,0.12)"),
        "{{warning}}": theme.get("warning", "#fbbf24"),
        "{{warning_light}}": theme.get("warning_light", "rgba(251,191,36,0.12)"),
        "{{danger}}": theme.get("danger", "#f87171"),
        "{{danger_hover}}": theme.get("danger_hover", "#ef4444"),
        "{{danger_light}}": theme.get("danger_light", "rgba(248,113,113,0.12)"),
        "{{info}}": theme.get("info", "#818cf8"),
        "{{info_light}}": theme.get("info_light", "rgba(129,140,248,0.12)"),
        # Table
        "{{table_alt}}": theme.get("table_alt", "#1a2332"),
        "{{table_grid}}": theme.get("table_grid", "#1e293b"),
        "{{table_header_bg}}": theme.get("table_header_bg", "#1a2332"),
        # Overlay
        "{{overlay_bg}}": theme.get("overlay_bg", "rgba(11,17,32,0.85)"),
        # Scrollbar
        "{{scrollbar_handle}}": theme.get("scrollbar_handle", "#334155"),
        "{{scrollbar_hover}}": theme.get("scrollbar_hover", "#475569"),
        # Sidebar
        "{{sidebar_bg}}": theme.get("sidebar_bg", "#0f172a"),
        "{{sidebar_item}}": theme.get("sidebar_item", "#94a3b8"),
        "{{sidebar_item_hover_bg}}": theme.get("sidebar_item_hover_bg", "rgba(129,140,248,0.08)"),
        "{{sidebar_item_active}}": theme.get("sidebar_item_active", "#818cf8"),
        "{{sidebar_item_active_bg}}": theme.get("sidebar_item_active_bg", "rgba(129,140,248,0.12)"),
        "{{sidebar_category_bg}}": theme.get("sidebar_category_bg", "#1a2332"),
        "{{sidebar_category_border}}": theme.get(
            "sidebar_category_border", "rgba(129,140,248,0.20)"
        ),
        "{{sidebar_footer_bg}}": theme.get("sidebar_footer_bg", "#1a2332"),
        # Progress
        "{{progress_bg}}": theme.get("progress_bg", "#1e293b"),
        "{{progress_chunk}}": theme.get("progress_chunk", "#6366f1"),
        # Tooltip
        "{{tooltip_bg}}": theme.get("tooltip_bg", "#f1f5f9"),
        "{{tooltip_fg}}": theme.get("tooltip_fg", "#0f172a"),
        # Calendar legend
        "{{legend_available_bg}}": theme.get("legend_available_bg", "#dbeafe"),
        "{{legend_rented_bg}}": theme.get("legend_rented_bg", "#dcfce7"),
        "{{legend_reserved_bg}}": theme.get("legend_reserved_bg", "#ffedd5"),
    }
    for key, val in replacements.items():
        base = base.replace(key, val)
    return base
