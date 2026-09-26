"""FM24-inspired dark skin QSS stylesheet."""

# Palette (FM24 default dark skin)
COLORS = {
    'window_bg':     '#131722',
    'surface':       '#1e2430',
    'elevated':      '#252f3f',
    'border':        '#2a3548',
    'border_bright': '#3a4a60',
    'text_primary':  '#e8ecf3',
    'text_secondary':'#7a8ba6',
    'text_dim':      '#4a5a72',
    'accent':        '#1969e1',
    'accent_hover':  '#2478f0',
    'accent_press':  '#1258c0',
    'hgp_green':     '#22c55e',
    'non_hgp_red':   '#ef4444',
    'warning':       '#f59e0b',
    'selection_bg':  '#1e3a6e',
}

QSS = f"""
/* ── Base ─────────────────────────────────────────────────────────── */
QWidget {{
    background-color: {COLORS['window_bg']};
    color: {COLORS['text_primary']};
    font-family: "Segoe UI", "Liberation Sans", Arial, sans-serif;
    font-size: 13px;
    border: none;
    outline: none;
}}

QMainWindow {{
    background-color: {COLORS['window_bg']};
}}

/* ── Panels / frames ─────────────────────────────────────────────── */
QFrame#panel {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
}}

/* ── Labels ──────────────────────────────────────────────────────── */
QLabel {{
    color: {COLORS['text_primary']};
    background: transparent;
}}
QLabel#header {{
    color: {COLORS['text_primary']};
    font-size: 16px;
    font-weight: bold;
}}
QLabel#subheader {{
    color: {COLORS['text_secondary']};
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QLabel#dim {{
    color: {COLORS['text_dim']};
    font-size: 11px;
}}
QLabel#hgp_yes {{
    color: {COLORS['hgp_green']};
    font-weight: bold;
}}
QLabel#hgp_no {{
    color: {COLORS['text_secondary']};
}}

/* ── Buttons ─────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    padding: 6px 14px;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: {COLORS['border']};
    border-color: {COLORS['border_bright']};
}}
QPushButton:pressed {{
    background-color: {COLORS['border']};
}}
QPushButton:disabled {{
    color: {COLORS['text_dim']};
    border-color: {COLORS['border']};
}}

QPushButton#accent {{
    background-color: {COLORS['accent']};
    color: #ffffff;
    border: none;
    padding: 7px 18px;
    font-weight: bold;
}}
QPushButton#accent:hover {{
    background-color: {COLORS['accent_hover']};
}}
QPushButton#accent:pressed {{
    background-color: {COLORS['accent_press']};
}}
QPushButton#accent:disabled {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text_dim']};
}}

/* ── Line edit / search ──────────────────────────────────────────── */
QLineEdit {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    padding: 6px 10px;
    selection-background-color: {COLORS['selection_bg']};
}}
QLineEdit:focus {{
    border-color: {COLORS['accent']};
}}
QLineEdit:disabled {{
    color: {COLORS['text_dim']};
}}

/* ── Table ───────────────────────────────────────────────────────── */
QTableWidget {{
    background-color: {COLORS['surface']};
    color: {COLORS['text_primary']};
    gridline-color: {COLORS['border']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    selection-background-color: {COLORS['selection_bg']};
    selection-color: {COLORS['text_primary']};
    alternate-background-color: {COLORS['elevated']};
}}
QTableWidget::item {{
    padding: 5px 8px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: {COLORS['selection_bg']};
}}
QHeaderView::section {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text_secondary']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    border-right: 1px solid {COLORS['border']};
    padding: 5px 8px;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QHeaderView::section:last {{
    border-right: none;
}}

/* ── Scrollbars ──────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {COLORS['surface']};
    width: 8px;
    border: none;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['border_bright']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {COLORS['surface']};
    height: 8px;
    border: none;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['border']};
    border-radius: 4px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {COLORS['border_bright']};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── Combo box ───────────────────────────────────────────────────── */
QComboBox {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    padding: 5px 10px;
}}
QComboBox:hover {{
    border-color: {COLORS['border_bright']};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['selection_bg']};
}}

/* ── Progress bar ────────────────────────────────────────────────── */
QProgressBar {{
    background-color: {COLORS['elevated']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    text-align: center;
    color: {COLORS['text_secondary']};
    font-size: 11px;
}}
QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 2px;
}}

/* ── Splitter ────────────────────────────────────────────────────── */
QSplitter::handle {{
    background: {COLORS['border']};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}
QSplitter::handle:vertical {{
    height: 1px;
}}

/* ── Checkboxes ──────────────────────────────────────────────────── */
QCheckBox {{
    color: {COLORS['text_primary']};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {COLORS['border_bright']};
    border-radius: 2px;
    background: {COLORS['elevated']};
}}
QCheckBox::indicator:checked {{
    background: {COLORS['accent']};
    border-color: {COLORS['accent']};
}}

/* ── Tooltip ─────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_bright']};
    padding: 4px 8px;
    border-radius: 3px;
}}

/* ── Status bar ──────────────────────────────────────────────────── */
QStatusBar {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border']};
    font-size: 11px;
}}
"""
