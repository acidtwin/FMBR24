"""FM24 default skin QSS stylesheet — colours extracted from game files.

Sources (settings.fmf → settings/fm colours.xml):
  alt_box_background     rgb(20,21,26)   → window_bg
  alt_dark_box_background rgb(26,34,38)  → surface
  alpha_box_background   rgb(41,43,50)   → elevated
  FM purple              rgb(105,51,189) → accent
  FM purple light        rgb(115,92,228) → accent_hover
  FM purple dark         rgb(100,30,170) → accent_press
  status_homegrown_club  rgb(90,160,209) → hgp_blue
  status_cannot_play     rgb(209,67,67)  → non_hgp_red
  default foreground     rgb(255,255,255)→ text_primary
"""

COLORS = {
    # backgrounds — from fm colours.xml box_background tokens
    'window_bg':     '#14151A',  # alt_box_background
    'surface':       '#1A2226',  # alt_dark_box_background
    'elevated':      '#292B32',  # alpha_box_background
    'border':        '#343740',
    'border_bright': '#454A58',
    # text — default foreground is white in the fm skin
    'text_primary':  '#FFFFFF',
    'text_secondary':'#8B96A8',
    'text_dim':      '#525B68',
    # FM purple brand accent (from fm colours.xml)
    'accent':        '#6933BD',  # FM purple rgb(105,51,189)
    'accent_hover':  '#735CE4',  # FM purple light rgb(115,92,228)
    'accent_press':  '#641EAA',  # FM purple dark rgb(100,30,170)
    # squad status colours (from fm colours.xml status_* tokens)
    'hgp_green':     '#5AA0D1',  # status_homegrown_club rgb(90,160,209)
    'non_hgp_red':   '#D14343',  # status_cannot_play rgb(209,67,67)
    'warning':       '#FF501E',  # FM orange
    'selection_bg':  '#2A1B4A',  # dark purple row selection
}

QSS = f"""
/* ── Base ─────────────────────────────────────────────────────────── */
QWidget {{
    background-color: {COLORS['window_bg']};
    color: {COLORS['text_primary']};
    font-family: "Roboto", "Segoe UI", "Liberation Sans", Arial, sans-serif;
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
    border-radius: 3px;
}}

/* ── Labels ──────────────────────────────────────────────────────── */
QLabel {{
    color: {COLORS['text_primary']};
    background: transparent;
}}
QLabel#header {{
    color: {COLORS['text_primary']};
    font-size: 15px;
    font-weight: bold;
    letter-spacing: 0.5px;
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
    border-radius: 2px;
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
    border-radius: 2px;
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
    border-radius: 2px;
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
    border-radius: 3px;
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
    border-radius: 2px;
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
    border-radius: 2px;
    text-align: center;
    color: {COLORS['text_secondary']};
    font-size: 11px;
}}
QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 1px;
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
    border-radius: 2px;
}}

/* ── Status bar ──────────────────────────────────────────────────── */
QStatusBar {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border']};
    font-size: 11px;
}}
"""
