"""Settings page: 1:1 translation of mockups/settings-page-design-a.html (Design A).

Layout: QScrollArea > centred column (max 760) > [section header + QFrame#setPanel > rows],
plus a fixed footer bar outside the scroll area. Values persist via fm_editor/settings.py.
Only the page content is built here; the hero / sidebar entry / gear live in main_window.py.

Mockup -> Qt translations (QSS can't do these):
  letter-spacing -> QFont.setLetterSpacing | text-transform -> .upper() | focus ring -> :focus border
  chip radius >= h/2 renders square -> chip h20 radius 9 | data-URI images -> svg files in tempdir
  rgba(r,g,b,a) -> rgba(r,g,b,round(a*255))
"""
import os
import tempfile

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QFont, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from fm_editor import cache as _cache
from fm_editor import settings as _settings
from fm_editor import weights as _weights
from gui.theme import COLORS

# Extra literals from the mockup (not in COLORS)
_HAIR = '#252C30'
_ERR_TEXT = '#E8696A'
_OK = '#4CAF82'

_FONT_HDR = "'Barlow Condensed','Arial Narrow',sans-serif"

# -- SVG assets (QSS image: needs real files) ---------------------------------------------

_TMP = tempfile.gettempdir()
_CHEV_SVG = os.path.join(_TMP, 'fmbr24_set_chevron.svg')
_CHECK_SVG = os.path.join(_TMP, 'fmbr24_set_check.svg')
try:
    with open(_CHEV_SVG, 'wb') as _f:  # mockup .sel background: polygon 0,0 6,0 3,4 #8B96A8 at 8x6
        _f.write(b"<svg xmlns='http://www.w3.org/2000/svg' width='8' height='6' viewBox='0 0 6 4'"
                 b" preserveAspectRatio='none'><polygon points='0,0 6,0 3,4' fill='#8B96A8'/></svg>")
    with open(_CHECK_SVG, 'wb') as _f:  # mockup .chk checked tick, 10x10
        _f.write(b"<svg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'>"
                 b"<path d='M2 5.2l2.2 2.2L8 3' fill='none' stroke='white' stroke-width='1.6'"
                 b" stroke-linecap='round' stroke-linejoin='round'/></svg>")
except Exception:
    _CHEV_SVG = _CHECK_SVG = ''

C = COLORS
_QSS = f"""
QWidget#settingsPage {{ background:{C['window_bg']}; }}
QWidget#setBare {{ background:transparent; }}
QScrollArea#setScroll {{ background:{C['window_bg']}; border:none; }}
QWidget#setBody {{ background:{C['window_bg']}; }}

QLabel#setSecHdr {{ background:transparent; color:{C['text_secondary']}; font-family:{_FONT_HDR};
    font-size:12px; font-weight:700; }}
QFrame#setPanel {{ background:{C['surface']}; border:1px solid {C['border']}; border-radius:3px; }}
QFrame#setRow {{ background:transparent; border:none; border-bottom:1px solid {_HAIR}; border-radius:0; }}
QFrame#setRowLast {{ background:transparent; border:none; border-radius:0; }}
QLabel#setLabel {{ background:transparent; color:{C['text_primary']}; font-size:13px; font-weight:500; }}
QLabel#setHelp {{ background:transparent; color:{C['text_secondary']}; font-size:11px; }}
QLabel#setLegal {{ background:transparent; color:{C['text_secondary']}; font-size:12px; }}
QLabel#setAboutName {{ background:transparent; color:{C['text_primary']}; font-family:{_FONT_HDR};
    font-size:20px; font-weight:700; }}
QLabel#setAboutVer {{ background:transparent; color:{C['text_secondary']}; font-size:11px; }}
QLabel#setChip {{ background:rgba(139,150,168,31); color:{C['text_secondary']}; font-family:{_FONT_HDR};
    font-size:11px; font-weight:700; padding:0 8px; border-radius:9px; }}
QLabel#setMsg {{ background:transparent; color:{C['text_secondary']}; font-size:11px; }}
QLabel#setMsg[bad="true"] {{ color:{_ERR_TEXT}; }}
QLabel#setFootTxt {{ background:transparent; color:{C['text_secondary']}; font-size:12px; }}
QLabel#setFootTxt[state="edited"] {{ color:{C['text_primary']}; }}
QLabel#setFootTxt[state="error"] {{ color:{_ERR_TEXT}; }}
QLabel#setLink {{ background:transparent; color:{C['accent_hover']}; font-size:13px; }}

QFrame#setFooter {{ background:{C['surface']}; border:none; border-top:1px solid {C['border']}; border-radius:0; }}

QWidget#settingsPage QPushButton {{ background:{C['elevated']}; color:{C['text_primary']};
    border:1px solid {C['border']}; border-radius:2px; padding:0 14px; font-size:13px; }}
QWidget#settingsPage QPushButton:hover {{ background:{C['border']}; border-color:{C['border_bright']}; }}
QWidget#settingsPage QPushButton:pressed {{ background:{C['border']}; }}
QWidget#settingsPage QPushButton:focus {{ border-color:{C['accent_hover']}; }}
QWidget#settingsPage QPushButton:disabled {{ color:{C['text_dim']}; background:{C['elevated']};
    border-color:{C['border']}; }}
QWidget#settingsPage QPushButton#setAccent {{ background:{C['accent']}; border:1px solid {C['accent']}; padding:0 18px;
    font-weight:700; }}
QWidget#settingsPage QPushButton#setAccent:hover {{ background:{C['accent_hover']}; border-color:{C['accent_hover']}; }}
QWidget#settingsPage QPushButton#setAccent:pressed {{ background:{C['accent_press']}; border-color:{C['accent_press']}; }}
QWidget#settingsPage QPushButton#setAccent:focus {{ border:1px solid #FFFFFF; }}
QWidget#settingsPage QPushButton#setAccent:disabled {{ background:{C['elevated']}; color:{C['text_dim']};
    border-color:{C['elevated']}; }}

QLineEdit#setInput {{ background:{C['elevated']}; color:{C['text_primary']}; border:1px solid {C['border']};
    border-radius:2px; padding:0 10px; placeholder-text-color:{C['text_dim']};
    selection-background-color:{C['selection_bg']}; }}
QLineEdit#setInput:hover {{ border-color:{C['border_bright']}; }}
QLineEdit#setInput:focus {{ border-color:{C['accent_hover']}; }}
QLineEdit#setInput[err="true"] {{ border-color:{C['non_hgp_red']}; }}
QLineEdit#setInput:disabled {{ color:{C['text_dim']}; background:{C['surface']}; }}
QLineEdit#setInput:read-only {{ background:{C['window_bg']}; color:{C['text_secondary']}; }}

QComboBox#setSelect {{ background:{C['elevated']}; color:{C['text_primary']}; border:1px solid {C['border']};
    border-radius:2px; padding:0 0 0 10px; }}  /* drop-down (30px) already reserves the right side */
QComboBox#setSelect:hover {{ border-color:{C['border_bright']}; }}
QComboBox#setSelect:focus, QComboBox#setSelect:on {{ border-color:{C['accent_hover']}; }}
QComboBox#setSelect:disabled {{ color:{C['text_dim']}; background:{C['surface']}; }}
QComboBox#setSelect::drop-down {{ subcontrol-origin:padding; subcontrol-position:center right;
    width:30px; border:none; background:transparent; }}
QComboBox#setSelect::down-arrow {{ image:url({_CHEV_SVG}); width:8px; height:6px; }}

QCheckBox#setCheck {{ background:transparent; color:{C['text_primary']}; spacing:8px; font-size:13px; }}
QCheckBox#setCheck:disabled {{ color:{C['text_dim']}; }}
QCheckBox#setCheck::indicator {{ width:14px; height:14px; border:1px solid {C['border_bright']};
    border-radius:2px; background:{C['elevated']}; }}
QCheckBox#setCheck::indicator:hover {{ border-color:{C['text_secondary']}; }}
QCheckBox#setCheck::indicator:focus {{ border-color:{C['accent_hover']}; }}
QCheckBox#setCheck::indicator:checked {{ background:{C['accent']}; border-color:{C['accent']};
    image:url({_CHECK_SVG}); }}
QCheckBox#setCheck::indicator:disabled {{ background:{C['surface']}; border-color:{C['border']}; }}
QCheckBox#setCheck::indicator:checked:disabled {{ background:{C['elevated']}; border-color:{C['border']};
    image:url({_CHECK_SVG}); }}

QWidget#settingsPage QPushButton#setSegL, QWidget#settingsPage QPushButton#setSegR {{ background:{C['elevated']}; border:1px solid {C['border']};
    color:{C['text_secondary']}; padding:0 14px; font-weight:400; }}
QWidget#settingsPage QPushButton#setSegL {{ border-top-left-radius:2px; border-bottom-left-radius:2px;
    border-top-right-radius:0; border-bottom-right-radius:0; }}
QWidget#settingsPage QPushButton#setSegR {{ border-left:none; border-top-right-radius:2px; border-bottom-right-radius:2px;
    border-top-left-radius:0; border-bottom-left-radius:0; }}
QWidget#settingsPage QPushButton#setSegL:checked, QWidget#settingsPage QPushButton#setSegR:checked {{ background:{C['selection_bg']};
    border-color:{C['accent']}; color:{C['text_primary']}; font-weight:700; }}
QWidget#settingsPage QPushButton#setSegR:checked {{ border-left:1px solid {C['accent']}; }}
QWidget#settingsPage QPushButton#setSegL:disabled, QWidget#settingsPage QPushButton#setSegR:disabled {{ color:{C['text_dim']}; background:{C['surface']};
    border-color:{C['border']}; }}
QWidget#settingsPage QPushButton#setSegL:checked:disabled, QWidget#settingsPage QPushButton#setSegR:checked:disabled {{ background:{C['elevated']};
    border-color:{C['border']}; font-weight:400; }}
"""

_LANDING_LABELS = (('save_info', 'Save Info'), ('club', 'Club'), ('players', 'Players'))


# -- small builders ----------------------------------------------------------------------------

def _bare(layout_cls=None):
    w = QWidget()
    w.setObjectName('setBare')
    if layout_cls:
        lay = layout_cls(w)
        lay.setContentsMargins(0, 0, 0, 0)
        return w, lay
    return w


def _spaced_font(w, px_spacing, bold=None):
    f = w.font()
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, px_spacing)
    w.setFont(f)


def _btn(text, accent=False):
    b = QPushButton(text)
    b.setFixedHeight(30)
    b.setFocusPolicy(Qt.FocusPolicy.TabFocus)  # mockup focus-visible: keyboard focus only
    if accent:
        b.setObjectName('setAccent')
    return b


def _help_label(text):
    lbl = QLabel(text)
    lbl.setObjectName('setHelp')
    lbl.setWordWrap(True)
    lbl.setTextFormat(Qt.TextFormat.RichText)
    lbl.setMinimumHeight(15)
    _set_help(lbl, text)
    return lbl


def _set_help(lbl, text):
    # line-height 15px (11/1.4 in the mockup)
    esc = text.replace('&', '&amp;').replace('<', '&lt;')
    lbl.setText(f'<p style="margin:0; line-height:15px;">{esc}</p>')


def _chip(text='Coming soon'):
    c = QLabel(text.upper())
    c.setObjectName('setChip')
    c.setFixedHeight(20)
    _spaced_font(c, 0.66)  # 0.06em * 11px
    return c


def _dot(color):
    d = QLabel()
    d.setFixedSize(7, 7)
    d.setStyleSheet(f"background:{color}; border-radius:3px;")
    return d


def _fmt_size(n):
    for unit, div in (('GB', 1 << 30), ('MB', 1 << 20), ('KB', 1 << 10)):
        if n >= div:
            return f'{n / div:.0f} {unit}' if n >= 10 * div else f'{n / div:.1f} {unit}'
    return f'{n} B'


class SettingsPage(QWidget):
    saved = pyqtSignal(dict)     # emitted after a successful Save settings
    message = pyqtSignal(str)    # short status text for the main window

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('settingsPage')
        self.setStyleSheet(_QSS)
        self._saved = {}
        self._folder_state = 'unset'
        self._soon = []
        self._fitted = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName('setScroll')
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName('setBody')
        body_l = QHBoxLayout(body)
        body_l.setContentsMargins(28, 24, 28, 32)  # mockup .page padding 24 28 32
        body_l.setSpacing(0)
        col, col_l = _bare(QVBoxLayout)
        col.setMaximumWidth(760)
        col_l.setSpacing(0)
        body_l.addStretch(1)
        body_l.addWidget(col, 100, Qt.AlignmentFlag.AlignTop)
        body_l.addStretch(1)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        self._build_save_games(col_l)
        self._build_scouting(col_l)
        self._build_interface(col_l)
        self._build_data(col_l)
        self._build_about(col_l)
        col_l.addStretch(1)
        root.addWidget(self._build_footer())

        self._wire()
        self.load_from_disk()

    # -- structure ---------------------------------------------------------------------------

    def _section(self, col_l, title, rows, first=False):
        hdr = QLabel(title.upper())
        hdr.setObjectName('setSecHdr')
        _spaced_font(hdr, 1.44)  # 0.12em * 12px
        col_l.addSpacing(0 if first else 28)
        col_l.addWidget(hdr)
        col_l.addSpacing(8)
        panel = QFrame()
        panel.setObjectName('setPanel')
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(0)
        for i, r in enumerate(rows):
            if i == len(rows) - 1:
                r.setObjectName('setRowLast')
            pl.addWidget(r)
        col_l.addWidget(panel)

    def _row(self, title=None, help_=None, ctl=None, soon=False, full=None):
        """Flex row: label column (fixed 280) + control column. `full` = widget spanning the row."""
        row = QFrame()
        row.setObjectName('setRow')
        row.setMinimumHeight(58)
        lay = QHBoxLayout(row)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(24)
        if full is not None:
            lay.addWidget(full, 1)
            return row
        lab, lab_l = _bare(QVBoxLayout)
        lab.setFixedWidth(280)
        lab_l.setContentsMargins(0, 4, 0, 0)  # .lab padding-top 4
        lab_l.setSpacing(3)                   # .help margin-top 3
        top, top_l = _bare(QHBoxLayout)
        top.setMinimumHeight(22)
        top_l.setSpacing(8)
        t = QLabel(title)
        t.setObjectName('setLabel')
        top_l.addWidget(t, 0)
        if soon:
            chip = _chip()
            top_l.addWidget(chip, 0, Qt.AlignmentFlag.AlignVCenter)
            self._soon.append((t, chip))  # label wraps only if it cannot fit beside the chip
        top_l.addStretch(1)
        lab_l.addWidget(top)
        self._last_help = None
        if help_:
            self._last_help = _help_label(help_)
            lab_l.addWidget(self._last_help)
        lab_l.addStretch(1)
        lay.addWidget(lab, 0, Qt.AlignmentFlag.AlignTop)
        ctl.setMinimumHeight(30)
        lay.addWidget(ctl, 1, Qt.AlignmentFlag.AlignTop)
        return row

    def _ctl_line(self, *widgets, stretch_first=False):
        w, l = _bare(QHBoxLayout)
        l.setSpacing(8)
        for i, x in enumerate(widgets):
            l.addWidget(x, 1 if (stretch_first and i == 0) else 0)
        if not stretch_first:
            l.addStretch(1)
        return w

    def _input(self, readonly=False):
        e = QLineEdit()
        e.setObjectName('setInput')
        e.setFixedHeight(30)
        e.setReadOnly(readonly)
        e.setProperty('err', False)
        return e

    def _select(self, width):
        c = QComboBox()
        c.setObjectName('setSelect')
        c.setFixedSize(width, 30)
        c.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        return c

    def _check(self, checked=False, disabled=False):
        c = QCheckBox('Enabled')
        c.setObjectName('setCheck')
        c.setFixedHeight(30)
        c.setChecked(checked)
        c.setEnabled(not disabled)
        c.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        return c

    # -- sections ----------------------------------------------------------------------------

    def _build_save_games(self, col_l):
        self._folder = self._input()
        self._folder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._folder.setPlaceholderText('Not set')
        self._folder.setAccessibleName('Default save game folder')
        self._browse = _btn('Browse…')
        line = self._ctl_line(self._folder, self._browse, stretch_first=True)
        msg_w, msg_l = _bare(QHBoxLayout)
        msg_l.setSpacing(6)
        dot_wrap = QWidget()
        dot_wrap.setObjectName('setBare')
        dot_wrap.setFixedSize(7, 15)
        self._folder_dot = _dot(_OK)
        self._folder_dot.setParent(dot_wrap)
        self._folder_dot.setGeometry(0, 4, 7, 7)  # .msg .dot margin-top 4
        self._folder_msg = QLabel()
        self._folder_msg.setObjectName('setMsg')
        self._folder_msg.setWordWrap(True)
        self._folder_msg.setProperty('bad', False)
        msg_l.addWidget(dot_wrap, 0, Qt.AlignmentFlag.AlignTop)
        msg_l.addWidget(self._folder_msg, 1)
        ctl, ctl_l = _bare(QVBoxLayout)
        ctl_l.setSpacing(6)
        ctl_l.addWidget(line)
        ctl_l.addWidget(msg_w)
        ctl_l.addStretch(1)

        detect = _btn('Detect')
        detect.setEnabled(False)
        reopen = self._check(False, disabled=True)
        self._section(col_l, 'Save games', [
            self._row('Default save game folder',
                      'Where FMBR24 opens the file dialog. Set manually for now.', ctl),
            self._row('Auto-detect common locations',
                      'Looks in Steam/Proton, native Linux, Flatpak and Windows paths.',
                      self._ctl_line(detect), soon=True),
            self._row('Reopen last save on launch', 'Skips the Load step when FMBR24 starts.',
                      self._ctl_line(reopen), soon=True),
        ], first=True)

    def _build_scouting(self, col_l):
        self._preset = self._select(180)
        self._preset_edit = _btn('Edit Weights…')
        self._preset_import = _btn('Import…')
        self._preset_delete = _btn('Delete…')  # user presets only (kept from the old dialog)
        self._trait_thr = self._select(220)
        for n in range(1, 21):
            self._trait_thr.addItem(f'{n}  (default)' if n == _settings.DEFAULTS['trait_threshold'] else str(n), n)
        self._section(col_l, 'Scouting', [
            self._row('Trait recommender threshold',
                      'Minimum average attribute for a trait to be recommended on the player window. '
                      'About 14-15 for top clubs, 11-12 for smaller sides.',
                      self._ctl_line(self._trait_thr)),
            self._row('Role weight preset',
                      'Drives the Best by Role report. Replaces the old Settings dialog.',
                      self._ctl_line(self._preset, self._preset_edit, self._preset_import,
                                     self._preset_delete)),
        ])

    def _build_interface(self, col_l):
        self._landing = self._select(220)
        for key, label in _LANDING_LABELS:
            self._landing.addItem(label, key)
        self._pending = self._check(True)
        self._ability = self._select(220)
        self._ability.addItem('Stars  (default)', 'stars')
        self._ability.addItem('Numbers', 'numbers')
        seg, seg_l = _bare(QHBoxLayout)
        seg_l.setSpacing(0)
        for name, text, on in (('setSegL', 'Comfortable', True), ('setSegR', 'Compact', False)):
            b = _btn(text)
            b.setObjectName(name)
            b.setCheckable(True)
            b.setChecked(on)
            b.setEnabled(False)
            seg_l.addWidget(b)
        seg_l.addStretch(1)
        self._section(col_l, 'Interface', [
            self._row('Landing page after loading a save', 'The page shown once parsing finishes.',
                      self._ctl_line(self._landing)),
            self._row('Show PENDING markers',
                      'Flags data FMBR24 cannot read from the save yet. Off hides those rows.',
                      self._ctl_line(self._pending)),
            self._row('Ability display',
                      'Show CA, PA and Dev Rate as stars or raw numbers in the player window header. '
                      'Stars are an approximation; hover for the number.',
                      self._ctl_line(self._ability)),
            self._row('Table density', 'Row height in every table.', seg, soon=True),
        ])

    def _build_data(self, col_l):
        self._use_cache = use_cache = self._check(True)
        self._cache_path = self._input(readonly=True)
        self._cache_path.setText(_cache.cache_dir())
        self._cache_path.setAccessibleName('Cache folder')
        self._cache_path.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._cache_open = _btn('Open')
        self._cache_clear = _btn('Clear cache')
        clear_row = self._row('Clear cache', 'x', self._ctl_line(self._cache_clear))
        self._cache_help = self._last_help
        self._section(col_l, 'Data', [
            self._row('Use parse cache',
                      'Skips the parse on Load when a save has not changed. Reload always re-parses.',
                      self._ctl_line(use_cache)),
            self._row('Cache folder', 'Read-only. Holds parsed saves.',
                      self._ctl_line(self._cache_path, self._cache_open, stretch_first=True)),
            clear_row,
        ])

    def _build_about(self, col_l):
        ident, ident_l = _bare(QHBoxLayout)
        ident_l.setSpacing(14)
        logo = QLabel()
        logo.setFixedSize(48, 48)
        px = QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'icon.png'))
        if not px.isNull():
            logo.setPixmap(px.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation))
            logo.setScaledContents(True)
        names, names_l = _bare(QVBoxLayout)
        names_l.setSpacing(2)
        name = QLabel(_settings.APP_NAME)
        name.setObjectName('setAboutName')
        name.setFixedHeight(24)
        _spaced_font(name, 0.8)  # 0.04em * 20px
        ver = QLabel(f'Version {_settings.APP_VERSION}')
        ver.setObjectName('setAboutVer')
        names_l.addWidget(name)
        names_l.addWidget(ver)
        ident_l.addWidget(logo)
        ident_l.addWidget(names, 1)

        link = QLabel(f'<a href="{_settings.APP_REPO_URL}" style="color:{C["accent_hover"]};'
                      f' text-decoration:none;">github.com/acidtwin/FMBR24</a>')
        link.setObjectName('setLink')
        link.setTextFormat(Qt.TextFormat.RichText)
        link.setOpenExternalLinks(True)
        link.setFixedHeight(30)
        legal = QLabel(_settings.LEGAL_LINE)
        legal.setObjectName('setLegal')
        legal.setWordWrap(True)
        self._legal = legal
        self._section(col_l, 'About', [
            self._row(full=ident),
            self._row('Source code', None, self._ctl_line(link)),
            self._row(full=legal),
        ])

    def _build_footer(self):
        foot = QFrame()
        foot.setObjectName('setFooter')
        foot.setFixedHeight(56)
        outer = QHBoxLayout(foot)
        outer.setContentsMargins(28, 0, 28, 0)
        outer.setSpacing(0)
        inner, inner_l = _bare(QHBoxLayout)
        inner.setMaximumWidth(760)
        inner_l.setSpacing(8)
        self._foot_dot = _dot(C['text_dim'])
        self._foot_txt = QLabel('All changes saved')
        self._foot_txt.setObjectName('setFootTxt')
        self._foot_txt.setProperty('state', 'clean')
        inner_l.addWidget(self._foot_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        inner_l.addWidget(self._foot_txt, 1)
        self._reset_btn = _btn('Reset to defaults')
        self._save_btn = _btn('Save settings', accent=True)
        inner_l.addWidget(self._reset_btn)
        inner_l.addWidget(self._save_btn)
        outer.addStretch(1)
        outer.addWidget(inner, 100)
        outer.addStretch(1)
        return foot

    def showEvent(self, e):
        super().showEvent(e)
        if not self._fitted:  # needs polished fonts, so not in __init__
            self._fitted = True
            for t, chip in self._soon:
                t.ensurePolished()
                chip.ensurePolished()
                avail = 280 - 8 - chip.sizeHint().width()
                need = t.fontMetrics().horizontalAdvance(t.text()) + 2
                t.setWordWrap(need > avail)
                t.setFixedWidth(min(need, avail))

    # -- behaviour ---------------------------------------------------------------------------

    def _wire(self):
        self._folder.textChanged.connect(self._on_changed)
        self._browse.clicked.connect(self._browse_folder)
        self._landing.currentIndexChanged.connect(self._on_changed)
        self._pending.toggled.connect(self._on_changed)
        self._use_cache.toggled.connect(self._on_changed)
        self._trait_thr.currentIndexChanged.connect(self._on_changed)
        self._ability.currentIndexChanged.connect(self._on_changed)
        self._preset.currentIndexChanged.connect(self._on_preset_changed)
        self._preset_edit.clicked.connect(self._edit_weights)
        self._preset_import.clicked.connect(self._import_preset)
        self._preset_delete.clicked.connect(self._delete_preset)
        self._cache_open.clicked.connect(self._open_cache_dir)
        self._cache_clear.clicked.connect(self._clear_cache)
        self._reset_btn.clicked.connect(self._reset)
        self._save_btn.clicked.connect(self._save)

    def _values(self):
        return {
            'default_save_dir': self._folder.text().strip(),
            'role_weights_preset': self._preset.currentText(),
            'landing_page': self._landing.currentData(),
            'show_pending': self._pending.isChecked(),
            'use_cache': self._use_cache.isChecked(),
            'trait_threshold': self._trait_thr.currentData(),
            'ability_display': self._ability.currentData(),
        }

    def is_dirty(self):
        return self._values() != self._saved

    def _apply_values(self, v):
        """Push a settings dict into the widgets (signals blocked; caller refreshes)."""
        for w in (self._folder, self._landing, self._pending, self._use_cache, self._preset, self._trait_thr, self._ability):
            w.blockSignals(True)
        self._folder.setText(v['default_save_dir'])
        self._landing.setCurrentIndex(max(0, self._landing.findData(v['landing_page'])))
        self._pending.setChecked(v['show_pending'])
        self._use_cache.setChecked(v['use_cache'])
        self._trait_thr.setCurrentIndex(max(0, self._trait_thr.findData(v['trait_threshold'])))
        self._ability.setCurrentIndex(max(0, self._ability.findData(v['ability_display'])))
        self._fill_presets(v['role_weights_preset'])
        for w in (self._folder, self._landing, self._pending, self._use_cache, self._preset, self._trait_thr, self._ability):
            w.blockSignals(False)
        self._after_preset_change()
        self._on_changed()

    def load_from_disk(self):
        self._apply_values(_settings.load())
        self._saved = self._values()  # effective values (a deleted preset falls back to first)
        self._on_changed()
        self.refresh_info()

    def on_shown(self):
        """Called whenever the page is opened: re-read disk unless there are unsaved edits."""
        if not self.is_dirty():
            self.load_from_disk()
        else:
            self.refresh_info()

    def refresh_info(self):
        """Cache stats (they change after every load)."""
        n, size = _cache.cache_info()
        if n:
            txt = f"{n} save{'s' if n != 1 else ''} · {_fmt_size(size)}. " \
                  "Saves parse again on next load (~60 s each)."
        else:
            txt = 'Cache is empty.'
        _set_help(self._cache_help, txt)
        self._cache_clear.setEnabled(n > 0)
        self._cache_path.setText(_cache.cache_dir())

    # folder ---------------------------------------------------------------------------------

    def _on_changed(self, *_):
        state, n = _settings.folder_status(self._folder.text())
        self._folder_state = state
        bad = state in ('missing', 'notdir')
        if state == 'ok':
            color, text = _OK, f"Folder found · {n} save{'s' if n != 1 else ''}"
        elif state == 'unset':
            color, text = C['text_dim'], 'No folder set. The Load dialog opens in its usual location.'
        elif state == 'notdir':
            color, text = C['non_hgp_red'], 'That path is not a folder. Check the path or choose another folder.'
        else:
            color, text = C['non_hgp_red'], 'Folder not found. Check the path or choose another folder.'
        self._folder_dot.setStyleSheet(f"background:{color}; border-radius:3px;")
        self._folder_msg.setText(text)
        self._folder_msg.setProperty('bad', bad)
        self._folder.setProperty('err', bad)
        for w in (self._folder_msg, self._folder):
            w.style().unpolish(w)
            w.style().polish(w)
        self._refresh_footer()

    def _refresh_footer(self):
        err = self._folder_state in ('missing', 'notdir')
        dirty = self.is_dirty()
        if err:
            state, text, dot = 'error', 'Fix the folder path to save', C['non_hgp_red']
        elif dirty:
            state, text, dot = 'edited', 'Unsaved changes', C['warning']
        else:
            state, text, dot = 'clean', 'All changes saved', C['text_dim']
        self._foot_txt.setText(text)
        self._foot_txt.setProperty('state', state)
        self._foot_txt.style().unpolish(self._foot_txt)
        self._foot_txt.style().polish(self._foot_txt)
        self._foot_dot.setStyleSheet(f"background:{dot}; border-radius:3px;")
        self._save_btn.setEnabled(dirty and not err)

    def _browse_folder(self):
        cur = os.path.expanduser(self._folder.text().strip())
        start = cur if os.path.isdir(cur) else os.path.expanduser('~')
        path = QFileDialog.getExistingDirectory(self.window(), 'Choose default save game folder', start)
        if path:
            self._folder.setText(path)

    # role weights (logic reused from the old SettingsDialog) --------------------------------

    def _fill_presets(self, select_name):
        self._presets = _weights.list_presets()
        self._preset.clear()
        idx = 0
        for i, p in enumerate(self._presets):
            self._preset.addItem(p['name'])
            if p['name'] == select_name:
                idx = i
        self._preset.setCurrentIndex(idx)

    def _after_preset_change(self):
        i = self._preset.currentIndex()
        p = self._presets[i] if 0 <= i < len(self._presets) else None
        self._preset_delete.setVisible(bool(p) and not p['bundled'])
        self._preset_edit.setEnabled(bool(p))
        tip = ''
        if p:
            tip = '\n'.join(x for x in (f"Style: {p['tactical_style']}" if p['tactical_style'] else '',
                                        p['description']) if x)
        self._preset.setToolTip(tip)

    def _on_preset_changed(self, *_):
        self._after_preset_change()
        self._refresh_footer()

    def _reselect(self, name=None):
        name = name or self._preset.currentText()
        self._preset.blockSignals(True)
        self._fill_presets(name)
        self._preset.blockSignals(False)
        self._on_preset_changed()

    def _edit_weights(self):
        from gui.main_window import WeightEditorDialog  # lazy: main_window imports this module
        i = self._preset.currentIndex()
        if not (0 <= i < len(self._presets)):
            return
        try:
            base = _weights.load_preset(self._presets[i]['path'])
        except Exception as e:
            QMessageBox.warning(self.window(), 'Error', f'Could not load preset:\n{e}')
            return
        dlg = WeightEditorDialog(base, self.window())
        if dlg.exec() == dlg.DialogCode.Accepted:
            new = dlg.saved_preset_name()
            if new:
                self._reselect(new)

    def _import_preset(self):
        path, _ = QFileDialog.getOpenFileName(
            self.window(), 'Import Weight Preset', '', 'JSON Files (*.json)')
        if not path:
            return
        try:
            self._reselect(_weights.import_preset(path))
        except Exception as e:
            QMessageBox.warning(self.window(), 'Import Error', f'Could not import preset:\n{e}')

    def _delete_preset(self):
        i = self._preset.currentIndex()
        if not (0 <= i < len(self._presets)) or self._presets[i]['bundled']:
            return
        name = self._presets[i]['name']
        if QMessageBox.question(
                self.window(), 'Delete Preset', f"Delete '{name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        _weights.delete_user_preset(name)
        self._reselect('')

    # data -----------------------------------------------------------------------------------

    def _open_cache_dir(self):
        d = _cache.cache_dir()
        if os.path.isdir(d):
            QDesktopServices.openUrl(QUrl.fromLocalFile(d))
        else:
            self.message.emit('Cache folder does not exist yet.')

    def _clear_cache(self):
        n, _size = _cache.cache_info()
        if not n:
            return
        if QMessageBox.question(
                self.window(), 'Clear cache',
                f"Delete {n} cached save{'s' if n != 1 else ''}? "
                "They will be parsed again on next load (~60 s each).",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        done = _cache.clear_all_caches()
        self.refresh_info()
        self.message.emit(f"Cleared {done} cached save{'s' if done != 1 else ''}.")

    # footer ---------------------------------------------------------------------------------

    def _reset(self):
        if QMessageBox.question(
                self.window(), 'Reset to defaults',
                'Reset every setting on this page to its default? '
                'Nothing is saved until you press Save settings.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        self._apply_values(dict(_settings.DEFAULTS))

    def _save(self):
        if not self._save_btn.isEnabled():
            return
        vals = self._values()
        if not _settings.save(vals):
            QMessageBox.warning(self.window(), 'Settings', 'Could not write the settings file.')
            return
        self._saved = vals
        self._refresh_footer()
        self.message.emit('Settings saved')
        self.saved.emit(dict(vals))
