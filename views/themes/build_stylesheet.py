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
