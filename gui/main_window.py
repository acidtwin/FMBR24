"""FM Backroom 24 - main window."""
import math
import os
from datetime import date
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QProgressBar, QStatusBar, QFrame, QSizePolicy, QMessageBox,
    QAbstractItemView, QMenu, QStackedWidget, QDialog, QScrollArea,
    QComboBox, QStyledItemDelegate, QSpinBox,
    QInputDialog, QGridLayout, QBoxLayout, QTableView, QStyle, QStyleOptionViewItem, QApplication, QToolTip,
)
from PyQt6.QtCore import Qt, QTimer, QSize, QRectF, QEvent, QElapsedTimer
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPixmap, QPainter, QAction, QLinearGradient, QBrush, QPen, QImageReader

from gui.icon import logo_pixmap
from gui.theme import COLORS
from gui.roles import role_rating, role_names_by_group, _ROLE_INDEX
from fm_editor.rolepos import role_positions
from fm_editor.clubextra import rep_stars
from gui.stars import _StarWidget, star_row_pixmap
from fm_editor.abilitystars import ability_stars
from fm_editor.nations import nation_name as _nation_name_long, nation_flag as _nation_flag
from fm_editor.cache import clear_cache
from gui.workers import ParseWorker, SaveWorker
from gui.search_suggest import _SearchSuggest, _SuggestDelegate, _SG_MAX  # noqa: F401 (re-exported)
from fm_editor import weights as _weights_mod
from fm_editor import settings as _settings_mod
from gui.about_dialog import AboutDialog
from gui.settings_page import SettingsPage
from gui.people_model import PeopleModel, num_key, HG_ROLE, ROWQ_ROLE, HG_BASE_ROLE, ROW_TINT
from gui.player_window import PlayerWindow
from gui.faces import get_service as _faces_service
from fm_editor.agecalc import person_age as _age, set_ref as _set_age_ref, get_ref as _get_age_ref

DEFAULT_SAVE_DIR = os.path.expanduser(
    '~/.local/share/Steam/steamapps/compatdata/2252570/pfx/drive_c'
    '/users/steamuser/Documents/Sports Interactive/Football Manager 2024/games/'
)

NATIONS = {
    11:  'Egypt',         29:  'Morocco',      33:  'Nigeria',
    97:  'Canada',        120: 'USA',
    187: 'Argentina',     189: 'Brazil',       195: 'Uruguay',
    61:  'Japan',         80:  'South Korea',  177: 'Australia',
    126: 'Albania',       129: 'Austria',      135: 'Croatia',
    146: 'Greece',        147: 'Hungary',      161: 'Poland',
    165: 'Russia',        176: 'Serbia',       219: 'Kosovo',
    131: 'Belgium',       137: 'Czech Rep.',   138: 'Denmark',
    139: 'England',       143: 'France',       145: 'Germany',
    150: 'Italy',         158: 'Netherlands',  159: 'N.Ireland',
    160: 'Norway',        162: 'Portugal',     163: 'Rep.Ireland',
    167: 'Scotland',      170: 'Spain',        171: 'Sweden',
    172: 'Switzerland',   173: 'Turkey',       175: 'Wales',
}

POSITIONS = ['GK','SW','DL','DC','DR','DM','ML','MC','MR','AML','AMC','AMR','ST','WBL','WBR']

# -- SVG icon strings ----------------------------------------------------------

_SVG_SEARCH = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round">'
    '<circle cx="6.5" cy="6.5" r="4.5"/>'
    '<line x1="9.5" y1="9.5" x2="14" y2="14"/>'
    '</svg>'
)
_SVG_COG = (
    '<svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">'
    '<path fill="{c}" fill-rule="evenodd" d="'
    'M6.5 1.2h3l.35 1.45c.32.1.62.24.9.4l1.38-.47 1.5 2.6-1.05.96'
    'c.04.24.07.49.07.76s-.03.52-.07.76l1.05.96-1.5 2.6-1.38-.47'
    'c-.28.16-.58.3-.9.4L9.5 12.8h-3l-.35-1.45c-.32-.1-.62-.24-.9-.4'
    'l-1.38.47-1.5-2.6 1.05-.96A4.1 4.1 0 0 1 3.35 7.6l-1.05-.96 1.5-2.6'
    ' 1.38.47c.28-.16.58-.3.9-.4L6.5 1.2z'
    ' M8 10a2.4 2.4 0 1 0 0-4.8A2.4 2.4 0 0 0 8 10z"/>'
    '</svg>'
)
_SVG_RELOAD = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M2.5 8a5.5 5.5 0 1 0 1-3.2"/>'
    '<path d="M2.5 2v3h3"/>'
    '</svg>'
)
_SVG_CLUB = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="2" y="8" width="12" height="6" rx="1"/>'
    '<path d="M1 8h14M5 8V5.5M11 8V5.5M8 8V4.5M3 5.5h10"/>'
    '</svg>'
)
_SVG_SQUAD = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="5.5" cy="5" r="2.5"/>'
    '<path d="M1 14c0-2.5 2-4 4.5-4s4.5 1.5 4.5 4"/>'
    '<circle cx="11.5" cy="5.5" r="2"/>'
    '<path d="M14.5 14c0-2-1.5-3.5-3-3.5"/>'
    '</svg>'
)
_SVG_STAFF = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="8" cy="5" r="3"/>'
    '<path d="M2 14c0-3 2.7-5 6-5s6 2 6 5"/>'
    '</svg>'
)
_SVG_SHORTLIST = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M8 2l1.6 3.2 3.5.5-2.5 2.5.6 3.5L8 10 4.8 11.7l.6-3.5L3 5.7l3.5-.5z"/>'
    '</svg>'
)
_SVG_REPORT = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="3" y="1" width="10" height="14" rx="1"/>'
    '<path d="M6 5h4M6 8h4M6 11h2"/>'
    '</svg>'
)
_SVG_LOAD = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M2 12V6a1 1 0 0 1 1-1h3.5L8 6.5H13a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1z"/>'
    '</svg>'
)
_SVG_SAVE = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="2" y="2" width="12" height="12" rx="1"/>'
    '<path d="M5 2v4h6V2"/>'
    '<rect x="4.5" y="9" width="7" height="4" rx="0.5"/>'
    '</svg>'
)

_SVG_INFO = (
    '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"'
    ' stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="8" cy="8" r="6.5"/>'
    '<path d="M8 7.2v4M8 4.6v.1"/>'
    '</svg>'
)
# Save Info avatar silhouette (mockup .avatar svg, viewBox 44x44, filled)
_SVG_AVATAR = (
    '<svg viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg">'
    '<circle cx="22" cy="15" r="8" fill="{c}"/>'
    '<path d="M4 44c0-11 8-17 18-17s18 6 18 17z" fill="{c}"/>'
    '</svg>'
)

# Growing dot cycle: . .. ... ....
_DOT_SEQ = [1, 2, 3, 4, 3, 2]  # bounces . .. ... .... ... .. (then . again), user's preferred animation

# Column header tooltips shared across all player tables
_COL_TT = {
    'INJ':    'Injured',
    'Pos':    'Primary playing position',
    'CA':     'Current Ability (1–200)\nOverall quality right now',
    'PA':     'Potential Ability (1–200)\nMaximum this player can reach',
    'Dev':    'Development rate (1–20)\nPredicted improvement speed, based on ambition, professionalism and determination',
    'Rating': 'Role suitability (1–20)\nMean of key attributes for the selected role',
    'HGP':    'Homegrown Player (nation)\nTrained in England for 3+ years between ages 15–21',
    'HGC':    'Homegrown at Club\nTrained at this club for 3+ years between ages 15–21',
    'CtrE':   'Contract End (YYYY-MM)',
    # Attribute abbreviations → full names (display value = max(1, min(20, round(raw/5))))
    'Cro': 'Crossing',      'Dri': 'Dribbling',      'Fin': 'Finishing',
    'Hea': 'Heading',       'Lsh': 'Long Shots',      'Mar': 'Marking',
    'OtB': 'Off The Ball',  'Pas': 'Passing',         'Pen': 'Penalties',
    'Tck': 'Tackling',      'Vis': 'Vision',          'Han': 'Handling',
    'AeR': 'Aerial Reach',  'CoA': 'Cmd of Area',     'Com': 'Communication',
    'Kic': 'Kicking',       'Thr': 'Throwing',        'Ant': 'Anticipation',
    'Dec': 'Decisions',     '1v1': 'One on Ones',     'Psn': 'Positioning',
    'Ref': 'Reflexes',      'Fir': 'First Touch',     'Tec': 'Technique',
    'LFo': 'Left Foot',     'RFo': 'Right Foot',      'Fla': 'Flair',
    'Cor': 'Corners',       'Tea': 'Teamwork',        'Wor': 'Work Rate',
    'LTh': 'Long Throws',   'Ecc': 'Eccentricity',    'RuO': 'Rushing Out',
    'Pun': 'Punching',      'Acc': 'Acceleration',    'FK':  'Free Kick',
    'Str': 'Strength',      'Sta': 'Stamina',         'Pac': 'Pace',
    'JR':  'Jumping Reach', 'Lea': 'Leadership',      'Dir': 'Dirtiness',
    'Bal': 'Balance',       'Bra': 'Bravery',         'Con': 'Consistency',
    'Agg': 'Aggression',    'Agi': 'Agility',         'BM':  'Big Matches',
    'IP':  'Injury Prone',  'Ver': 'Versatility',     'NF':  'Natural Fitness',
    'Det': 'Determination', 'Cmp': 'Composure',       'Cnc': 'Concentration',
}


def _svg_icon(svg_tpl: str, color: str = '#8B96A8', size: int = 16) -> QIcon:
    """Render an SVG template string (with {c} color placeholder) to QIcon."""
    try:
        from PyQt6.QtSvg import QSvgRenderer
        svg_bytes = svg_tpl.replace('{c}', color).encode()
        renderer = QSvgRenderer(svg_bytes)
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        painter = QPainter(px)
        renderer.render(painter)
        painter.end()
        return QIcon(px)
    except Exception:
        return QIcon()


# -- Helpers -------------------------------------------------------------------

class _SortItem(QTableWidgetItem):
    def __init__(self, text, sort_key=None):
        super().__init__(text)
        self._sk = sort_key
    def __lt__(self, other):
        try:
            a = self._sk if self._sk is not None else self.text()
            b = other._sk if isinstance(other, _SortItem) and other._sk is not None else other.text()
            try:
                return float(a) < float(b)
            except (ValueError, TypeError):
                return str(a) < str(b)
        except Exception:
            return False


class _BusyVeil(QWidget):
    """Dim, click-blocking layer over the main content while a save / reload / load is running.
    Child of `target`, resizes with it. (Plain QWidget paints nothing by itself: we fill it.)"""
    ALPHA = 140  # 0-255; window_bg (#14151A) at ~55%

    def __init__(self, target):
        super().__init__(target)
        self._target = target
        target.installEventFilter(self)
        self.setCursor(Qt.CursorShape.BusyCursor)
        self.hide()

    def eventFilter(self, obj, ev):
        if obj is self._target and ev.type() == QEvent.Type.Resize:
            self.setGeometry(self._target.rect())
        return False

    def show_veil(self, on):
        if on:
            self.setGeometry(self._target.rect())
            self.raise_()
        self.setVisible(on)

    def set_text(self, base, dots=0):
        self._base, self._dots = base, dots
        self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(20, 21, 26, self.ALPHA))
        base = getattr(self, '_base', '')
        if not base:
            return
        f = QFont(self.font())
        f.setPixelSize(18)
        f.setWeight(QFont.Weight.DemiBold)
        p.setFont(f)
        p.setPen(QColor(COLORS['text_primary']))
        fm = QFontMetrics(f)
        total = fm.horizontalAdvance(base + '....')  # reserve the widest dot count so the text never wobbles
        x = (self.width() - total) // 2
        y = self.height() // 2 + fm.ascent() // 2
        p.drawText(x, y, base)
        p.drawText(x + fm.horizontalAdvance(base), y, '.' * getattr(self, '_dots', 0))

    def mousePressEvent(self, ev):  # swallow clicks / wheel so nothing underneath reacts
        ev.accept()

    mouseReleaseEvent = mouseDoubleClickEvent = mouseMoveEvent = wheelEvent = mousePressEvent


class _SidebarFrame(QFrame):
    """QFrame subclass that paints a texture overlay over the QSS background."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bg_px = None

    def set_bg(self, pixmap: 'QPixmap'):
        self._bg_px = pixmap
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtWidgets import QStyleOption, QStyle
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        # Paint QSS-defined background (surface colour, border etc.)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, self)
        # Texture overlay
        if self._bg_px and not self._bg_px.isNull():
            p.setOpacity(0.22)
            scaled = self._bg_px.scaled(
                self.width(), self.height(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            p.drawPixmap(0, 0, scaled)
        p.end()


def _primary_pos(positions):
    return POSITIONS[positions.index(max(positions))]


# -- Club overview page (mockups/club-page-design-a.html 1:1 translation) -----
# Position badge colors (bg, fg) — mockup .badge.pos-XX rules, literal hex.
_CLUB_POS_BADGE = {
    'GK':  ('#1a3a6e', '#7aaeff'),
    'DC':  ('#1a3a1a', '#6fdd6f'),
    'ST':  ('#3a1a1a', '#ff7777'),
    'AMC': ('#1a3030', '#66ddcc'),
    'AMR': ('#2a2a1a', '#ddcc66'),
    'AML': ('#3a1a3a', '#cc88ff'),
    'MC':  ('#1e2850', '#88aaee'),
    'DR':  ('#1a2a2a', '#66cccc'),
    'DL':  ('#1a2a2a', '#66cccc'),
    'DM':  ('#2a1a4a', '#aa88ff'),
    'INJ': ('#4a0f0f', '#ff6666'),
}
_CLUB_POS_BADGE_FALLBACK = ('#202c3a', '#7a8fa6')

# 3x3 position-count grid (mockup .a-pos-grid) — 9 cells, mockup-exact
# order/colors, a curated subset of POSITIONS (not the full position list).
_CLUB_POS_GRID = [
    ('GK', '#7aaeff'), ('DR', '#66cccc'), ('DC', '#6fdd6f'),
    ('DL', '#66cccc'), ('MC', '#88aaee'), ('AMR', '#ddcc66'),
    ('AML', '#cc88ff'), ('AMC', '#66ddcc'), ('ST', '#ff7777'),
]

_CLUB_PENDING_QSS = (
    "background:rgba(122,143,166,0.12); color:#7a8fa6; font-weight:bold;"
    " font-size:10px; letter-spacing:0.06em; text-transform:uppercase;"
    " padding:3px 8px; border-radius:10px;"
)


def _contract_expiry_counts(squad, today):
    """Pure helper for the club page 'Contracts' panel — no Qt involved.

    Returns (n_expiring_6mo, n_expiring_1yr, longest_deal) from each squad
    player's p['contract_end'] 'YYYY-MM' string. Both counts are cumulative
    (the 1yr bucket includes the 6mo one) and exclude already-expired
    contracts. longest_deal is the max 'YYYY-MM' string, or '' if none.
    """
    today_months = today.year * 12 + today.month
    n6 = n12 = 0
    longest = ''
    for p in squad:
        ce = p.get('contract_end')
        if not ce:
            continue
        try:
            y_str, m_str = ce.split('-')
            months_out = (int(y_str) * 12 + int(m_str)) - today_months
        except (ValueError, AttributeError):
            continue
        if 0 <= months_out < 6:
            n6 += 1
        if 0 <= months_out < 12:
            n12 += 1
        if ce > longest:
            longest = ce
    return n6, n12, longest


def _club_badge(text, bg, fg, font_size=11, padding='2px 6px'):
    lbl = QLabel(text.upper())
    lbl.setStyleSheet(
        f"background:{bg}; color:{fg}; font-weight:bold; font-size:{font_size}px;"
        f" letter-spacing:0.06em; text-transform:uppercase; padding:{padding};"
        " border-radius:2px;")
    return lbl


_SHOW_PENDING = True  # Settings > Show PENDING markers (set by MainWindow._apply_ui_prefs)


def _club_pending_vis(lbl, pending):
    """Hide PENDING chips (and their Club-page key/value row) when the setting is off."""
    show = _SHOW_PENDING or not pending
    lbl.setVisible(show)
    row = lbl.parentWidget()
    if row is not None and row.objectName() == 'clubKvRow':
        row.setVisible(show)


def _club_pending_chip(text='PENDING'):
    lbl = QLabel(text)
    lbl.setStyleSheet(_CLUB_PENDING_QSS)
    if not _SHOW_PENDING:
        lbl.setVisible(False)
    return lbl


def _club_hide_row(lbl):
    """No data for this Club-page row in the save: hide the whole row (never a placeholder)."""
    lbl.setVisible(False)
    row = lbl.parentWidget()
    if row is not None and row.objectName() == 'clubKvRow':
        row.setVisible(False)


def _club_set_value(lbl, text, color='#e8edf2'):
    _club_pending_vis(lbl, False)
    lbl.setText(text)
    lbl.setVisible(True)
    row = lbl.parentWidget()
    if row is not None and row.objectName() == 'clubKvRow':
        row.setVisible(True)
    lbl.setStyleSheet(f"color:{color}; font-size:12px; font-weight:500; background:transparent;")


def _club_money(v, per_week=False):
    """GBP int -> '£62.3M' / '£3.66M p/w' / '£540K'; negatives keep the sign."""
    sign, a = ('-' if v < 0 else ''), abs(v)
    if a >= 1_000_000:
        txt = f'{a / 1e6:.2f}M' if per_week else f'{a / 1e6:.1f}M'
    else:
        txt = f'{a / 1e3:.0f}K'
    return f'{sign}£{txt}' + (' p/w' if per_week else '')


def _ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _club_sec_hdr(text, sub=False):
    lbl = QLabel(text.upper())  # QSS text-transform is not honoured
    margin = "margin-top:16px; " if sub else ""
    lbl.setStyleSheet(
        f"{margin}color:#4a5f73; font-size:12px; font-weight:bold;"
        " letter-spacing:0.12em; text-transform:uppercase;"
        " padding-bottom:8px; border-bottom:1px solid #263140; background:transparent;")
    return lbl


def _club_kv_row(label_text, value_widget):
    row = QWidget()
    row.setObjectName('clubKvRow')
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 5, 0, 5)
    lay.setSpacing(8)
    lbl = QLabel(label_text)
    lbl.setStyleSheet("color:#4a5f73; font-size:12px; background:transparent;")
    lay.addWidget(lbl)
    lay.addStretch(1)
    lay.addWidget(value_widget)
    row.setStyleSheet(
        "QWidget#clubKvRow { border-bottom:1px solid rgba(255,255,255,0.04); background:transparent; }")
    return row


def _club_kv_value(text='', color='#e8edf2'):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{color}; font-size:12px; font-weight:500; background:transparent;")
    lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return lbl


# -- Save Info page helpers (mockups/save-info-page-design-b.html) --------------

_SI_DAYS = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
# Brand shown in the sidebar header (mockups/sidebar-header-options.html, option A).
# The app is due a rename: change these two lines (plus the hard-coded titles listed in main.py / MainWindow).
_BRAND_MARK_PX = 48   # sidebar logo (the FMBR24 floppy: the wordmark text on it needs this size to read)
_APP_WORDMARK = 'FMBR24'

_SI_MONTHS = ('January', 'February', 'March', 'April', 'May', 'June', 'July',
              'August', 'September', 'October', 'November', 'December')


def _fmt_game_date(iso):
    """'2028-01-02' -> 'Sunday 2nd January 2028' (the game's own date wording); None if unparseable."""
    try:
        d = date.fromisoformat(iso)
    except (TypeError, ValueError):
        return None
    suffix = 'th' if 10 <= d.day % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d.day % 10, 'th')
    return f"{_SI_DAYS[d.weekday()]} {d.day}{suffix} {_SI_MONTHS[d.month - 1]} {d.year}"


def _fmt_short_date(iso):
    """'2028-01-02' -> '2 Jan 2028'; None if unparseable."""
    try:
        d = date.fromisoformat(iso)
    except (TypeError, ValueError):
        return None
    return f"{d.day} {_SI_MONTHS[d.month - 1][:3]} {d.year}"


def _fmt_game_time(seconds):
    """116137 -> '1 Day, 8 Hours, 16 Minutes' (rounded to the nearest minute, zero units dropped)."""
    total = (int(seconds) + 30) // 60
    days, rem = divmod(total, 1440)
    hours, mins = divmod(rem, 60)
    parts = [f"{n} {unit}{'' if n == 1 else 's'}"
             for n, unit in ((days, 'Day'), (hours, 'Hour'), (mins, 'Minute')) if n]
    return ', '.join(parts) or '0 Minutes'


def _fmt_file_size(n):
    """Human-readable size, 1024-based: 197537792 -> '188.4 MB'."""
    n = float(n)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return f"{int(n)} B" if unit == 'B' else f"{n:.1f} {unit}"
        n /= 1024


def _si_of(key, fn=str):
    """Save Info row formatter: fn(src[key]), or None (row hidden) when the key is absent."""
    return lambda src: fn(src[key]) if src.get(key) is not None else None


def _si_folder(src):
    p = src.get('folder_path')
    if not p:
        return None
    parts = [x for x in p.split(os.sep) if x]
    return (('…/' + '/'.join(parts[-2:])) if len(parts) > 2 else p, p)   # (text, tooltip)


def _si_version(src):
    v, b = src.get('game_version'), src.get('game_build')
    return f"{v}+{b}" if v and b else (str(v or b) if (v or b) else None)


def _si_nations_leagues(src):
    n, lg = src.get('nations_count'), src.get('leagues')
    return f"{n} · {len(lg)}" if n and lg else None


def _si_league_note(src):
    lg = src.get('leagues')
    return None if not lg else ', '.join(lg[:3]) + (f' and {len(lg) - 3} more' if len(lg) > 3 else '')


# The ledger, one band per tuple: (band title, rows). A row is
#   (placement, key, label, formatter[, dim])
# placement: 'full' (spans both columns) | 'left' | 'right' | 'note' (small text under the fields).
# formatter(src) -> str | (str, tooltip) | None; None hides the row, and a band with no visible
# rows hides. `src` = the parsed save_info dict + the file/database facts added by
# _update_save_info_view (file_name, folder_path, file_size, file_modified, people_total).
# To show a new saveinfo.py key, add ONE row here, e.g.
#   ('left', 'database_size', 'Size', _si_of('database_size', _fmt_file_size)),
_SI_LAYOUT = (
    ('Save File', (
        ('full',  'file_name',     'File name',    _si_of('file_name')),
        ('full',  'folder',        'Folder',       _si_folder, True),
        ('left',  'file_size',     'Size on disk', _si_of('file_size', _fmt_file_size)),
        ('right', 'file_modified', 'Modified',     _si_of('file_modified')),
    )),
    ('Game', (
        ('full',  'game_name',    'Game name',    _si_of('game_name')),
        ('full',  'in_game_date', 'In-game date', _si_of('in_game_date', _fmt_game_date)),
        ('full',  'date_created', 'Date created', _si_of('date_created', _fmt_game_date)),
        ('full',  'start_date',   'Game started', _si_of('start_date', _fmt_game_date)),
        ('full',  'game_time',    'Game time',    _si_of('game_time_seconds', _fmt_game_time)),
        ('left',  'times_saved',  'Times saved',  _si_of('times_saved', '{:,}'.format)),
        ('right', 'game_version', 'Game version', _si_version),
    )),
    ('Database', (
        ('left',  'db_people',  'Players + staff',   _si_of('people_total', '{:,}'.format)),
        ('left',  'db_version', 'Version',           _si_of('database_version')),
        ('right', 'db_changes', 'Changes',           _si_of('database_changes', '{:,}'.format)),
        ('right', 'db_nat',     'Nations · leagues', _si_nations_leagues),
        ('note',  'db_note',    '',                  _si_league_note),
    )),
)


def _si_label(text, size, color, bold=False, spacing_em=0.0, upper=False, weight=None):
    """Save Info text label: QSS carries size/colour/weight, letter-spacing goes on the QFont
    (QSS letter-spacing is not honoured; text-transform likewise, hence upper=)."""
    lbl = QLabel(text.upper() if upper else text)
    wt = f" font-weight:{weight};" if weight else (" font-weight:bold;" if bold else "")
    lbl.setStyleSheet(f"color:{color}; font-size:{size}px;{wt} background:transparent;")
    if spacing_em:
        f = lbl.font()
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, size * spacing_em)
        lbl.setFont(f)
    return lbl


class _ElideLabel(QLabel):
    """QLabel that elides (with tooltip) instead of forcing its layout wider."""

    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(0)
        self._full = ''
        self.set_full_text(text)

    def set_full_text(self, text):
        self._full = text
        self.setToolTip(text)
        self._elide()

    def _elide(self):
        self.setText(self.fontMetrics().elidedText(
            self._full, Qt.TextElideMode.ElideRight, max(self.width(), 0) or 10 ** 6))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._elide()

    def showEvent(self, event):
        super().showEvent(event)
        self._elide()


class _FitLabel(_ElideLabel):
    """_ElideLabel that first shrinks its font (start_px .. min_px, bold) to fit — the rail's
    manager name, where the mockup's condensed Barlow face isn't bundled and the fallback is wider."""

    def __init__(self, start_px, min_px, color, spacing_em, parent=None):
        self._start, self._min, self._color, self._sp = start_px, min_px, color, spacing_em
        self._px = start_px
        super().__init__('', parent)
        self._style(start_px)

    def _style(self, px):
        self._px = px
        self.setStyleSheet(f"color:{self._color}; font-size:{px}px; font-weight:bold;"
                           " background:transparent;")
        f = self.font()
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, px * self._sp)
        self.setFont(f)

    def _elide(self):
        if self.width() > 0 and self._full:
            f = QFont(self.font())
            f.setBold(True)
            px = self._start
            while px > self._min:
                f.setPixelSize(px)
                f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, px * self._sp)
                if QFontMetrics(f).horizontalAdvance(self._full) <= self.width():
                    break
                px -= 1
            if px != self._px:
                self._style(px)
        super()._elide()


class _WidthWatcher(QWidget):
    """Plain container that reports its width on resize (drives the Save Info narrow layout)."""

    def __init__(self, on_width, parent=None):
        super().__init__(parent)
        self._on_width = on_width

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._on_width(event.size().width())


# Mockup .rating-pill: green when >= 7.00 (.rating-good), muted otherwise (.rating-avg).
# border-radius 20px in the mockup -> 10px here (QSS renders radius >= half the height as square).
_CLUB_PILL_GOOD = ("background:rgba(93,196,90,0.15); color:#5dc45a; border:1px solid rgba(93,196,90,0.28);"
                   " font-size:13px; font-weight:bold; padding:3px 8px; border-radius:10px;")
_CLUB_PILL_AVG = ("background:rgba(74,95,115,0.12); color:#4a5f73; border:1px solid rgba(74,95,115,0.2);"
                  " font-size:13px; font-weight:bold; padding:3px 8px; border-radius:10px;")
_CLUB_TOP_N = 7


def _club_rating_pill(text, good):
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setMinimumWidth(48)
    lbl.setStyleSheet(_CLUB_PILL_GOOD if good else _CLUB_PILL_AVG)
    return lbl


def _club_top_players(squad, n=_CLUB_TOP_N):
    """Club page 'Top Players' list (pure, no Qt): ('rating'|'ca', [(player, value_text, good)]).

    Ranked by season average match rating (p['stats']['rating'], all competitive games) among
    players with enough rated appearances: at least 40% of the club's most-used player's rated
    appearances, never fewer than 3 (FM's own best-rating lists use a similar minimum-games rule).
    Ties: more rated apps, then higher CA, then name. Goalkeepers are included. With no eligible
    player (club outside the detailed-stats leagues) it falls back to current ability (CA).
    """
    def st(p):
        return p.get('stats') or {}
    rated = [p for p in squad if st(p).get('rating') is not None]
    most = max((st(p)['rated'] for p in rated), default=0)
    floor = max(3, -(-most * 2 // 5))  # ceil(0.4 * most)
    elig = [p for p in rated if st(p)['rated'] >= floor]
    if len(elig) >= 3:
        elig.sort(key=lambda p: (-st(p)['rating'], -st(p)['rated'], -(p.get('ca') or 0),
                                 p.get('name', '')))
        return 'rating', [(p, f"{st(p)['rating']:.2f}", st(p)['rating'] >= 7.0) for p in elig[:n]]
    by_ca = sorted((p for p in squad if p.get('ca') is not None),
                   key=lambda p: (-p['ca'], p.get('name', '')))
    return 'ca', [(p, str(p['ca']), False) for p in by_ca[:n]]


def _club_player_row(rank, pos_code, name, injured, value_widget):
    row = QWidget()
    row.setObjectName('clubPlayerRow')
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 6, 0, 6)
    lay.setSpacing(8)
    rank_lbl = QLabel(str(rank))
    rank_lbl.setFixedWidth(14)
    rank_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    rank_lbl.setStyleSheet("color:#4a5f73; font-size:10px; background:transparent;")
    lay.addWidget(rank_lbl)
    bg, fg = _CLUB_POS_BADGE.get(pos_code, _CLUB_POS_BADGE_FALLBACK)
    lay.addWidget(_club_badge(pos_code, bg, fg))
    name_lbl = QLabel(name)
    name_lbl.setStyleSheet("color:#e8edf2; font-size:12px; font-weight:500; background:transparent;")
    lay.addWidget(name_lbl, 1)
    if injured:
        ibg, ifg = _CLUB_POS_BADGE['INJ']
        lay.addWidget(_club_badge('INJ', ibg, ifg, font_size=9, padding='1px 4px'))
    lay.addWidget(value_widget)
    row.setStyleSheet(
        "QWidget#clubPlayerRow { border-bottom:1px solid rgba(255,255,255,0.04); background:transparent; }")
    return row


def _club_inj_row(name, days):
    row = QWidget()
    row.setObjectName('clubInjRow')
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 6, 0, 6)
    lay.setSpacing(8)
    bg, fg = _CLUB_POS_BADGE['INJ']
    lay.addWidget(_club_badge('INJ', bg, fg, font_size=9))
    name_lbl = QLabel(name)
    name_lbl.setStyleSheet("color:#e8edf2; font-size:12px; background:transparent;")
    lay.addWidget(name_lbl, 1)
    days_lbl = QLabel(f"{days}d")
    days_lbl.setStyleSheet("color:#c0392b; font-size:11px; font-weight:bold; background:transparent;")
    lay.addWidget(days_lbl)
    row.setStyleSheet(
        "QWidget#clubInjRow { border-bottom:1px solid rgba(255,255,255,0.04); background:transparent; }")
    return row


def _club_muted_row(text):
    lbl = QLabel(text)
    lbl.setStyleSheet("color:#4a5f73; font-size:12px; padding:6px 0; background:transparent;")
    return lbl


def _age_in_range(p, mn, mx):
    """Age filter: a bound of 0 means disabled (no lower / no upper limit)."""
    if not mn and not mx:
        return True
    age = _age(p)
    return age >= mn and (not mx or age <= mx)


def _progress_rate(person):
    personality = person.get('personality', [])
    raw_attrs = person.get('raw_attrs', [])
    if not personality or not raw_attrs:
        return None
    ambition = personality[1]
    professionalism = personality[4]
    det_raw = raw_attrs[51]
    determination = max(1, min(20, round(det_raw / 5)))
    return round((ambition + professionalism + determination) / 3)


# -- Background workers --------------------------------------------------------

# -- Player detail modal -------------------------------------------------------

def _attr_val_color(v: int) -> str:
    if v >= 17: return '#52C287'   # FM: green is best
    if v >= 16: return '#EAD95C'   # light yellow just below
    if v >= 13: return COLORS['accent_hover']
    if v >= 10: return COLORS['text_secondary']
    if v >= 7:  return COLORS['text_primary']
    return COLORS['non_hgp_red']


def _nation_cell(nid, default=''):
    """Flag emoji, else a short name, else the verified long name from fm_editor.nations, else default."""
    return _nation_flag(nid) or NATIONS.get(nid) or _nation_name_long(nid) or default


_STAFF_COL_TOOLTIPS = {
    'Age': 'Age', 'Club': 'Club',
    'Atk': 'Attacking', 'Def': 'Defending', 'Fit': 'Fitness',
    'Mnt': 'Mental',    'SPc': 'Set Pieces', 'Tac': 'Tactical',
    'Tch': 'Technical', 'WwY': 'Working with Youngsters',
    'Det': 'Determination', 'Mot': 'Motivating', 'PMg': 'People Management',
    'JPA': 'Judging Player Ability', 'JSA': 'Judging Staff Ability',
    'TKn': 'Tactical Knowledge',
    'Neg': 'Negotiating', 'GKH': 'GK Handling', 'GKS': 'GK Shot Stopping',
    'Adp': 'Adaptability', 'Amb': 'Ambition', 'Loy': 'Loyalty',
    'Prs': 'Pressure',    'Pro': 'Professionalism', 'Spt': 'Sportsmanship',
    'Tmp': 'Temperament', 'Ctr': 'Controversy',
}

_STAFF_COACHING_COLS = [
    'Atk', 'Def', 'Fit', 'Mnt', 'SPc', 'Tac', 'Tch', 'WwY',
    'Det', 'Mot', 'PMg',
    'JPA', 'JSA', 'TKn',
    'Neg', 'GKH', 'GKS',
]
_STAFF_COACHING_MAP = {
    'Atk': 'Attacking', 'Def': 'Defending', 'Fit': 'Fitness',
    'Mnt': 'Mental',    'SPc': 'Set Pieces', 'Tac': 'Tactical',
    'Tch': 'Technical', 'WwY': 'WwY',
    'Det': 'Determination', 'Mot': 'Motivating', 'PMg': 'People Mgt',
    'JPA': 'JPA',       'JSA': 'JSA',       'TKn': 'Tact Knowledge',
    'Neg': 'Negotiating', 'GKH': 'GK Handling', 'GKS': 'GK Shot Stop',
}
_STAFF_PERS_COLS = ['Adp', 'Amb', 'Loy', 'Prs', 'Pro', 'Spt', 'Tmp', 'Ctr']
_STAFF_COLS = ['Name', 'Club', 'Nation', 'Age'] + _STAFF_COACHING_COLS + _STAFF_PERS_COLS

# Position → (background, foreground) matching mockup color scheme
_POS_BADGE_COLORS = {
    'INJ': ('#8B1A1A', '#FFFFFF'),  # dark red injury badge
    'GK':  ('#C07B2A', '#FFFFFF'),
    'SW':  ('#3A6BA8', '#FFFFFF'),
    'DL':  ('#3A6BA8', '#FFFFFF'), 'DC': ('#3A6BA8', '#FFFFFF'),
    'DR':  ('#3A6BA8', '#FFFFFF'),
    'DM':  ('#5A3A8A', '#FFFFFF'),  # purple — distinct from DC blue
    'WBL': ('#3A6BA8', '#FFFFFF'), 'WBR': ('#3A6BA8', '#FFFFFF'),
    'ML':  ('#3A8A5A', '#FFFFFF'), 'MC': ('#3A8A5A', '#FFFFFF'),
    'MR':  ('#3A8A5A', '#FFFFFF'), 'AML': ('#3A8A5A', '#FFFFFF'),
    'AMC': ('#3A8A5A', '#FFFFFF'), 'AMR': ('#3A8A5A', '#FFFFFF'),
    'ST':  ('#A83A3A', '#FFFFFF'),
}

# Default sort order for position column (lower = higher in list)
_POS_SORT_ORDER = {
    'GK': 0,
    'DR': 1, 'WBR': 2, 'DL': 3, 'WBL': 4,
    'DC': 5, 'SW': 6,
    'DM': 7, 'MC': 8,
    'MR': 9, 'AMR': 10, 'ML': 11, 'AML': 12,
    'AMC': 13, 'ST': 14,
}

_MIN_POS_DEFAULT = 12   # Best by Role: min position familiarity (1-20) at any position the role is played from

_REPORT_ICONS = {'prospects': 'best_prospects', 'wonderkids': 'wonderkids', 'best_pos': 'best_in_position', 'best_role': 'best_by_role'}
_REPORT_LABELS = {
    'prospects': 'Best Prospects (PA 160+)',
    'wonderkids': 'Wonderkids (U21, PA 150+)',
    'best_pos':   'Best in Position',
    'best_role':  'Best by Role',
}


class _RowMarkDelegate(QStyledItemDelegate):
    """Default delegate of the player lists (the badge delegates build on it): a player with any queued edit
    (ROWQ_ROLE of the row's column 0) gets a faint yellow tint under every cell and a 3px yellow bar at the
    left edge of the Name cell. Painted here, not via BackgroundRole: the app QSS item rule ignores that."""
    def paint(self, painter, option, index):
        marked = bool(index.siblingAtColumn(0).data(ROWQ_ROLE))
        if marked:
            painter.fillRect(option.rect, ROW_TINT)
        super().paint(painter, option, index)
        if marked and index.column() == 0:
            painter.fillRect(option.rect.x(), option.rect.y(), 3, option.rect.height(), QColor(COLORS['queued']))


_AB_W_STARS, _AB_W_NUM = 76, 45   # CA / PA column width in the lists: 10 inset (= header text) + 5 stars (58) + 8 | the old number width


class StarsDelegate(_RowMarkDelegate):
    """CA / PA cell of the player lists as 5 stars (mockups/list-stars.html), composed on the row-mark delegate
    (tint, selection, queued bar come from it). The raw value is the cell's text (the number the table
    already shows; sorting uses the items' own raw sort key / PeopleModel key, never the stars). `stars_on` is the
    Settings > Ability display flag, set by MainWindow._apply_ui_prefs; Numbers mode (or a non-numeric cell such
    as '?' / '-') = the normal text cell, untouched. Stars mode adds the raw number as a tooltip ('CA 149')."""
    stars_on = True
    SIZE, GAP, INSET = 10, 2, 10

    def __init__(self, label, parent=None):
        super().__init__(parent)
        self._label = label

    def _raw(self, index):
        if not StarsDelegate.stars_on:
            return None
        t = index.data(Qt.ItemDataRole.DisplayRole)
        return int(t) if isinstance(t, str) and t.isdigit() else None

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if self._raw(index) is not None:
            option.text = ''   # the stars are the content

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        v = self._raw(index)
        if v is None:
            return
        pm = star_row_pixmap(ability_stars(v), self.SIZE, self.GAP, painter.device().devicePixelRatioF())
        r = option.rect
        painter.drawPixmap(r.x() + self.INSET, r.y() + (r.height() - self.SIZE) // 2, pm)

    def tip(self, index):
        v = self._raw(index)
        return None if v is None else f'{self._label} {v}'

    def helpEvent(self, event, view, option, index):
        if event.type() == QEvent.Type.ToolTip and self.tip(index):
            QToolTip.showText(event.globalPos(), self.tip(index), view)
            return True
        return super().helpEvent(event, view, option, index)

    def sizeHint(self, option, index):
        sh = super().sizeHint(option, index)
        return QSize(_AB_W_STARS, sh.height()) if self._raw(index) is not None else sh


def _ability_w():
    return _AB_W_STARS if StarsDelegate.stars_on else _AB_W_NUM


def _set_star_delegates(table, ca_col, pa_col):
    table.setItemDelegateForColumn(ca_col, StarsDelegate('CA', table))
    table.setItemDelegateForColumn(pa_col, StarsDelegate('PA', table))


class _PosBadgeDelegate(_RowMarkDelegate):
    def paint(self, painter, option, index):
        try:
            super().paint(painter, option, index)
            text = index.data(Qt.ItemDataRole.DisplayRole) or ''
            if not text or text == '?':
                return
            bg, fg = _POS_BADGE_COLORS.get(text, ('#2A2D35', COLORS['text_secondary']))
            painter.save()
            try:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                font = QFont(painter.font())
                font.setPixelSize(10)
                font.setBold(True)
                painter.setFont(font)
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(text)
                bw = tw + 10
                bh = 16
                x = option.rect.x() + 8
                y = option.rect.y() + (option.rect.height() - bh) // 2
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(bg))
                painter.drawRoundedRect(QRectF(x, y, bw, bh), 2, 2)
                painter.setPen(QColor(fg))
                painter.drawText(QRectF(x, y, bw, bh), Qt.AlignmentFlag.AlignCenter, text)
            finally:
                painter.restore()
        except Exception:
            import traceback
            traceback.print_exc()

    def sizeHint(self, option, index):
        try:
            return QSize(68, option.rect.height() or 28)
        except Exception:
            import traceback
            traceback.print_exc()
            return QSize(68, 28)


class _HGBadgeDelegate(_RowMarkDelegate):
    """HGP / HGC pill, same size and radius as the Pos badge. HG_ROLE: 'set' = green (HGP dark, HGC darker),
    'queued' = yellow outline + faint fill with a '+' prefix; anything else paints the cell normally (empty)."""
    def __init__(self, kind, parent=None):
        super().__init__(parent)
        self._kind = kind

    def paint(self, painter, option, index):
        try:
            state = index.data(HG_ROLE) or ''
            text = index.data(Qt.ItemDataRole.DisplayRole) or ''
            if state not in ('set', 'queued') or not text:
                super().paint(painter, option, index)
                return
            opt = QStyleOptionViewItem(option)
            self.initStyleOption(opt, index)
            opt.text = ''  # row background / selection only; the pill is the content
            if index.siblingAtColumn(0).data(ROWQ_ROLE):
                painter.fillRect(option.rect, ROW_TINT)
            style = opt.widget.style() if opt.widget else QApplication.style()
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)
            painter.save()
            try:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                font = QFont(painter.font())
                font.setPixelSize(10)
                font.setBold(True)
                painter.setFont(font)
                bw = painter.fontMetrics().horizontalAdvance(text) + 10
                bh = 16
                r = QRectF(option.rect.x() + 8, option.rect.y() + (option.rect.height() - bh) // 2, bw, bh)
                if state == 'set':
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(COLORS['hgp_badge' if self._kind == 'hgp' else 'hgc_badge']))
                    fg = QColor('#FFFFFF')
                else:
                    fg = QColor(COLORS['queued'])
                    painter.setPen(QPen(fg, 1))
                    painter.setBrush(QColor(234, 217, 92, 36))  # rgba(234,217,92,.14), as the player-window pill
                    r = r.adjusted(0.5, 0.5, -0.5, -0.5)
                painter.drawRoundedRect(r, 2, 2)
                painter.setPen(fg)
                painter.drawText(r, Qt.AlignmentFlag.AlignCenter, text)
            finally:
                painter.restore()
        except Exception:
            import traceback
            traceback.print_exc()

    def sizeHint(self, option, index):
        return QSize(62, option.rect.height() or 28)  # fits '+ HGP'


def _hg_apply(item, kind, set_, queued):
    """Style one QTableWidget HGP/HGC cell. set_ = value in the save (True / False / None unknown); the
    sort key puts set and queued first, then unset, then unknown (HGC of a player with no club)."""
    label = kind.upper()
    state = 'set' if set_ else 'queued' if queued else ''
    item.setData(HG_BASE_ROLE, set_)
    item.setData(HG_ROLE, state)
    item.setText(label if state == 'set' else f'+ {label}' if state else '?' if set_ is None else '')
    item._sk = 0 if state else 2 if set_ is None else 1
    item.setForeground(QColor(COLORS['text_dim']))
    item.setToolTip('Queued: written when you click Save Changes' if state == 'queued' else '')


def _queue_map(queue):
    qm = {}
    for pid, kind in queue:
        qm.setdefault(pid, set()).add(kind)
    return qm


def _mark_rows(table, qm, hg_cols):
    """QTableWidget: refresh HG cells (hg_cols: col -> kind) and mark (ROWQ_ROLE on col 0) the rows whose player
    (UserRole of col 0) has a queued edit. Tables here are small (squad / 200-row report / shortlist)."""
    rc = table.rowCount()
    if not rc:
        return
    was = table.isSortingEnabled()
    table.setSortingEnabled(False)
    try:
        for row in range(rc):
            it0 = table.item(row, 0)
            if it0 is None:
                continue
            kinds = qm.get(it0.data(Qt.ItemDataRole.UserRole), ())
            for col, kind in hg_cols.items():
                it = table.item(row, col)
                if it is not None:
                    _hg_apply(it, kind, it.data(HG_BASE_ROLE), kind in kinds)
            it0.setData(ROWQ_ROLE, bool(kinds))
    finally:
        table.setSortingEnabled(was)
    table.viewport().update()  # the tint is painted per cell by the delegates; only column 0's item changed


class StaffDetailDialog(QDialog):
    _PERS_LABELS = [
        ('Adaptability', 0), ('Ambition', 1), ('Loyalty', 2), ('Pressure', 3),
        ('Professionalism', 4), ('Sportsmanship', 5), ('Temperament', 6), ('Controversy', 7),
    ]

    def __init__(self, person, save_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(person.get('name', 'Staff'))
        self.setMinimumSize(680, 480)
        self.resize(780, 560)
        self._person = person
        self._save_data = save_data
        self._shortlist_added = False
        self._build()

    def _build(self):
        p = self._person
        nation_name = NATIONS.get(p.get('nation', 0), f"n={p.get('nation', 0)}")
        age = _age(p)
        personality = p.get('personality', [])

        # Resolve club name
        club_name = ''
        if self._save_data:
            clubs = self._save_data.get('clubs', [])
            club_by_id = {c['id']: c['name'] for c in clubs}
            club_by_entity = {c['id'] + 1: c['name'] for c in clubs}
            club_staff = self._save_data.get('club_staff', {})
            employment = self._save_data.get('employment', {})
            pid = p.get('id', -1)
            staff_club: dict[int, int] = {}
            for cid, pids in club_staff.items():
                for ppid in pids:
                    if ppid not in staff_club:
                        staff_club[ppid] = cid
            cid = staff_club.get(pid)
            if cid is not None:
                club_name = club_by_id.get(cid, '')
            else:
                entity_id = employment.get(pid)
                club_name = club_by_entity.get(entity_id, '') if entity_id else ''

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar
        topbar = QFrame()
        topbar.setFixedHeight(40)
        topbar.setObjectName('qfStrip')  # scoped: a bare QSS would leak the border onto child QLabels
        topbar.setStyleSheet(
            f"QFrame#qfStrip {{ background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']}; }}")
        tb_row = QHBoxLayout(topbar)
        tb_row.setContentsMargins(14, 0, 10, 0)
        tb_row.setSpacing(8)
        title_wrap = QWidget()
        title_wrap.setStyleSheet("background:transparent;")
        tw_vbox = QVBoxLayout(title_wrap)
        tw_vbox.setContentsMargins(0, 4, 0, 4)
        tw_vbox.setSpacing(0)
        name_lbl = QLabel(p.get('name', ''))
        name_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:14px; font-weight:bold;")
        sub_lbl = QLabel(f"{nation_name}  ·  Age {age}")
        sub_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        tw_vbox.addWidget(name_lbl)
        tw_vbox.addWidget(sub_lbl)
        tb_row.addWidget(title_wrap, 1)
        close_btn = QPushButton('✕')
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: none; border: none;
                color: {COLORS['text_dim']}; font-size: 16px; border-radius: 2px;
            }}
            QPushButton:hover {{ background: {COLORS['border']}; color: {COLORS['text_primary']}; }}
        """)
        close_btn.clicked.connect(self.accept)
        tb_row.addWidget(close_btn)
        layout.addWidget(topbar)

        # Body
        body = QWidget()
        body.setStyleSheet(f"background:{COLORS['window_bg']};")
        body_hbox = QHBoxLayout(body)
        body_hbox.setContentsMargins(0, 0, 0, 0)
        body_hbox.setSpacing(0)

        # Left panel
        left = QFrame()
        left.setFixedWidth(190)
        left.setStyleSheet(
            f"background:{COLORS['surface']}; border-right:1px solid {COLORS['border']};")
        left_vbox = QVBoxLayout(left)
        left_vbox.setContentsMargins(0, 0, 0, 0)
        left_vbox.setSpacing(0)

        photo = QFrame()
        photo.setFixedSize(190, 120)
        photo.setObjectName('qfStrip')  # scoped: a bare QSS would leak the border onto child QLabels
        photo.setStyleSheet(
            f"QFrame#qfStrip {{ background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']}; }}")
        photo_inner = QVBoxLayout(photo)
        photo_inner.setContentsMargins(0, 0, 0, 0)  # the face picture fills the 190x119 box
        photo_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_icon = QLabel()
        photo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        face = _faces_service().pixmap(p.get('uid'), 190, 119, self.devicePixelRatioF(), fit=True)  # whole picture, 119 = box - 1px border
        photo_icon.setPixmap(face if face is not None
                             else _svg_icon(_SVG_STAFF, COLORS['text_dim'], 48).pixmap(48, 48))
        photo_inner.addWidget(photo_icon)
        left_vbox.addWidget(photo)

        info_frame = QFrame()
        info_frame.setObjectName('qfStrip')  # scoped: a bare QSS would leak the border onto child QLabels
        info_frame.setStyleSheet(
            f"QFrame#qfStrip {{ border-bottom:1px solid {COLORS['border']}; background:transparent; }}")
        info_vbox = QVBoxLayout(info_frame)
        info_vbox.setContentsMargins(12, 8, 12, 8)
        info_vbox.setSpacing(0)

        def _info_row(label: str, value: str):
            row = QHBoxLayout()
            row.setContentsMargins(0, 3, 0, 3)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:11px;")
            val = QLabel(value)
            val.setStyleSheet(
                f"color:{COLORS['text_primary']}; font-size:11px; font-weight:500;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            return row

        if club_name:
            info_vbox.addLayout(_info_row('Club', club_name))
        info_vbox.addLayout(_info_row('Nation', nation_name))
        info_vbox.addLayout(_info_row('Age', str(age)))
        left_vbox.addWidget(info_frame)
        left_vbox.addStretch()
        body_hbox.addWidget(left)

        coaching = p.get('coaching', {})
        _COACHING_DISPLAY = {
            'WwY': 'Working w/ Youngsters', 'People Mgt': 'People Management',
            'JPA': 'Judging Player Ability', 'JSA': 'Judging Staff Ability',
            'Tact Knowledge': 'Tactical Knowledge', 'GK Shot Stop': 'GK Shot Stopping',
        }
        _COACHING_LEFT = [
            'Attacking', 'Defending', 'Fitness', 'Mental', 'Set Pieces',
            'Tactical', 'Technical', 'WwY', 'People Mgt',
        ]
        _COACHING_RIGHT = [
            'Determination', 'Motivating', 'JPA', 'JSA',
            'Tact Knowledge', 'Negotiating', 'GK Handling', 'GK Shot Stop',
        ]

        # Center: coaching + personality
        center_scroll = QScrollArea()
        center_scroll.setWidgetResizable(True)
        center_scroll.setStyleSheet(
            f"QScrollArea {{ border:none; background:{COLORS['window_bg']}; }}")
        center_w = QWidget()
        center_w.setStyleSheet(f"background:{COLORS['window_bg']};")
        center_vbox = QVBoxLayout(center_w)
        center_vbox.setContentsMargins(16, 16, 16, 16)
        center_vbox.setSpacing(8)

        def _section_title(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"color:{COLORS['text_dim']}; font-size:10px; letter-spacing:1px;"
                f"border-bottom:1px solid {COLORS['border']}; padding-bottom:4px; margin-bottom:2px;")
            return lbl

        def _attr_bar_row(label, v, label_w=150):
            row = QHBoxLayout()
            row.setSpacing(6)
            n = QLabel(label)
            n.setFixedWidth(label_w)
            n.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
            bar_bg = QFrame()
            bar_bg.setFixedHeight(4)
            bar_bg.setStyleSheet(f"background:{COLORS['border']}; border-radius:2px;")
            bar_fill = QFrame(bar_bg)
            bar_fill.setFixedHeight(4)
            bar_fill.setStyleSheet(f"background:{COLORS['accent']}; border-radius:2px;")
            bar_fill.setMaximumWidth(int(120 * v / 20))
            v_lbl = QLabel(str(v))
            v_lbl.setFixedWidth(24)
            v_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            v_lbl.setStyleSheet(
                f"color:{_attr_val_color(v)}; font-size:11px; font-weight:bold;")
            row.addWidget(n)
            row.addWidget(bar_bg, 1)
            row.addWidget(v_lbl)
            return row

        if coaching:
            center_vbox.addWidget(_section_title('COACHING ATTRIBUTES'))
            cols_w = QWidget()
            cols_w.setStyleSheet("background:transparent;")
            cols_hbox = QHBoxLayout(cols_w)
            cols_hbox.setContentsMargins(0, 0, 0, 0)
            cols_hbox.setSpacing(16)

            for col_keys in (_COACHING_LEFT, _COACHING_RIGHT):
                col_w = QWidget()
                col_w.setStyleSheet("background:transparent;")
                col_vbox = QVBoxLayout(col_w)
                col_vbox.setContentsMargins(0, 0, 0, 0)
                col_vbox.setSpacing(4)
                for key in col_keys:
                    v = coaching.get(key)
                    if v is None:
                        continue
                    display = _COACHING_DISPLAY.get(key, key)
                    col_vbox.addLayout(_attr_bar_row(display, v))
                col_vbox.addStretch()
                cols_hbox.addWidget(col_w, 1)

            center_vbox.addWidget(cols_w)

        staff_ca = p.get('staff_ca')
        staff_pa = p.get('staff_pa')
        if staff_ca is not None:
            center_vbox.addWidget(_section_title('ABILITY'))
            ab_row = QHBoxLayout()
            ab_row.setSpacing(24)
            for label, val in (('CA', staff_ca), ('PA', staff_pa)):
                pair = QHBoxLayout()
                pair.setSpacing(6)
                lbl = QLabel(label)
                lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:11px;")
                num = QLabel(str(val))
                num.setStyleSheet(
                    f"color:{_attr_val_color(round(val / 10))};"
                    f" font-size:13px; font-weight:bold;")
                pair.addWidget(lbl)
                pair.addWidget(num)
                ab_row.addLayout(pair)
            ab_row.addStretch()
            center_vbox.addLayout(ab_row)

        center_vbox.addWidget(_section_title('PERSONALITY'))
        if personality:
            for attr_name, idx in self._PERS_LABELS:
                v = personality[idx] if idx < len(personality) else 0
                center_vbox.addLayout(_attr_bar_row(attr_name, v))
        else:
            no_data = QLabel('No personality data available.')
            no_data.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:11px;")
            center_vbox.addWidget(no_data)

        center_vbox.addStretch()

        # Action strip
        action_frame = QFrame()
        action_frame.setObjectName('qfStrip')  # scoped: a bare QSS would leak the border onto child QLabels
        action_frame.setStyleSheet(
            f"QFrame#qfStrip {{ border-top:1px solid {COLORS['border']}; background:transparent; }}")
        action_row = QHBoxLayout(action_frame)
        action_row.setContentsMargins(0, 8, 0, 4)
        action_row.addStretch()
        _btn_ss = f"""
            QPushButton {{
                background:{COLORS['accent']}; color:#fff; border:none;
                padding:6px 16px; font-weight:bold; border-radius:2px; font-size:11px;
            }}
            QPushButton:hover {{ background:{COLORS['accent_hover']}; }}
            QPushButton:pressed {{ background:{COLORS['accent_press']}; }}
        """
        add_btn = QPushButton('Add to Shortlist')
        add_btn.setStyleSheet(_btn_ss)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(lambda checked=False: self._do_add_shortlist())
        action_row.addWidget(add_btn)
        center_vbox.addWidget(action_frame)

        center_scroll.setWidget(center_w)
        body_hbox.addWidget(center_scroll, 1)
        layout.addWidget(body)

    def _do_add_shortlist(self):
        self._shortlist_added = True
        self.accept()


# -- Role attribute names for weight editor ------------------------------------

# Short column labels for the squad table (54 attrs, same order as raw_attrs)
_ATTR_ABBREV = [
    'Cro', 'Dri', 'Fin', 'Hea', 'Lsh', 'Mar', 'OtB', 'Pas', 'Pen', 'Tck', 'Vis', 'Han',
    'AeR', 'CoA', 'Com', 'Kic', 'Thr', 'Ant', 'Dec', '1v1', 'Psn', 'Ref', 'Fir', 'Tec',
    'LFo', 'RFo', 'Fla', 'Cor', 'Tea', 'Wor', 'LTh', 'Ecc', 'RuO', 'Pun', 'Acc', 'FK',
    'Str', 'Sta', 'Pac', 'JR',  'Lea', 'Dir', 'Bal', 'Bra', 'Con', 'Agg', 'Agi', 'BM',
    'IP',  'Ver', 'NF',  'Det', 'Cmp', 'Cnc',
]

_ATTR_DISPLAY = [
    'Crossing', 'Dribbling', 'Finishing', 'Heading', 'Long Shots', 'Marking',
    'Off The Ball', 'Passing', 'Penalties', 'Tackling', 'Vision', 'Handling',
    'Aerial Reach', 'Cmd of Area', 'Communication', 'Kicking', 'Throwing',
    'Anticipation', 'Decisions', 'One on Ones', 'Positioning', 'Reflexes',
    'First Touch', 'Technique', 'Left Foot', 'Right Foot', 'Flair', 'Corners',
    'Teamwork', 'Work Rate', 'Long Throws', 'Eccentricity', 'Rushing Out',
    'Punching', 'Acceleration', 'Free Kick', 'Strength', 'Stamina', 'Pace',
    'Jumping Reach', 'Leadership', 'Dirtiness', 'Balance', 'Bravery',
    'Consistency', 'Aggression', 'Agility', 'Big Matches', 'Injury Prone',
    'Versatility', 'Natural Fitness', 'Determination', 'Composure', 'Concentration',
]

_DIALOG_SS = lambda: f"""
    QDialog {{
        background: {COLORS['window_bg']};
        color: {COLORS['text_primary']};
    }}
    QLabel {{
        color: {COLORS['text_primary']};
        background: transparent;
    }}
    QComboBox, QSpinBox {{
        background: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 2px;
        padding: 2px 6px;
        min-height: 24px;
    }}
    QComboBox::drop-down {{ border: none; }}
    QComboBox QAbstractItemView {{
        background: {COLORS['elevated']};
        color: {COLORS['text_primary']};
        selection-background-color: {COLORS['selection_bg']};
        border: 1px solid {COLORS['border_bright']};
    }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{
        background: {COLORS['surface']}; width: 6px; border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['border_bright']}; border-radius: 3px; min-height: 20px;
    }}
"""

_BTN_SS = lambda accent=False: (
    f"QPushButton {{ background: {COLORS['accent'] if accent else COLORS['surface']};"
    f" color: {'#fff' if accent else COLORS['text_primary']};"
    f" border: {'none' if accent else '1px solid ' + COLORS['border']};"
    f" border-radius: 3px; padding: 5px 14px; font-size: 12px; }}"
    f"QPushButton:hover {{ background: {COLORS['accent'] if accent else COLORS['selection_bg']}; }}"
    f"QPushButton:disabled {{ background: {COLORS['elevated']}; color: {COLORS['text_dim']}; border: 1px solid {COLORS['border']}; }}"
)


# -- Weight editor dialog -------------------------------------------------------

class WeightEditorDialog(QDialog):
    """Edit per-role attribute weights. Operates on a mutable copy of a preset."""

    def __init__(self, base_preset: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Role Weight Editor')
        self.setMinimumSize(520, 580)
        self.setStyleSheet(_DIALOG_SS())
        self._edited: dict[str, dict[int, int]] = {
            role: dict(w) for role, w in base_preset.get('roles', {}).items()
        }
        self._current_role = None
        self._spinboxes: dict[int, QSpinBox] = {}
        self._saved_preset_path: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Role selector
        top = QHBoxLayout()
        top.setSpacing(8)
        top.addWidget(QLabel('Role:'))
        self._role_combo = QComboBox()
        self._role_combo.setFixedWidth(260)
        for group, names in role_names_by_group():
            sep = self._role_combo.count()
            self._role_combo.addItem(f'── {group} ──')
            self._role_combo.model().item(sep).setEnabled(False)
            for name in names:
                self._role_combo.addItem(name)
        self._role_combo.setCurrentIndex(1)
        top.addWidget(self._role_combo)
        top.addStretch()
        layout.addLayout(top)

        # Info label
        self._info_lbl = QLabel('Zero = attribute not used for this role.')
        self._info_lbl.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:11px;")
        layout.addWidget(self._info_lbl)

        # Attr list scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner.setStyleSheet(f"background:{COLORS['surface']}; border-radius:3px;")
        self._attr_layout = QVBoxLayout(inner)
        self._attr_layout.setContentsMargins(10, 8, 10, 8)
        self._attr_layout.setSpacing(4)
        scroll.setWidget(inner)
        layout.addWidget(scroll, 1)

        # Buttons
        btns = QHBoxLayout()
        btns.setSpacing(8)
        reset_btn = QPushButton('Reset Role')
        reset_btn.setStyleSheet(_BTN_SS())
        reset_btn.clicked.connect(self._reset_current_role)
        btns.addWidget(reset_btn)
        btns.addStretch()
        cancel_btn = QPushButton('Cancel')
        cancel_btn.setStyleSheet(_BTN_SS())
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        save_btn = QPushButton('Save as New Preset…')
        save_btn.setStyleSheet(_BTN_SS(accent=True))
        save_btn.clicked.connect(self._save_as)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

        self._role_combo.currentTextChanged.connect(self._on_role_changed)
        self._on_role_changed(self._role_combo.currentText())

    def _on_role_changed(self, role_name: str):
        if not role_name or role_name.startswith('──'):
            return
        self._flush_current()
        self._current_role = role_name

        # Clear old spinboxes
        while self._attr_layout.count():
            item = self._attr_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._spinboxes.clear()

        key_indices = set(_ROLE_INDEX.get(role_name, ()))
        current_weights = self._edited.get(role_name, {})

        for idx, name in enumerate(_ATTR_DISPLAY):
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl = QLabel(name)
            lbl.setFixedWidth(140)
            lbl.setStyleSheet(
                f"color:{COLORS['text_primary'] if idx in key_indices else COLORS['text_dim']};"
                f"font-size:12px;")
            row.addWidget(lbl)
            spin = QSpinBox()
            spin.setRange(0, 20)
            spin.setFixedWidth(55)
            spin.setValue(current_weights.get(idx, 0))
            spin.setStyleSheet(
                f"QSpinBox {{ background:{COLORS['elevated']};"
                f" color:{COLORS['text_primary']}; border:1px solid {COLORS['border']};"
                f" border-radius:2px; padding:1px 4px; font-size:12px; }}")
            row.addWidget(spin)
            if idx in key_indices:
                kw_lbl = QLabel('key attr')
                kw_lbl.setStyleSheet(f"color:{COLORS['accent']}; font-size:10px;")
                row.addWidget(kw_lbl)
            row.addStretch()
            container = QWidget()
            container.setLayout(row)
            self._attr_layout.addWidget(container)
            self._spinboxes[idx] = spin

        self._attr_layout.addStretch()

    def _flush_current(self):
        if self._current_role and self._spinboxes:
            self._edited[self._current_role] = {
                idx: spin.value() for idx, spin in self._spinboxes.items()
                if spin.value() > 0
            }

    def _reset_current_role(self):
        if not self._current_role:
            return
        # Restore equal-weight defaults from key_indices
        key_indices = _ROLE_INDEX.get(self._current_role, ())
        for idx, spin in self._spinboxes.items():
            spin.setValue(10 if idx in key_indices else 0)

    def _save_as(self):
        self._flush_current()
        name, ok = QInputDialog.getText(self, 'Save Preset', 'Preset name:')
        if not ok or not name.strip():
            return
        name = name.strip()
        desc, ok2 = QInputDialog.getText(self, 'Save Preset', 'Description (optional):')
        if not ok2:
            return
        path = _weights_mod.save_custom_preset(name, desc.strip(), self._edited)
        self._saved_preset_path = path
        self.accept()

    def saved_preset_name(self) -> str | None:
        if not self._saved_preset_path:
            return None
        try:
            import json
            with open(self._saved_preset_path, encoding='utf-8') as f:
                return json.load(f).get('name')
        except Exception:
            return None


# -- Hero header widget --------------------------------------------------------

# Welcome-hero "loading glow": the grid lines pulse while the first load runs (all tunables here).
HERO_GLOW = dict(
    period_ms=3400,         # one slow, smooth pulse
    peak_alpha=0.10,        # painter opacity of the glow layers at full intensity: subtle
    tint=(150, 130, 255),   # lilac, between COLORS['accent_hover'] and the progress-bar shimmer peak
    halo_gain=0.40,         # wide soft halo strength relative to the core line
    halo_widths=(14, 7),    # halo stroke widths (px); the core line is the grid's own 2 px
    floor=0.35,             # intensity at the bottom of the pulse (the glow never fully dies while loading)
    depth=0.65,             # intensity added at the top of each pulse (floor + depth = 1.0)
    fade_in_ms=900,         # ease in from 0 when the load starts
    fade_ms=350,            # ease out when the load ends (the bar reached 100 %)
    delay_ms=800,           # a load that ends sooner than this never glows; a ~2 s cached load gets a short, gentle pulse
    fps_ms=16,              # ~60 fps timer: smooth
)


def _smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


class _HeaderHeroWidget(QWidget):
    """140px header bar painted with dark base + stadium image + gradient + pitch-line texture."""

    _PAGE_IMAGE = {
        'welcome':    'welcome.webp',
        'club':       'stadium.webp',
        'squad':      'squad.webp',
        'staff':      'staff.webp',
        'shortlist':  'shortlist.webp',
        'staff_shortlist': 'staff_shortlist.webp',
        'reports':    'reports.webp',
        'players':    'players.webp',
        'club_staff': 'club_staff.webp',
        'settings':   'settings.webp',
        'save_info':  'save_info.webp',
        'prospects':  'prospects.webp',
        'wonderkids': 'wonderkids.webp',
        'best_pos':   'best_pos.webp',
        'best_role':  'best_role.webp',
    }
    _FALLBACK = 'stadium.webp'

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap_cache = {}
        self._bg_pixmap = self._load('welcome.webp')
        self._page = 'welcome'
        self._g_state = 'off'    # 'off' | 'wait' (load started, glow not yet) | 'run' (glowing) | 'end' (fade out)
        self._g_t = 0.0          # ms since the glow started
        self._g_end_t = 0.0      # ms since the finish began
        self._g_from = 0.0       # intensity when the finish began (the fade eases from here: no jump)
        self._g_cache = None     # ((w, h, dpr), core, halo)
        self._g_clock = QElapsedTimer()
        self._g_timer = QTimer(self)
        self._g_timer.setInterval(HERO_GLOW['fps_ms'])
        self._g_timer.timeout.connect(self._glow_timer_tick)
        self._g_delay = QTimer(self)
        self._g_delay.setSingleShot(True)
        self._g_delay.setInterval(HERO_GLOW['delay_ms'])
        self._g_delay.timeout.connect(self._glow_begin)
        self.setFixedHeight(186)

    def _load(self, filename):
        import os as _os
        if filename in self._pixmap_cache:
            return self._pixmap_cache[filename]
        assets = _os.path.join(_os.path.dirname(__file__), 'assets')
        path = _os.path.join(assets, filename)
        if not _os.path.exists(path):
            path = _os.path.join(assets, self._FALLBACK)
        if not _os.path.exists(path):
            return None
        reader = QImageReader(path)
        img = reader.read()
        px = QPixmap.fromImage(img) if not img.isNull() else QPixmap(path)
        self._pixmap_cache[filename] = px
        return px

    def set_page(self, key: str):
        self._page = key
        if key != 'welcome' and self._g_state != 'off':
            self.glow_stop()   # never leak onto the page the load lands on
        filename = self._PAGE_IMAGE.get(key, self._FALLBACK)
        self._bg_pixmap = self._load(filename)
        self.update()

    def set_bg(self, pixmap):
        self._bg_pixmap = pixmap
        self.update()

    @staticmethod
    def _grid_lines(w, h):
        """The pitch-texture grid (mockup ::before): single source for the faint texture AND the glow mask."""
        return ([(x, 0, x, h) for x in range(38, w, 40)] + [(0, y, w, y) for y in range(58, h, 60)])

    # -- loading glow (Welcome page, first load only) ----------------------------

    def glow_start(self):
        """First load began (Welcome hero only; the caller says nothing about veils). The glow itself starts after
        `delay_ms`, so a sub-second load never glows and a ~2 s cached load gets a short, gentle pulse."""
        if self._page != 'welcome':
            return
        self._g_state = 'wait'
        self._g_delay.start()

    def _glow_begin(self):
        if self._g_state == 'wait':
            self._g_state, self._g_t = 'run', 0.0
            self._glow_timer_resume()

    def glow_finish(self):
        """Load ended (the bar is done): ease from the current intensity down to 0, then stop."""
        if self._g_state == 'wait':      # load ended before the glow began: nothing to show
            self.glow_stop()
            return
        if self._g_state != 'run':
            return
        self._g_from = self.glow_intensity()
        self._g_end_t = 0.0
        self._g_state = 'end'
        self._glow_timer_resume()

    def glow_stop(self):
        self._g_state, self._g_t, self._g_end_t = 'off', 0.0, 0.0
        self._g_delay.stop()
        self._g_timer.stop()
        self.update()

    def glow_active(self):
        return self._g_state != 'off'

    def _glow_timer_resume(self):
        self._g_clock.start()
        if self.isVisible():
            self._g_timer.start()
        self.update()

    def glow_intensity(self):
        """0..1 glow strength now (pure function of state; the paint opacity is peak_alpha * this)."""
        g = HERO_GLOW
        if self._g_state == 'run':
            pulse = 0.5 - 0.5 * math.cos(2 * math.pi * self._g_t / g['period_ms'])  # 0 at t=0: starts at a trough
            return (g['floor'] + g['depth'] * pulse) * _smooth(self._g_t / g['fade_in_ms'])
        if self._g_state == 'end':
            return self._g_from * (1.0 - _smooth(self._g_end_t / g['fade_ms']))
        return 0.0

    def glow_step(self, dt_ms):
        """Advance the animation by dt_ms; stops the timer when finished (no idle cost)."""
        if self._g_state == 'run':
            self._g_t += dt_ms
        elif self._g_state == 'end':
            self._g_end_t += dt_ms
            g = HERO_GLOW
            if self._g_end_t >= g['fade_ms']:
                self.glow_stop()
                return
        self.update()

    def _glow_timer_tick(self):
        if not self.isVisible():     # minimised / hidden: stop burning cycles; showEvent resumes
            self._g_timer.stop()
            return
        self.glow_step(self._g_clock.restart())

    def showEvent(self, e):
        super().showEvent(e)
        if self._g_state in ('run', 'end'):
            self._glow_timer_resume()

    def hideEvent(self, e):
        super().hideEvent(e)
        self._g_timer.stop()

    def _glow_layers(self):
        """Core + halo pixmaps: the grid itself drawn in the tint (cached per size). This IS the line mask."""
        w, h, dpr = self.width(), self.height(), self.devicePixelRatioF()
        if self._g_cache and self._g_cache[0] == (w, h, dpr):
            return self._g_cache[1], self._g_cache[2]
        g = HERO_GLOW
        lines = self._grid_lines(w, h)

        def layer(strokes):
            px = QPixmap(round(w * dpr), round(h * dpr))
            px.setDevicePixelRatio(dpr)
            px.fill(Qt.GlobalColor.transparent)
            q = QPainter(px)
            for width, a in strokes:
                c = QColor(*g['tint'], round(255 * a))
                q.setPen(QPen(c, width))
                for ln in lines:
                    q.drawLine(*ln)
            q.end()
            return px

        core = layer([(2, 1.0)])
        n = len(g['halo_widths'])
        halo = layer([(wd, 0.35 * (i + 1) / n) for i, wd in enumerate(g['halo_widths'])])
        self._g_cache = ((w, h, dpr), core, halo)
        return core, halo

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()

        # 1. Base: diagonal gradient matching mockup .a-hero background
        # linear-gradient(135deg, #0d1f35 0%, #0f2a1a 50%, #1a1208 100%)
        base_grad = QLinearGradient(0, 0, w, h)
        base_grad.setColorAt(0.00, QColor(0x0d, 0x1f, 0x35))
        base_grad.setColorAt(0.50, QColor(0x0f, 0x2a, 0x1a))
        base_grad.setColorAt(1.00, QColor(0x1a, 0x12, 0x08))
        p.fillRect(0, 0, w, h, QBrush(base_grad))

        # 2. Stadium image at 38% opacity (mockup .a-hero-bg, z-index auto — lowest)
        if self._bg_pixmap and not self._bg_pixmap.isNull():
            p.setOpacity(0.38)
            scaled = self._bg_pixmap.scaled(
                w, h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            x_off = (w - scaled.width()) // 2
            y_off = int((h - scaled.height()) * 0.40)
            p.drawPixmap(x_off, y_off, scaled)
            p.setOpacity(1.0)

        # 3. Dark vignette ON TOP of image (mockup .a-hero-overlay, z-index 1)
        # rgba(8,12,18,0.30) 0%, rgba(8,12,18,0.55) 55%, rgba(8,12,18,0.90) 100%
        overlay = QLinearGradient(0, 0, 0, h)
        overlay.setColorAt(0.00, QColor(8, 12, 18, 77))
        overlay.setColorAt(0.55, QColor(8, 12, 18, 140))
        overlay.setColorAt(1.00, QColor(8, 12, 18, 230))
        p.fillRect(0, 0, w, h, QBrush(overlay))

        # 4. Pitch texture — from mockup ::before:
        # Vertical lines: repeating every 40px, 2px wide, alpha ~4 (0.016*255)
        # Horizontal lines: repeating every 60px, 2px wide, alpha ~4
        pen = QPen(QColor(255, 255, 255, 4))
        pen.setWidth(2)
        p.setPen(pen)
        for ln in self._grid_lines(w, h):
            p.drawLine(*ln)

        # 4b. Loading glow on those same grid lines (additive, behind the title labels)
        if self._g_state != 'off':
            v = self.glow_intensity()
            if v > 0.001:
                core, halo = self._glow_layers()
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
                p.setOpacity(HERO_GLOW['peak_alpha'] * v * HERO_GLOW['halo_gain'])
                p.drawPixmap(0, 0, halo)
                p.setOpacity(HERO_GLOW['peak_alpha'] * v)
                p.drawPixmap(0, 0, core)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                p.setOpacity(1.0)

        # 5. Bottom border
        p.setPen(QColor(255, 255, 255, 15))
        p.drawLine(0, h - 1, w, h - 1)

        p.end()


# -- Search autocomplete -------------------------------------------------------

# -- Main window ---------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FM Backroom 24')
        self.setMinimumSize(1000, 660)
        self.resize(1200, 780)

        self._save_data = None
        self._dirty = False  # queued changes not yet written with Save Changes (== bool(self._queue))
        self._pending = []  # human-readable list of unsaved edits (for the Save / discard prompts)
        self._queue = {}  # queued homegrown changes: (person id, 'hgp'|'hgc') -> person dict; NEVER touches game_db bytes
        self._pw_open = None  # the open player window (told when the queue changes)
        self._last_applied = (0, 0)  # (HGP, HGC) edits the last Save Changes actually wrote
        self._after_save = None  # callback run once Save Changes succeeds (load-another / close)
        self._after_reload_status = None  # one-shot status text shown once the post-save reload finishes
        self._ui_snap = None  # _capture_ui_state() taken when a reload starts, applied once it finishes
        self._busy = False  # True from _set_busy(True) to _set_busy(False): Save / Reload / Load / Back / Forward / Settings locked
        self._squad = []
        self._club_first_team = []  # first-team squad of the Club page (self._squad follows the tab)
        self._worker = None
        self._current_club = None
        self._hdr_key = None        # view key of the current page header (re-applied when club badges become available)
        self._header_club = None    # club whose badge the page header circle shows (None = the page icon)
        _faces_service().ready.connect(self._refresh_badges)
        self._shortlist = []        # players only
        self._staff_shortlist = []  # staff only
        self._status_base = ''
        self._veil_word = None   # 'Saving' | 'Reloading' while the busy veil is up
        self._dot_phase = -1
        self._table_mode = 'squad'
        self._current_report_key = ''
        self._report_ratings = {}
        self._active_preset = _weights_mod.load_active_preset()
        self._apply_ui_prefs()  # Settings > Show PENDING markers, before any chip is created

        self._dot_timer = QTimer(self)
        self._dot_timer.setInterval(420)
        self._dot_timer.timeout.connect(self._tick_dots)

        self._shimmer_phase = 0.0
        self._progress_target = 0.0
        self._progress_displayed = 0.0
        self._shimmer_timer = QTimer(self)
        self._shimmer_timer.setInterval(30)
        self._shimmer_timer.timeout.connect(self._tick_shimmer)

        self._build_ui()
        self._update_ui_state()
        self._main_stack.setCurrentIndex(self._VIEW_INDEX['welcome'])
        self._set_header('FM Backroom 24', 'Load a save to begin')

    # -- UI construction -------------------------------------------------------

    def _make_hline(self):
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background:{COLORS['border']};")
        return line

    def _make_nav_btn(self, svg_tpl: str, label: str, callback) -> QPushButton:
        btn = QPushButton(f'  {label}')
        btn.setCheckable(True)
        btn.setIcon(_svg_icon(svg_tpl, COLORS['text_secondary'], 15))
        btn.setIconSize(QSize(15, 15))
        btn.clicked.connect(callback)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-left: 3px solid transparent;
                color: {COLORS['text_secondary']};
                text-align: left;
                padding: 7px 15px 7px 12px;
                font-size: 12px;
                border-radius: 0;
            }}
            QPushButton:hover {{
                background: {COLORS['elevated']};
                color: {COLORS['text_primary']};
                border-left: 3px solid {COLORS['border_bright']};
            }}
            QPushButton:checked {{
                background: {COLORS['selection_bg']};
                color: {COLORS['text_primary']};
                font-weight: bold;
                border-left: 3px solid {COLORS['accent']};
            }}
            QPushButton:disabled {{
                color: {COLORS['text_dim']};
                background: transparent;
                border-left: 3px solid transparent;
            }}
        """)
        return btn

    def _make_section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:10px; font-weight:600; "
            "letter-spacing:1.2px; padding:10px 15px 3px;"
        )
        return lbl

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_hbox = QHBoxLayout(root)
        root_hbox.setContentsMargins(0, 0, 0, 0)
        root_hbox.setSpacing(0)

        # Sidebar spans full window height
        root_hbox.addWidget(self._make_sidebar())

        # Right side: topbar + progress + content
        right = QWidget()
        right_vbox = QVBoxLayout(right)
        right_vbox.setContentsMargins(0, 0, 0, 0)
        right_vbox.setSpacing(0)

        self._progress = QProgressBar()
        self._progress.setRange(0, 10000)
        self._progress.setValue(0)
        self._progress.setFixedHeight(3)
        self._progress.setTextVisible(False)
        self._progress.setVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{ background: rgba(255,255,255,0.08); border:none; }}
            QProgressBar::chunk {{ background:{COLORS['accent']}; }}
        """)
        self._hero = self._make_header_bar()
        right_vbox.addWidget(self._hero)
        right_vbox.addWidget(self._progress)

        self._main_stack = QStackedWidget()
        self._main_stack.addWidget(self._make_view_club())        # 0
        self._main_stack.addWidget(self._make_view_squad())       # 1
        self._main_stack.addWidget(self._make_view_staff())       # 2
        self._main_stack.addWidget(self._make_view_shortlist())   # 3
        self._main_stack.addWidget(self._make_view_reports())     # 4
        self._main_stack.addWidget(self._make_view_players())     # 5
        self._main_stack.addWidget(self._make_view_club_staff())  # 6
        self._main_stack.addWidget(self._make_view_welcome())     # 7
        self._main_stack.addWidget(self._make_view_save_info())   # 8
        self._main_stack.addWidget(self._make_view_staff_shortlist())  # 9
        self._settings_page = SettingsPage()
        self._settings_page.saved.connect(self._on_settings_saved)
        self._settings_page.message.connect(lambda m: self._status.showMessage(m, 4000))
        self._main_stack.addWidget(self._settings_page)           # 10
        right_vbox.addWidget(self._main_stack)
        self._busy_veil = _BusyVeil(self._main_stack)

        self._status = QStatusBar()
        self._status.setSizeGripEnabled(False)
        self._status_ready_lbl = QLabel('Open an FM24 save file to get started.')
        self._status_ready_lbl.setTextFormat(Qt.TextFormat.RichText)
        self._status_ready_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        self._status.addWidget(self._status_ready_lbl, 1)
        self._status_info_lbl = QLabel('')
        self._status_info_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._status_info_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px; padding-right:8px;")
        self._status.addPermanentWidget(self._status_info_lbl)
        right_vbox.addWidget(self._status)
        root_hbox.addWidget(right)
        self.statusBar().hide()
        self._save_path = None

    # -- Persistent header bar ------------------------------------------------

    def _make_header_bar(self):
        hero = _HeaderHeroWidget()

        # Outer VBox: nav row at top, stretch, content strip at bottom
        outer = QVBoxLayout(hero)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Nav row (absorbed from _make_topbar)
        nav_row = QHBoxLayout()
        nav_row.setContentsMargins(8, 6, 12, 0)
        nav_row.setSpacing(6)

        _nav_ss = """
            QPushButton {
                background: transparent; border: none;
                color: rgba(255,255,255,0.55); font-size: 13px;
                padding: 4px 6px; border-radius: 2px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.10); color: rgba(255,255,255,0.85); }
            QPushButton:disabled { color: rgba(255,255,255,0.20); }
        """
        self._back_btn = QPushButton('◀')
        self._back_btn.setFixedSize(26, 26)
        self._back_btn.setEnabled(False)
        self._back_btn.setStyleSheet(_nav_ss)
        self._back_btn.clicked.connect(self._nav_back)
        self._fwd_btn = QPushButton('▶')
        self._fwd_btn.setFixedSize(26, 26)
        self._fwd_btn.setEnabled(False)
        self._fwd_btn.setStyleSheet(_nav_ss)
        self._fwd_btn.clicked.connect(self._nav_fwd)
        self._nav_history: list[tuple] = []
        self._nav_pos: int = -1

        self._breadcrumb = QLabel('FM Backroom 24')
        self._breadcrumb.setStyleSheet(
            "color: rgba(255,255,255,0.55); font-size:12px; background:transparent;")

        nav_row.addWidget(self._back_btn)
        nav_row.addWidget(self._fwd_btn)

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText('Search clubs, players or staff...')
        self._search_box.setEnabled(False)
        self._search_box.returnPressed.connect(self._do_search)
        self._search_box.setFixedHeight(26)
        self._search_box.setMaximumWidth(16777215)
        self._search_box.setStyleSheet("""
            QLineEdit {
                background: rgba(8,14,24,0.60);
                border: 1px solid rgba(255,255,255,0.22);
                border-radius: 2px;
                padding: 4px 10px;
                font-size: 12px;
                color: rgba(255,255,255,0.90);
            }
            QLineEdit:focus { border-color: rgba(255,255,255,0.45); background: rgba(8,14,24,0.80); }
            QLineEdit:disabled { color: rgba(255,255,255,0.18); border-color: rgba(255,255,255,0.06);
                                 background: rgba(8,14,24,0.45); }
        """)
        # SVG icons for nav — must use hex (QSvgRenderer doesn't support rgba in attributes)
        def _nav_icon(svg_tpl, size=13):
            """QIcon with distinct normal (#B8C8D8) and disabled (#3A4A58) states."""
            icon = QIcon()
            nm = _svg_icon(svg_tpl, '#B8C8D8', size)
            dis = _svg_icon(svg_tpl, '#3A4A58', size)
            icon.addPixmap(nm.pixmap(size, size), QIcon.Mode.Normal)
            icon.addPixmap(dis.pixmap(size, size), QIcon.Mode.Disabled)
            return icon

        search_action = QAction(_nav_icon(_SVG_SEARCH, 14), '', self._search_box)
        self._search_box.addAction(search_action, QLineEdit.ActionPosition.LeadingPosition)
        nav_row.addWidget(self._search_box, 1)
        # autocomplete: >=3 chars, debounced; index built lazily per loaded save
        self._sg_idx = None
        self._report_timer = QTimer(self)
        self._report_timer.setSingleShot(True)
        self._report_timer.setInterval(150)
        self._report_timer.timeout.connect(self._apply_report_filters)
        self._sg_timer = QTimer(self)
        self._sg_timer.setSingleShot(True)
        self._sg_timer.setInterval(130)
        self._sg_timer.timeout.connect(self._sg_refresh)
        self._sg_popup = _SearchSuggest(self, self._search_box, self._sg_pick, self._sg_flush)
        self._search_box.textChanged.connect(self._sg_text_changed)

        _tbtn_accent_ss = (
            "QPushButton { background: #2b6cb0; color: #fff;"
            " border: none; border-radius: 2px;"
            " padding: 3px 10px; font-size: 11px; font-weight: 600; }"
            "QPushButton:hover { background: #3182ce; }"
            "QPushButton:pressed { background: #2c5282; }"
            "QPushButton:disabled { background: rgba(8,14,24,0.55); color: rgba(255,255,255,0.22);"
            " border: 1px solid rgba(255,255,255,0.08); font-weight: normal; }"
        )
        _tbtn_save_ss = (
            "QPushButton { background: #1a3d28; color: rgba(255,255,255,0.85);"
            " border: 1px solid rgba(80,160,100,0.30); border-radius: 2px;"
            " padding: 3px 10px; font-size: 11px; font-weight: 600; }"
            "QPushButton:hover { background: #1f4d32; border-color: rgba(80,160,100,0.50); color: #fff; }"
            "QPushButton:pressed { background: #142e1e; }"
            "QPushButton:disabled { background: rgba(8,14,24,0.55); color: rgba(255,255,255,0.22);"
            " border: 1px solid rgba(255,255,255,0.08); font-weight: normal; }"
        )
        _tbtn_reload_ss = (
            "QPushButton { background: #3a2608; color: rgba(255,255,255,0.85);"
            " border: 1px solid rgba(160,110,40,0.30); border-radius: 2px;"
            " padding: 3px 10px; font-size: 11px; font-weight: 600; }"
            "QPushButton:hover { background: #4a3010; border-color: rgba(160,110,40,0.50); color: #fff; }"
            "QPushButton:pressed { background: #2a1c06; }"
            "QPushButton:disabled { background: rgba(8,14,24,0.55); color: rgba(255,255,255,0.22);"
            " border: 1px solid rgba(255,255,255,0.08); font-weight: normal; }"
        )

        self._save_btn = QPushButton('Save Changes')
        self._save_btn.setFixedHeight(26)
        self._save_btn.setEnabled(False)
        self._save_btn.setToolTip('Write your edits to the save: backs up the current file (bk1, bk2), then overwrites it in place')
        _save_icon = QIcon()
        _save_icon.addPixmap(_svg_icon(_SVG_SAVE, '#ffffff', 13).pixmap(13, 13), QIcon.Mode.Normal)
        _save_icon.addPixmap(_svg_icon(_SVG_SAVE, '#3A4A58', 13).pixmap(13, 13), QIcon.Mode.Disabled)
        self._save_btn.setIcon(_save_icon)
        self._save_btn.setIconSize(QSize(13, 13))
        self._save_btn.setStyleSheet(_tbtn_save_ss)
        self._save_btn.clicked.connect(self._do_save)

        self._load_btn = QPushButton('Load')
        self._load_btn.setFixedHeight(26)
        self._load_btn.setObjectName('accent')
        self._load_btn.setToolTip('Open an FM24 save file')
        _load_icon = QIcon()
        _load_icon.addPixmap(_svg_icon(_SVG_LOAD, '#ffffff', 13).pixmap(13, 13), QIcon.Mode.Normal)
        _load_icon.addPixmap(_svg_icon(_SVG_LOAD, '#3A4A58', 13).pixmap(13, 13), QIcon.Mode.Disabled)
        self._load_btn.setIcon(_load_icon)
        self._load_btn.setIconSize(QSize(13, 13))
        self._load_btn.setStyleSheet(_tbtn_accent_ss)
        self._load_btn.clicked.connect(self._load_file)

        self._reload_btn = QPushButton('Reload')
        self._reload_btn.setFixedHeight(26)
        self._reload_btn.setEnabled(False)
        self._reload_btn.setToolTip('Re-read the save from disk (asks before discarding unsaved changes)')
        _reload_icon = QIcon()
        _reload_icon.addPixmap(_svg_icon(_SVG_RELOAD, '#ffffff', 13).pixmap(13, 13), QIcon.Mode.Normal)
        _reload_icon.addPixmap(_svg_icon(_SVG_RELOAD, '#3A4A58', 13).pixmap(13, 13), QIcon.Mode.Disabled)
        self._reload_btn.setIcon(_reload_icon)
        self._reload_btn.setIconSize(QSize(13, 13))
        self._reload_btn.setStyleSheet(_tbtn_reload_ss)
        self._reload_btn.clicked.connect(self._on_reload_clicked)

        self._settings_btn = QPushButton()
        self._settings_btn.setFixedSize(28, 26)
        self._settings_btn.setIcon(_nav_icon(_SVG_COG, 15))
        self._settings_btn.setIconSize(QSize(15, 15))
        self._settings_btn.setToolTip('Settings')
        self._settings_btn.setStyleSheet("""
            QPushButton {
                background: rgba(8,14,24,0.70);
                border: 1px solid rgba(255,255,255,0.18);
                border-radius: 2px;
                padding: 0;
            }
            QPushButton:hover { background: rgba(20,32,50,0.85); border-color: rgba(255,255,255,0.32); }
            QPushButton:checked { background: rgba(42,27,74,230); border-color: #735CE4; }
        """)
        self._settings_btn.setCheckable(True)  # checked = Settings page open (set in _update_header_for_view)
        self._settings_btn.clicked.connect(self._open_settings)

        nav_row.addWidget(self._save_btn)
        nav_row.addWidget(self._load_btn)
        nav_row.addWidget(self._reload_btn)
        nav_row.addWidget(self._settings_btn)

        outer.addLayout(nav_row)
        outer.addStretch(1)

        # Content row — bottom-aligned
        content_row = QHBoxLayout()
        content_row.setContentsMargins(16, 0, 16, 14)
        content_row.setSpacing(12)

        # Badge circle
        self._header_badge_lbl = QLabel('')
        self._header_badge_lbl.setFixedSize(56, 56)
        self._header_badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._header_badge_ss = (
            "border-radius: 28px;"
            " background: rgba(255,255,255,0.08);"
            " border: 2px solid rgba(255,255,255,0.18);"
            " color: #E8EDF3;"
            " font-size: 22px;"
            " font-weight: bold;"
            " font-family: 'Barlow Condensed', 'Arial Narrow', sans-serif;"
        )
        self._header_badge_lbl.setStyleSheet(self._header_badge_ss)
        self._app_logo_px = logo_pixmap(56, self.devicePixelRatioF())   # Welcome header logo: vector master
        if self._app_logo_px.isNull():
            self._app_logo_px = QPixmap(os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 'resources', 'icon.png')).scaled(
                56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        # Title + subtitle block
        text_block = QWidget()
        text_block.setStyleSheet("background: transparent;")
        tb_layout = QVBoxLayout(text_block)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        tb_layout.setSpacing(2)

        self._header_title_lbl = QLabel('')
        self._header_title_lbl.setStyleSheet(
            "color: #E8EDF3; font-size: 28px; font-weight: bold;"
            " font-family: 'Barlow Condensed', 'Arial Narrow', sans-serif;"
            " letter-spacing: 0.04em;"
            " background: transparent;"
        )
        self._header_subtitle_lbl = QLabel('')
        self._header_subtitle_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.6); font-size: 11px;"
            " letter-spacing: 0.08em; text-transform: uppercase;"
            " margin-top: 4px; background: transparent;"
        )
        tb_layout.addWidget(self._header_title_lbl)
        tb_layout.addWidget(self._header_subtitle_lbl)

        content_row.addWidget(self._header_badge_lbl)
        content_row.addWidget(text_block)
        content_row.addStretch(1)

        # Right slot (220px, fixed)
        self._header_right_slot = QWidget()
        self._header_right_slot.setFixedWidth(220)
        self._header_right_slot.setStyleSheet("background: transparent;")
        self._header_right_slot_layout = QHBoxLayout(self._header_right_slot)
        self._header_right_slot_layout.setContentsMargins(0, 0, 0, 0)
        self._header_right_slot_layout.setSpacing(8)
        self._header_right_slot_layout.addStretch(1)
        self._header_right_slot.hide()
        content_row.addWidget(self._header_right_slot)

        outer.addLayout(content_row)
        return hero

    _PAGE_ICONS = {}   # name -> QPixmap cache for the header badge icons (resources/icons/pages/<name>.png)
    _PAGE_ICON_PX = 46  # logical size of the icon CELL; the glyph fills ~62 % of it (about 28 px) inside the 56 px badge circle

    def _page_icon(self, name):
        px = self._PAGE_ICONS.get(name)
        if px is None:
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'icons', 'pages', name + '.png')
            src = QPixmap(path)
            if src.isNull():
                px = QPixmap()
            else:
                dpr = self.devicePixelRatioF()
                px = src.scaled(round(self._PAGE_ICON_PX * dpr), round(self._PAGE_ICON_PX * dpr),
                                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                px.setDevicePixelRatio(dpr)
            self._PAGE_ICONS[name] = px
        return px

    _HEADER_LOGO_PX = 40   # club badge box inside the 56 px header circle (mockups/club-page-design-a.html .a-badge-ph .logo)

    def _club_badge_px(self, club, size):
        """Club badge pixmap for `size` logical px (None: no club / no logo pack / no logo / still loading / setting off)."""
        return _faces_service().club_pixmap((club or {}).get('uid'), size, self.devicePixelRatioF()) if club else None

    def _set_header(self, title: str, subtitle: str = '', right_widget=None, icon=None, club=None):
        self._header_club = club
        self._header_title_lbl.setText(title)
        self._header_subtitle_lbl.setText(subtitle)
        self._header_subtitle_lbl.setVisible(bool(subtitle))
        if title == 'FM Backroom 24' and not self._app_logo_px.isNull():
            # welcome screen: app logo instead of an initial
            self._header_badge_lbl.setText('')
            self._header_badge_lbl.setPixmap(self._app_logo_px)
            self._header_badge_lbl.setStyleSheet("background: transparent; border: none;")
        else:
            self._header_badge_lbl.setPixmap(QPixmap())
            self._header_badge_lbl.setStyleSheet(self._header_badge_ss)
            self._header_badge_lbl.setText(title[0].upper() if title else '')
            ipx = self._page_icon(icon) if icon else None
            if ipx is not None and not ipx.isNull():   # page icon instead of the initial (falls back to the letter)
                self._header_badge_lbl.setText('')
                self._header_badge_lbl.setPixmap(ipx)
            lpx = self._club_badge_px(club, self._HEADER_LOGO_PX)   # the club's own badge replaces the page icon when found
            if lpx is not None:
                self._header_badge_lbl.setText('')
                self._header_badge_lbl.setPixmap(lpx)

        # Clear old right slot contents
        while self._header_right_slot_layout.count():
            item = self._header_right_slot_layout.takeAt(0)
            cw = item.widget()
            if cw is not None:
                # deleteLater alone leaves it a visible child of the slot (painted over the next page's widget)
                # until the event loop runs: detach + hide now
                cw.hide()
                cw.setParent(None)
                cw.deleteLater()

        if right_widget is not None:
            self._header_right_slot_layout.addStretch(1)
            self._header_right_slot_layout.addWidget(right_widget, 0, Qt.AlignmentFlag.AlignBottom)
            right_widget.show()   # a re-parented widget stays hidden until the next event-loop pass otherwise
            self._header_right_slot.show()
        else:
            self._header_right_slot.hide()

    def _refresh_si_badge(self):
        """Save Info rail: the manager's club badge before the club name (hidden without a logo)."""
        px = self._club_badge_px(self._si_badge_club, 22)
        if px is not None:
            self._si_badge.setPixmap(px)
        self._si_badge.setVisible(px is not None)

    def _refresh_badges(self):
        """FaceService.ready (index / club key table loaded, or Settings changed): re-apply the club badges."""
        try:
            if self._hdr_key in ('club', 'squad', 'club_staff') and self._current_club:
                self._update_header_for_view(self._hdr_key)
            self._refresh_si_badge()
        except RuntimeError:
            pass   # window closing

    def _make_squad_stats_label(self):
        """Squads header stats strip from the html _populate_squad_table left in _squad_info (None = no squad yet)."""
        html = self._squad_info.text()
        if not html:
            return None
        lbl = QLabel(html)
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setStyleSheet("background: transparent; font-size: 12px;")
        return lbl

    def _make_header_rep_widget(self, stars: int, rep=None) -> QWidget:
        # stars: 0-5 in half steps from clubextra.rep_stars (fitted to 3 in-game points); `rep` = raw 1-10000
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(3)

        caption = QLabel(f'CLUB REPUTATION · {rep:,}' if rep else 'CLUB REPUTATION')
        caption.setAlignment(Qt.AlignmentFlag.AlignRight)
        caption.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:10px; font-weight:600;"
            " letter-spacing:1.2px; background: transparent;"
        )
        outer.addWidget(caption)

        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent;")
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        for i in range(5):
            row.addWidget(_StarWidget(max(0.0, min(1.0, stars - i))))
        outer.addWidget(row_widget, 0, Qt.AlignmentFlag.AlignRight)
        return w

    def _update_header_for_view(self, key: str):
        # each Player Report has its own header image (falls back to the shared reports image)
        self._hdr_key = key
        self._hero.set_page(self._current_report_key if key == 'reports' and self._current_report_key in self._hero._PAGE_IMAGE else key)
        self._settings_btn.setChecked(key == 'settings')
        club = self._current_club
        club_name = club['name'] if club else ''

        if key == 'club':
            from fm_editor.nations import nation_name
            country = nation_name(club.get('nation')) if club else None
            lg = (club or {}).get('league')
            pos = f"{_ordinal(lg['pos'])} of {lg['of']}" if lg else None
            club_sub = ' · '.join(x for x in (country, pos) if x)
            self._set_header(club_name or 'Club', club_sub,
                             self._make_header_rep_widget(rep_stars((club or {}).get('rep')), (club or {}).get('rep')),
                             icon='club', club=club)
        elif key == 'squad':
            n = len(getattr(self, '_squad', []))
            self._set_header('Squads', f"{club_name} · {n} players", self._make_squad_stats_label(), icon='squads', club=club)
        elif key == 'staff':
            self._set_header('Staff', self._scouting_count_text(self._staff_model, 'staff'), icon='staff')
        elif key == 'reports':
            label = _REPORT_LABELS.get(self._current_report_key, '')
            n = self._reports_table.rowCount() if hasattr(self, '_reports_table') else 0
            tot = getattr(self, '_report_total', n)
            cnt = '' if not n else f'{n:,} players' if tot <= n else f'top {n:,} of {tot:,} players'
            if self._current_report_key == 'best_role' and hasattr(self, '_report_minpos'):
                role, mp = self._report_role_combo.currentText(), self._report_minpos.value()
                label = ' · '.join(x for x in (label, role if not role.startswith('──') else '',
                                                f'position \u2265 {mp}' if mp > 1 else '') if x)
            parts = [p for p in (label, cnt) if p]
            self._set_header('Player Reports', ' · '.join(parts), icon=_REPORT_ICONS.get(self._current_report_key, 'player_reports'))
        elif key == 'players':
            self._set_header('All Players', self._scouting_count_text(self._players_model, 'players'), icon='players')
        elif key == 'shortlist':
            n = len(self._shortlist)
            self._set_header('Player Shortlist', f"{n} players", icon='player_shortlist')
        elif key == 'staff_shortlist':
            n = len(self._staff_shortlist)
            self._set_header('Staff Shortlist', f"{n} staff", icon='staff_shortlist')
        elif key == 'club_staff':
            n = self._club_staff_table.rowCount() if hasattr(self, '_club_staff_table') else 0
            sub = f"{club_name} · {n} staff" if club_name else f"{n} staff"
            self._set_header('Club Staff', sub, icon='club_staff', club=club)
        elif key == 'save_info':
            info = (self._save_data or {}).get('save_info') or {}
            self._set_header('Save Info', info.get('game_name')
                             or (os.path.basename(self._save_path) if self._save_path else ''), icon='save_info')
        elif key == 'welcome':
            self._set_header('FM Backroom 24', 'Load a save to begin')
        elif key == 'settings':
            self._set_header('Settings', 'Preferences & paths', icon='settings')

    def _make_sidebar(self):
        sidebar = _SidebarFrame()
        sidebar.setFixedWidth(192)
        sidebar.setObjectName('sidebar')
        sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background: {COLORS['surface']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        vbox = QVBoxLayout(sidebar)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # Brand anchor (mockup option A): fixed mark + wordmark, one status line below.
        brand_block = QWidget()
        brand_block.setObjectName('sbBrand')
        brand_block.setStyleSheet("QWidget#sbBrand { background: transparent; }")
        bb = QVBoxLayout(brand_block)
        bb.setContentsMargins(15, 14, 15, 12)
        bb.setSpacing(8)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(9)
        mark = QLabel()
        mark.setObjectName('sbMark')
        mark.setFixedSize(_BRAND_MARK_PX, _BRAND_MARK_PX)
        mark.setStyleSheet("QLabel#sbMark { background:transparent; }")
        _mark_px = logo_pixmap(_BRAND_MARK_PX, self.devicePixelRatioF())   # vector master, crisp at any DPR
        if _mark_px.isNull():   # SVG missing: raster fallback
            _mark_px = QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'icon-source.png'))
            _mark_px = _mark_px.scaled(_BRAND_MARK_PX * 2, _BRAND_MARK_PX * 2, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
            mark.setScaledContents(True)
        if not _mark_px.isNull():
            mark.setPixmap(_mark_px)
        wordmark = QLabel(_APP_WORDMARK.upper())
        wordmark.setObjectName('sbWordmark')
        wordmark.setFixedHeight(_BRAND_MARK_PX)
        wordmark.setStyleSheet(
            f"QLabel#sbWordmark {{ background:transparent; color:{COLORS['text_primary']};"
            " font-family:'Barlow Condensed','Arial Narrow',sans-serif;"
            " font-size:18px; font-weight:700; letter-spacing:0.05em; }")
        brand_row.addWidget(mark)
        brand_row.addWidget(wordmark, 1)
        bb.addLayout(brand_row)

        status_row = QHBoxLayout()
        status_row.setSpacing(7)
        self._sb_dot = QLabel()
        self._sb_dot.setObjectName('sbDot')
        self._sb_dot.setFixedSize(7, 7)
        self._sb_status = QLabel()
        self._sb_status.setObjectName('sbStatus')
        self._sb_status.setTextFormat(Qt.TextFormat.RichText)
        self._sb_status.setStyleSheet(
            f"QLabel#sbStatus {{ background:transparent; color:{COLORS['text_secondary']}; font-size:11px; }}")
        status_row.addWidget(self._sb_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        status_row.addWidget(self._sb_status, 1)
        bb.addLayout(status_row)
        vbox.addWidget(brand_block)
        self._update_sidebar_status()
        vbox.addWidget(self._make_hline())

        # Main nav
        vbox.addWidget(self._make_section_label('MAIN'))
        self._nav_btns = {}
        for key, svg, label in [
            ('save_info',  _SVG_INFO,      'Save Info'),
            ('club',       _SVG_CLUB,      'Club'),
            ('squad',      _SVG_SQUAD,     'Squads'),
            ('club_staff', _SVG_STAFF,     'Club Staff'),
            ('shortlist',  _SVG_SHORTLIST, 'Player Shortlist'),
            ('staff_shortlist', _SVG_SHORTLIST, 'Staff Shortlist'),
        ]:
            if key == 'squad':
                btn = self._make_nav_btn(svg, label, self._nav_to_squad_view)
            else:
                btn = self._make_nav_btn(svg, label, lambda checked, k=key: self._nav_to(k))
            self._nav_btns[key] = btn
            vbox.addWidget(btn)
        self._nav_btns['save_info'].setEnabled(False)
        self._nav_btns['club'].setEnabled(False)

        vbox.addWidget(self._make_hline())

        # Scouting
        vbox.addWidget(self._make_section_label('SCOUTING'))

        self._players_nav_btn = self._make_nav_btn(
            _SVG_SQUAD, 'Players', lambda checked: self._open_players_view())
        self._players_nav_btn.setEnabled(False)
        vbox.addWidget(self._players_nav_btn)

        self._scouting_staff_nav_btn = self._make_nav_btn(
            _SVG_STAFF, 'Staff', lambda checked: self._nav_to('staff'))
        self._scouting_staff_nav_btn.setEnabled(False)
        vbox.addWidget(self._scouting_staff_nav_btn)

        vbox.addWidget(self._make_section_label('PLAYER REPORTS'))

        self._report_btns = {}
        for key, label in [
            ('prospects', 'Best Prospects'),
            ('wonderkids', 'Wonderkids'),
            ('best_pos',   'Best in Position'),
            ('best_role',  'Best by Role'),
        ]:
            btn = self._make_nav_btn(_SVG_REPORT, label, lambda checked, k=key: self._run_report(k))
            btn.setEnabled(False)
            self._report_btns[key] = btn
            vbox.addWidget(btn)

        vbox.addWidget(self._make_hline())
        vbox.addWidget(self._make_section_label('STAFF REPORTS'))
        staff_rpt_btn = self._make_nav_btn(_SVG_REPORT, 'Coming Soon', lambda checked: None)
        staff_rpt_btn.setEnabled(False)
        vbox.addWidget(staff_rpt_btn)

        vbox.addStretch()
        vbox.addSpacing(10)
        import os as _os
        _sb_img_path = _os.path.join(_os.path.dirname(__file__), 'assets', 'sidebar.webp')
        if _os.path.exists(_sb_img_path):
            _sb_reader = QImageReader(_sb_img_path)
            _sb_img = _sb_reader.read()
            if not _sb_img.isNull():
                sidebar.set_bg(QPixmap.fromImage(_sb_img))
        return sidebar

    def _make_view_club(self):
        """1:1 translation of mockups/club-page-design-a.html (Design A).

        The mockup's own hero (.a-hero) is skipped — _HeaderHeroWidget
        already renders the stadium bg / club name / rep stars for the
        'club' page key (see _update_header_for_view). This content starts
        at the KPI bar and ends after the 3-column body — the mockup's own
        card styling (.a-wrap) and footer actions (.a-actions) are dropped
        so this sits flush on the page background like every other tab
        (see _make_view_squad's header bar for the convention).
        """
        w = QWidget()
        w.setObjectName('view_club')
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"QScrollArea {{ border:none; background:{COLORS['window_bg']}; }}")
        scroll.setWidget(w)

        outer = QWidget()
        outer.setObjectName('view_club_outer')
        outer_vbox = QVBoxLayout(outer)
        outer_vbox.setContentsMargins(0, 0, 0, 0)
        outer_vbox.setSpacing(0)
        outer_vbox.addWidget(scroll, 1)

        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # Orphan label kept only so external .setText() calls (_on_parse_done,
        # _show_squad) don't crash — pre-existing behavior, never laid out.
        self._club_view_info = QLabel('Load an FM24 save file to get started.')

        self._club_empty_lbl = QLabel('Load an FM24 save file to get started.')
        self._club_empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._club_empty_lbl.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-size:13px; padding:40px 0; background:transparent;")
        vbox.addWidget(self._club_empty_lbl)

        # ── Content container (was .a-wrap card; now a plain layout box —
        # no background/border/radius of its own, so it sits flush on the
        # page background like every other tab. Kept only so
        # _update_club_view has something to show/hide for the empty state. ──
        wrap = QFrame()
        wrap.setObjectName('clubWrap')
        wrap.setVisible(False)
        self._club_wrap = wrap
        # Old attribute names some call sites outside these two functions
        # still toggle on save-clear/load — they all alias the one card now.
        self._club_stats_frame = self._club_pos_frame = self._club_top_frame = wrap
        wrap_vbox = QVBoxLayout(wrap)
        wrap_vbox.setContentsMargins(0, 0, 0, 0)
        wrap_vbox.setSpacing(0)

        def _col(border_right=True, fixed_width=None):
            cw = QFrame()
            # Scoped by #clubCol, not a bare "QFrame" type selector — QLabel
            # is itself a QFrame subclass, so an unscoped selector's border
            # leaks onto every descendant QLabel that doesn't set its own
            # border (visible as a stray box around each label's text).
            cw.setObjectName('clubCol')
            border = "border-right:1px solid #263140;" if border_right else ""
            cw.setStyleSheet(f"QFrame#clubCol {{ background:transparent; {border} }}")
            if fixed_width:
                cw.setFixedWidth(fixed_width)
            cl = QVBoxLayout(cw)
            cl.setContentsMargins(16, 16, 16, 16)
            cl.setSpacing(6)
            return cw, cl

        # ── KPI bar (.a-kpis) — same bar convention as _squad_header_bar /
        # club-staff hdr: elevated bg + border-bottom only, no card look ──
        kpis = QFrame()
        kpis.setObjectName('clubKpiBar')
        kpis.setStyleSheet(
            f"QFrame#clubKpiBar {{ background:{COLORS['elevated']};"
            f" border-bottom:1px solid {COLORS['border']}; }}")
        kpi_row = QHBoxLayout(kpis)
        kpi_row.setContentsMargins(0, 0, 0, 0)
        kpi_row.setSpacing(0)
        self._club_kpi_labels = {}
        kpi_defs = [
            ('squad', 'Squad', '#3d8bcd'),
            ('avg_ca', 'Avg CA', '#e8edf2'),
            ('hgp', 'HGP', '#4caf82'),
            ('hgc', 'HGC', '#e6b840'),
            ('injured', 'Injured', '#c0392b'),
            ('staff', 'Staff', '#8b5cf6'),
        ]
        for idx, (key, label, color) in enumerate(kpi_defs):
            cell = QFrame()
            cell.setObjectName('clubKpiCell')
            border = f"border-right:1px solid {COLORS['border']};" if idx < len(kpi_defs) - 1 else ""
            cell.setStyleSheet(f"QFrame#clubKpiCell {{ background:transparent; {border} }}")
            cvbox = QVBoxLayout(cell)
            cvbox.setContentsMargins(4, 10, 4, 10)
            cvbox.setSpacing(3)
            val_lbl = QLabel('0')
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_lbl.setStyleSheet(f"color:{color}; font-size:22px; font-weight:bold; background:transparent;")
            lbl_lbl = QLabel(label.upper())
            lbl_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_lbl.setStyleSheet(
                "color:#4a5f73; font-size:10px; letter-spacing:0.07em; background:transparent;")
            cvbox.addWidget(val_lbl)
            cvbox.addWidget(lbl_lbl)
            kpi_row.addWidget(cell, 1)
            self._club_kpi_labels[key] = val_lbl
        wrap_vbox.addWidget(kpis)

        # ── Body (.a-body): 3 columns ────────────────────────────────────
        body = QFrame()
        body_row = QHBoxLayout(body)
        body_row.setContentsMargins(0, 0, 0, 0)
        body_row.setSpacing(0)
        wrap_vbox.addWidget(body)

        # -- Col 1: Top Players / Positions ---------------------------------
        col1, col1_l = _col()
        self._club_top_hdr = _club_sec_hdr('Top Players · Avg Rating')
        col1_l.addWidget(self._club_top_hdr)
        self._club_top_list_w = QWidget()
        top_list_l = QVBoxLayout(self._club_top_list_w)
        top_list_l.setContentsMargins(0, 0, 0, 0)
        top_list_l.setSpacing(0)
        col1_l.addWidget(self._club_top_list_w)

        col1_l.addWidget(_club_sec_hdr('Positions', sub=True))
        pos_grid_w = QWidget()
        pos_grid = QGridLayout(pos_grid_w)
        pos_grid.setSpacing(6)
        self._club_pos_vals = {}
        for idx, (code, color) in enumerate(_CLUB_POS_GRID):
            cell = QFrame()
            cell.setObjectName('clubPosCell')
            cell.setStyleSheet(
                "QFrame#clubPosCell { background:#18212d; border:1px solid #263140;"
                " border-radius:3px; }")
            cell_l = QVBoxLayout(cell)
            cell_l.setContentsMargins(4, 7, 4, 7)
            cell_l.setSpacing(1)
            n_lbl = QLabel(code)
            n_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            n_lbl.setStyleSheet(
                "color:#4a5f73; font-size:10px; font-weight:bold; letter-spacing:0.06em;"
                " text-transform:uppercase; background:transparent;")
            v_lbl = QLabel('0')
            v_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v_lbl.setStyleSheet(f"color:{color}; font-size:17px; font-weight:bold; background:transparent;")
            cell_l.addWidget(n_lbl)
            cell_l.addWidget(v_lbl)
            pos_grid.addWidget(cell, idx // 3, idx % 3)
            self._club_pos_vals[code] = v_lbl
        col1_l.addWidget(pos_grid_w)
        col1_l.addStretch(1)
        body_row.addWidget(col1, 1)

        # -- Col 2: Club Info / Finances. Region, Year founded and Facilities are not in the
        # save, so they have no rows; a row whose value is absent for a club is hidden. -----
        col2, col2_l = _col()
        col2_l.addWidget(_club_sec_hdr('Club Info'))
        self._club_info_vals = {}
        for label in ('Status', 'Reputation', 'Stadium', 'League position'):
            self._club_info_vals[label] = _club_kv_value('')
            col2_l.addWidget(_club_kv_row(label, self._club_info_vals[label]))
        self._club_status_val = self._club_info_vals['Status']
        col2_l.addWidget(_club_sec_hdr('Finances', sub=True))
        self._club_fin_vals = {}
        for label in ('Transfer budget', 'Wage budget', 'Scouting budget', 'Balance'):
            self._club_fin_vals[label] = _club_kv_value('')
            col2_l.addWidget(_club_kv_row(label, self._club_fin_vals[label]))
        col2_l.addStretch(1)
        body_row.addWidget(col2, 1)

        # -- Col 3: Injuries / Staff / Contracts / Homegrown (220px). The
        # mockup's .a-col3-inner is only a 2-col grid inside the
        # @media(max-width:860px) block — at the width this 220px rail
        # actually renders, its two child <div>s (Injuries+Staff,
        # Contracts+Homegrown) are plain blocks and simply stack, so this
        # is a single QVBoxLayout in literal DOM order, not a QHBoxLayout
        # of two sub-columns. ------------------------------------------------
        col3, col3_l = _col(border_right=False, fixed_width=220)

        self._club_inj_hdr = _club_sec_hdr('Injuries (0)')
        col3_l.addWidget(self._club_inj_hdr)
        self._club_inj_list_w = QWidget()
        inj_list_l = QVBoxLayout(self._club_inj_list_w)
        inj_list_l.setContentsMargins(0, 0, 0, 0)
        inj_list_l.setSpacing(0)
        col3_l.addWidget(self._club_inj_list_w)

        self._club_staff_hdr = _club_sec_hdr('Staff (0)', sub=True)
        col3_l.addWidget(self._club_staff_hdr)
        self._club_avg_coaching_val = _club_kv_value('')
        col3_l.addWidget(_club_kv_row('Avg coaching attr', self._club_avg_coaching_val))
        self._club_best_staff_ca_val = _club_kv_value('')
        col3_l.addWidget(_club_kv_row('Best staff CA', self._club_best_staff_ca_val))
        self._club_manager_val = _club_kv_value('')
        col3_l.addWidget(_club_kv_row('Manager', self._club_manager_val))

        col3_l.addWidget(_club_sec_hdr('Contracts', sub=True))
        self._club_exp6_val = _club_kv_value('0', color='#c0392b')
        col3_l.addWidget(_club_kv_row('Expiring <6mo', self._club_exp6_val))
        self._club_exp1yr_val = _club_kv_value('0', color='#e6b840')
        col3_l.addWidget(_club_kv_row('Expiring <1yr', self._club_exp1yr_val))
        self._club_longest_val = _club_kv_value('—')
        col3_l.addWidget(_club_kv_row('Longest deal', self._club_longest_val))

        col3_l.addWidget(_club_sec_hdr('Homegrown', sub=True))
        self._club_hgp_val = _club_kv_value('0 / 0', color='#4caf82')
        col3_l.addWidget(_club_kv_row('HGP', self._club_hgp_val))
        self._club_hgc_val = _club_kv_value('0 / 0', color='#e6b840')
        col3_l.addWidget(_club_kv_row('HGC', self._club_hgc_val))
        col3_l.addStretch(1)

        body_row.addWidget(col3, 0)

        # Footer actions (.a-actions: View Squad / Staff buttons) removed —
        # those options already live in the sidebar nav (Squads, Club Staff).

        vbox.addWidget(wrap, 1)
        vbox.addStretch(1)
        return outer

    def _make_view_save_info(self):
        """1:1 translation of mockups/save-info-page-design-b.html (Design B).

        The mockup's context-only sidebar / masthead / Preview switch are skipped (the app's own
        shared masthead is used). No PENDING state: a row whose value is absent from the parsed
        save_info dict is hidden, and a band with no visible rows vanishes
        (see _update_save_info_view). Sits flat on the page background — no card, no footer.
        """
        BORDER, DIM, TEXT = '#263140', '#7a8fa6', '#e8edf2'

        page = _WidthWatcher(self._si_apply_width)
        page.setObjectName('view_save_info')
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"QScrollArea {{ border:none; background:{COLORS['window_bg']}; }}")
        scroll.setWidget(page)
        outer = QWidget()
        outer.setObjectName('view_save_info_outer')
        outer_vbox = QVBoxLayout(outer)
        outer_vbox.setContentsMargins(0, 0, 0, 0)
        outer_vbox.setSpacing(0)
        outer_vbox.addWidget(scroll, 1)

        # .page: grid 280px 1fr
        page_row = QHBoxLayout(page)
        page_row.setContentsMargins(0, 0, 0, 0)
        page_row.setSpacing(0)

        # ── Rail (.rail): elevated surface, 1px right divider, padding 24 22 28 ──
        rail = QFrame()
        rail.setObjectName('siRail')
        rail.setFixedWidth(280)
        rail.setStyleSheet(
            f"QFrame#siRail {{ background:#141c27; border-right:1px solid {BORDER}; }}")
        self._si_rail = rail
        rail_v = QVBoxLayout(rail)
        rail_v.setContentsMargins(22, 24, 22, 28)
        rail_v.setSpacing(0)

        # .id: column, gap 16 — avatar then labels. Bottom margin 32 = .counts margin-top.
        self._si_id_block = QWidget()
        self._si_id_block.setObjectName('siIdBlock')
        self._si_id_block.setStyleSheet("QWidget#siIdBlock { background:transparent; }")
        id_v = QVBoxLayout(self._si_id_block)
        id_v.setContentsMargins(0, 0, 0, 32)
        id_v.setSpacing(16)
        avatar = QFrame()
        avatar.setObjectName('siAvatar')
        avatar.setFixedSize(88, 88)
        avatar.setStyleSheet(
            f"QFrame#siAvatar {{ background:#18212d; border:1px solid {BORDER}; border-radius:3px; }}")
        av_v = QVBoxLayout(avatar)
        av_v.setContentsMargins(0, 0, 0, 0)
        av_icon = QLabel()
        av_icon.setPixmap(_svg_icon(_SVG_AVATAR, '#2a394b', 62).pixmap(62, 62))
        av_icon.setStyleSheet("background:transparent;")
        av_v.addWidget(av_icon, 0, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        id_v.addWidget(avatar)
        id_text = QVBoxLayout()
        id_text.setContentsMargins(0, 0, 0, 0)
        id_text.setSpacing(0)
        id_text.addWidget(_si_label('Manager', 11, DIM, spacing_em=0.07, upper=True))
        id_text.addSpacing(2)
        self._si_name = _FitLabel(38, 22, TEXT, 0.02)   # .id-name: 38px/44px bold
        self._si_name.setFixedHeight(44)
        id_text.addWidget(self._si_name)
        id_text.addSpacing(14)                          # .lbl2 margin-top
        id_text.addWidget(_si_label('Current club', 11, DIM, spacing_em=0.07, upper=True))
        id_text.addSpacing(2)
        self._si_club = _ElideLabel()                   # .id-club: 15px / 500, 24px tall
        self._si_club.setFixedHeight(24)
        club_row = QHBoxLayout()                        # .id-club: badge 22x22 + gap 8 + name (badge hidden without a logo)
        club_row.setContentsMargins(0, 0, 0, 0)
        club_row.setSpacing(8)
        self._si_badge = QLabel()
        self._si_badge.setFixedSize(22, 22)
        self._si_badge.setStyleSheet("background:transparent;")
        self._si_badge.hide()
        self._si_badge_club = None
        club_row.addWidget(self._si_badge)
        club_row.addWidget(self._si_club, 1)
        id_text.addLayout(club_row)
        id_v.addLayout(id_text)
        rail_v.addWidget(self._si_id_block)

        # .counts: 1px top divider, padding-top 12, three .count rows
        self._si_counts = QWidget()
        self._si_counts.setObjectName('siCounts')
        self._si_counts.setStyleSheet("QWidget#siCounts { background:transparent; }")
        counts_v = QVBoxLayout(self._si_counts)
        counts_v.setContentsMargins(0, 0, 0, 0)
        counts_v.setSpacing(0)
        top_line = QFrame()
        top_line.setFixedHeight(1)
        top_line.setStyleSheet(f"background:{BORDER};")
        counts_v.addWidget(top_line)
        counts_v.addSpacing(12)
        self._si_count_vals = {}
        for i, (key, label, color) in enumerate((
                ('clubs', 'Clubs', '#3d8bcd'),
                ('players', 'Players', '#4caf82'),
                ('staff', 'Staff', '#8b5cf6'))):
            row = QFrame()
            row.setObjectName('siCount')
            row.setStyleSheet(
                "QFrame#siCount { background:transparent;"
                + (" border-bottom:1px solid rgba(255,255,255,0.04);" if i < 2 else "") + " }")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 7, 0, 7)
            rl.setSpacing(0)
            lbl = _si_label(label, 11, DIM, spacing_em=0.07, upper=True)
            lbl.setContentsMargins(0, 0, 0, 3)          # baseline-align with the 22px value
            rl.addWidget(lbl, 0, Qt.AlignmentFlag.AlignBottom)
            rl.addStretch(1)
            val = _si_label('0', 22, color, bold=True)
            val.setFixedHeight(28)                      # .count-val line-height 28px
            rl.addWidget(val)
            counts_v.addWidget(row)
            self._si_count_vals[key] = val
        rail_v.addWidget(self._si_counts)
        rail_v.addStretch(1)
        page_row.addWidget(rail)

        # ── Ledger (.ledger): one .band per topic ────────────────────────────
        ledger = QWidget()
        ledger_v = QVBoxLayout(ledger)
        ledger_v.setContentsMargins(0, 0, 0, 0)
        ledger_v.setSpacing(0)
        self._si_rows = {}      # key -> (row frame, key label, value label)
        self._si_bands = []     # (band frame, header label, [(row keys, is_full)], [(note key, note label)])
        self._si_formatters = {}  # row key -> formatter(src)

        def _kv(key, label, dim=False):
            row = QFrame()
            row.setObjectName('siKv')
            row.setMinimumHeight(28)
            hl = QHBoxLayout(row)
            hl.setContentsMargins(0, 5, 0, 5)
            hl.setSpacing(0)
            lbl = _si_label(label, 12, DIM)
            lbl.setFixedWidth(112)                      # .fields .kv: 112px label column
            hl.addWidget(lbl)
            val = _ElideLabel()
            val.setStyleSheet(
                f"color:{DIM if dim else TEXT}; font-size:12px;"
                f" font-weight:{400 if dim else 500}; background:transparent;")
            hl.addWidget(val, 1)
            self._si_rows[key] = (row, lbl, val)
            return row

        def _band(title, rows):
            band = QFrame()
            band.setObjectName('siBand')
            bl = QBoxLayout(QBoxLayout.Direction.LeftToRight, band)
            bl.setContentsMargins(28, 20, 28, 20)
            bl.setSpacing(24)
            hdr = _si_label(title, 12, DIM, bold=True, spacing_em=0.12, upper=True)
            hdr.setFixedWidth(120)
            hdr.setContentsMargins(0, 6, 0, 0)          # .band-h padding-top 6
            bl.addWidget(hdr, 0, Qt.AlignmentFlag.AlignTop)
            fields = QWidget()
            grid = QGridLayout(fields)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setHorizontalSpacing(40)               # .fields column-gap 40
            grid.setVerticalSpacing(0)
            grid.setColumnStretch(0, 1)
            grid.setColumnStretch(1, 1)
            by = {pl: [row for row in rows if row[0] == pl] for pl in ('full', 'left', 'right', 'note')}
            groups = []
            r = 0
            for row in by['full']:                      # .kv.full spans both columns
                grid.addWidget(_kv(row[1], row[2], len(row) > 4 and row[4]), r, 0, 1, 2)
                r += 1
            if by['full']:
                groups.append(([row[1] for row in by['full']], True))
            for col, pl in enumerate(('left', 'right')):
                if not by[pl]:
                    continue
                colw = QWidget()
                cv = QVBoxLayout(colw)
                cv.setContentsMargins(0, 0, 0, 0)
                cv.setSpacing(0)
                for row in by[pl]:
                    cv.addWidget(_kv(row[1], row[2], len(row) > 4 and row[4]))
                cv.addStretch(1)
                grid.addWidget(colw, r, col)
                groups.append(([row[1] for row in by[pl]], False))
            notes = []
            for row in by['note']:                      # .nat
                nl = _si_label('', 11, DIM)
                nl.setWordWrap(True)
                nl.setContentsMargins(0, 8, 0, 0)
                grid.addWidget(nl, r + 1 + len(notes), 0, 1, 2)
                notes.append((row[1], nl))
            bl.addWidget(fields, 1)
            ledger_v.addWidget(band)
            self._si_bands.append((band, hdr, groups, notes))
            self._si_formatters.update({row[1]: row[3] for row in rows})

        for title, rows in _SI_LAYOUT:
            _band(title, rows)
        ledger_v.addStretch(1)
        page_row.addWidget(ledger, 1)
        return outer

    def _si_apply_width(self, width):
        """Mockup @media (max-width:1100px) collapse — rail 240px, band title stacked above its
        fields. Breakpoint raised from the mockup's 908px content width to 980px: the real
        values (full-length dates, game time) are wider than the mockup's abbreviations, and
        the 2-column grid clips them below that."""
        if not hasattr(self, '_si_bands'):
            return
        narrow = width < 980
        self._si_rail.setFixedWidth(240 if narrow else 280)
        for band, hdr, groups, note in self._si_bands:
            bl = band.layout()
            bl.setDirection(QBoxLayout.Direction.TopToBottom if narrow
                            else QBoxLayout.Direction.LeftToRight)
            bl.setSpacing(4 if narrow else 24)
            hdr.setFixedWidth(16777215 if narrow else 120)
            hdr.setContentsMargins(0, 0 if narrow else 6, 0, 0)

    def _update_save_info_view(self):
        """Fill the Save Info page from self._save_data['save_info'] + file stats.
        Absent values hide their row; a band with no visible rows hides; no PENDING chips."""
        sd = self._save_data or {}
        info = sd.get('save_info') or {}
        people = sd.get('people') or []

        # -- source facts: parsed save_info + what the app itself knows about the file / database --
        src = dict(info)
        path = self._save_path
        if path:
            src['file_name'] = os.path.basename(path)
            src['folder_path'] = os.path.dirname(path)
            try:
                st = os.stat(path)
                from datetime import datetime
                src['file_size'] = st.st_size
                src['file_modified'] = datetime.fromtimestamp(st.st_mtime).strftime('%-d %b %Y, %H:%M')
            except OSError:
                pass
        if people:
            src['people_total'] = len(people)
        vals, tips = {}, {}
        for key, fmt in self._si_formatters.items():
            try:
                out = fmt(src)
            except Exception:                           # one bad value must not blank the page
                out = None
            if isinstance(out, tuple):
                out, tips[key] = out
            if out is not None:
                vals[key] = out

        # -- database counts the app already knows --
        n_players = sum(1 for p in people if 'ca' in p)
        counts = {}
        if 'clubs' in sd:
            counts['clubs'] = len(sd['clubs'])
        if people:
            counts['players'], counts['staff'] = n_players, len(people) - n_players
        for key, lbl in self._si_count_vals.items():
            lbl.parent().setVisible(key in counts)
            lbl.setText(f"{counts.get(key, 0):,}")
        self._si_counts.setVisible(bool(counts))

        # -- rail identity --
        mgr = info.get('manager_name')
        self._si_rail.setVisible(bool(mgr or counts))
        self._si_id_block.setVisible(bool(mgr))
        if mgr:
            self._si_name.set_full_text(mgr)
            club = info.get('manager_club_name') or info.get('manager_club_short')
            self._si_club.set_full_text(club or 'No club')
            self._si_badge_club = next((c for c in sd.get('clubs') or ()
                                        if c.get('id') == info.get('manager_club_id')), None) if club else None
            self._si_club.setStyleSheet(
                f"color:{'#e8edf2' if club else '#7a8fa6'}; font-size:15px; font-weight:500;"
                " background:transparent;")
        else:
            self._si_badge_club = None
        self._refresh_si_badge()

        # -- rows, hairlines, bands --
        hair = "QFrame#siKv { border-bottom:1px solid rgba(255,255,255,0.04); }"
        last_band = None
        for band, hdr, groups, note in self._si_bands:
            any_row = False
            below = any(vals.get(k) is not None
                        for keys, is_full in groups if not is_full for k in keys)
            for keys, is_full in groups:
                shown = [k for k in keys if vals.get(k) is not None]
                for k in keys:
                    row, _, val = self._si_rows[k]
                    row.setVisible(k in shown)
                    if k in shown:
                        val.set_full_text(vals[k])
                        if k in tips:
                            val.setToolTip(tips[k])
                for i, k in enumerate(shown):           # .kv:last-child has no hairline
                    more = i < len(shown) - 1 or (is_full and below)
                    self._si_rows[k][0].setStyleSheet(hair if more else "")
                any_row = any_row or bool(shown)
            for nkey, nlbl in note:
                nlbl.setVisible(nkey in vals)
                nlbl.setText(vals.get(nkey, ''))
                any_row = any_row or nkey in vals
            band.setVisible(any_row)
            if any_row:
                last_band = band
        for band, *_ in self._si_bands:
            band.setStyleSheet(
                "" if band is last_band
                else "QFrame#siBand { border-bottom:1px solid #263140; }")

    def _update_club_view(self):
        from fm_editor.patch import is_hgc
        squad = self._club_first_team  # not self._squad: that follows the U21/U18 tab
        b = self._save_data.get('b') if self._save_data else None
        club = self._current_club

        has_club = bool(club and squad is not None)
        self._club_empty_lbl.setVisible(not has_club)
        self._club_wrap.setVisible(has_club)

        if not has_club:
            return

        club_staff = self._save_data.get('club_staff', {}) if self._save_data else {}
        people = self._save_data.get('people', []) if self._save_data else []
        people_by_id = {p.get('id'): p for p in people}
        staff = [people_by_id[pid] for pid in club_staff.get(club['id'], [])
                 if pid in people_by_id]

        n_hgp = sum(1 for p in squad if p.get('hgp', False))
        n_hgc = sum(1 for p in squad
                    if b is not None and self._entity_of(p) is not None
                    and is_hgc(b, p, self._entity_of(p)))
        n_injured = sum(1 for p in squad if p.get('injured', False))
        cas = [p['ca'] for p in squad if p.get('ca') is not None]
        avg_ca = round(sum(cas) / len(cas)) if cas else 0

        self._club_kpi_labels['squad'].setText(str(len(squad)))
        self._club_kpi_labels['avg_ca'].setText(str(avg_ca))
        self._club_kpi_labels['hgp'].setText(str(n_hgp))
        self._club_kpi_labels['hgc'].setText(str(n_hgc))
        self._club_kpi_labels['injured'].setText(str(n_injured))
        self._club_kpi_labels['staff'].setText(str(len(staff)))

        # -- Col 1: top players (avg match rating, or CA when the club has no stats) + 9-cell grid --
        while self._club_top_list_w.layout().count():
            cw_item = self._club_top_list_w.layout().takeAt(0)
            if cw_item.widget():
                cw_item.widget().deleteLater()
        mode, top = _club_top_players(squad)
        self._club_top_hdr.setText('Top Players · Avg Rating' if mode == 'rating'
                                   else 'Top Players · Current Ability')
        for rank, (p, text, good) in enumerate(top, start=1):
            pos = _primary_pos(p['positions']) if p.get('positions') else '?'
            self._club_top_list_w.layout().addWidget(
                _club_player_row(rank, pos, p.get('name', ''), p.get('injured', False),
                                 _club_rating_pill(text, good)))

        pos_counts = {code: 0 for code, _ in _CLUB_POS_GRID}
        for p in squad:
            if p.get('positions'):
                pos = _primary_pos(p['positions'])
                if pos in pos_counts:
                    pos_counts[pos] += 1
        for code, val_lbl in self._club_pos_vals.items():
            val_lbl.setText(str(pos_counts.get(code, 0)))

        # -- Col 2: status (club record hdr byte, verified); Col 3: human manager only --
        from fm_editor.nations import STATUS_NAMES
        st = STATUS_NAMES.get(club.get('status'))
        if st:
            _club_set_value(self._club_status_val, st)
        else:
            _club_hide_row(self._club_status_val)
        iv = self._club_info_vals
        rep = club.get('rep')  # raw 1-10000 (verified); the 0-5 star mapping is NOT known yet
        if rep:
            _club_set_value(iv['Reputation'], f'{rep:,} / 10,000')
        else:
            _club_hide_row(iv['Reputation'])
        sd = club.get('stadium')
        if sd:
            _club_set_value(iv['Stadium'], f"{sd['capacity']:,} · built {sd['built']}")
        else:
            _club_hide_row(iv['Stadium'])
        lg = club.get('league')
        if lg:
            _club_set_value(iv['League position'],
                            f"{_ordinal(lg['pos'])} of {lg['of']} · {lg['PTS']} pts from {lg['P']}")
        else:
            _club_hide_row(iv['League position'])
        fin = club.get('fin') or {}
        for label, key, pw in (('Transfer budget', 'transfer_budget', False),
                               ('Wage budget', 'wage_budget', True),
                               ('Scouting budget', 'scouting_budget', False),
                               ('Balance', 'balance', False)):
            lbl = self._club_fin_vals[label]
            if key in fin:
                _club_set_value(lbl, _club_money(fin[key], pw),
                                color='#c0392b' if fin[key] < 0 else '#e8edf2')
            else:
                _club_hide_row(lbl)
        si = (self._save_data or {}).get('save_info') or {}
        if si.get('manager_name') and si.get('manager_club_id') == club['id']:
            _club_set_value(self._club_manager_val, si['manager_name'])
        else:
            _club_hide_row(self._club_manager_val)

        # -- Col 3 left: injuries + staff -------------------------------------
        self._club_inj_hdr.setText(f'Injuries ({n_injured})')
        while self._club_inj_list_w.layout().count():
            cw_item = self._club_inj_list_w.layout().takeAt(0)
            if cw_item.widget():
                cw_item.widget().deleteLater()
        injured_players = [p for p in squad if p.get('injured', False)][:5]
        if injured_players:
            for p in injured_players:
                self._club_inj_list_w.layout().addWidget(
                    _club_inj_row(p.get('name', ''), p.get('injury_days', 0)))
        else:
            self._club_inj_list_w.layout().addWidget(_club_muted_row('None'))

        self._club_staff_hdr.setText(f'Staff ({len(staff)})')
        coaching_vals = [v for p in staff for v in p.get('coaching', {}).values() if v is not None]
        if coaching_vals:
            _club_set_value(self._club_avg_coaching_val,
                             f'{sum(coaching_vals) / len(coaching_vals):.0f} / 20')
        else:
            _club_hide_row(self._club_avg_coaching_val)

        staff_cas = [p['staff_ca'] for p in staff if p.get('staff_ca') is not None]
        if staff_cas:
            _club_set_value(self._club_best_staff_ca_val, str(max(staff_cas)), color='#e6b840')
        else:
            _club_hide_row(self._club_best_staff_ca_val)

        # -- Col 3 right: contracts + homegrown --------------------------------
        n6, n12, longest = _contract_expiry_counts(squad, _get_age_ref())  # in-game date, not wall clock
        self._club_exp6_val.setText(str(n6))
        self._club_exp1yr_val.setText(str(n12))
        self._club_longest_val.setText(longest or '—')

        total = len(squad)
        self._club_hgp_val.setText(f'{n_hgp} / {total}')
        self._club_hgc_val.setText(f'{n_hgc} / {total}')

    def _make_view_squad(self):
        w = QWidget()
        w.setObjectName('view_squad')
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # Content header: club name + squad switcher
        self._squad_header_bar = QFrame()
        header_bar = self._squad_header_bar  # keep alive — children referenced as instance attrs
        header_bar.setFixedHeight(44)
        header_bar.setObjectName('qfStrip')  # scoped: a bare QSS would leak the border onto child QLabels
        header_bar.setStyleSheet(
            f"QFrame#qfStrip {{ background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']}; }}")
        header_row = QHBoxLayout(header_bar)
        header_row.setContentsMargins(16, 0, 16, 0)
        header_row.setSpacing(12)

        self._squad_club_label = QLabel('')
        self._squad_club_label.setStyleSheet(
            f"color:{COLORS['text_primary']}; font-size:14px; font-weight:bold;")
        header_row.addWidget(self._squad_club_label)
        header_row.addStretch()

        self._squad_info = QLabel('')
        self._squad_info.setTextFormat(Qt.TextFormat.RichText)
        self._squad_info.setStyleSheet(f"color:{COLORS['text_dim']}; font-size:12px;")
        header_row.addWidget(self._squad_info)
        # Squad tab row — shows "First Team" + sub-squads when loaded
        tab_bar = QFrame()
        tab_bar.setFixedHeight(40)
        tab_bar.setObjectName('qfStrip')  # scoped: a bare QSS would leak the border onto child QLabels
        tab_bar.setStyleSheet(
            f"QFrame#qfStrip {{ background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']}; }}")
        tab_row = QHBoxLayout(tab_bar)
        tab_row.setContentsMargins(12, 3, 12, 0)
        tab_row.setSpacing(0)

        _squad_tab_ss = f"""
            QPushButton {{
                background: transparent; border: none;
                border-bottom: 2px solid transparent;
                color: {COLORS['text_secondary']};
                padding: 0px 16px; font-size: 12px; border-radius: 0;
                min-width: 80px;
            }}
            QPushButton:hover {{ color: {COLORS['text_primary']}; }}
            QPushButton:checked {{
                color: {COLORS['text_primary']};
                border-bottom: 2px solid {COLORS['accent']};
                font-weight: bold;
            }}
        """
        self._squad_tab_ss_str = _squad_tab_ss
        self._squad_tab_bar = tab_row   # keep reference to add dynamic tabs later
        self._squad_tab_btns = []
        self._squad_tab_dynamic_btns = []

        # First Team tab always present
        ft_btn = QPushButton('First Team')
        ft_btn.setCheckable(True)
        ft_btn.setChecked(True)
        ft_btn.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        ft_btn.setStyleSheet(_squad_tab_ss)
        tab_row.addWidget(ft_btn)
        self._squad_tab_btns.append(ft_btn)

        tab_row.addStretch()

        # Patch action buttons in tab bar (right side)
        _accent_ss = (
            f"QPushButton {{ background:{COLORS['accent']}; color:#fff; border:none;"
            f" border-radius:2px; padding:4px 14px; font-size:12px; font-weight:bold; }}"
            f"QPushButton:hover {{ background:{COLORS['accent_hover']}; }}"
            f"QPushButton:pressed {{ background:{COLORS['accent_press']}; }}"
            f"QPushButton:disabled {{ background:{COLORS['surface']}; color:{COLORS['text_dim']};"
            f" border:1px solid {COLORS['border']}; }}"
        )
        self._patch_hgp_btn = QPushButton('Make HGP')
        self._patch_hgp_btn.setStyleSheet(_accent_ss)
        self._patch_hgp_btn.setFixedHeight(28)
        self._patch_hgp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._patch_hgp_btn.setToolTip('Queue the selected players as Homegrown Player (written when you Save Changes)')
        self._patch_hgp_btn.clicked.connect(lambda checked=False: self._queue_selected('hgp'))
        self._patch_hgp_btn.setEnabled(False)
        self._patch_hgc_btn = QPushButton('Make HGC')
        self._patch_hgc_btn.setStyleSheet(_accent_ss)
        self._patch_hgc_btn.setFixedHeight(28)
        self._patch_hgc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._patch_hgc_btn.setToolTip('Queue the selected players as Homegrown at Club (written when you Save Changes)')
        self._patch_hgc_btn.clicked.connect(lambda checked=False: self._queue_selected('hgc'))
        self._patch_hgc_btn.setEnabled(False)
        tab_row.addWidget(self._patch_hgp_btn)
        tab_row.addSpacing(4)
        tab_row.addWidget(self._patch_hgc_btn)
        tab_row.addSpacing(4)
        vbox.addWidget(tab_bar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setEnabled(False)
        self._table.setSortingEnabled(True)
        self._table.horizontalHeader().setHighlightSections(False)
        self._table.doubleClicked.connect(self._on_row_double_clicked)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_table_context_menu)
        self._inj_delegate = _PosBadgeDelegate(self._table)
        self._pos_delegate = _PosBadgeDelegate(self._table)
        self._table.setItemDelegateForColumn(1, self._inj_delegate)
        self._table.setItemDelegateForColumn(2, self._pos_delegate)
        self._table.setItemDelegate(_RowMarkDelegate(self._table))
        self._table.setItemDelegateForColumn(8, _HGBadgeDelegate('hgp', self._table))
        self._table.setItemDelegateForColumn(9, _HGBadgeDelegate('hgc', self._table))
        _set_star_delegates(self._table, 3, 4)
        self._configure_table_for_mode('squad')
        vbox.addWidget(self._table)


        return w

    def _make_quick_filters_frame(self):
        """Elevated 'Quick Filters' strip (caption row above, filter row below).
        Mirrors the Players view; returns (frame, filter_row_layout)."""
        frame = QFrame()
        frame.setObjectName('qfStrip')  # scoped: a bare QSS would leak the border onto child QLabels
        frame.setStyleSheet(
            f"QFrame#qfStrip {{ background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']}; }}")
        frame_vbox = QVBoxLayout(frame)
        frame_vbox.setContentsMargins(0, 0, 0, 0)
        frame_vbox.setSpacing(0)
        title_row = QHBoxLayout()
        title_row.setContentsMargins(16, 10, 16, 6)
        title_lbl = QLabel('Quick Filters')
        title_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        frame_vbox.addLayout(title_row)
        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(16, 0, 16, 10)
        filter_row.setSpacing(8)
        frame_vbox.addLayout(filter_row)
        return frame, filter_row

    def _make_view_staff(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        hdr, hdr_row = self._make_quick_filters_frame()

        staff_age_lbl = QLabel('Age:')
        staff_age_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        hdr_row.addWidget(staff_age_lbl)
        self._staff_age_min = QSpinBox()
        self._staff_age_min.setRange(0, 99)
        self._staff_age_min.setValue(0)
        self._staff_age_min.setFixedSize(52, 26)
        self._staff_age_min.valueChanged.connect(lambda _v: self._populate_staff_table())
        hdr_row.addWidget(self._staff_age_min)
        staff_dash = QLabel('-')
        staff_dash.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        hdr_row.addWidget(staff_dash)
        self._staff_age_max = QSpinBox()
        self._staff_age_max.setRange(0, 99)
        self._staff_age_max.setValue(0)
        self._staff_age_max.setFixedSize(52, 26)
        self._staff_age_max.valueChanged.connect(lambda _v: self._populate_staff_table())
        hdr_row.addWidget(self._staff_age_max)

        hdr_row.addStretch()

        staff_clear_btn = QPushButton('Clear')
        staff_clear_btn.setFixedHeight(26)
        staff_clear_btn.setStyleSheet(
            f"background:transparent; color:{COLORS['text_secondary']}; font-size:11px;"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:0 10px;")
        staff_clear_btn.clicked.connect(self._clear_staff_filter)
        hdr_row.addWidget(staff_clear_btn)

        self._staff_count_lbl = QLabel('')
        vbox.addWidget(hdr)

        self._staff_model, self._staff_table = self._make_scouting_view(
            self._make_staff_model(), _STAFF_COL_TOOLTIPS,
            {0: 200, 1: 160, 2: 50, 3: 40}, 35, sort=(-1, Qt.SortOrder.AscendingOrder))
        self._staff_table.doubleClicked.connect(self._on_staff_double_click)
        vbox.addWidget(self._staff_table, 1)
        return w

    def _make_scouting_view(self, model, tips, fixed_widths, default_w, sort):
        """Virtualised QTableView for Scouting Players/Staff (QTableWidget can't hold 78k rows)."""
        tv = QTableView()
        tv.setModel(model)
        tv.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tv.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tv.setAlternatingRowColors(True)
        tv.verticalHeader().setVisible(False)
        tv.verticalHeader().setDefaultSectionSize(30)  # = old QTableWidget row height
        tv.setShowGrid(False)
        hdr = tv.horizontalHeader()
        hdr.setHighlightSections(False)
        hdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for i in range(model.columnCount()):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            tv.setColumnWidth(i, fixed_widths.get(i, default_w))
        hdr.setResizeContentsPrecision(150)  # fit-to-content looks at ~150 rows (default 1000 = ~90 ms/column)
        hdr.setSortIndicatorShown(True)
        hdr.sortIndicatorChanged.connect(model.sort)  # own sort: see people_model.py
        hdr.setSortIndicator(*sort)
        model._sort = sort
        return model, tv

    def _make_staff_model(self):
        num = lambda v: '' if v is None else str(v)
        spec = [(str, None), (str, None), (str, None), (str, None)] \
            + [(num, num_key)] * (len(_STAFF_COACHING_COLS) + len(_STAFF_PERS_COLS))
        return PeopleModel(_STAFF_COLS, spec, _STAFF_COL_TOOLTIPS)

    def _staff_row(self, p, club_by_id, club_by_entity, staff_club, employment):
        pid = p.get('id', -1)
        cid = staff_club.get(pid)
        if cid is not None:
            club_name = club_by_id.get(cid, '')
        else:
            eid = employment.get(pid)
            club_name = club_by_entity.get(eid, '') if eid else ''
        nid = p.get('nation', 0)
        coaching = p.get('coaching', {})
        pers = p.get('personality', [])
        return (p.get('name', ''), club_name, _nation_cell(nid, ''),
                _age(p),
                *[coaching.get(_STAFF_COACHING_MAP.get(c, c)) for c in _STAFF_COACHING_COLS],
                *[pers[i] if i < len(pers) else None for i in range(8)])

    def _make_staff_table(self):
        """Staff table (name/club/nation/age + coaching + personality); shared by Staff and Staff Shortlist."""
        tbl = QTableWidget()
        tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        tbl.setSortingEnabled(True)
        shdr = tbl.horizontalHeader()
        shdr.setHighlightSections(False)
        shdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        _COACHING_COLS = _STAFF_COACHING_COLS
        self._staff_coaching_cols = _COACHING_COLS
        self._coaching_col_map = _STAFF_COACHING_MAP
        cols = _STAFF_COLS
        tbl.setColumnCount(len(cols))
        tbl.setHorizontalHeaderLabels(cols)
        for i, col in enumerate(cols):
            if col in _STAFF_COL_TOOLTIPS:
                tbl.horizontalHeaderItem(i).setToolTip(_STAFF_COL_TOOLTIPS[col])
        for i in range(len(cols)):
            shdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        widths = {0: 200, 1: 160, 2: 50, 3: 40}
        for i in range(4, len(cols)):
            widths[i] = 35
        for i, cw in widths.items():
            tbl.setColumnWidth(i, cw)
        shdr.setSectionsMovable(True)
        shdr.setFirstSectionMovable(False)
        shdr.setStretchLastSection(False)
        return tbl

    def _fill_staff_rows(self, tbl, staff):
        employment = self._save_data.get('employment', {})
        club_staff = self._save_data.get('club_staff', {})
        clubs = self._save_data.get('clubs', [])
        club_by_id = {c['id']: c['name'] for c in clubs}
        club_by_entity = {c['id'] + 1: c['name'] for c in clubs}
        # Build reverse map: person_id -> club_id from club_staff arrays
        staff_club: dict[int, int] = {}
        for cid, pids in club_staff.items():
            for pid in pids:
                if pid not in staff_club:
                    staff_club[pid] = cid
        coaching_cols = getattr(self, '_staff_coaching_cols', [])
        coaching_col_map = getattr(self, '_coaching_col_map', {})
        tbl.setSortingEnabled(False)
        tbl.setRowCount(len(staff))
        for row, p in enumerate(staff):
            pid = p.get('id', -1)
            name = p.get('name', '')
            # club_staff array first, fall back to employment record
            cid = staff_club.get(pid)
            if cid is not None:
                club_name = club_by_id.get(cid, '')
            else:
                entity_id = employment.get(pid)
                club_name = club_by_entity.get(entity_id, '') if entity_id else ''
            nation_id = p.get('nation', 0)
            flag = _nation_cell(nation_id, '')
            age = _age(p)
            coaching = p.get('coaching', {})
            coaching_items = []
            for short_label in coaching_cols:
                key = coaching_col_map.get(short_label, short_label)
                v = coaching.get(key)
                coaching_items.append(_SortItem(str(v) if v is not None else '', v if v is not None else -1))
            pers = p.get('personality', [])
            pers_items = []
            for idx in range(8):
                v = pers[idx] if idx < len(pers) else None
                pers_items.append(_SortItem(str(v) if v is not None else '', v if v is not None else -1))
            name_item = _SortItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, pid)
            items = [name_item, _SortItem(club_name), _SortItem(flag), _SortItem(str(age), age)] + coaching_items + pers_items
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                tbl.setItem(row, col, item)
        tbl.setSortingEnabled(True)
        for i in range(tbl.columnCount()):
            tbl.resizeColumnToContents(i)

    def _populate_staff_table(self):
        """Apply the Staff age filter to the WHOLE staff set (no cap) and refresh counts."""
        m = self._staff_model
        rows = m.rows
        idx = range(len(rows))
        if hasattr(self, '_staff_age_min'):
            mn, mx = self._staff_age_min.value(), self._staff_age_max.value()
            if mn or mx:
                idx = [i for i in idx if rows[i][3] >= mn and (not mx or rows[i][3] <= mx)]
        m.set_base(list(idx))
        text = self._scouting_count_text(m, 'staff')
        self._staff_count_lbl.setText(text)
        self._status_info_lbl.setText(text)
        if self._main_stack.currentIndex() == self._VIEW_INDEX['staff']:
            self._update_header_for_view('staff')

    @staticmethod
    def _scouting_count_text(m, noun):
        """'54,058 staff' when everything is shown, else '1,234 of 54,058 staff'."""
        shown, total = m.rowCount(), m.total()
        return f'{shown:,} {noun}' if shown == total else f'{shown:,} of {total:,} {noun}'

    def _clear_staff_filter(self):
        self._staff_age_min.blockSignals(True)
        self._staff_age_max.blockSignals(True)
        self._staff_age_min.setValue(0)
        self._staff_age_max.setValue(0)
        self._staff_age_min.blockSignals(False)
        self._staff_age_max.blockSignals(False)
        self._populate_staff_table()

    def _make_view_welcome(self):
        w = QWidget()
        w.setStyleSheet(f"background: {COLORS['window_bg']};")

        outer = QVBoxLayout(w)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setContentsMargins(0, 0, 0, 0)

        inner = QWidget()
        inner.setFixedWidth(340)
        vbox = QVBoxLayout(inner)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon / logo
        icon_lbl = QLabel('⚽')
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 48px; background: transparent;")
        vbox.addWidget(icon_lbl)
        vbox.addSpacing(16)

        # Title
        title_lbl = QLabel('FM Backroom 24')
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(
            "font-family: 'Barlow Condensed', 'Barlow', 'Arial Narrow', sans-serif;"
            f" font-size: 28px; font-weight: 700; color: {COLORS['text_primary']};"
            " background: transparent;"
        )
        vbox.addWidget(title_lbl)
        vbox.addSpacing(8)

        # Subtitle
        sub_lbl = QLabel('Load a save file to get started')
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet(
            f"font-size: 13px; color: {COLORS['text_secondary']}; background: transparent;"
        )
        vbox.addWidget(sub_lbl)
        vbox.addSpacing(28)

        # Load button
        self._welcome_load_btn = QPushButton('Load Save')
        self._welcome_load_btn.setFixedHeight(36)
        self._welcome_load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._welcome_load_btn.setStyleSheet(_BTN_SS(accent=True))
        self._welcome_load_btn.clicked.connect(self._load_file)
        vbox.addWidget(self._welcome_load_btn)
        vbox.addSpacing(12)

        # Hint
        hint_lbl = QLabel('Supports FM24 .fm save files')
        hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_lbl.setStyleSheet(
            f"font-size: 11px; color: {COLORS['text_dim']}; background: transparent;"
        )
        vbox.addWidget(hint_lbl)
        vbox.addSpacing(10)

        about_btn = QPushButton('About')
        about_btn.setFlat(True)
        about_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        about_btn.setStyleSheet(
            f"QPushButton {{ color: {COLORS['text_dim']}; font-size: 11px; background: transparent;"
            f" border: none; }} QPushButton:hover {{ color: {COLORS['accent_hover']}; }}")
        about_btn.clicked.connect(lambda checked: AboutDialog(self).exec())
        vbox.addWidget(about_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        outer.addWidget(inner)
        return w

    def _make_view_club_staff(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        qf_bar, qf_row = self._make_quick_filters_frame()

        cstaff_age_lbl = QLabel('Age:')
        cstaff_age_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        qf_row.addWidget(cstaff_age_lbl)
        self._club_staff_age_min = QSpinBox()
        self._club_staff_age_min.setRange(0, 99)
        self._club_staff_age_min.setValue(0)
        self._club_staff_age_min.setFixedSize(52, 26)
        self._club_staff_age_min.valueChanged.connect(lambda _v: self._populate_club_staff_table())
        qf_row.addWidget(self._club_staff_age_min)
        cstaff_dash = QLabel('-')
        cstaff_dash.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        qf_row.addWidget(cstaff_dash)
        self._club_staff_age_max = QSpinBox()
        self._club_staff_age_max.setRange(0, 99)
        self._club_staff_age_max.setValue(0)
        self._club_staff_age_max.setFixedSize(52, 26)
        self._club_staff_age_max.valueChanged.connect(lambda _v: self._populate_club_staff_table())
        qf_row.addWidget(self._club_staff_age_max)

        qf_row.addStretch()

        cstaff_clear_btn = QPushButton('Clear')
        cstaff_clear_btn.setFixedHeight(26)
        cstaff_clear_btn.setStyleSheet(
            f"background:transparent; color:{COLORS['text_secondary']}; font-size:11px;"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:0 10px;")
        cstaff_clear_btn.clicked.connect(self._clear_club_staff_filter)
        qf_row.addWidget(cstaff_clear_btn)

        vbox.addWidget(qf_bar)

        self._club_staff_table = QTableWidget()
        self._club_staff_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._club_staff_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._club_staff_table.setAlternatingRowColors(True)
        self._club_staff_table.verticalHeader().setVisible(False)
        self._club_staff_table.setShowGrid(False)
        self._club_staff_table.setSortingEnabled(True)
        self._club_staff_table.setStyleSheet(self._staff_table.styleSheet())
        shdr = self._club_staff_table.horizontalHeader()
        shdr.setHighlightSections(False)
        shdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # Coaching cols (Section B confirmed + Section A extras), then personality
        _STAFF_COACHING_COLS = [
            'Atk', 'Def', 'Fit', 'Mnt', 'SPc', 'Tac', 'Tch', 'WwY',  # coaching area
            'Det', 'Mot', 'PMg',                                          # mental
            'JPA', 'JSA', 'TKn',                                          # knowledge
            'Neg', 'GKH', 'GKS',                                          # other
        ]
        self._club_staff_coaching_cols = _STAFF_COACHING_COLS
        # Map short label → coaching dict key
        self._coaching_col_map = {
            'Atk': 'Attacking', 'Def': 'Defending', 'Fit': 'Fitness',
            'Mnt': 'Mental',    'SPc': 'Set Pieces','Tac': 'Tactical',
            'Tch': 'Technical', 'WwY': 'WwY',
            'Det': 'Determination', 'Mot': 'Motivating', 'PMg': 'People Mgt',
            'JPA': 'JPA',       'JSA': 'JSA',       'TKn': 'Tact Knowledge',
            'Neg': 'Negotiating','GKH': 'GK Handling','GKS': 'GK Shot Stop',
        }
        cols = ['Name', 'Nation', 'Age'] + _STAFF_COACHING_COLS + [
            'Adp', 'Amb', 'Loy', 'Prs', 'Pro', 'Spt', 'Tmp', 'Ctr']
        self._club_staff_table.setColumnCount(len(cols))
        self._club_staff_table.setHorizontalHeaderLabels(cols)
        for i, col in enumerate(cols):
            if col in _STAFF_COL_TOOLTIPS:
                self._club_staff_table.horizontalHeaderItem(i).setToolTip(_STAFF_COL_TOOLTIPS[col])
        for i in range(len(cols)):
            shdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        widths = {0: 220, 1: 45, 2: 38}
        for i in range(3, len(cols)):
            widths[i] = 35
        for i, cw in widths.items():
            self._club_staff_table.setColumnWidth(i, cw)
        shdr.setSectionsMovable(True)
        shdr.setFirstSectionMovable(False)
        shdr.setStretchLastSection(False)
        self._club_staff_table.cellDoubleClicked.connect(self._on_club_staff_double_click)
        vbox.addWidget(self._club_staff_table, 1)
        return w

    def _populate_club_staff_table(self):
        if not self._save_data or not self._current_club:
            return
        club = self._current_club
        people = self._save_data.get('people', [])
        employment = self._save_data.get('employment', {})
        club_staff = self._save_data.get('club_staff', {})

        # Primary: club-side staff array (coaches, physios, scouts, analysts).
        # Fallback: employment records for managers / ex-player coaches.
        cid = club['id']
        staff_pids = set(club_staff.get(cid, []))
        # Add any employment-linked staff not already in the array
        club_entity_id = cid + 1
        for pid, eid in employment.items():
            if eid == club_entity_id:
                staff_pids.add(pid)

        people_by_id = {p.get('id'): p for p in people}
        staff = [people_by_id[pid] for pid in staff_pids
                 if pid in people_by_id and 'ca' not in people_by_id[pid]]
        if hasattr(self, '_club_staff_age_min'):
            mn, mx = self._club_staff_age_min.value(), self._club_staff_age_max.value()
            staff = [p for p in staff if _age_in_range(p, mn, mx)]
        staff.sort(key=lambda p: p.get('name', ''))

        self._club_staff_table.setSortingEnabled(False)
        self._club_staff_table.setRowCount(len(staff))
        coaching_col_map = getattr(self, '_coaching_col_map', {})
        coaching_cols = getattr(self, '_club_staff_coaching_cols', [])
        for row, p in enumerate(staff):
            pid = p.get('id', -1)
            name = p.get('name', '')
            nation_id = p.get('nation', 0)
            flag = _nation_cell(nation_id, '')
            age = _age(p)
            coaching = p.get('coaching', {})
            coaching_items = []
            for short_label in coaching_cols:
                key = coaching_col_map.get(short_label, short_label)
                v = coaching.get(key)
                coaching_items.append(_SortItem(str(v) if v is not None else '', v if v is not None else -1))
            pers = p.get('personality', [])
            pers_items = []
            for idx in range(8):
                v = pers[idx] if idx < len(pers) else None
                pers_items.append(_SortItem(str(v) if v is not None else '', v if v is not None else -1))
            name_item = _SortItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, pid)
            items = [name_item, _SortItem(flag), _SortItem(str(age), age)] + coaching_items + pers_items
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._club_staff_table.setItem(row, col, item)
        self._club_staff_table.setSortingEnabled(True)
        for i in range(self._club_staff_table.columnCount()):
            self._club_staff_table.resizeColumnToContents(i)
        self._status_info_lbl.setText(f'{len(staff):,} staff')

    def _clear_club_staff_filter(self):
        self._club_staff_age_min.blockSignals(True)
        self._club_staff_age_max.blockSignals(True)
        self._club_staff_age_min.setValue(0)
        self._club_staff_age_max.setValue(0)
        self._club_staff_age_min.blockSignals(False)
        self._club_staff_age_max.blockSignals(False)
        self._populate_club_staff_table()

    def _make_view_shortlist(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # Filter bar — same structure as Players' Quick Filters
        filter_hdr = QFrame()
        filter_hdr.setObjectName('qfStrip')  # scoped: a bare QSS would leak the border onto child QLabels
        filter_hdr.setStyleSheet(
            f"QFrame#qfStrip {{ background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']}; }}")
        filter_vbox = QVBoxLayout(filter_hdr)
        filter_vbox.setContentsMargins(0, 0, 0, 0)
        filter_vbox.setSpacing(0)

        sl_title_row = QHBoxLayout()
        sl_title_row.setContentsMargins(16, 10, 16, 6)
        sl_title_lbl = QLabel('Quick Filters')
        sl_title_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        sl_title_row.addWidget(sl_title_lbl)
        sl_title_row.addStretch()
        filter_vbox.addLayout(sl_title_row)

        sl_filter_row = QHBoxLayout()
        sl_filter_row.setContentsMargins(16, 0, 16, 10)
        sl_filter_row.setSpacing(8)

        self._shortlist_name_filter = QLineEdit()
        self._shortlist_name_filter.setPlaceholderText('Filter by name...')
        self._shortlist_name_filter.setFixedHeight(26)
        self._shortlist_name_filter.setMaximumWidth(220)
        self._shortlist_name_filter.setStyleSheet(
            f"background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:3px 8px; font-size:11px;")
        self._shortlist_name_filter.returnPressed.connect(self._apply_shortlist_filter)
        sl_filter_row.addWidget(self._shortlist_name_filter)

        self._shortlist_pos_filter = QComboBox()
        self._shortlist_pos_filter.addItem('All Positions')
        self._shortlist_pos_filter.addItems(POSITIONS)
        self._shortlist_pos_filter.setFixedHeight(26)
        self._shortlist_pos_filter.setFixedWidth(130)
        self._shortlist_pos_filter.setStyleSheet(
            f"background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:2px 6px; font-size:11px;")
        self._shortlist_pos_filter.currentIndexChanged.connect(self._apply_shortlist_filter)
        sl_filter_row.addWidget(self._shortlist_pos_filter)

        sl_min_ca_lbl = QLabel('Min CA:')
        sl_min_ca_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        sl_filter_row.addWidget(sl_min_ca_lbl)
        self._shortlist_ca_filter = QSpinBox()
        self._shortlist_ca_filter.setRange(0, 200)
        self._shortlist_ca_filter.setValue(0)
        self._shortlist_ca_filter.setFixedSize(56, 26)
        self._shortlist_ca_filter.valueChanged.connect(self._apply_shortlist_filter)
        sl_filter_row.addWidget(self._shortlist_ca_filter)

        sl_min_pa_lbl = QLabel('Min PA:')
        sl_min_pa_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        sl_filter_row.addWidget(sl_min_pa_lbl)
        self._shortlist_pa_filter = QSpinBox()
        self._shortlist_pa_filter.setRange(0, 200)
        self._shortlist_pa_filter.setValue(0)
        self._shortlist_pa_filter.setFixedSize(56, 26)
        self._shortlist_pa_filter.valueChanged.connect(self._apply_shortlist_filter)
        sl_filter_row.addWidget(self._shortlist_pa_filter)

        sl_age_lbl = QLabel('Age:')
        sl_age_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        sl_filter_row.addWidget(sl_age_lbl)
        self._shortlist_age_min = QSpinBox()
        self._shortlist_age_min.setRange(0, 99)
        self._shortlist_age_min.setValue(0)
        self._shortlist_age_min.setFixedSize(52, 26)
        self._shortlist_age_min.valueChanged.connect(self._apply_shortlist_filter)
        sl_filter_row.addWidget(self._shortlist_age_min)
        sl_dash = QLabel('-')
        sl_dash.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        sl_filter_row.addWidget(sl_dash)
        self._shortlist_age_max = QSpinBox()
        self._shortlist_age_max.setRange(0, 99)
        self._shortlist_age_max.setValue(0)
        self._shortlist_age_max.setFixedSize(52, 26)
        self._shortlist_age_max.valueChanged.connect(self._apply_shortlist_filter)
        sl_filter_row.addWidget(self._shortlist_age_max)

        sl_dev_lbl = QLabel('Min Dev:')
        sl_dev_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        sl_filter_row.addWidget(sl_dev_lbl)
        self._shortlist_dev_filter = QSpinBox()
        self._shortlist_dev_filter.setRange(0, 20)
        self._shortlist_dev_filter.setValue(0)
        self._shortlist_dev_filter.setFixedSize(52, 26)
        self._shortlist_dev_filter.valueChanged.connect(self._apply_shortlist_filter)
        sl_filter_row.addWidget(self._shortlist_dev_filter)

        sl_filter_row.addStretch()

        sl_clear_btn = QPushButton('Clear')
        sl_clear_btn.setFixedHeight(26)
        sl_clear_btn.setStyleSheet(
            f"background:transparent; color:{COLORS['text_secondary']}; font-size:11px;"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:0 10px;")
        sl_clear_btn.clicked.connect(self._clear_shortlist_filter)
        sl_filter_row.addWidget(sl_clear_btn)

        filter_vbox.addLayout(sl_filter_row)
        vbox.addWidget(filter_hdr)

        self._shortlist_table = QTableWidget()
        self._shortlist_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._shortlist_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._shortlist_table.setAlternatingRowColors(True)
        self._shortlist_table.verticalHeader().setVisible(False)
        self._shortlist_table.setShowGrid(False)
        self._shortlist_table.setSortingEnabled(True)
        shdr = self._shortlist_table.horizontalHeader()
        shdr.setHighlightSections(False)
        shdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cols = ['Name', 'Club', 'Type', 'Pos', 'CA', 'PA', 'Age', 'Nation']
        self._shortlist_table.setColumnCount(len(cols))
        self._shortlist_table.setHorizontalHeaderLabels(cols)
        for i in range(len(cols)):
            shdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        for i, cw in {0: 150, 1: 160, 2: 55, 3: 55, 4: _ability_w(), 5: _ability_w(), 6: 40, 7: 50}.items():
            self._shortlist_table.setColumnWidth(i, cw)
        self._shortlist_table.setItemDelegate(_RowMarkDelegate(self._shortlist_table))
        _set_star_delegates(self._shortlist_table, 4, 5)
        shdr.setSectionsMovable(True)
        shdr.setFirstSectionMovable(False)
        shdr.setStretchLastSection(True)

        self._shortlist_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._shortlist_table.customContextMenuRequested.connect(
            lambda pos: self._shortlist_context_menu(
                self._shortlist_table, self._shortlist, self._apply_shortlist_filter, pos))

        self._shortlist_empty_lbl = QLabel(
            'No players shortlisted.\nDouble-click a player and choose Add to Shortlist.')
        self._shortlist_empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._shortlist_empty_lbl.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-size:13px; padding:40px;")
        self._shortlist_empty_lbl.setWordWrap(True)

        self._shortlist_stack = QStackedWidget()
        self._shortlist_stack.addWidget(self._shortlist_empty_lbl)
        self._shortlist_stack.addWidget(self._shortlist_table)
        vbox.addWidget(self._shortlist_stack, 1)
        return w

    def _add_to_shortlist(self, person):
        """Players ('ca' key) go to the Player Shortlist, staff to the Staff Shortlist."""
        is_player = 'ca' in person
        lst = self._shortlist if is_player else self._staff_shortlist
        pid = person.get('id', -1)
        if any(p.get('id') == pid for p in lst):
            return
        lst.append(person)
        if is_player:
            self._populate_shortlist()
        else:
            self._apply_staff_shortlist_filter()
        kind = 'player' if is_player else 'staff'
        self._status.showMessage(f'Added {person.get("name", "")} to {kind} shortlist', 2000)

    def _shortlist_context_menu(self, table, lst, refresh, pos):
        """Right-click a shortlist row -> Remove from Shortlist."""
        item = table.item(table.rowAt(pos.y()), 0)
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        remove = menu.addAction(f'Remove from Shortlist: {item.text()}')
        if menu.exec(table.viewport().mapToGlobal(pos)) == remove:
            lst[:] = [p for p in lst if p.get('id') != pid]
            refresh()
            self._update_header_for_view('shortlist' if lst is self._shortlist else 'staff_shortlist')

    def _populate_shortlist(self, people=None):
        people = people if people is not None else self._shortlist
        self._shortlist_table.setSortingEnabled(False)
        self._shortlist_table.setRowCount(len(people))
        clubs = self._save_data.get('clubs', []) if self._save_data else []
        squads = self._save_data.get('squads', {}) if self._save_data else {}
        club_staff = self._save_data.get('club_staff', {}) if self._save_data else {}
        employment = self._save_data.get('employment', {}) if self._save_data else {}
        club_by_id = {c['id']: c['name'] for c in clubs}
        club_by_entity = {c['id'] + 1: c['name'] for c in clubs}
        staff_club: dict[int, int] = {}
        for cid, pids in club_staff.items():
            for ppid in pids:
                if ppid not in staff_club:
                    staff_club[ppid] = cid
        for row, p in enumerate(people):
            pid = p.get('id', -1)
            is_player = 'ca' in p
            name = p.get('name', '')
            # Club
            if is_player:
                cid = squads.get(pid)
                club_name = club_by_id.get(cid, '') if cid else ''
            else:
                cid = staff_club.get(pid)
                if cid is not None:
                    club_name = club_by_id.get(cid, '')
                else:
                    eid = employment.get(pid)
                    club_name = club_by_entity.get(eid, '') if eid else ''
            ptype = 'Player' if is_player else 'Staff'
            pos = _primary_pos(p['positions']) if is_player and p.get('positions') else '-'
            ca = str(p.get('ca', '-')) if is_player else '-'
            pa = str(p.get('pa', '-')) if is_player else '-'
            age = _age(p)
            nation = _nation_cell(p.get('nation', 0))
            name_item = _SortItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, pid)
            row_items = [
                name_item,
                _SortItem(club_name),
                _SortItem(ptype),
                _SortItem(pos, _POS_SORT_ORDER.get(pos, 99)),
                _SortItem(ca, p.get('ca', -1) if is_player else -1),
                _SortItem(pa, p.get('pa', -1) if is_player else -1),
                _SortItem(str(age), age),
                _SortItem(nation),
            ]
            for col, item in enumerate(row_items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._shortlist_table.setItem(row, col, item)
        _mark_rows(self._shortlist_table, _queue_map(self._queue), {})
        self._shortlist_table.setSortingEnabled(True)
        for c in range(self._shortlist_table.columnCount()):
            self._shortlist_table.resizeColumnToContents(c)
        n = len(people)
        self._shortlist_stack.setCurrentIndex(1 if n > 0 else 0)

    def _clear_shortlist_filter(self):
        self._shortlist_name_filter.blockSignals(True)
        self._shortlist_pos_filter.blockSignals(True)
        self._shortlist_ca_filter.blockSignals(True)
        self._shortlist_pa_filter.blockSignals(True)
        self._shortlist_age_min.blockSignals(True)
        self._shortlist_age_max.blockSignals(True)
        self._shortlist_dev_filter.blockSignals(True)
        self._shortlist_name_filter.clear()
        self._shortlist_pos_filter.setCurrentIndex(0)
        self._shortlist_ca_filter.setValue(0)
        self._shortlist_pa_filter.setValue(0)
        self._shortlist_age_min.setValue(0)
        self._shortlist_age_max.setValue(0)
        self._shortlist_dev_filter.setValue(0)
        self._shortlist_name_filter.blockSignals(False)
        self._shortlist_pos_filter.blockSignals(False)
        self._shortlist_ca_filter.blockSignals(False)
        self._shortlist_pa_filter.blockSignals(False)
        self._shortlist_age_min.blockSignals(False)
        self._shortlist_age_max.blockSignals(False)
        self._shortlist_dev_filter.blockSignals(False)
        self._apply_shortlist_filter()

    def _apply_shortlist_filter(self):
        name_q = self._shortlist_name_filter.text().strip().lower()
        pos_q = self._shortlist_pos_filter.currentText()
        if pos_q == 'All Positions':
            pos_q = ''
        min_ca = self._shortlist_ca_filter.value()
        min_pa = self._shortlist_pa_filter.value()
        age_min = self._shortlist_age_min.value()
        age_max = self._shortlist_age_max.value()
        min_dev = self._shortlist_dev_filter.value()

        filtered = self._shortlist
        if name_q:
            filtered = [p for p in filtered if name_q in p.get('name', '').lower()]
        if pos_q and pos_q in POSITIONS:
            pos_idx = POSITIONS.index(pos_q)
            filtered = [p for p in filtered
                        if p.get('positions') and pos_idx < len(p['positions'])
                        and p['positions'][pos_idx] == max(p['positions'])]
        if min_ca:
            filtered = [p for p in filtered if 'ca' not in p or (p.get('ca') or 0) >= min_ca]
        if min_pa:
            filtered = [p for p in filtered if 'ca' not in p or (p.get('pa') or 0) >= min_pa]
        filtered = [p for p in filtered if _age_in_range(p, age_min, age_max)]
        if min_dev:
            filtered = [p for p in filtered if 'ca' not in p or (_progress_rate(p) or 0) >= min_dev]

        self._populate_shortlist(filtered)

    def _make_view_staff_shortlist(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        hdr, hdr_row = self._make_quick_filters_frame()
        age_lbl = QLabel('Age:')
        age_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        hdr_row.addWidget(age_lbl)
        self._staff_sl_age_min = QSpinBox()
        self._staff_sl_age_min.setRange(0, 99)
        self._staff_sl_age_min.setValue(0)
        self._staff_sl_age_min.setFixedSize(52, 26)
        self._staff_sl_age_min.valueChanged.connect(lambda _v: self._apply_staff_shortlist_filter())
        hdr_row.addWidget(self._staff_sl_age_min)
        dash = QLabel('-')
        dash.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        hdr_row.addWidget(dash)
        self._staff_sl_age_max = QSpinBox()
        self._staff_sl_age_max.setRange(0, 99)
        self._staff_sl_age_max.setValue(0)
        self._staff_sl_age_max.setFixedSize(52, 26)
        self._staff_sl_age_max.valueChanged.connect(lambda _v: self._apply_staff_shortlist_filter())
        hdr_row.addWidget(self._staff_sl_age_max)
        hdr_row.addStretch()
        clear_btn = QPushButton('Clear')
        clear_btn.setFixedHeight(26)
        clear_btn.setStyleSheet(
            f"background:transparent; color:{COLORS['text_secondary']}; font-size:11px;"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:0 10px;")
        clear_btn.clicked.connect(self._clear_staff_shortlist_filter)
        hdr_row.addWidget(clear_btn)
        vbox.addWidget(hdr)

        self._staff_shortlist_table = self._make_staff_table()
        self._staff_shortlist_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._staff_shortlist_table.customContextMenuRequested.connect(
            lambda pos: self._shortlist_context_menu(
                self._staff_shortlist_table, self._staff_shortlist,
                self._apply_staff_shortlist_filter, pos))

        self._staff_shortlist_empty_lbl = QLabel(
            'No staff shortlisted.\nDouble-click a staff member and choose Add to Shortlist.')
        self._staff_shortlist_empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._staff_shortlist_empty_lbl.setStyleSheet(
            f"color:{COLORS['text_dim']}; font-size:13px; padding:40px;")
        self._staff_shortlist_empty_lbl.setWordWrap(True)

        self._staff_shortlist_stack = QStackedWidget()
        self._staff_shortlist_stack.addWidget(self._staff_shortlist_empty_lbl)
        self._staff_shortlist_stack.addWidget(self._staff_shortlist_table)
        vbox.addWidget(self._staff_shortlist_stack, 1)
        return w

    def _clear_staff_shortlist_filter(self):
        self._staff_sl_age_min.blockSignals(True)
        self._staff_sl_age_max.blockSignals(True)
        self._staff_sl_age_min.setValue(0)
        self._staff_sl_age_max.setValue(0)
        self._staff_sl_age_min.blockSignals(False)
        self._staff_sl_age_max.blockSignals(False)
        self._apply_staff_shortlist_filter()

    def _apply_staff_shortlist_filter(self):
        mn, mx = self._staff_sl_age_min.value(), self._staff_sl_age_max.value()
        staff = [p for p in self._staff_shortlist if _age_in_range(p, mn, mx)]
        if self._save_data:
            self._fill_staff_rows(self._staff_shortlist_table, staff)
        self._staff_shortlist_stack.setCurrentIndex(1 if staff else 0)

    def _make_view_reports(self):
        from PyQt6.QtWidgets import QComboBox
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        filter_frame, filter_row2 = self._make_quick_filters_frame()
        vbox.addWidget(filter_frame)

        self._report_name_filter = QLineEdit()
        self._report_name_filter.setPlaceholderText('Filter by name...')
        self._report_name_filter.setFixedHeight(26)
        self._report_name_filter.setMaximumWidth(220)
        # Players' name box ends up ~156px wide via layout slack; the extra
        # Position/Role bar here would otherwise squeeze it to ~125px.
        self._report_name_filter.setMinimumWidth(156)
        self._report_name_filter.setStyleSheet(
            f"background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:3px 8px; font-size:11px;")
        self._report_name_filter.returnPressed.connect(self._on_report_age_changed)
        filter_row2.addWidget(self._report_name_filter)

        self._report_pos_bar = QWidget()
        self._report_pos_bar.setObjectName('rptBar')
        self._report_pos_bar.setStyleSheet('QWidget#rptBar{background:transparent;}')  # plain QWidget would paint the app bg over the strip
        self._report_pos_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        pos_row = QHBoxLayout(self._report_pos_bar)
        pos_row.setContentsMargins(0, 0, 0, 0)
        pos_row.setSpacing(6)
        pos_lbl = QLabel('Position:')
        pos_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        pos_row.addWidget(pos_lbl)
        self._report_pos_combo = QComboBox()
        self._report_pos_combo.addItems(POSITIONS)
        self._report_pos_combo.setFixedHeight(26)
        self._report_pos_combo.setFixedWidth(130)
        self._report_pos_combo.setStyleSheet(
            f"background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:2px 6px; font-size:11px;")
        self._report_pos_combo.currentTextChanged.connect(self._on_report_pos_changed)
        pos_row.addWidget(self._report_pos_combo)
        self._report_pos_bar.setVisible(False)
        filter_row2.addWidget(self._report_pos_bar)

        # Role picker bar (best_role mode)
        self._report_role_bar = QWidget()
        self._report_role_bar.setObjectName('rptBar')
        self._report_role_bar.setStyleSheet('QWidget#rptBar{background:transparent;}')
        self._report_role_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        role_row = QHBoxLayout(self._report_role_bar)
        role_row.setContentsMargins(0, 0, 0, 0)
        role_row.setSpacing(6)
        role_lbl = QLabel('Role:')
        role_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        role_row.addWidget(role_lbl)
        self._report_role_combo = QComboBox()
        self._report_role_combo.setFixedHeight(26)
        self._report_role_combo.setFixedWidth(220)
        self._report_role_combo.setStyleSheet(
            f"background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:2px 6px; font-size:11px;")
        for group, names in role_names_by_group():
            sep = self._report_role_combo.count()
            self._report_role_combo.addItem(f'── {group} ──')
            self._report_role_combo.model().item(sep).setEnabled(False)
            for name in names:
                self._report_role_combo.addItem(name)
        self._report_role_combo.setCurrentIndex(1)  # first real role, skip group header
        self._report_role_combo.currentTextChanged.connect(self._on_report_role_changed)
        role_row.addWidget(self._report_role_combo)
        minpos_tt = 'Ratings use attributes only; this hides players who cannot play the position'
        minpos_lbl = QLabel('Min position:')
        minpos_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        minpos_lbl.setToolTip(minpos_tt)
        role_row.addWidget(minpos_lbl)
        # 12+ = mid Competent (10-14) and up; Natural 20 / Accomplished 15-19 always pass. 1 = no position check.
        self._report_minpos = QSpinBox()
        self._report_minpos.setRange(1, 20)
        self._report_minpos.setValue(_MIN_POS_DEFAULT)
        self._report_minpos.setFixedSize(52, 26)
        self._report_minpos.setToolTip(minpos_tt)
        self._report_minpos.valueChanged.connect(self._on_report_age_changed)
        role_row.addWidget(self._report_minpos)
        self._weights_lbl = QLabel()
        self._report_role_bar.setVisible(False)
        filter_row2.addWidget(self._report_role_bar)

        min_ca_lbl = QLabel('Min CA:')
        min_ca_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row2.addWidget(min_ca_lbl)
        self._report_ca_filter = QSpinBox()
        self._report_ca_filter.setRange(0, 200)
        self._report_ca_filter.setValue(0)
        self._report_ca_filter.setFixedSize(56, 26)
        self._report_ca_filter.valueChanged.connect(self._on_report_age_changed)
        filter_row2.addWidget(self._report_ca_filter)

        min_pa_lbl = QLabel('Min PA:')
        min_pa_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row2.addWidget(min_pa_lbl)
        self._report_pa_filter = QSpinBox()
        self._report_pa_filter.setRange(0, 200)
        self._report_pa_filter.setValue(0)
        self._report_pa_filter.setFixedSize(56, 26)
        self._report_pa_filter.valueChanged.connect(self._on_report_age_changed)
        filter_row2.addWidget(self._report_pa_filter)

        # Age range filter — always visible
        age_lbl = QLabel('Age:')
        age_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row2.addWidget(age_lbl)
        self._report_age_min = QSpinBox()
        self._report_age_min.setRange(0, 99)
        self._report_age_min.setValue(0)
        self._report_age_min.setFixedSize(52, 26)
        filter_row2.addWidget(self._report_age_min)
        dash_lbl = QLabel('-')
        dash_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row2.addWidget(dash_lbl)
        self._report_age_max = QSpinBox()
        self._report_age_max.setRange(0, 99)
        self._report_age_max.setValue(0)
        self._report_age_max.setFixedSize(52, 26)
        filter_row2.addWidget(self._report_age_max)
        self._report_age_min.valueChanged.connect(self._on_report_age_changed)
        self._report_age_max.valueChanged.connect(self._on_report_age_changed)

        dev_lbl = QLabel('Min Dev:')
        dev_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row2.addWidget(dev_lbl)
        self._report_dev_filter = QSpinBox()
        self._report_dev_filter.setRange(0, 20)
        self._report_dev_filter.setValue(0)
        self._report_dev_filter.setFixedSize(52, 26)
        self._report_dev_filter.valueChanged.connect(self._on_report_age_changed)
        filter_row2.addWidget(self._report_dev_filter)

        filter_row2.addStretch()

        self._report_clear_btn = QPushButton('Clear')
        self._report_clear_btn.setFixedHeight(26)
        self._report_clear_btn.setStyleSheet(
            f"background:transparent; color:{COLORS['text_secondary']}; font-size:11px;"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:0 10px;")
        self._report_clear_btn.clicked.connect(self._clear_report_filter)
        filter_row2.addWidget(self._report_clear_btn)

        self._reports_table = QTableWidget()
        self._reports_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._reports_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._reports_table.setAlternatingRowColors(True)
        self._reports_table.verticalHeader().setVisible(False)
        self._reports_table.setShowGrid(False)
        self._reports_table.setSortingEnabled(True)

        self._reports_inj_delegate = _PosBadgeDelegate(self._reports_table)
        self._reports_pos_delegate = _PosBadgeDelegate(self._reports_table)
        self._reports_table.setItemDelegateForColumn(1, self._reports_inj_delegate)
        self._reports_table.setItemDelegateForColumn(2, self._reports_pos_delegate)
        self._reports_table.setItemDelegate(_RowMarkDelegate(self._reports_table))
        self._reports_table.setItemDelegateForColumn(8, _HGBadgeDelegate('hgp', self._reports_table))
        _set_star_delegates(self._reports_table, 3, 4)

        rhdr = self._reports_table.horizontalHeader()
        rhdr.setHighlightSections(False)
        rhdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cols = ['Name', 'INJ', 'Pos', 'CA', 'PA', 'Dev', 'Age', 'Nation', 'HGP', 'Club', 'CtrE'] + _ATTR_ABBREV
        self._reports_table.setColumnCount(len(cols))
        self._reports_table.setHorizontalHeaderLabels(cols)
        for i, col in enumerate(cols):
            if col in _COL_TT:
                self._reports_table.horizontalHeaderItem(i).setToolTip(_COL_TT[col])
        for i in range(len(cols)):
            rhdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        fixed_widths = {0: 150, 1: 35, 2: 55, 3: _ability_w(), 4: _ability_w(), 5: 45, 6: 40, 7: 50, 8: 62, 9: 160, 10: 65}
        for i, cw in fixed_widths.items():
            self._reports_table.setColumnWidth(i, cw)
        for i in range(11, len(cols)):
            self._reports_table.setColumnWidth(i, 35)
        rhdr.setSectionsMovable(True)
        rhdr.setFirstSectionMovable(False)
        rhdr.setStretchLastSection(True)
        self._reports_table.doubleClicked.connect(self._on_reports_table_dblclick)
        self._reports_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._reports_table.customContextMenuRequested.connect(
            lambda pos: self._on_list_table_context_menu(self._reports_table, pos))
        vbox.addWidget(self._reports_table, 1)
        return w

    def _get_report_players(self, key, pos_name=None, role_name=None):
        self._report_ratings = {}
        self._report_total = 0
        if not self._save_data:
            return []
        people = self._save_data.get('people', [])
        if key == 'prospects':
            c = [p for p in people if p.get('pa', 0) >= 160]
            c.sort(key=lambda p: -p['pa'])
        elif key == 'wonderkids':
            c = [p for p in people
                 if p.get('ca') and _age(p) <= 21
                 and p.get('pa', 0) >= 150]
            c.sort(key=lambda p: -p['pa'])
        elif key == 'best_pos':
            pname = pos_name or (POSITIONS[0] if POSITIONS else '')
            if pname not in POSITIONS:
                return []
            idx = POSITIONS.index(pname)
            c = [p for p in people if p.get('positions')
                 and p['positions'][idx] == max(p['positions'])]
            c.sort(key=lambda p: -p.get('ca', 0))
        elif key == 'best_role':
            rname = role_name or ''
            role_weights = _weights_mod.get_role_weights(self._active_preset, rname)
            mn_age = self._report_age_min.value()
            mx_age = self._report_age_max.value()
            min_pos = self._report_minpos.value()
            pos_idx = [POSITIONS.index(x) for x in role_positions(rname)]
            rated = []
            for p in people:
                if not _age_in_range(p, mn_age, mx_age):
                    continue
                if min_pos > 1 and pos_idx:  # attribute-only ratings rate a centre-back as a forward: require the position familiarity
                    pl = p.get('positions')
                    if not pl or max(pl[i] for i in pos_idx) < min_pos:
                        continue
                r = role_rating(p, rname, role_weights)
                if r is not None:
                    rated.append((p, r))
            rated.sort(key=lambda x: -x[1])
            self._report_ratings = {p.get('id', -1): r for p, r in rated}
            c = [p for p, _ in rated]
        else:
            return []
        # Quick-filter fields (name/CA/PA/age/dev) — shared by every report mode.
        mn_age = self._report_age_min.value()
        mx_age = self._report_age_max.value()
        c = [p for p in c if _age_in_range(p, mn_age, mx_age)]
        name_q = self._report_name_filter.text().strip().lower()
        if name_q:
            c = [p for p in c if name_q in p.get('name', '').lower()]
        min_ca = self._report_ca_filter.value()
        if min_ca:
            c = [p for p in c if (p.get('ca') or 0) >= min_ca]
        min_pa = self._report_pa_filter.value()
        if min_pa:
            c = [p for p in c if (p.get('pa') or 0) >= min_pa]
        min_dev = self._report_dev_filter.value()
        if min_dev:
            c = [p for p in c if (_progress_rate(p) or 0) >= min_dev]
        self._report_total = len(c)  # reports are deliberately top-200; header says so
        return c[:200]

    def _populate_reports_table(self, players):
        if not self._save_data:
            return
        clubs = self._save_data.get('clubs', [])
        squads = self._save_data.get('squads', {})
        club_by_id = {c['id']: c['name'] for c in clubs}
        is_role = self._current_report_key == 'best_role'
        ratings = getattr(self, '_report_ratings', {})
        rhdr = self._reports_table.horizontalHeader()
        col4_label = 'Rating' if is_role else 'Dev'
        self._reports_table.setHorizontalHeaderItem(5, _SortItem(col4_label))
        self._reports_table.horizontalHeaderItem(5).setToolTip(_COL_TT.get(col4_label, ''))
        rhdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._reports_table.setSortingEnabled(False)
        self._reports_table.setRowCount(len(players))
        self._reports_table.clearSelection()
        for row, p in enumerate(players):
            try:
                pos = _primary_pos(p['positions']) if p.get('positions') else '?'
            except Exception:
                pos = '?'
            ca = p.get('ca')
            pa = p.get('pa')
            col4_val = ratings.get(p.get('id'), None) if is_role else _progress_rate(p)
            age = _age(p)
            nation_id = p.get('nation', 0)
            flag = _nation_cell(nation_id, '')
            club_id = squads.get(p.get('id'))
            club_name = club_by_id.get(club_id, '') if club_id else ''
            injured = p.get('injured', False)
            injury_days = p.get('injury_days', 0)
            contract_end = p.get('contract_end', '')
            raw_attrs = p.get('raw_attrs', [])
            hgp = p.get('hgp', False)

            inj_item = _SortItem('INJ' if injured else '', 1 if injured else 0)
            if injured and injury_days > 0:
                inj_item.setToolTip(f"Out for {injury_days} days")

            name_item = _SortItem(p.get('name', ''))
            name_item.setData(Qt.ItemDataRole.UserRole, p.get('id', -1))
            hgp_item = _SortItem('')
            _hg_apply(hgp_item, 'hgp', bool(hgp), False)
            items = [
                name_item,
                inj_item,
                _SortItem(pos, _POS_SORT_ORDER.get(pos, 99)),
                _SortItem(str(ca) if ca is not None else '?', ca if ca is not None else -1),
                _SortItem(str(pa) if pa is not None else '?', pa if pa is not None else -1),
                _SortItem(str(col4_val) if col4_val is not None else '?',
                          col4_val if col4_val is not None else -1),
                _SortItem(str(age), age),
                _SortItem(flag),
                hgp_item,
                _SortItem(club_name),
                _SortItem(contract_end),
            ]
            for raw in raw_attrs:
                dv = max(1, min(20, round(raw / 5)))
                items.append(_SortItem(str(dv), dv))
            while len(items) < 11 + 54:
                items.append(_SortItem(''))
            for col, item in enumerate(items):
                if col == 7:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
                    f = QFont()
                    f.setPointSize(14)
                    if not item.text()[:1].isalpha():  # big font is for emoji flags only
                        item.setFont(f)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._reports_table.setItem(row, col, item)
        _mark_rows(self._reports_table, _queue_map(self._queue), {8: 'hgp'})
        self._reports_table.setSortingEnabled(True)
        self._reports_table.sortByColumn(2, Qt.SortOrder.AscendingOrder)
        # Same as Players; safe here because reports are capped at 200 rows.
        for i in range(self._reports_table.columnCount()):
            self._reports_table.resizeColumnToContents(i)
        info = f'{len(players):,} players'
        if self._current_report_key == 'best_role':
            preset = self._weights_lbl.text().strip('[]')
            if preset:
                info += f'  ·  {preset}'
        self._status_info_lbl.setText(info)
        if self._main_stack.currentIndex() == self._VIEW_INDEX['reports']:
            self._update_header_for_view('reports')  # subtitle carries role / position filter / counts

    def _on_report_pos_changed(self, pos):
        if self._current_report_key == 'best_pos' and self._save_data:
            players = self._get_report_players('best_pos', pos)
            self._populate_reports_table(players)

    def _on_report_role_changed(self, role):
        if self._current_report_key == 'best_role' and self._save_data:
            if not role or role.startswith('──'):
                return
            players = self._get_report_players('best_role', role_name=role)
            self._populate_reports_table(players)

    def _on_report_age_changed(self, *_):
        # debounce: Best-by-Role rates all ~130k people (0.25-0.36 s) so spin ticks must coalesce
        self._report_timer.start()

    def _apply_report_filters(self):
        # Despite the name, this re-derives the report for every quick-filter
        # field (name/CA/PA/age/dev), not just age — kept as-is to avoid
        # touching every connect() call site.
        if not self._current_report_key or not self._save_data:
            return
        mn, mx = self._report_age_min.value(), self._report_age_max.value()
        if mx and mn > mx:
            return
        key = self._current_report_key
        pos = self._report_pos_combo.currentText() if key == 'best_pos' else None
        role = self._report_role_combo.currentText() if key == 'best_role' else None
        if role and role.startswith('──'):
            return
        players = self._get_report_players(key, pos, role)
        self._populate_reports_table(players)

    def _clear_report_filter(self):
        self._report_name_filter.blockSignals(True)
        self._report_ca_filter.blockSignals(True)
        self._report_pa_filter.blockSignals(True)
        self._report_age_min.blockSignals(True)
        self._report_age_max.blockSignals(True)
        self._report_dev_filter.blockSignals(True)
        self._report_minpos.blockSignals(True)
        self._report_minpos.setValue(_MIN_POS_DEFAULT)
        self._report_minpos.blockSignals(False)
        self._report_name_filter.clear()
        self._report_ca_filter.setValue(0)
        self._report_pa_filter.setValue(0)
        self._report_age_min.setValue(0)
        self._report_age_max.setValue(0)
        self._report_dev_filter.setValue(0)
        self._report_name_filter.blockSignals(False)
        self._report_ca_filter.blockSignals(False)
        self._report_pa_filter.blockSignals(False)
        self._report_age_min.blockSignals(False)
        self._report_age_max.blockSignals(False)
        self._report_dev_filter.blockSignals(False)
        self._report_timer.stop()
        self._apply_report_filters()

    def _on_reports_table_dblclick(self, index):
        item = self._reports_table.item(index.row(), 0)
        if item:
            self._open_player_detail_by_pid(item.data(Qt.ItemDataRole.UserRole))

    def _make_view_players(self):
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # Header / filter strip
        hdr = QFrame()
        hdr.setObjectName('qfStrip')  # scoped: a bare QSS would leak the border onto child QLabels
        hdr.setStyleSheet(
            f"QFrame#qfStrip {{ background:{COLORS['elevated']}; border-bottom:1px solid {COLORS['border']}; }}")
        hdr_vbox = QVBoxLayout(hdr)
        hdr_vbox.setContentsMargins(0, 0, 0, 0)
        hdr_vbox.setSpacing(0)

        # Title row
        title_row = QHBoxLayout()
        title_row.setContentsMargins(16, 10, 16, 6)
        title_lbl = QLabel('Quick Filters')
        title_lbl.setStyleSheet(
            f"color:{COLORS['text_secondary']}; font-size:11px;")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        self._players_count_lbl = QLabel('')
        hdr_vbox.addLayout(title_row)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(16, 0, 16, 10)
        filter_row.setSpacing(8)

        self._players_name_filter = QLineEdit()
        self._players_name_filter.setPlaceholderText('Filter by name...')
        self._players_name_filter.setFixedHeight(26)
        self._players_name_filter.setMaximumWidth(220)
        self._players_name_filter.setStyleSheet(
            f"background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:3px 8px; font-size:11px;")
        self._players_name_filter.returnPressed.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_name_filter)

        self._players_pos_filter = QComboBox()
        self._players_pos_filter.addItem('All Positions')
        self._players_pos_filter.addItems(POSITIONS)
        self._players_pos_filter.setFixedHeight(26)
        self._players_pos_filter.setFixedWidth(130)
        self._players_pos_filter.setStyleSheet(
            f"background:{COLORS['surface']}; color:{COLORS['text_primary']};"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:2px 6px; font-size:11px;")
        self._players_pos_filter.currentIndexChanged.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_pos_filter)

        min_ca_lbl = QLabel('Min CA:')
        min_ca_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row.addWidget(min_ca_lbl)
        self._players_ca_filter = QSpinBox()
        self._players_ca_filter.setRange(0, 200)
        self._players_ca_filter.setValue(0)
        self._players_ca_filter.setFixedSize(56, 26)
        self._players_ca_filter.valueChanged.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_ca_filter)

        min_pa_lbl = QLabel('Min PA:')
        min_pa_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row.addWidget(min_pa_lbl)
        self._players_pa_filter = QSpinBox()
        self._players_pa_filter.setRange(0, 200)
        self._players_pa_filter.setValue(0)
        self._players_pa_filter.setFixedSize(56, 26)
        self._players_pa_filter.valueChanged.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_pa_filter)

        age_lbl = QLabel('Age:')
        age_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row.addWidget(age_lbl)
        self._players_age_min = QSpinBox()
        self._players_age_min.setRange(0, 99)
        self._players_age_min.setValue(0)
        self._players_age_min.setFixedSize(52, 26)
        self._players_age_min.valueChanged.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_age_min)
        dash = QLabel('-')
        dash.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row.addWidget(dash)
        self._players_age_max = QSpinBox()
        self._players_age_max.setRange(0, 99)
        self._players_age_max.setValue(0)
        self._players_age_max.setFixedSize(52, 26)
        self._players_age_max.valueChanged.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_age_max)

        dev_lbl = QLabel('Min Dev:')
        dev_lbl.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:11px;")
        filter_row.addWidget(dev_lbl)
        self._players_dev_filter = QSpinBox()
        self._players_dev_filter.setRange(0, 20)
        self._players_dev_filter.setValue(0)
        self._players_dev_filter.setFixedSize(52, 26)
        self._players_dev_filter.valueChanged.connect(self._apply_players_filter)
        filter_row.addWidget(self._players_dev_filter)

        filter_row.addStretch()

        clear_btn = QPushButton('Clear')
        clear_btn.setFixedHeight(26)
        clear_btn.setStyleSheet(
            f"background:transparent; color:{COLORS['text_secondary']}; font-size:11px;"
            f"border:1px solid {COLORS['border']}; border-radius:2px; padding:0 10px;")
        clear_btn.clicked.connect(lambda checked=False: self._clear_players_filter())
        filter_row.addWidget(clear_btn)

        hdr_vbox.addLayout(filter_row)
        vbox.addWidget(hdr)

        # Players table: virtualised QTableView + PeopleModel (all players, no cap)
        self._players_model, self._players_table = self._make_scouting_view(
            self._make_players_model(), _COL_TT,
            {0: 150, 1: 35, 2: 55, 3: _ability_w(), 4: _ability_w(), 5: 45, 6: 40, 7: 50, 8: 62, 9: 160, 10: 65}, 35,
            sort=(2, Qt.SortOrder.AscendingOrder))
        self._players_inj_delegate = _PosBadgeDelegate(self._players_table)
        self._players_pos_delegate = _PosBadgeDelegate(self._players_table)
        self._players_table.setItemDelegateForColumn(1, self._players_inj_delegate)
        self._players_table.setItemDelegateForColumn(2, self._players_pos_delegate)
        self._players_table.setItemDelegate(_RowMarkDelegate(self._players_table))
        self._players_table.setItemDelegateForColumn(8, _HGBadgeDelegate('hgp', self._players_table))
        _set_star_delegates(self._players_table, 3, 4)
        self._players_table.horizontalHeader().setStretchLastSection(True)
        self._players_table.doubleClicked.connect(self._on_players_table_dblclick)
        self._players_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._players_table.customContextMenuRequested.connect(
            lambda pos: self._on_list_table_context_menu(self._players_table, pos))
        vbox.addWidget(self._players_table)

        self._players_subset = None  # search-result restriction (list of person dicts) or None = everyone
        return w

    def _make_players_model(self):
        opt = lambda v: '?' if v is None else str(v)
        spec = [
            (str, None),                                                   # 0 name
            (lambda v: 'INJ' if v else '', int),                           # 1 injured
            (str, lambda v: _POS_SORT_ORDER.get(v, 99)),                   # 2 pos
            (opt, num_key), (opt, num_key), (opt, num_key),                # 3-5 CA PA Dev
            (str, None), (str, None),                                      # 6 age, 7 flag
            (lambda v: 'HGP' if v else '', None),                          # 8 hgp (badge; sort key set by hg_cols)
            (str, None), (str, None),                                      # 9 club, 10 contract end
        ]
        def attr(p, c):  # columns 11+: raw_attrs[c-11] shown on the 1-20 scale
            ra = p.get('raw_attrs') or ()
            return max(1, min(20, round(ra[c - 11] / 5))) if c - 11 < len(ra) else None
        m = PeopleModel(['Name', 'INJ', 'Pos', 'CA', 'PA', 'Dev', 'Age', 'Nation', 'HGP', 'Club', 'CtrE']
                        + _ATTR_ABBREV, spec, _COL_TT, attr)
        m.align_center = {7}
        f = QFont()
        f.setPointSize(14)
        m.big_font_cols = {7: f}
        m.hg_cols = {8: 'hgp'}
        m.tooltip_fn = lambda p, c: (f"Out for {p.get('injury_days', 0)} days"
                                     if c == 1 and p.get('injured') and p.get('injury_days', 0) > 0
                                     else 'Queued: written when you click Save Changes'
                                     if c == 8 and 'hgp' in m.queued.get(p.get('id'), ()) and not p.get('hgp') else None)
        return m

    @staticmethod
    def _player_row(p, squads, club_by_id):
        pos = _primary_pos(p['positions']) if p.get('positions') else '?'
        nid = p.get('nation', 0)
        cid = squads.get(p.get('id'))
        return (p.get('name', ''), bool(p.get('injured', False)), pos, p.get('ca'), p.get('pa'),
                _progress_rate(p), _age(p),
                _nation_cell(nid, ''), bool(p.get('hgp', False)),
                club_by_id.get(cid, '') if cid else '', p.get('contract_end', ''))

    def _open_players_view(self, players=None, highlight_name=None):
        """Navigate to Players view: everyone, or (players given) just those search results."""
        self._main_stack.setCurrentIndex(self._VIEW_INDEX['players'])
        for btn in self._nav_btns.values():
            btn.setChecked(False)
        for btn in self._report_btns.values():
            btn.setChecked(False)
        self._players_nav_btn.setChecked(True)
        self._scouting_staff_nav_btn.setChecked(False)

        self._players_subset = players
        self._clear_players_filter(silent=True)
        self._apply_players_filter()  # also refreshes header + counts
        self._players_table.clearSelection()

        if highlight_name:
            m = self._players_model
            for r in range(m.rowCount()):
                if m.rows[m.view[r]][0] == highlight_name:
                    self._players_table.selectRow(r)
                    self._players_table.scrollTo(m.index(r, 0))
                    break

    def _clear_players_filter(self, silent=False):
        self._players_name_filter.blockSignals(True)
        self._players_pos_filter.blockSignals(True)
        self._players_ca_filter.blockSignals(True)
        self._players_pa_filter.blockSignals(True)
        self._players_age_min.blockSignals(True)
        self._players_age_max.blockSignals(True)
        self._players_dev_filter.blockSignals(True)
        self._players_name_filter.clear()
        self._players_pos_filter.setCurrentIndex(0)
        self._players_ca_filter.setValue(0)
        self._players_pa_filter.setValue(0)
        self._players_age_min.setValue(0)
        self._players_age_max.setValue(0)
        self._players_dev_filter.setValue(0)
        self._players_name_filter.blockSignals(False)
        self._players_pos_filter.blockSignals(False)
        self._players_ca_filter.blockSignals(False)
        self._players_pa_filter.blockSignals(False)
        self._players_age_min.blockSignals(False)
        self._players_age_max.blockSignals(False)
        self._players_dev_filter.blockSignals(False)
        if not silent:  # the Clear button: back to everyone
            self._players_subset = None
            self._apply_players_filter()

    def _apply_players_filter(self):
        """Filters run over the WHOLE player set (or the search-result subset); nothing is capped."""
        m = self._players_model
        rows, src = m.rows, m.src
        name_q = self._players_name_filter.text().strip().lower()
        pos_q = self._players_pos_filter.currentText()
        if pos_q == 'All Positions':
            pos_q = ''
        min_ca = self._players_ca_filter.value()
        min_pa = self._players_pa_filter.value()
        age_min = self._players_age_min.value()
        age_max = self._players_age_max.value()
        min_dev = self._players_dev_filter.value()

        if self._players_subset is not None:
            ids = {id(p) for p in self._players_subset}
            idx = [i for i in range(len(src)) if id(src[i]) in ids]
        else:
            idx = list(range(len(src)))
        if name_q:
            idx = [i for i in idx if name_q in rows[i][0].lower()]
        if pos_q and pos_q in POSITIONS:
            pos_idx = POSITIONS.index(pos_q)
            def best(p):
                ps = p.get('positions')
                return bool(ps) and pos_idx < len(ps) and ps[pos_idx] == max(ps)
            idx = [i for i in idx if best(src[i])]
        if min_ca:
            idx = [i for i in idx if (rows[i][3] or 0) >= min_ca]
        if min_pa:
            idx = [i for i in idx if (rows[i][4] or 0) >= min_pa]
        if age_min or age_max:
            idx = [i for i in idx if rows[i][6] >= age_min and (not age_max or rows[i][6] <= age_max)]
        if min_dev:
            idx = [i for i in idx if (rows[i][5] or 0) >= min_dev]

        m.set_base(idx)
        text = self._scouting_count_text(m, 'players')
        self._players_count_lbl.setText(text)
        self._status_info_lbl.setText(text)
        if self._main_stack.currentIndex() == self._VIEW_INDEX['players']:
            self._update_header_for_view('players')

    def _on_players_table_dblclick(self, index):
        p = self._players_model.person(index.row())
        if p is not None:
            self._open_player_detail_by_pid(p.get('id', -1), person=p)

    # -- Navigation -----------------------------------------------------------

    _VIEW_INDEX = {'club': 0, 'squad': 1, 'staff': 2, 'shortlist': 3, 'reports': 4, 'players': 5, 'club_staff': 6, 'welcome': 7,
                   'save_info': 8, 'staff_shortlist': 9, 'settings': 10}

    def _nav_to(self, key: str):
        if key == 'club' and not self._current_club:
            key = 'welcome'
        if key == 'staff':  # list is pre-built during load (_preload_scouting); just show it
            self._status_info_lbl.setText(self._staff_count_lbl.text())
        if key == 'club_staff':
            self._populate_club_staff_table()
        if key == 'save_info':
            self._update_save_info_view()
        if key == 'staff_shortlist':
            self._apply_staff_shortlist_filter()
        if key == 'settings':
            self._settings_page.on_shown()
        if key in ('club', 'squad', 'shortlist', 'staff_shortlist', 'save_info', 'settings'):
            self._status_info_lbl.setText('')
        idx = self._VIEW_INDEX.get(key, 0)
        # Push to history for non-club views (club is pushed by _show_squad)
        if key != 'club':
            self._nav_push(idx, {})
        self._main_stack.setCurrentIndex(idx)
        for k, btn in self._nav_btns.items():
            btn.setChecked(k == key)
        self._players_nav_btn.setChecked(False)
        self._scouting_staff_nav_btn.setChecked(key == 'staff')
        if key not in ('squad',):
            for btn in self._report_btns.values():
                btn.setChecked(False)
        self._update_header_for_view(key)

    def _nav_to_squad_view(self, checked=False):
        if self._squad:
            self._populate_squad_table(self._squad)
        else:
            self._status_info_lbl.setText('')
        self._main_stack.setCurrentIndex(self._VIEW_INDEX['squad'])
        for k, btn in self._nav_btns.items():
            btn.setChecked(k == 'squad')
        self._players_nav_btn.setChecked(False)
        self._scouting_staff_nav_btn.setChecked(False)
        for btn in self._report_btns.values():
            btn.setChecked(False)
        self._update_header_for_view('squad')

    def _nav_push(self, stack_idx: int, context: dict):
        """Push a nav entry, truncate forward history, update back/fwd buttons."""
        if not hasattr(self, '_nav_history'):
            self._nav_history = []
            self._nav_pos = -1
        # Don't push duplicate of current (checked first: Back/Forward re-enter _nav_to, which must
        # not truncate the forward history)
        if self._nav_history and self._nav_history[self._nav_pos] == (stack_idx, context):
            return
        # Truncate forward history on new push
        if self._nav_pos < len(self._nav_history) - 1:
            self._nav_history = self._nav_history[:self._nav_pos + 1]
        self._nav_history.append((stack_idx, context))
        self._nav_pos = len(self._nav_history) - 1
        self._back_btn.setEnabled(not self._busy and self._nav_pos > 0)
        self._fwd_btn.setEnabled(False)

    def _nav_back(self, checked=False):
        if not hasattr(self, '_nav_history') or self._nav_pos <= 0:
            return
        self._nav_pos -= 1
        self._nav_back_btn_update()
        self._nav_restore(self._nav_history[self._nav_pos])

    def _nav_fwd(self, checked=False):
        if not hasattr(self, '_nav_history') or self._nav_pos >= len(self._nav_history) - 1:
            return
        self._nav_pos += 1
        self._nav_back_btn_update()
        self._nav_restore(self._nav_history[self._nav_pos])

    def _nav_back_btn_update(self):
        pos = getattr(self, '_nav_pos', -1)
        self._back_btn.setEnabled(not self._busy and pos > 0)
        self._fwd_btn.setEnabled(not self._busy and pos < len(getattr(self, '_nav_history', ())) - 1)

    def _nav_restore(self, entry: tuple):
        stack_idx, context = entry
        key = next((k for k, v in self._VIEW_INDEX.items() if v == stack_idx), None)
        if key == 'club' and 'club' in context:
            self._show_squad(context['club'])
        elif key is not None:
            self._nav_to(key)

    # -- Staff double-click handlers ------------------------------------------

    def _on_staff_double_click(self, index):
        person = self._staff_model.person(index.row())
        if not person:
            return
        dlg = StaffDetailDialog(person, self._save_data, self)
        dlg.exec()
        if dlg._shortlist_added:
            self._add_to_shortlist(person)

    def _on_club_staff_double_click(self, row: int, col: int):
        item = self._club_staff_table.item(row, 0)
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        people = self._save_data.get('people', []) if self._save_data else []
        person = next((p for p in people if p.get('id') == pid and 'ca' not in p), None)
        if not person:
            return
        dlg = StaffDetailDialog(person, self._save_data, self)
        dlg.exec()
        if dlg._shortlist_added:
            self._add_to_shortlist(person)

    # -- Table configuration --------------------------------------------------

    def _configure_table_for_mode(self, mode):
        hdr = self._table.horizontalHeader()
        hdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        _TT = _COL_TT | {
            'Age': 'Age on the save\'s in-game date',
        }
        cols = ['Name', 'INJ', 'Pos', 'CA', 'PA', 'Dev', 'Age', 'Nation', 'HGP', 'HGC',
                'CtrE'] + _ATTR_ABBREV
        self._table.setColumnCount(len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        for i in range(len(cols)):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        fixed_widths = {0: 150, 1: 35, 2: 55, 3: _ability_w(), 4: _ability_w(), 5: 45, 6: 40, 7: 50, 8: 62,
                        9: 62, 10: 65}  # 1=INJ, 8/9=HGP/HGC badges ('+ HGP' fits), 10=CtrE
        for i, cw in fixed_widths.items():
            self._table.setColumnWidth(i, cw)
        # Attr columns: 35px each
        for i in range(11, len(cols)):
            self._table.setColumnWidth(i, 35)
        for i, col in enumerate(cols):
            if col in _TT:
                hdr_item = self._table.horizontalHeaderItem(i)
                if hdr_item is not None:
                    hdr_item.setToolTip(_TT[col])
        hdr.setSectionsMovable(True)
        hdr.setFirstSectionMovable(False)
        hdr.setStretchLastSection(True)
        self._table_mode = mode

    def closeEvent(self, event):
        w = getattr(self, '_worker', None)
        if isinstance(w, (SaveWorker, ParseWorker)) and w.isRunning():
            event.ignore()
            self._status.showMessage('Working: wait until the current load/save finishes before closing.')
            return
        if self._dirty:
            B = QMessageBox.StandardButton
            box = QMessageBox(QMessageBox.Icon.Warning, 'Unsaved changes',
                              f'You have unsaved changes ({self._pending_text()}).\n\nSave them before closing?',
                              parent=self)
            box.setStandardButtons(B.Save | B.Discard | B.Cancel)
            box.setDefaultButton(B.Save)
            r = box.exec()
            if r != B.Discard:
                event.ignore()
                if r == B.Save:
                    self._do_save(after=self.close, confirm=False)  # closes again once saved
                return
        super().closeEvent(event)

    # -- State helpers --------------------------------------------------------

    def _update_sidebar_status(self):
        """Sidebar status line: No save loaded / Save loaded - <in-game date> / Unsaved changes."""
        if self._save_data is None:
            dot = f"background:transparent; border:1px solid {COLORS['text_secondary']};"
            text = 'No save loaded'
        elif self._dirty:
            dot = "background:#e6b840; border:none;"
            text = 'Unsaved changes'
        else:
            dot = "background:#4caf82; border:none;"
            text = 'Save loaded'
            d = _fmt_short_date(((self._save_data.get('save_info') or {}).get('in_game_date')))
            if d:
                text += f" &middot; <span style='color:{COLORS['text_primary']}'>{d}</span>"
        self._sb_dot.setStyleSheet(f"QLabel#sbDot {{ {dot} border-radius:3px; }}")  # Qt: radius must stay < size/2
        self._sb_status.setText(text)

    def _update_ui_state(self):
        self._update_sidebar_status()
        has_file = bool(self._save_path)
        has_data = self._save_data is not None
        has_b = has_data and 'b' in self._save_data
        idle = not self._busy  # while a Save / Reload / Load runs nothing may be re-enabled here
        self._reload_btn.setEnabled(idle and has_file)
        self._save_btn.setEnabled(idle and has_b and self._dirty)
        self._search_box.setEnabled(idle and has_data)
        has_abilities = has_data and any(
            'ca' in p for p in self._save_data.get('people', []))
        for btn in self._report_btns.values():
            btn.setEnabled(idle and has_abilities)
        self._players_nav_btn.setEnabled(idle and has_abilities)
        self._nav_btns['save_info'].setEnabled(idle and has_data)
        self._nav_btns['club'].setEnabled(idle and self._current_club is not None)
        self._nav_btns['squad'].setEnabled(idle and has_data and self._current_club is not None)
        self._nav_btns['club_staff'].setEnabled(idle and has_data and self._current_club is not None)
        self._nav_btns['shortlist'].setEnabled(idle)
        self._nav_btns['staff_shortlist'].setEnabled(idle)
        self._scouting_staff_nav_btn.setEnabled(idle and has_data)
        self._table.setEnabled(has_data)
        self._update_patch_btns()

    # -- File loading ---------------------------------------------------------

    def _load_file(self):
        """Open file picker then immediately start loading."""
        start_dir = _settings_mod.save_dialog_dir(  # Settings > Default save game folder, else old behaviour
            DEFAULT_SAVE_DIR if os.path.isdir(DEFAULT_SAVE_DIR) else os.path.expanduser('~'))
        path, _ = QFileDialog.getOpenFileName(
            self, 'Open FM24 Save File', start_dir, 'FM Save Files (*.fm);;All Files (*)')
        if not path:
            return
        self._guard_dirty(lambda: self._load_path(path), 'loading another save')

    def _load_path(self, path):
        if self._busy:
            return
        self._save_path = path
        self._save_data = None
        self._squad = []
        self._club_first_team = []
        self._current_club = None
        self._table.setRowCount(0)
        self._squad_info.setText('')
        self._clear_queue()
        self._dirty = False
        self._pending = []
        self._status_ready_lbl.setText(
            f'<span style="color:{COLORS["text_dim"]};">&#9679;</span> Loading...')
        self._update_ui_state()
        self._reload_save(use_cache=_settings_mod.load()['use_cache'])  # Load may use the cache; Reload never

    def _reload_save(self, use_cache=False):
        if not self._save_path or self._busy:
            return
        self._ui_snap = self._capture_ui_state() if self._save_data else None  # None: first load / another file
        self._set_busy(True, 'Parsing save file')
        self._preload_gen = getattr(self, '_preload_gen', 0) + 1  # cancels any preload in flight
        self._worker = ParseWorker(self._save_path, use_cache)
        self._worker.progress.connect(self._on_progress)
        self._worker.pct.connect(self._on_progress_pct)
        self._worker.done.connect(self._on_parse_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_parse_done(self, result):
        """Parse finished. Stay in the busy/locked state while the Scouting Players + Staff models
        are built in ~10 ms GUI-thread slices (no processEvents), then _finish_load unlocks."""
        _set_age_ref((result.get('save_info') or {}).get('in_game_date'))  # ages follow the save's date
        self._preload_gen = getattr(self, '_preload_gen', 0) + 1
        token = self._preload_gen
        self._players_model.clear()
        self._staff_model.clear()
        self._dot_timer.stop()  # we write our own "Preparing ... N%" status text
        gen = self._preload_scouting(result)
        self._step_preload(gen, token, lambda: self._finish_load(result))

    def _step_preload(self, gen, token, done):
        if token != self._preload_gen:
            return  # a newer load superseded this one
        try:
            pct = next(gen)
        except StopIteration:
            self._run_done(done)
            return
        except Exception:
            import traceback
            traceback.print_exc()
            self._players_model.clear()
            self._staff_model.clear()
            self._run_done(done)
            return
        self._progress_target = 98 + 1.9 * pct / 100
        self._status.showMessage(f'Preparing player and staff lists\u2026 {pct}%')
        QTimer.singleShot(0, lambda: self._step_preload(gen, token, done))

    def _run_done(self, done):
        """Run the load-finished callback; if it throws, unlock the window and show the error."""
        try:
            done()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._on_error(f'Loading the save failed: {e}')

    def _preload_scouting(self, sd):
        """Generator: build the Players (default sort) and Staff models. Each `yield pct` returns
        to the event loop; work between yields is time-boxed to ~10 ms so the window stays live."""
        from time import perf_counter as now
        BUDGET = 0.010
        people = sd.get('people', [])
        clubs = sd.get('clubs', [])
        squads = sd.get('squads', {})
        t0 = now()

        players, staff = [], []
        for i, p in enumerate(people):
            if p.get('ca') is not None:
                players.append(p)
            elif 'ca' not in p:
                staff.append(p)
            if not (i & 1023) and now() - t0 > BUDGET:
                yield 5 * i // max(1, len(people))
                t0 = now()
        yield 5
        # players in base order = CA descending (old "All Players" order; default-sort ties keep it)
        ks = []
        for i, p in enumerate(players):
            ks.append(-(p.get('ca') or 0))
            if not (i & 1023) and now() - t0 > BUDGET:
                yield 5 + 10 * i // max(1, len(players))
                t0 = now()
        order = sorted(range(len(players)), key=ks.__getitem__)
        players = [players[i] for i in order]
        del ks, order
        yield 15
        club_by_id = {c['id']: c['name'] for c in clubs}
        yield 16
        t0 = now()
        prows = []
        for i, p in enumerate(players):
            prows.append(self._player_row(p, squads, club_by_id))
            if not (i & 255) and now() - t0 > BUDGET:
                yield 16 + 44 * i // len(players)
                t0 = now()
        yield 60
        club_by_entity = {c['id'] + 1: c['name'] for c in clubs}
        employment = sd.get('employment', {})
        staff_club = {}
        for cid, pids in sd.get('club_staff', {}).items():
            for pid in pids:
                staff_club.setdefault(pid, cid)
        yield 61
        t0 = now()
        srows = []
        for i, p in enumerate(staff):
            srows.append(self._staff_row(p, club_by_id, club_by_entity, staff_club, employment))
            if not (i & 255) and now() - t0 > BUDGET:
                yield 61 + 24 * i // len(staff)
                t0 = now()
        yield 85
        self._players_model.set_data(players, prows)  # applies the default sort (Pos asc)
        yield 90
        self._staff_model.set_data(staff, srows)
        yield 93
        # column widths: fit to the first rows, floored so long names/clubs further down aren't clipped
        for tv, floor in ((self._players_table, {0: 260, 9: 240}), (self._staff_table, {0: 230, 1: 300})):
            for c in range(tv.model().columnCount()):
                tv.resizeColumnToContents(c)
                tv.setColumnWidth(c, max(tv.columnWidth(c), floor.get(c, 0)))
                yield 93 + 7 * c // tv.model().columnCount() // 2
        yield 100

    def _reset_session_state(self, result):
        """Drop everything that still points at the previous parse's person/club dicts (stale offsets
        would be patched into the new bytes). Shortlists survive a Reload of the same file, re-resolved by id."""
        same_file = getattr(self, '_loaded_path', None) == self._save_path
        self._loaded_path = self._save_path
        self._prev_club_id = (self._current_club or {}).get('id') if same_file else None
        by_id = {p.get('id'): p for p in result.get('people', []) if p.get('id', -1) != -1}
        for lst in (self._shortlist, self._staff_shortlist):
            lst[:] = [by_id[p.get('id')] for p in lst if same_file and p.get('id') in by_id]
        self._squad = []
        self._club_first_team = []
        self._current_club = None
        self._report_ratings = {}
        self._nav_history = []
        self._nav_pos = -1
        self._nav_back_btn_update()  # history was just emptied: both disabled
        self._table.setRowCount(0)
        self._squad_info.setText('')
        for btn in self._squad_tab_dynamic_btns:
            self._squad_tab_bar.removeWidget(btn)
            btn.deleteLater()
        self._squad_tab_dynamic_btns = []
        self._squad_tab_btns = self._squad_tab_btns[:1]
        self._club_staff_table.setRowCount(0)
        self._populate_reports_table([])
        self._populate_shortlist()
        self._apply_staff_shortlist_filter()

    def _finish_load(self, result):
        try:
            self._finish_load_inner(result)
        finally:
            if self._busy:  # an exception above must never leave the veil / lock up
                self._set_busy(False)

    def _finish_load_inner(self, result):
        self._save_data = result
        self._reset_session_state(result)
        self._clear_queue()
        self._dirty = False
        self._pending = []
        self._save_data['save_path'] = self._save_path
        _faces_service().set_clubs(result.get('clubs'), result.get('club_uids_extra') or (), self._save_path)  # club uid -> logo id table
        _faces_service().start(self._save_path)  # background facepack / logo index (fm_editor/faces.py)
        self._save_data['disk_sig'] = result.get('disk_sig')  # taken by the ParseWorker of THIS parse
        self._sg_idx = None  # search index is rebuilt lazily
        # fresh lists: reset filters/search subset without re-running them
        self._players_subset = None
        self._clear_players_filter(silent=True)
        for sp in (self._staff_age_min, self._staff_age_max):
            sp.blockSignals(True)
            sp.setValue(0)
            sp.blockSignals(False)
        self._players_count_lbl.setText(self._scouting_count_text(self._players_model, 'players'))
        self._staff_count_lbl.setText(self._scouting_count_text(self._staff_model, 'staff'))
        self._set_busy(False)
        n_clubs = len(result.get('clubs', []))
        n_people = self._players_model.total()
        n_staff = self._staff_model.total()
        fname = os.path.basename(self._save_path) if self._save_path else ''
        self._status_ready_lbl.setText(
            f'<span style="color:#4ade80;">&#9679;</span> Ready &nbsp;&middot;&nbsp; {fname}'
            f' &nbsp;&middot;&nbsp; {n_clubs:,} clubs, {n_people:,} players, {n_staff:,} staff')
        self._club_view_info.setText(
            f"{n_clubs:,} clubs, {n_people:,} players with ability data.")
        self._club_stats_frame.setVisible(False)
        self._club_pos_frame.setVisible(False)
        self._club_top_frame.setVisible(False)
        self._update_ui_state()
        snap, self._ui_snap = self._ui_snap, None
        if not self._apply_ui_state(snap):  # reload of the same save: back where the user was
            self._land_after_load()  # else Settings > Landing page (default Save Info)
        msg, self._after_reload_status = self._after_reload_status, None
        if msg:
            self._status.showMessage(msg)

    # -- Search ---------------------------------------------------------------

    def _do_search(self):
        try:
            self._do_search_inner()
        except Exception:
            import traceback
            traceback.print_exc()
            self._status.showMessage('Search failed. See crash log.')

    def _do_search_inner(self):
        if not self._save_data:
            return
        query = self._search_box.text().strip()
        if not query:
            return
        clubs = self._save_data.get('clubs', [])
        squads = self._save_data.get('squads', {})
        query_l = query.lower()
        matches = [c for c in clubs if query_l in c['name'].lower()]
        if not matches:
            people = self._save_data.get('people', [])
            name_matches = [p for p in people
                            if p.get('id', -1) != -1 and query_l in p.get('name', '').lower()]
            player_matches = [p for p in name_matches if p.get('ca') is not None]
            staff_matches = [p for p in name_matches if p.get('ca') is None]
            if player_matches:
                player_matches.sort(key=lambda p: p.get('name', ''))
                self._show_player_results(player_matches)
                return
            if staff_matches:
                staff_matches.sort(key=lambda p: p.get('name', ''))
                self._show_staff_results(staff_matches)
                return
            self._status.showMessage(f"No club, player, or staff matching '{query}'.")
            return
        if len(matches) == 1:
            self._show_squad(matches[0])
            return
        squad_counts = {}
        for cid in squads.values():
            squad_counts[cid] = squad_counts.get(cid, 0) + 1
        matches.sort(key=lambda c: squad_counts.get(c['id'], 0), reverse=True)
        self._show_search_dropdown(matches)

    # -- Squad / table views --------------------------------------------------

    def _show_search_dropdown(self, matches):
        """Enter-key fallback: list club matches in the autocomplete popup."""
        self._sg_popup.set_rows([(0, c, c['name'], '') for c in matches[:_SG_MAX]])

    # -- Search autocomplete (popup view: _SearchSuggest) ----------------------

    def _sg_index(self):
        """Lowercase name index, built once per loaded save: (lname, name, kind, obj)
        with kind 0 club / 1 staff / 2 player. ponytail: a few hundred k tuples in
        memory and a linear scan per query (~tens of ms); trie/n-gram if it ever lags."""
        if self._sg_idx is None:
            sd = self._save_data or {}
            idx = []
            for c in sd.get('clubs', []):
                n = c.get('name') or ''
                if n:
                    idx.append((n.lower(), n, 0, c))
            for p in sd.get('people', []):
                n = p.get('name') or ''
                if n and p.get('id', -1) != -1:
                    idx.append((n.lower(), n, 2 if p.get('ca') is not None else 1, p))
            self._sg_idx = idx
        return self._sg_idx

    def _sg_text_changed(self, text):
        if len(text.strip()) < 3 or not self._save_data:
            self._sg_timer.stop()
            self._sg_popup.close_popup()
        else:
            self._sg_timer.start()

    def _sg_flush(self):
        if self._sg_timer.isActive():
            self._sg_timer.stop()
            self._sg_refresh()

    def _sg_refresh(self):
        import heapq
        q = self._search_box.text().strip().lower()
        if len(q) < 3 or not self._save_data:
            self._sg_popup.close_popup()
            return
        sp = ' ' + q
        hits = [((0 if e[0].startswith(q) else 1 if sp in e[0] else 2), e[2], e[1], e[3])
                for e in self._sg_index() if q in e[0]]
        top = heapq.nsmallest(_SG_MAX, hits, key=lambda h: h[:3])  # rank, type, name
        squads = self._save_data.get('squads', {})
        club_name = {c['id']: c['name'] for c in self._save_data.get('clubs', [])} \
            if any(h[1] for h in top) else {}
        rows = [(k, o, n, '' if k == 0 else club_name.get(squads.get(o.get('id')), ''))
                for _r, k, n, o in top]
        self._sg_popup.set_rows(rows)

    def _sg_pick(self, kind, obj, name):
        """Route a chosen suggestion exactly like the old Enter search did."""
        self._sg_timer.stop()
        self._search_box.blockSignals(True)
        self._search_box.setText(name)
        self._search_box.blockSignals(False)
        if kind == 0:
            self._show_squad(obj)
        elif kind == 2:
            self._show_player_results([obj])
        else:
            self._show_staff_results([obj])

    def _show_squad(self, club):
        self._configure_table_for_mode('squad')
        self._current_club = club
        squads = self._save_data.get('squads', {})
        people = self._save_data.get('people', [])

        club_pids = {pid for pid, cid in squads.items() if cid == club['id']}
        squad = [p for p in people if p.get('id', -1) in club_pids]
        squad.sort(key=lambda p: p['name'])
        self._squad = squad
        self._club_first_team = squad

        # Update sidebar + header
        dim = COLORS['text_dim']
        self._breadcrumb.setText(
            f"FM Backroom 24 <span style='color:{dim}'> &rsaquo; </span>"
            f"<b>{club['name']}</b>"
            f"<span style='color:{dim}'> &rsaquo; </span><b>Squads</b>")
        self._breadcrumb.setTextFormat(Qt.TextFormat.RichText)
        self._squad_club_label.setText(club['name'])
        # Update club view
        self._club_view_info.setText(f"{len(squad)} players in squad")
        self._update_club_view()

        self._populate_squad_table(squad)
        self._build_squad_tabs(club, squad)
        self._nav_push(self._VIEW_INDEX['club'], {'club': club})
        self._nav_to('club')
        self._nav_btns['club'].setChecked(True)
        self._update_ui_state()
        try:
            self._table.itemSelectionChanged.disconnect()
        except (RuntimeError, TypeError):
            pass
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

    def _build_squad_tabs(self, main_club, main_squad):
        """Detect sub-clubs (e.g. U21, U18, B team) and populate tab bar."""
        # Remove old dynamic tabs
        for btn in self._squad_tab_dynamic_btns:
            self._squad_tab_bar.removeWidget(btn)
            btn.deleteLater()
        self._squad_tab_dynamic_btns = []
        # Reset btn list to ft_btn only
        ft_btn = self._squad_tab_btns[0]
        self._squad_tab_btns = [ft_btn]
        ft_btn.setChecked(True)
        try:
            ft_btn.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass
        ft_btn.clicked.connect(lambda checked: self._switch_sub_squad(0, main_squad))

        clubs = self._save_data.get('clubs', [])
        squads = self._save_data.get('squads', {})
        people = self._save_data.get('people', [])
        prefix = main_club['name'] + ' '

        # Kind-based sub-squads (English clubs: same club_id, different kind byte)
        _KIND_LABEL = {21: 'U21', 23: 'U23', 20: 'Reserves', 19: 'U19', 18: 'U18'}
        _KIND_ORDER = {21: 1, 23: 2, 20: 3, 19: 4, 18: 5}
        sub_squads = self._save_data.get('sub_squads', {})
        people_by_id = {p['id']: p for p in people if 'id' in p}

        sub_entries = []
        kind_map = sub_squads.get(main_club['id'], {})
        for kind, pids in kind_map.items():
            sub_squad = [people_by_id[pid] for pid in pids if pid in people_by_id]
            if sub_squad:
                label = _KIND_LABEL.get(kind, f'Squad {kind}')
                order = _KIND_ORDER.get(kind, 99)
                sub_entries.append((label, sub_squad, order))

        # Prefix-based sub-clubs (German/Spanish B teams: separate club entity)
        for c in clubs:
            if not c['name'].startswith(prefix):
                continue
            club_pids = {pid for pid, cid in squads.items() if cid == c['id']}
            sub_squad = [p for p in people if p.get('id', -1) in club_pids]
            if sub_squad:
                label = c['name'][len(prefix):]
                sub_entries.append((label, sub_squad, 0))  # B teams sort first

        sub_entries.sort(key=lambda x: (x[2], x[0]))

        for i, (label, sub_squad, _order) in enumerate(sub_entries):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setSizePolicy(
                QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            btn.setStyleSheet(self._squad_tab_ss_str)
            tab_idx = i + 1
            btn.clicked.connect(
                lambda checked, idx=tab_idx, sq=sub_squad: self._switch_sub_squad(idx, sq))
            self._squad_tab_bar.insertWidget(1 + i, btn)
            self._squad_tab_dynamic_btns.append(btn)
            self._squad_tab_btns.append(btn)

    def _switch_sub_squad(self, tab_idx, sub_squad):
        """Switch squad tab: update check state, repopulate table."""
        for i, btn in enumerate(self._squad_tab_btns):
            btn.setChecked(i == tab_idx)
        self._squad = sub_squad
        self._configure_table_for_mode('squad')
        self._populate_squad_table(sub_squad)

    def _populate_squad_table(self, squad):
        from fm_editor.patch import is_hgc
        b = self._save_data.get('b') if self._save_data else None

        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(squad))
        self._table.clearSelection()

        for row, p in enumerate(squad):
            nation_id = p.get('nation', 0)
            flag = _nation_cell(nation_id, '?')
            hgp = p.get('hgp', False)
            ent = self._entity_of(p)  # club id + 1: the same entity the write uses
            hgc = is_hgc(b, p, ent) if (b is not None and ent is not None) else None
            pos = _primary_pos(p['positions']) if p.get('positions') else '?'
            ca = p.get('ca')
            pa = p.get('pa')
            dev = _progress_rate(p)
            age = _age(p)

            name_item = _SortItem(p.get('name', ''))
            name_item.setData(Qt.ItemDataRole.UserRole, p.get('id', -1))
            hgp_item, hgc_item = _SortItem(''), _SortItem('')
            _hg_apply(hgp_item, 'hgp', bool(hgp), False)
            _hg_apply(hgc_item, 'hgc', hgc, False)
            injured = p.get('injured', False)
            injury_days = p.get('injury_days', 0)

            contract_end = p.get('contract_end', '')
            raw_attrs = p.get('raw_attrs', [])

            inj_item = _SortItem('INJ' if injured else '', 1 if injured else 0)
            if injured and injury_days > 0:
                inj_item.setToolTip(f"Out for {injury_days} days")
            items = [
                name_item,
                inj_item,
                _SortItem(pos, _POS_SORT_ORDER.get(pos, 99)),
                _SortItem(str(ca) if ca is not None else '?', ca if ca is not None else -1),
                _SortItem(str(pa) if pa is not None else '?', pa if pa is not None else -1),
                _SortItem(str(dev) if dev is not None else '?', dev if dev is not None else -1),
                _SortItem(str(age), age),
                _SortItem(flag),
                hgp_item,
                hgc_item,
                _SortItem(contract_end),
            ]
            # Append 54 attribute columns (display value = max(1, min(20, round(raw/5))))
            for raw in raw_attrs:
                dv = max(1, min(20, round(raw / 5)))
                items.append(_SortItem(str(dv), dv))
            # Pad missing attrs with empty items
            while len(items) < 11 + 54:
                items.append(_SortItem(''))

            for col, item in enumerate(items):
                if col == 7:  # Nation flag — center
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
                    f = QFont()
                    f.setPointSize(14)
                    if not item.text()[:1].isalpha():  # big font is for emoji flags only
                        item.setFont(f)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._table.setItem(row, col, item)

        _mark_rows(self._table, _queue_map(self._queue), {8: 'hgp', 9: 'hgc'})  # queued cells + row tint
        self._table.setSortingEnabled(True)
        self._table.sortByColumn(2, Qt.SortOrder.AscendingOrder)
        for c in range(self._table.columnCount()):
            self._table.resizeColumnToContents(c)
        n_hgp = sum(1 for p in squad if p.get('hgp', False))
        b = self._save_data.get('b') if self._save_data else None
        from fm_editor.patch import is_hgc
        n_hgc = sum(1 for p in squad
                    if b is not None and self._entity_of(p) is not None and is_hgc(b, p, self._entity_of(p)))
        n_inj = sum(1 for p in squad if p.get('injured', False))
        def _stat(val, label, color=COLORS['text_secondary']):
            return (f'<span style="color:{COLORS["text_primary"]};font-weight:600;">{val}</span>'
                    f'&nbsp;<span style="color:{color};font-size:11px;">{label}</span>')
        sep = f'<span style="color:{COLORS["border"]};">&nbsp;&nbsp;·&nbsp;&nbsp;</span>'
        inj_part = (sep + _stat(n_inj, 'injured', '#C0392B')) if n_inj > 0 else ''
        stats_html = (_stat(len(squad), 'players') + sep
                      + _stat(n_hgp, 'HGP', COLORS['hgp_green']) + sep
                      + _stat(n_hgc, 'HGC', COLORS['hgp_green'])
                      + inj_part)
        self._squad_info.setText(stats_html)
        club_name = self._current_club['name'] if self._current_club else ''
        self._set_header('Squads', f"{club_name} · {len(squad)} players", self._make_squad_stats_label(), icon='squads',
                         club=self._current_club)
        self._status_info_lbl.setText(f'{len(squad)} players')

    def _show_player_results(self, players):
        """Route player search results into the Players view."""
        highlight = players[0]['name'] if len(players) == 1 else None
        self._open_players_view(players=players, highlight_name=highlight)
        if len(players) == 1:
            self._players_name_filter.setText(players[0]['name'])

    def _show_staff_results(self, staff):
        """Route staff search results into the Staff view."""
        self._nav_to('staff')
        self._staff_table.clearSelection()
        names = {p['name'] for p in staff}
        m = self._staff_model
        sel = self._staff_table.selectionModel()
        first = True
        for r in range(m.rowCount()):
            if m.rows[m.view[r]][0] in names:
                if first:
                    self._staff_table.scrollTo(m.index(r, 0))
                    first = False
                sel.select(m.index(r, 0), sel.SelectionFlag.Select | sel.SelectionFlag.Rows)

    def _on_row_double_clicked(self, index):
        self._open_player_detail(index.row())

    def _open_player_detail(self, row: int):
        item = self._table.item(row, 0)
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        person = next((p for p in self._squad if p.get('id') == pid), None)
        if not person:
            return
        self._run_player_window(person)

    def _run_player_window(self, person, club_entity_id=None, in_squad=None):
        """Show the player window; then run the shortlist flow it asked for. Its HGP / HGC pills queue
        changes through this window (queue_*) only for players of a human-managed club, from any page."""
        pid = person.get('id')
        sd = self._save_data or {}
        club_id = sd.get('squads', {}).get(pid)
        can_patch = club_id is not None and club_id in sd.get('human_clubs', ())
        if club_id is not None:
            club_entity_id = club_id + 1  # club entity id = club id + 1 (memory fm24-binary-format)
        why = 'Open from Squads to patch' if club_id is None else 'Not your club'
        dlg = PlayerWindow(person, sd, club_entity_id, self,
                           shortlisted=any(p.get('id') == pid for p in self._shortlist),
                           can_patch=can_patch and 'b' in sd, queue=self, patch_tip=why)
        self._pw_open = dlg
        try:
            dlg.exec()
        finally:
            self._pw_open = None
        if dlg._shortlist_added:
            self._add_to_shortlist(person)

    def _open_player_detail_by_pid(self, pid, person=None):
        """Open the player window for any player by ID (reports/players views)."""
        if not self._save_data or pid is None:
            return
        people = self._save_data.get('people', [])
        person = person or next((p for p in people if p.get('id') == pid), None)
        if not person:
            return
        self._run_player_window(person)

    def _on_list_table_context_menu(self, table, pos):
        """Shared context menu for reports and players tables."""
        if isinstance(table.model(), PeopleModel):  # virtualised Players view
            p = table.model().person(table.rowAt(pos.y()))
            if p is None:
                return
            name = p.get('name', '')
        else:
            row = table.rowAt(pos.y())
            if row < 0:
                return
            item = table.item(row, 0)
            if not item:
                return
            name = item.text()
        menu = QMenu(self)
        copy_action = menu.addAction(f'Copy name: {name}')
        action = menu.exec(table.viewport().mapToGlobal(pos))
        if action == copy_action:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(name)
            self._status.showMessage(f'Copied: {name}')

    def _open_settings(self, checked=False):
        self._nav_to('settings')

    def _on_settings_saved(self, vals):
        """Apply a saved Settings page: role weights, PENDING markers. (Landing page / Load
        folder are read when needed.)"""
        self._active_preset = _weights_mod.load_active_preset()
        self._weights_lbl.setText(f"[{vals['role_weights_preset']}]")
        # Re-run Best by Role if it's currently shown
        if self._current_report_key == 'best_role':
            role = self._report_role_combo.currentText()
            if role and not role.startswith('──'):
                players = self._get_report_players('best_role', role_name=role)
                self._populate_reports_table(players)
        self._apply_ui_prefs(vals)
        _faces_service().start(self._save_path)  # faces_enabled / faces_dir may have changed

    def _apply_ui_prefs(self, vals=None):
        global _SHOW_PENDING
        vals = vals or _settings_mod.load()
        stars = vals.get('ability_display', 'stars') == 'stars'
        if stars != StarsDelegate.stars_on:   # Ability display changed: new CA/PA column width + repaint, no reload
            StarsDelegate.stars_on = stars
            self._refresh_ability_cols()
        show = bool(vals.get('show_pending', True))
        if show != _SHOW_PENDING:
            _SHOW_PENDING = show
            if self._current_club:
                self._update_club_view()

    def _refresh_ability_cols(self):
        """CA / PA columns of the player lists after the Ability display setting changed (tables may not exist yet)."""
        for name, cols in (('_table', (3, 4)), ('_reports_table', (3, 4)), ('_players_table', (3, 4)),
                           ('_shortlist_table', (4, 5))):
            t = getattr(self, name, None)
            if t is not None:
                for c in cols:
                    t.setColumnWidth(c, _ability_w())
                t.viewport().update()

    def _land_after_load(self):
        """Page shown once a save finishes parsing (Settings > Landing page)."""
        self._apply_ui_prefs()
        if self._main_stack.currentIndex() == self._VIEW_INDEX['settings']:
            return  # don't yank the user off the Settings page
        page = _settings_mod.load()['landing_page']
        sd = self._save_data or {}
        club_id = self._prev_club_id if getattr(self, '_prev_club_id', None) is not None else (sd.get('save_info') or {}).get('manager_club_id')
        self._prev_club_id = None
        club = next((c for c in sd.get('clubs', []) if c.get('id') == club_id), None)
        if page == 'club' and club:
            self._show_squad(club)
        elif page == 'players' and self._players_nav_btn.isEnabled():
            self._open_players_view()
        else:
            self._nav_to('save_info')

    # -- Reload: put the user back where they were (state kept by stable ids, never row indices/objects) --

    _SNAP_FILTERS = {  # view -> quick-filter widgets (QLineEdit text / QComboBox text / QSpinBox value)
        'players': ('_players_name_filter', '_players_pos_filter', '_players_ca_filter', '_players_pa_filter',
                    '_players_age_min', '_players_age_max', '_players_dev_filter'),
        'staff': ('_staff_age_min', '_staff_age_max'),
        'reports': ('_report_pos_combo', '_report_role_combo', '_report_name_filter', '_report_ca_filter',
                    '_report_pa_filter', '_report_age_min', '_report_age_max', '_report_dev_filter'),
        'shortlist': ('_shortlist_name_filter', '_shortlist_pos_filter', '_shortlist_ca_filter',
                      '_shortlist_pa_filter', '_shortlist_age_min', '_shortlist_age_max', '_shortlist_dev_filter'),
        'staff_shortlist': ('_staff_sl_age_min', '_staff_sl_age_max'),
        'club_staff': ('_club_staff_age_min', '_club_staff_age_max'),
    }

    def _snap_table(self, view):
        return {'squad': self._table, 'players': self._players_table, 'staff': self._staff_table,
                'reports': self._reports_table, 'shortlist': self._shortlist_table,
                'staff_shortlist': self._staff_shortlist_table, 'club_staff': self._club_staff_table}.get(view)

    @staticmethod
    def _pid_rows(tbl):
        """person id -> row for a list table (PeopleModel view or QTableWidget with the id in col 0 UserRole)."""
        m = tbl.model()
        if isinstance(m, PeopleModel):
            return {m.src[i].get('id', -1): r for r, i in enumerate(m.view)}
        out = {}
        for r in range(tbl.rowCount()):
            it = tbl.item(r, 0)
            if it is not None:
                out[it.data(Qt.ItemDataRole.UserRole)] = r
        return out

    @staticmethod
    def _set_quiet(w, val):
        """Set a filter widget without firing its change signal."""
        w.blockSignals(True)
        if isinstance(w, QLineEdit):
            w.setText(val)
        elif isinstance(w, QComboBox):
            w.setCurrentIndex(max(0, w.findText(val)))
        else:
            w.setValue(val)
        w.blockSignals(False)

    def _capture_ui_state(self):
        """Snapshot of what the user is looking at, taken just before a reload re-parses the save."""
        sd = self._save_data or {}
        view = next((k for k, v in self._VIEW_INDEX.items() if v == self._main_stack.currentIndex()), None)
        snap = {'path': self._save_path, 'view': view, 'search': self._search_box.text(),
                'club': (self._current_club or {}).get('id'), 'report': self._current_report_key,
                'tab': next((b.text() for b in self._squad_tab_btns if b.isChecked()), None),
                'subset': None if self._players_subset is None else [p.get('id') for p in self._players_subset],
                'filters': {},
                'history': [(i, c['club'].get('id') if 'club' in c else None) for i, c in self._nav_history],
                'pos': self._nav_pos}
        for v, names in self._SNAP_FILTERS.items():
            snap['filters'][v] = {n: (w.text() if isinstance(w, QLineEdit) else w.currentText()
                                      if isinstance(w, QComboBox) else w.value())
                                  for n in names for w in (getattr(self, n),)}
        tbl = self._snap_table(view)  # sort / scroll / selection of the list being looked at
        if tbl is not None:
            hdr = tbl.horizontalHeader()
            row_pid = {r: pid for pid, r in self._pid_rows(tbl).items()}
            sel = tbl.selectionModel().selectedRows()
            snap['table'] = {
                'sort': (hdr.sortIndicatorSection(), hdr.sortIndicatorOrder().value),
                'top': row_pid.get(tbl.rowAt(0)),  # first visible row = scroll position
                'sel': [row_pid[i.row()] for i in sel if i.row() in row_pid]}
        return snap

    def _apply_ui_state(self, snap):
        """Restore a _capture_ui_state() snapshot silently once the new parse is in. False = nothing usable
        (different file, view/club gone, error): the caller falls back to the landing page."""
        if not snap or snap.get('path') != self._save_path or not self._save_data:
            return False
        view = snap['view']
        if view in (None, 'welcome', 'settings'):
            return False
        sd = self._save_data
        club = next((c for c in sd.get('clubs', []) if c.get('id') == snap['club']), None)
        if view in ('club', 'squad', 'club_staff') and club is None:
            return False
        try:
            self._apply_ui_prefs()
            self._prev_club_id = None
            by_id = {p.get('id'): p for p in sd.get('people', [])}
            self._search_box.blockSignals(True)
            self._search_box.setText(snap['search'])
            self._search_box.blockSignals(False)
            if club is not None:  # also keeps the Club / Club Staff buttons alive when the view is elsewhere
                self._show_squad(club)
                tab = next((i for i, b in enumerate(self._squad_tab_btns) if b.text() == snap['tab']), 0)
                if tab:
                    self._squad_tab_btns[tab].click()
            set_filters = lambda vals: [self._set_quiet(getattr(self, n), val) for n, val in vals.items()]
            for vals in snap['filters'].values():
                set_filters(vals)
            if view == 'squad':
                self._nav_to_squad_view()
            elif view == 'players':
                self._open_players_view()
                sub = [by_id[i] for i in snap['subset'] or [] if i in by_id]
                self._players_subset = sub or None
                set_filters(snap['filters']['players'])  # _open_players_view cleared them
                self._apply_players_filter()
            elif view == 'staff':
                self._nav_to('staff')
                self._populate_staff_table()
            elif view == 'reports':
                self._run_report(snap['report'])
            elif view == 'shortlist':
                self._nav_to('shortlist')
                self._apply_shortlist_filter()
            elif view != 'club':  # staff_shortlist / club_staff apply their own filters on entry; club is shown
                self._nav_to(view)
            tbl = self._snap_table(view)
            if tbl is not None:
                st = snap['table']
                if st['sort'][0] >= 0:
                    tbl.sortByColumn(st['sort'][0], Qt.SortOrder(st['sort'][1]))
                rows = self._pid_rows(tbl)
                sm, m = tbl.selectionModel(), tbl.model()
                sm.clearSelection()
                for pid in st['sel']:
                    if pid in rows:
                        sm.select(m.index(rows[pid], 0), sm.SelectionFlag.Select | sm.SelectionFlag.Rows)
                if st['top'] in rows:
                    tbl.scrollTo(m.index(rows[st['top']], 0), QAbstractItemView.ScrollHint.PositionAtTop)
            # Back/Forward: same entries, clubs re-resolved by id (entries whose club is gone are dropped)
            clubs = {c.get('id'): c for c in sd.get('clubs', [])}
            hist, pos = [], -1
            for n, (i, cid) in enumerate(snap['history']):
                if cid is None:
                    hist.append((i, {}))
                elif cid in clubs:
                    hist.append((i, {'club': clubs[cid]}))
                else:
                    continue
                if n <= snap['pos']:
                    pos = len(hist) - 1
            if hist:
                self._nav_history, self._nav_pos = hist, max(pos, 0)
                self._nav_back_btn_update()
            return True
        except Exception:
            import traceback
            traceback.print_exc()
            return False

    def _run_report(self, key: str):
        try:
            if not self._save_data:
                return
            self._current_report_key = key
            for k, btn in self._report_btns.items():
                btn.setChecked(k == key)
            for btn in self._nav_btns.values():
                btn.setChecked(False)
            self._players_nav_btn.setChecked(False)
            self._scouting_staff_nav_btn.setChecked(False)
            self._report_pos_bar.setVisible(key == 'best_pos')
            self._report_role_bar.setVisible(key == 'best_role')
            if key == 'best_role':
                pname = _weights_mod.get_active_preset_name()
                self._weights_lbl.setText(f'[{pname}]')
            pos = self._report_pos_combo.currentText() if key == 'best_pos' else None
            role = self._report_role_combo.currentText() if key == 'best_role' else None
            players = self._get_report_players(key, pos, role)
            self._populate_reports_table(players)
            self._main_stack.setCurrentIndex(self._VIEW_INDEX['reports'])
            self._update_header_for_view('reports')
        except Exception:
            import traceback
            traceback.print_exc()
            self._status.showMessage('Report error. See log.')

    def _on_table_context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0:
            return
        item = self._table.item(row, 0)
        if not item:
            return
        name = item.text()
        menu = QMenu(self)
        copy_action = menu.addAction(f'Copy name: {name}')
        action = menu.exec(self._table.viewport().mapToGlobal(pos))
        if action == copy_action:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(name)
            self._status.showMessage(f'Copied: {name}')

    def _on_selection_changed(self):
        self._update_patch_btns()

    def _can_patch(self, person):
        """Only players of a human-managed club may be queued (the player-window pills use the same rule)."""
        sd = self._save_data or {}
        cid = sd.get('squads', {}).get(person.get('id'))
        return cid is not None and cid in sd.get('human_clubs', ())

    def _update_patch_btns(self):
        """Squads toolbar Make HGP / Make HGC: enabled only for a selection that has patchable players
        (human-managed club) still lacking the flag; never while a Save / Reload runs."""
        has_b = self._save_data is not None and 'b' in self._save_data
        sel = self._get_selected_persons() if (has_b and not self._busy and self._table_mode == 'squad'
                                               and self._squad) else []
        sel = [p for p in sel if self._can_patch(p)]
        all_hgp = all_hgc = True
        if sel:
            from fm_editor.patch import is_hgc
            b = self._save_data['b']
            # nothing left to queue = every selected player already has the flag or has it queued
            all_hgp = all(p.get('hgp', False) or self.queue_has(p, 'hgp') for p in sel)
            all_hgc = all(self.queue_has(p, 'hgc') or is_hgc(b, p, self._entity_of(p)) for p in sel)
        self._patch_hgp_btn.setEnabled(bool(sel) and not all_hgp)
        self._patch_hgc_btn.setEnabled(bool(sel) and not all_hgc)

    def _get_selected_persons(self):
        pid_map = {p.get('id', -1): p for p in self._squad}
        selected_rows = sorted({idx.row() for idx in self._table.selectedIndexes()})
        persons = []
        for r in selected_rows:
            pid = self._table.item(r, 0).data(Qt.ItemDataRole.UserRole) \
                if self._table.item(r, 0) else -1
            person = pid_map.get(pid)
            if person:
                persons.append(person)
        return persons

    # -- Homegrown queue (nothing touches game_db bytes until Save Changes) ---------

    def queue_has(self, person, kind):
        return (person.get('id'), kind) in self._queue

    def queue_count(self):
        return len(self._queue)

    def queue_toggle(self, person, kind):
        """Player-window pill: queue / unqueue one change. Returns True when it is now queued."""
        key = (person.get('id'), kind)
        if key in self._queue:
            del self._queue[key]
        else:
            self._queue[key] = person
        self._queue_changed()
        return key in self._queue

    def _queue_selected(self, kind):
        """Squads toolbar Make HGP / Make HGC: queue the selected players that still lack that flag."""
        if self._busy or not self._save_data or 'b' not in self._save_data:
            return
        b = self._save_data['b']
        from fm_editor.patch import is_hgc
        n = 0
        for p in self._get_selected_persons():
            if not self._can_patch(p):  # only players of a human-managed club
                continue
            ent = self._entity_of(p)
            have = p.get('hgp', False) if kind == 'hgp' else (ent is not None and is_hgc(b, p, ent))
            if not have and (p.get('id'), kind) not in self._queue:
                self._queue[(p.get('id'), kind)] = p
                n += 1
        self._queue_changed()
        self._status.showMessage(f'{kind.upper()}: {n} player(s) queued. Click Save Changes to write them.'
                                 if n else f'{kind.upper()}: nothing to queue (only players of a human-managed '
                                           'club that still lack it can be queued).')

    def _queue_changed(self):
        """Queue edited anywhere: dirty flag, pending text, Squads cells, open player window."""
        n = {k: sum(1 for _pid, kk in self._queue if kk == k) for k in ('hgp', 'hgc')}
        self._dirty = bool(self._queue)
        self._pending = [f'{k.upper()}: {v} player(s)' for k, v in n.items() if v]
        self._update_ui_state()
        self._refresh_queue_marks()
        if self._pw_open is not None:
            self._pw_open.refresh_queue()

    def _refresh_queue_marks(self):
        """Queue changed (or cleared): HGP/HGC badges + row marking in every list. Only the cheap parts run:
        QTableWidget tables are small, the Players model repaints just the affected rows."""
        qm = _queue_map(self._queue)
        self._players_model.set_queue(qm)
        if self._table_mode == 'squad' and self._squad and self._save_data:
            _mark_rows(self._table, qm, {8: 'hgp', 9: 'hgc'})
            self._on_selection_changed()
        _mark_rows(self._reports_table, qm, {8: 'hgp'})
        _mark_rows(self._shortlist_table, qm, {})

    def _clear_queue(self):
        self._queue.clear()
        self._refresh_queue_marks()

    def _entity_of(self, person):
        """Club entity id of a player's club (club id + 1), or None."""
        cid = (self._save_data or {}).get('squads', {}).get(person.get('id'))
        return None if cid is None else cid + 1

    # -- Save / discard guards ------------------------------------------------

    def _pending_text(self):
        return '; '.join(self._pending) or 'edits'

    def _guard_dirty(self, proceed, what):
        """Call proceed() now, or after Save / Discard / Cancel when there are unsaved changes."""
        if not self._dirty:
            proceed()
            return
        box = QMessageBox(QMessageBox.Icon.Warning, 'Unsaved changes',
                          f'You have unsaved changes ({self._pending_text()}).\n\n'
                          f'Save them before {what}?', parent=self)
        B = QMessageBox.StandardButton
        box.setStandardButtons(B.Save | B.Discard | B.Cancel)
        box.setDefaultButton(B.Save)
        r = box.exec()
        if r == B.Save:
            self._do_save(after=proceed, confirm=False)
        elif r == B.Discard:
            proceed()

    def _on_reload_clicked(self, checked=False):
        if self._dirty:
            B = QMessageBox.StandardButton
            box = QMessageBox(QMessageBox.Icon.Warning, 'Discard unsaved changes?',
                              f'Reload re-reads {os.path.basename(self._save_path)} from disk and '
                              f'discards your unsaved changes ({self._pending_text()}).\n\n'
                              'Discard them?', parent=self)
            box.setStandardButtons(B.Discard | B.Cancel)
            box.setDefaultButton(B.Cancel)
            if box.exec() != B.Discard:
                return
        self._reload_save()

    def _do_save(self, checked=False, after=None, confirm=True):
        """Save Changes: verified temp file, 2 backups, overwrite in place (fm_editor/savefile.py)."""
        if self._busy or not self._save_data or 'b' not in self._save_data or not self._dirty:
            return
        from fm_editor.savefile import backup_state
        path = self._save_path
        name = os.path.basename(path)
        first, _prev = backup_state(path)
        if confirm:
            plan = (f'First save of this file: the current original is kept in BOTH {name}.bk1 and '
                    f'{name}.bk2.' if first else
                    f'Backups: {name}.bk2 becomes the previous bk1, {name}.bk1 becomes the file as it '
                    'is now.')
            box = QMessageBox(QMessageBox.Icon.Question, 'Save changes',
                              f'Overwrite {name} with your changes?\n\n{self._pending_text()}\n\n'
                              f'{plan}\n\nThe save keeps its name and location. This can take up to a minute.',
                              parent=self)
            box.setStandardButtons(QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel)
            if box.exec() != QMessageBox.StandardButton.Save:
                return
        sd = self._apply_queue_copy()
        if sd is None:
            return
        self._after_save = after
        self._set_busy(True, 'Saving')
        self._worker = SaveWorker(sd, path)
        self._worker.progress.connect(self._on_progress)
        self._worker.pct.connect(self._on_progress_pct)
        self._worker.done.connect(self._on_save_done)
        self._worker.error.connect(self._on_save_error)
        self._worker.start()

    def _apply_queue_copy(self):
        """Apply the queued HGP/HGC changes (patch.apply_queue: HGP in place, then HGC inserts in descending
        offset order) to a COPY of game_db. Returns the save_data to write (shallow copy holding the patched
        buffer) or None after showing the error. Nothing in self._save_data / on disk changes either way."""
        from fm_editor import patch as _patch
        sd = dict(self._save_data)
        by_id = {p.get('id'): p for p in sd.get('people', [])}
        try:
            nb = bytearray(sd['b'])
            self._last_applied = _patch.apply_queue(
                nb, [(by_id.get(pid, p), kind) for (pid, kind), p in self._queue.items()], self._entity_of)
            sd['b'] = nb
        except Exception as e:
            self._on_save_error(f'could not apply the queued changes ({e}).')
            return None
        return sd

    def _on_save_done(self, info):
        self._worker.wait()  # run() returns right after emitting; lets close-after-save proceed
        n_hgp, n_hgc = self._last_applied
        asked = {k: sum(1 for _pid, kk in self._queue if kk == k) for k in ('hgp', 'hgc')}
        try:
            self._clear_queue()
            self._dirty = False
            self._pending = []
            clear_cache(self._save_path)  # cache is keyed by path+mtime; drop the entry for the old layout
        finally:
            self._set_busy(False)  # always unlock, whatever the bookkeeping above did
        name = os.path.basename(self._save_path)
        msg = (f'Saved {name} \u00b7 original kept in both backups ({name}.bk1, {name}.bk2)'
               if info.get('first') else f'Saved {name} \u00b7 backups bk1, bk2 updated')
        if info.get('backup_error'):  # the save is in place; only the backup rotation failed
            msg = (f'Saved {name}, but backup rotation failed: {info["backup_error"]} '
                   f'(the existing backups were kept as they were)')
        msg += f' \u00b7 HGP {n_hgp}, HGC {n_hgc}'
        if (n_hgp, n_hgc) != (asked['hgp'], asked['hgc']):
            msg += f' ({asked["hgp"] - n_hgp + asked["hgc"] - n_hgc} queued change(s) needed no edit)'
        after, self._after_save = self._after_save, None
        if after:  # load-another / close: no point reloading this save
            self._status.showMessage(msg)
            after()
        else:  # the in-memory lists and offsets are stale (HGC inserts): re-read the saved file
            self._after_reload_status = msg
            self._reload_save()

    def _on_save_error(self, msg):
        self._after_save = None
        self._on_error(msg if msg.startswith('Saved') else
                       f'Save failed: {msg}\n\nThe original save file was not changed.')

    # -- Progress / error -----------------------------------------------------

    def _tick_dots(self):
        self._dot_phase = (self._dot_phase + 1) % len(_DOT_SEQ)
        dots = '.' * _DOT_SEQ[self._dot_phase]
        self._status.showMessage(self._status_base + dots)
        self._busy_veil.set_text(self._veil_word or '', _DOT_SEQ[self._dot_phase])

    def _on_progress_pct(self, pct: int):
        self._progress_target = float(pct)

    def _tick_shimmer(self):
        # Smooth progress: lerp toward target, constant slow creep between chunks
        target = self._progress_target
        disp = self._progress_displayed
        if target > disp:
            disp += (target - disp) * 0.10
            if target - disp < 0.005:
                disp = target
        else:
            # Always creep forward slowly — never stops, never auto-fills past 99
            disp = min(disp + 0.04, 99.0)
        self._progress_displayed = disp
        self._progress.setValue(round(disp * 100))

        self._shimmer_phase = (self._shimmer_phase + 0.017) % 1.0
        # peak sweeps -0.25 → 1.25 so shimmer fully enters and exits
        peak = -0.25 + self._shimmer_phase * 1.5
        hw = 0.18
        stops: dict[float, str] = {0.0: '#4a2290', 1.0: '#4a2290'}
        for offset, col in ((-hw, '#5a2da0'), (-hw * 0.5, '#6933bd'),
                            (0.0, '#c0a8fa'), (hw * 0.5, '#6933bd'), (hw, '#5a2da0')):
            p = round(peak + offset, 4)
            if 0.001 <= p <= 0.999:
                stops[p] = col
        s = ' '.join(f'stop:{p} {c}' for p, c in sorted(stops.items()))
        self._progress.setStyleSheet(
            f"QProgressBar {{ background:{COLORS['elevated']}; border:none; }}"
            f"QProgressBar::chunk {{ background:qlineargradient("
            f"x1:0,y1:0,x2:1,y2:0,{s}); }}"
        )

    def _on_progress(self, msg):
        self._status_base = msg.rstrip('.')
        self._dot_phase = -1
        self._status.showMessage(self._status_base)

    def _on_error(self, msg):
        self._after_reload_status = None  # a failed post-save reload must not leak its text into the next load
        self._set_busy(False, failed=True)
        QMessageBox.critical(self, 'Error', msg)
        self._status.showMessage(f'Error: {msg}')

    def _set_busy(self, busy, msg='', failed=False):
        self._busy = bool(busy)
        if busy:
            self._progress.setValue(0)
            self._shimmer_phase = 0.0
            self._progress_target = 0.0
            self._progress_displayed = 0.0
            self._shimmer_timer.start()
            self._dot_phase = -1
            self._status_base = msg or self._status_base
            self._status.showMessage(self._status_base)
            # veil word: Saving / Reloading only (a first load keeps the Welcome page's own loading state, no veil)
            self._veil_word = 'Saving' if msg == 'Saving' else ('Reloading' if self._ui_snap is not None else None)
            self._busy_veil.set_text(self._veil_word or '', 1)
            self._dot_timer.start()
            if self._veil_word is None:
                self._hero.glow_start()   # first load only (reload / save use the veil); no-op off the Welcome page
            self._load_btn.setText('Loading')
            for k, btn in self._nav_btns.items():
                btn.setEnabled(False)
            self._players_nav_btn.setEnabled(False)
            self._scouting_staff_nav_btn.setEnabled(False)
            for btn in self._report_btns.values():   # Player Reports buttons too
                btn.setEnabled(False)
            self._welcome_load_btn.setEnabled(False)
            self._welcome_load_btn.setText('Loading Save')
            self._back_btn.setEnabled(False)
            self._fwd_btn.setEnabled(False)
        else:
            self._shimmer_timer.stop()
            self._hero.glow_finish()
            self._progress.setStyleSheet(
                f"QProgressBar {{ background:{COLORS['elevated']}; border:none; }}"
                f"QProgressBar::chunk {{ background:{COLORS['accent']}; }}"
            )
            self._dot_timer.stop()
            self._status.clearMessage()
            self._load_btn.setText('Load')
            self._welcome_load_btn.setText('Load Save')
        self._progress.setVisible(busy)
        veil = bool(busy and self._veil_word)
        self._main_stack.setEnabled(not veil)   # no keyboard / clicks into the lists while saving / reloading
        self._busy_veil.show_veil(veil)
        self._load_btn.setEnabled(not busy)
        self._welcome_load_btn.setEnabled(not busy)
        self._reload_btn.setEnabled(not busy and bool(self._save_path))
        self._save_btn.setEnabled(not busy and self._dirty and bool(self._save_data) and 'b' in (self._save_data or {}))
        self._search_box.setEnabled(not busy and self._save_data is not None)
        self._settings_btn.setEnabled(not busy)
        self._patch_hgp_btn.setEnabled(False)
        self._patch_hgc_btn.setEnabled(False)
        if msg and not busy:
            self._status.showMessage(msg)
        if not busy:
            self._nav_back_btn_update()
            self._update_ui_state()
