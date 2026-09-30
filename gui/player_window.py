"""Player window: left-hand tab strip (TABS table) over a QStackedWidget. Styling from mockups/player-window-options.html option B.

Profile = hero (identity, status chips, CA/PA, actions), four-column attribute tile grid with a Current | At potential
switch, and a rail (personality, traits). Contract = Until/Wage/Value panel. Positions = mini pitch + best positions.
The other tabs are "Coming soon" placeholders. To add a real tab: write a `_page_<key>` method returning a QWidget and
put its name in the TABS row (None = placeholder using SOON[key]).

Data the save does not give us yet is read from `data` (see `player_extra_data`) and shown as PENDING
(respecting Settings > Show PENDING markers) until the value is supplied. Projected ("at potential")
values are display only: nothing here touches the patch/save code.
"""
import calendar

from PyQt6.QtCore import Qt, QPointF, QRect, QRectF, QSize
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QKeySequence, QPainter, QPen, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QButtonGroup, QDialog, QFrame, QHBoxLayout, QLabel, QLayout, QPushButton, QScrollArea,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from fm_editor import potential as _pot
from fm_editor.agecalc import person_age
from fm_editor.traits import trait_names
from gui.theme import COLORS

# -- tokens (mockup comment block, literal) ------------------------------------------------------
C_POT = '#9A8AF5'       # potential half of "14 / 17"
C_ALT = '#1E292E'       # zebra
C_TX3 = COLORS['text_dim']
TIER_HEX = ['', '#E8696A', '#E0973C', '#8B96A8', '#E6EAF0', '#EAD95C', '#52C287']  # best = green (FM), 14-16 = light yellow
TIER_RGB = [None, (232, 105, 106), (224, 151, 60), (139, 150, 168), (230, 234, 240), (234, 217, 92), (82, 194, 135)]
TILE_ALPHA = round(0.14 * 255)  # 36


def tier(v):
    return 1 if v <= 4 else 2 if v <= 8 else 3 if v <= 11 else 4 if v <= 13 else 5 if v <= 16 else 6


def _rgba(t, a=TILE_ALPHA):
    r, g, b = TIER_RGB[t]
    return f'rgba({r},{g},{b},{a})'


# -- attribute groups: (label, raw_attrs index, lower_is_better) -----------------------------------
TECH = [('Corners', 27), ('Crossing', 0), ('Dribbling', 1), ('Finishing', 2), ('First Touch', 22),
        ('Free Kick', 35), ('Heading', 3), ('Long Shots', 4), ('Long Throws', 30), ('Marking', 5),
        ('Passing', 7), ('Penalties', 8), ('Tackling', 9), ('Technique', 23)]
MENT = [('Aggression', 45), ('Anticipation', 17), ('Bravery', 43), ('Composure', 52), ('Concentration', 53),
        ('Decisions', 18), ('Determination', 51), ('Flair', 26), ('Leadership', 40), ('Off the Ball', 6),
        ('Positioning', 20), ('Teamwork', 28), ('Vision', 10), ('Work Rate', 29)]
PHYS = [('Acceleration', 34), ('Agility', 46), ('Balance', 42), ('Jumping Reach', 39),
        ('Natural Fitness', 50), ('Pace', 38), ('Stamina', 37), ('Strength', 36)]
GKA = [('Aerial Reach', 12), ('Command of Area', 13), ('Communication', 14), ('Eccentricity', 31),
       ('Handling', 11), ('Kicking', 15), ('One on Ones', 19), ('Punching', 33), ('Reflexes', 21),
       ('Rushing Out', 32), ('Throwing', 16)]
HIDD = [('Consistency', 44), ('Dirtiness', 41), ('Important Matches', 47), ('Injury Prone', 48),
        ('Versatility', 49)]
FOOT = [('Left Foot', 24), ('Right Foot', 25)]
LOWER_BETTER = {31, 41, 48}   # Eccentricity, Dirtiness, Injury Prone: coloured on 21 - v
PERS = ['Adaptability', 'Ambition', 'Loyalty', 'Pressure', 'Professionalism', 'Sportsmanship', 'Temperament']

POS_ORDER = ['GK', 'SW', 'DL', 'DC', 'DR', 'DM', 'ML', 'MC', 'MR', 'AML', 'AMC', 'AMR', 'ST', 'WBL', 'WBR']
POS_NAME = {
    'GK': 'Goalkeeper', 'SW': 'Sweeper', 'DL': 'Left Back', 'DC': 'Centre Back', 'DR': 'Right Back',
    'WBL': 'Left Wing-Back', 'WBR': 'Right Wing-Back', 'DM': 'Defensive Midfielder',
    'ML': 'Left Midfielder', 'MC': 'Central Midfielder', 'MR': 'Right Midfielder',
    'AML': 'Left Winger', 'AMC': 'Attacking Midfielder', 'AMR': 'Right Winger', 'ST': 'Striker',
}
# Mini-pitch dot centres as percent (x, y) of the pitch's padding box, attacking UP. ONE table: edit here to
# polish. Rows are >= 12% apart vertically (dot = 20px on a 166px box) so dots never overlap.
PITCH = {
    'ST': (50, 9),
    'AML': (16, 23), 'AMC': (50, 23), 'AMR': (84, 23),
    'ML': (14, 38), 'MC': (50, 38), 'MR': (86, 38),
    'DM': (50, 53),
    'WBL': (9, 57), 'WBR': (91, 57),
    'DL': (22, 70), 'DC': (50, 70), 'DR': (78, 70),
    'SW': (50, 82),
    'GK': (50, 93),
}

_PERSON_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#525B68" '
               'stroke-width="1.6"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/></svg>')

# (key, label, builder method name or None = "Coming soon" placeholder described by SOON[key])
TABS = [
    ('profile', 'Profile', '_page_profile'),
    ('contract', 'Contract', '_page_contract'),
    ('transfer', 'Transfer', None),
    ('positions', 'Positions', '_page_positions'),
    ('general', 'General Rating', None),
    ('positional', 'Positional Rating', None),
    ('role', 'Role Rating', None),
    ('history', 'History', None),
]
SOON = {
    'transfer': 'Market value, asking price and transfer / loan status.',
    'general': 'Overall rating and a summary of the role ratings.',
    'positional': 'Rating per position, over time and across seasons.',
    'role': 'Suitability for each tactical role.',
    'history': 'Career stats by season and club. The save holds this data; it will be plugged in here later.',
}
_LAST_TAB = 'profile'     # last opened tab, remembered for the session

CAPTION = 'Projection from CA weights; real growth depends on training, playing time and personality.'


def player_extra_data(person, save_data):
    """PLUG IN: per-player data the parser does not decode yet. Return any of these keys (None = unknown,
    shown as PENDING). Strings are displayed as-is.
        wage       e.g. '£100K p/w'          value      e.g. '£88M - £97M'
        height_cm  int                        weight_kg  int
        traits     list[str] of trait labels from person['trait_mask'] (A/B names, else 'Trait #n')
        history    reserved (career history is not shown in layout B yet)
    """
    mask = person.get('trait_mask')
    traits = trait_names(mask) if mask is not None else None     # None = old cache / unknown -> PENDING
    return {'wage': None, 'value': None, 'height_cm': None, 'weight_kg': None, 'traits': traits, 'history': None}


def _dlg_qss():
    c = COLORS
    return f"""
QDialog#playerWindow {{ background:{c['window_bg']}; }}
QDialog#playerWindow QWidget {{ background:transparent; }}
QDialog#playerWindow QScrollArea {{ background:transparent; border:none; }}
QDialog#playerWindow QWidget#pwBody {{ background:{c['window_bg']}; }}
QDialog#playerWindow QLabel {{ background:transparent; color:{c['text_primary']}; font-size:12px; }}
QDialog#playerWindow QFrame#pwPanel {{ background:{c['surface']}; border:1px solid {c['border']}; border-radius:3px; }}
QDialog#playerWindow QFrame#pwRowAlt {{ background:{C_ALT}; }}
QDialog#playerWindow QFrame#pwRow {{ background:transparent; }}
QDialog#playerWindow QFrame#pwTabs {{ background:{c['surface']}; border:none; border-right:1px solid {c['border']}; }}
QDialog#playerWindow QPushButton#pwTab {{ background:transparent; border:none; border-left:3px solid transparent;
    color:{c['text_secondary']}; text-align:left; padding:8px 12px; font-size:12px; border-radius:0; }}
QDialog#playerWindow QPushButton#pwTab:hover {{ background:{c['elevated']}; color:{c['text_primary']};
    border-left:3px solid {c['border_bright']}; }}
QDialog#playerWindow QPushButton#pwTab:checked {{ background:{c['selection_bg']}; color:{c['text_primary']};
    font-weight:bold; border-left:3px solid {c['accent']}; }}
QDialog#playerWindow QLabel#pwSoonT {{ font-size:20px; font-weight:bold; }}
QDialog#playerWindow QLabel#pwSoonTag {{ color:{c['text_secondary']}; font-size:10px; font-weight:bold;
    border:1px solid {c['border_bright']}; border-radius:10px; padding:0 10px; }}
QDialog#playerWindow QLabel#pwSoonD {{ color:{c['text_secondary']}; font-size:12px; }}
QDialog#playerWindow QWidget#pwHead {{ background:transparent; }}
QDialog#playerWindow QLabel#pwHeadT, QDialog#playerWindow QLabel#pwColHead {{
    color:{c['text_secondary']}; font-size:11px; font-weight:bold; }}
QDialog#playerWindow QLabel#pwName {{ font-size:24px; font-weight:bold; }}
QDialog#playerWindow QLabel#pwSub {{ color:{c['text_secondary']}; font-size:12px; }}
QDialog#playerWindow QLabel#pwBigLab {{ color:{c['text_secondary']}; font-size:10px; font-weight:bold; }}
QDialog#playerWindow QLabel#pwBigNum {{ font-size:36px; font-weight:bold; }}
QDialog#playerWindow QLabel#pwAttrName, QDialog#playerWindow QLabel#pwKvL {{ color:{c['text_secondary']}; }}
QDialog#playerWindow QLabel#pwKvR {{ font-weight:600; }}
QDialog#playerWindow QLabel#pwTrait {{ font-weight:600; }}
QDialog#playerWindow QLabel#pwNote {{ color:{c['text_secondary']}; font-size:11px; }}
QDialog#playerWindow QLabel#pwHint {{ color:{c['text_secondary']}; font-size:11px; }}
QDialog#playerWindow QLabel#pwAvatar {{ background:{c['elevated']}; border-radius:3px; }}
QDialog#playerWindow QLabel#pwBadge {{ color:#FFFFFF; font-size:10px; font-weight:bold; border-radius:2px; }}
QDialog#playerWindow QLabel#pwPill {{ color:{c['text_secondary']}; font-size:10px; font-weight:bold;
    border:1px solid {c['border_bright']}; border-radius:10px; padding:0 9px; }}
QDialog#playerWindow QLabel#pwPillOn {{ color:{c['hgp_green']}; font-size:10px; font-weight:bold;
    border:1px solid {c['hgp_green']}; border-radius:10px; padding:0 9px; background:rgba(90,160,209,36); }}
QDialog#playerWindow QLabel#pwPillUnk {{ color:{c['text_secondary']}; font-size:10px; font-weight:bold; padding:0 2px; }}
QDialog#playerWindow QLabel#pwChip {{ background:{c['elevated']}; color:#FFFFFF; font-size:11px; font-weight:600;
    border-radius:3px; padding:0 8px; }}
QDialog#playerWindow QLabel#pwChipInj {{ background:#8B1A1A; color:#FFFFFF; font-size:11px; font-weight:600;
    border-radius:3px; padding:0 8px; }}
QDialog#playerWindow QLabel#pwChipOk {{ background:{c['elevated']}; color:#52C287; font-size:11px; font-weight:600;
    border-radius:3px; padding:0 8px; }}
QDialog#playerWindow QLabel#pwChipDev {{ background:{c['window_bg']}; color:#FFFFFF; font-size:11px; font-weight:600;
    border:1px solid {c['border']}; border-radius:3px; padding:0 8px; }}
QDialog#playerWindow QFrame#pwSeg {{ background:{c['window_bg']}; border:1px solid {c['border_bright']}; border-radius:3px; }}
QDialog#playerWindow QPushButton#pwSegL, QDialog#playerWindow QPushButton#pwSegR {{ background:{c['window_bg']}; color:{c['text_secondary']};
    border:none; font-size:11px; font-weight:bold; padding:0 12px; }}
QDialog#playerWindow QPushButton#pwSegL {{ border-top-left-radius:2px; border-bottom-left-radius:2px; }}
QDialog#playerWindow QPushButton#pwSegR {{ border-top-right-radius:2px; border-bottom-right-radius:2px; }}
QDialog#playerWindow QPushButton#pwSegL:checked, QDialog#playerWindow QPushButton#pwSegR:checked {{ background:{c['accent']}; color:#FFFFFF; }}
QDialog#playerWindow QPushButton#pwSegR:disabled {{ color:{C_TX3}; background:{c['window_bg']}; }}
QDialog#playerWindow QPushButton#pwPrimary {{ background:{c['accent']}; color:#FFFFFF; border:1px solid transparent; border-radius:3px;
    font-size:12px; font-weight:bold; }}
QDialog#playerWindow QPushButton#pwPrimary:hover {{ background:{c['accent_hover']}; }}
QDialog#playerWindow QPushButton#pwPrimary:pressed {{ background:{c['accent_press']}; }}
QDialog#playerWindow QPushButton#pwShortOn, QDialog#playerWindow QPushButton#pwShortOn:disabled {{ background:{c['selection_bg']}; color:{C_POT};
    border:1px solid {c['accent_hover']}; border-radius:3px; font-size:12px; font-weight:bold; }}
QDialog#playerWindow QPushButton#pwGhost {{ background:{c['surface']}; color:#FFFFFF; border:1px solid {c['border_bright']};
    border-radius:3px; font-size:12px; font-weight:bold; }}
QDialog#playerWindow QPushButton#pwGhost:hover {{ background:{c['elevated']}; }}
QDialog#playerWindow QPushButton#pwGhost:disabled {{ background:{c['elevated']}; color:{C_TX3}; border:1px solid {c['border']}; }}
"""


def _spaced(lbl, px=0.88):
    f = lbl.font()
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, px)
    lbl.setFont(f)
    return lbl


def _lab(text, name, align=None, h=None):
    lbl = QLabel(text)
    lbl.setObjectName(name)
    if align is not None:
        lbl.setAlignment(align)
    if h:
        lbl.setFixedHeight(h)
    return lbl


class _ElideLabel(QLabel):
    """Single-line label that elides its text with an ellipsis instead of clipping (mockup text-overflow)."""

    def __init__(self, text, name):
        super().__init__(text)
        self.setObjectName(name)
        self._full = text
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.setText(self.fontMetrics().elidedText(self._full, Qt.TextElideMode.ElideRight, self.width()))


class _Flow(QLayout):
    """Left-to-right wrapping layout (Qt flow-layout example) for the hero chips."""

    def __init__(self, parent=None, hspace=6, vspace=6):
        super().__init__(parent)
        self._items, self._h, self._v = [], hspace, vspace
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return self._do(QRect(0, 0, w, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        s = QSize()
        for it in self._items:
            s = s.expandedTo(it.minimumSize())
        return s

    def _do(self, rect, test):
        x, y, row_h = rect.x(), rect.y(), 0
        for it in self._items:
            sz = it.sizeHint()
            if x + sz.width() > rect.right() + 1 and row_h > 0:
                x, y, row_h = rect.x(), y + row_h + self._v, 0
            if not test:
                it.setGeometry(QRect(x, y, sz.width(), sz.height()))
            x += sz.width() + self._h
            row_h = max(row_h, sz.height())
        return y + row_h - rect.y()


class _Bar(QWidget):
    """6px square-ended bar (mockup .bar): track #343740, fill `color` up to `frac`."""

    def __init__(self, frac, color, parent=None):
        super().__init__(parent)
        self._frac, self._color = max(0.0, min(1.0, frac)), QColor(color)
        self.setFixedHeight(6)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(COLORS['border']))
        p.fillRect(QRect(0, 0, round(self.width() * self._frac), self.height()), self._color)


class _Pitch(QWidget):
    """112x168 mini pitch (mockup .pitch) with the 15 position ratings as tier-coloured dots."""
    W, H = 112, 168

    def __init__(self, ratings, parent=None):
        super().__init__(parent)
        self._r = ratings            # {pos: rating}
        self.setFixedSize(self.W, self.H)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QColor(COLORS['window_bg'])
        # box: 1px border #454A58, radius 3, bg #14151A
        p.setPen(QPen(QColor(COLORS['border_bright']), 1))
        p.setBrush(bg)
        p.drawRoundedRect(QRectF(0.5, 0.5, self.W - 1, self.H - 1), 3, 3)
        iw, ih = self.W - 2, self.H - 2      # padding box (inside the 1px border), origin (1, 1)
        line = QPen(QColor(COLORS['border']), 1)
        p.setPen(line)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(QPointF(0, 1 + ih * 0.5 + 0.5), QPointF(self.W, 1 + ih * 0.5 + 0.5))                 # halfway
        top = 1 + ih * 0.44
        p.drawEllipse(QRectF(1 + iw * 0.5 - 14 + 0.5, top + 0.5, 27, 27))                               # centre circle 28
        bx0, bx1 = 1 + iw * 0.25, 1 + iw * 0.75
        p.drawRect(QRectF(bx0 + 0.5, 0.5, bx1 - bx0 - 1, 19))                                           # boxes top/bottom
        p.drawRect(QRectF(bx0 + 0.5, self.H - 20.5, bx1 - bx0 - 1, 19))
        f = p.font()
        f.setPixelSize(10)
        f.setBold(True)
        p.setFont(f)
        for pos, (x, y) in PITCH.items():
            v = self._r.get(pos, 1)
            t = tier(v)
            cx, cy = 1 + iw * x / 100, 1 + ih * y / 100
            col = QColor(TIER_HEX[t])
            fill = QColor(col)
            fill.setAlpha(TILE_ALPHA)
            # fill over the pitch background, then a 1px inset border
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(fill)
            p.drawEllipse(QRectF(cx - 10, cy - 10, 20, 20))
            p.setPen(QPen(col, 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(cx - 9.5, cy - 9.5, 19, 19))
            p.drawText(QRectF(cx - 10, cy - 10, 20, 20), Qt.AlignmentFlag.AlignCenter, str(v))


class PlayerWindow(QDialog):
    """Modal player window. Results for the caller: `_patch_mode` ('hgp' / 'hgc' / None) and
    `_shortlist_added`; both close the window via accept(), the caller then runs its existing flow."""

    def __init__(self, person, save_data, club_entity_id, parent=None, shortlisted=False, can_patch=False,
                 data=None):
        super().__init__(parent)
        self.setObjectName('playerWindow')
        self.setWindowTitle(person['name'])
        self.setMinimumSize(1040, 640)
        self.resize(1100, 760)
        self.setStyleSheet(_dlg_qss())
        self._person = person
        self._save_data = save_data
        self._club_entity_id = club_entity_id
        self._shortlisted = shortlisted
        self._can_patch = can_patch
        self._patch_mode = None
        self._shortlist_added = False
        self._pot_on = False
        self._proj = None
        self._data = {**player_extra_data(person, save_data), **(data or {})}
        self._build()      # NB: Profile page must build first (sets _is_gk/_hgp/_ratings used by other tabs)

    # -- data helpers ------------------------------------------------------------------------
    @staticmethod
    def _disp(raw_v):
        return max(1, min(20, round(raw_v / 5)))

    def _show_pending(self):
        from gui import main_window as mw
        return mw._SHOW_PENDING

    def _pend_chip(self):
        from gui import main_window as mw
        return mw._club_pending_chip()        # existing PENDING chip; hidden when the setting is off

    def _club_name(self):
        sd = self._save_data or {}
        cid = (sd.get('squads') or {}).get(self._person.get('id'))
        if cid is None:
            return ''
        return next((c['name'] for c in sd.get('clubs', []) if c.get('id') == cid), '')

    # -- building ------------------------------------------------------------------------------
    def _build(self):
        global _LAST_TAB
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        strip = QFrame()
        strip.setObjectName('pwTabs')
        strip.setFixedWidth(150)
        sv = QVBoxLayout(strip)
        sv.setContentsMargins(0, 8, 0, 8)
        sv.setSpacing(0)
        self._stack = QStackedWidget()
        self._tab_btns = {}
        self._tab_keys = [k for k, _l, _b in TABS]
        grp = QButtonGroup(self)
        grp.setExclusive(True)
        self._tab_group = grp
        for i, (key, label, builder) in enumerate(TABS):
            btn = QPushButton(label)
            btn.setObjectName('pwTab')
            btn.setCheckable(True)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._select_tab(k))
            grp.addButton(btn)
            sv.addWidget(btn)
            self._tab_btns[key] = btn
            self._stack.addWidget(getattr(self, builder)() if builder else self._page_soon(label, SOON[key]))
        sv.addStretch()
        outer.addWidget(strip)
        outer.addWidget(self._stack, 1)
        QShortcut(QKeySequence('Ctrl+Tab'), self, activated=lambda: self._step_tab(1))
        QShortcut(QKeySequence('Ctrl+Shift+Tab'), self, activated=lambda: self._step_tab(-1))
        self._select_tab(_LAST_TAB if _LAST_TAB in self._tab_btns else 'profile')

    def _select_tab(self, key):
        global _LAST_TAB
        _LAST_TAB = key
        self._tab_btns[key].setChecked(True)
        self._stack.setCurrentIndex(self._tab_keys.index(key))

    def _step_tab(self, d):
        self._select_tab(self._tab_keys[(self._stack.currentIndex() + d) % len(self._tab_keys)])

    @staticmethod
    def _scrolled(content):
        """Wrap a page in a vertical-only scroll area over the window background."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content.setObjectName('pwBody')
        scroll.setWidget(content)
        return scroll

    def _page_soon(self, label, text):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.setSpacing(10)
        al = Qt.AlignmentFlag.AlignHCenter
        v.addWidget(_lab(label, 'pwSoonT', al), 0, al)
        v.addWidget(_spaced(_lab('COMING SOON', 'pwSoonTag', Qt.AlignmentFlag.AlignCenter, 20)), 0, al)
        d = _lab(text, 'pwSoonD', al)
        d.setWordWrap(True)
        d.setFixedWidth(360)
        v.addWidget(d, 0, al)
        return w

    def _page_profile(self):
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(12, 12, 12, 12)
        bl.setSpacing(12)
        bl.addWidget(self._hero())
        main = QHBoxLayout()
        main.setSpacing(12)
        main.addWidget(self._attr_panel(), 1)
        main.addWidget(self._rail(), 0, Qt.AlignmentFlag.AlignTop)
        bl.addLayout(main)
        bl.addStretch()
        return self._scrolled(body)

    def _page_contract(self):
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(12, 12, 12, 12)
        bl.setSpacing(12)
        cp = self._contract_panel()
        cp.setFixedWidth(360)
        bl.addWidget(cp)
        bl.addWidget(_lab('Bonuses, clauses and release terms will be added here.', 'pwNote'))
        bl.addStretch()
        return self._scrolled(body)

    def _page_positions(self):
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(12, 12, 12, 12)
        bl.setSpacing(12)
        panel, v = self._panel('Positions')
        row = QHBoxLayout()
        row.setContentsMargins(16, 6, 16, 16)
        row.setSpacing(24)
        row.addWidget(_Pitch(self._ratings), 0, Qt.AlignmentFlag.AlignTop)
        row.addWidget(self._best_positions(), 0, Qt.AlignmentFlag.AlignTop)
        row.addStretch()
        v.addLayout(row)
        panel.setFixedWidth(420)
        bl.addWidget(panel)
        bl.addStretch()
        return self._scrolled(body)

    def _best_positions(self):
        ratings = self._ratings
        top = sorted(POS_ORDER, key=lambda x: (-ratings[x], POS_ORDER.index(x)))[:5]
        tp = QVBoxLayout()
        tp.setSpacing(4)
        tp.setContentsMargins(0, 0, 0, 0)
        head = _spaced(_lab('BEST POSITIONS', 'pwBigLab'))
        head.setContentsMargins(0, 0, 0, 2)
        tp.addWidget(head)
        for ps in top:
            r = QHBoxLayout()
            r.setSpacing(8)
            r.setContentsMargins(0, 0, 0, 0)
            r.addWidget(self._badge(ps))
            r.addStretch()
            v = ratings[ps]
            vl = _lab(str(v), 'pwKvR')
            vl.setStyleSheet(f'QLabel#pwKvR {{ color:{TIER_HEX[tier(v)]}; font-size:13px; font-weight:bold; }}')
            r.addWidget(vl)
            rw = QWidget()
            rw.setFixedHeight(24)
            rw.setLayout(r)
            tp.addWidget(rw)
        tw = QWidget()
        tw.setFixedWidth(120)
        tw.setLayout(tp)
        return tw

    def _panel(self, title, right=None):
        """-> (QFrame#pwPanel, body QVBoxLayout). 36px header, 11/700 UPPERCASE #8B96A8."""
        f = QFrame()
        f.setObjectName('pwPanel')
        v = QVBoxLayout(f)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        head = QWidget()
        head.setObjectName('pwHead')
        head.setFixedHeight(36)
        h = QHBoxLayout(head)
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(8)
        h.addWidget(_spaced(_lab(title.upper(), 'pwHeadT')))
        h.addStretch()
        if right is not None:
            h.addWidget(right, 0, Qt.AlignmentFlag.AlignVCenter)
        v.addWidget(head)
        return f, v

    def _kv(self, left, right, alt, pending=False):
        """24px key/value row; `right` = text or a widget. Zebra on even rows (alt)."""
        row = QFrame()
        row.setObjectName('pwRowAlt' if alt else 'pwRow')
        row.setFixedHeight(24)
        h = QHBoxLayout(row)
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(8)
        h.addWidget(_lab(left, 'pwKvL'))
        h.addStretch()
        if isinstance(right, QWidget):
            h.addWidget(right, 0, Qt.AlignmentFlag.AlignVCenter)
        else:
            h.addWidget(_lab(right, 'pwKvR', Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
        if pending and not self._show_pending():
            row.setVisible(False)
        return row

    # hero ---------------------------------------------------------------------------------------
    def _badge(self, pos):
        from gui.main_window import _POS_BADGE_COLORS
        bg = _POS_BADGE_COLORS.get(pos, ('#2A2D35', '#FFFFFF'))[0]
        lbl = _lab(pos, 'pwBadge', Qt.AlignmentFlag.AlignCenter, 16)
        lbl.setMinimumWidth(28)
        lbl.setStyleSheet(f'QLabel#pwBadge {{ background:{bg}; padding:0 5px; }}')
        return lbl

    def _hero(self):
        from gui import main_window as mw
        p = self._person
        pos_list = p.get('positions') or [1] * 15
        self._ratings = ratings = dict(zip(POS_ORDER, pos_list))
        pos = mw._primary_pos(pos_list) if p.get('positions') else '?'
        age = person_age(p)
        nation = mw.NATIONS.get(p.get('nation'), f"n={p.get('nation')}")
        ca, pa = p.get('ca'), p.get('pa')
        dev = mw._progress_rate(p)
        self._is_gk = pos == 'GK'
        b = self._save_data.get('b') if self._save_data else None
        from fm_editor.patch import is_hgc
        self._hgp = bool(p.get('hgp', False))
        self._hgc = is_hgc(b, p, self._club_entity_id) if (b is not None and self._club_entity_id) else None

        hero = QFrame()
        hero.setObjectName('pwPanel')
        hero.setFixedHeight(152)
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(16, 16, 16, 16)
        hl.setSpacing(24)

        # identity
        idl = QHBoxLayout()
        idl.setSpacing(14)
        av = QLabel()
        av.setObjectName('pwAvatar')
        av.setFixedSize(64, 64)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setPixmap(self._svg_pixmap(_PERSON_SVG, 40))
        idl.addWidget(av, 0, Qt.AlignmentFlag.AlignTop)
        txt = QVBoxLayout()
        txt.setSpacing(0)
        name = _lab(p['name'], 'pwName')
        name.setWordWrap(True)
        txt.addWidget(name)
        club = self._club_name()
        born = self._born_text()
        sub = ' · '.join(s for s in (POS_NAME.get(pos, pos), nation, f'{age} years ({born})', club) if s)
        s1 = _lab(sub, 'pwSub')
        s1.setWordWrap(True)
        s1.setContentsMargins(0, 4, 0, 0)
        txt.addWidget(s1)
        self._hw_lbl = self._height_weight_line()
        txt.addWidget(self._hw_lbl)
        chips = _Flow(hspace=6, vspace=6)
        for lab, on in (('HGP', self._hgp), ('HGC', self._hgc)):
            if on:
                c = _lab(lab, 'pwPillOn', Qt.AlignmentFlag.AlignCenter, 20)
            elif on is False:
                c = _lab(lab, 'pwPill', Qt.AlignmentFlag.AlignCenter, 20)
            else:
                c = _lab(lab + '?', 'pwPillUnk', Qt.AlignmentFlag.AlignCenter, 20)
                c.setToolTip('Homegrown status at this club could not be determined')
            chips.addWidget(c)
        if p.get('injured'):
            d = p.get('injury_days', 0)
            chips.addWidget(_lab(f'Injured · {d} days' if d else 'Injured', 'pwChipInj', Qt.AlignmentFlag.AlignCenter, 20))
        else:
            chips.addWidget(_lab('Fit', 'pwChipOk', Qt.AlignmentFlag.AlignCenter, 20))
        if dev is not None:
            dv = _lab(f'Dev Rate <b style="color:{TIER_HEX[tier(dev)]}; margin-left:6px">{dev}</b>', 'pwChipDev',
                      Qt.AlignmentFlag.AlignCenter, 20)
            dv.setTextFormat(Qt.TextFormat.RichText)
            chips.addWidget(dv)
        chip_host = QVBoxLayout()
        chip_host.setContentsMargins(0, 10, 0, 0)
        chip_host.addLayout(chips)
        txt.addLayout(chip_host)
        txt.addStretch()
        idl.addLayout(txt, 1)
        hl.addLayout(idl, 1)

        # CA / PA
        big = QHBoxLayout()
        big.setSpacing(20)
        for lab, val, color in (('CA · Current', ca, COLORS['accent_hover']), ('PA · Potential', pa, C_POT)):
            col = QVBoxLayout()
            col.setSpacing(0)
            col.addWidget(_spaced(_lab(lab.upper(), 'pwBigLab')))
            num = _lab(str(val) if val is not None else '?', 'pwBigNum')
            num.setStyleSheet(f'QLabel#pwBigNum {{ color:{color}; }}')
            num.setContentsMargins(0, 2, 0, 6)
            col.addWidget(num)
            col.addWidget(_Bar((val or 0) / 200, color))
            col.addStretch()
            big.addLayout(col, 1)
        bw = QWidget()
        bw.setFixedWidth(208)
        bw.setLayout(big)
        big.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(bw)

        # actions
        hl.addWidget(self._actions())
        return hero

    @staticmethod
    def _svg_pixmap(svg, size):
        from PyQt6.QtSvg import QSvgRenderer
        r = QSvgRenderer(svg.encode())
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        pa = QPainter(px)
        r.render(pa)
        pa.end()
        return px

    def _born_text(self):
        p = self._person
        by, bd = p.get('birth_year'), p.get('birth_day')
        if by is None:
            return 'born ?'
        if bd:
            from datetime import date, timedelta
            d = date(by, 1, 1) + timedelta(days=bd - 1)
            return f'born {d.day} {calendar.month_abbr[d.month]} {d.year}'
        return f'born {by}'

    def _height_weight_line(self):
        d = self._data
        h, w = d.get('height_cm'), d.get('weight_kg')
        host = QWidget()
        hb = QHBoxLayout(host)
        hb.setContentsMargins(0, 2, 0, 0)
        hb.setSpacing(6)
        if h is None or w is None:
            hb.addWidget(_lab('Height / weight', 'pwSub'))
            hb.addWidget(self._pend_chip(), 0, Qt.AlignmentFlag.AlignVCenter)
            if not self._show_pending():
                host.setVisible(False)
        else:
            hb.addWidget(_lab(f'{h} cm · {w} kg', 'pwSub'))
        hb.addStretch()
        return host

    def _actions(self):
        w = QWidget()
        w.setFixedWidth(196)
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        v.addStretch()
        if self._shortlisted:
            sl = QPushButton('✓ On Player Shortlist')
            sl.setObjectName('pwShortOn')
            sl.setEnabled(False)
        else:
            sl = QPushButton('Add to Shortlist')
            sl.setObjectName('pwPrimary')
            sl.setCursor(Qt.CursorShape.PointingHandCursor)
            sl.clicked.connect(lambda checked=False: self._do_add_shortlist())
        sl.setFixedHeight(32)
        v.addWidget(sl)
        two = QHBoxLayout()
        two.setSpacing(8)
        tips = 'Open the player from Squads to patch homegrown status.'
        for mode, lab, is_set, ok in (('hgp', 'HGP', self._hgp, True), ('hgc', 'HGC', self._hgc, self._hgc is not None)):
            btn = QPushButton(f'{lab} set' if is_set else f'Make {lab}')
            btn.setObjectName('pwGhost')
            btn.setFixedHeight(32)
            btn.setEnabled(bool(ok) and not is_set and self._can_patch)
            if not is_set and not self._can_patch:
                btn.setToolTip(tips)
            elif not is_set and not ok:
                btn.setToolTip('Club unknown for this player.')
            btn.clicked.connect(lambda checked=False, m=mode: self._emit_patch(m))
            two.addWidget(btn, 1)
        v.addLayout(two)
        v.addStretch()
        return w

    # attribute grid -----------------------------------------------------------------------------
    def _attr_panel(self):
        right = QWidget()
        rh = QHBoxLayout(right)
        rh.setContentsMargins(0, 0, 0, 0)
        rh.setSpacing(8)
        self._note = _lab('', 'pwNote')
        rh.addWidget(self._note)
        seg = QFrame()
        seg.setObjectName('pwSeg')
        sl = QHBoxLayout(seg)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)
        self._seg_cur = QPushButton('Current')
        self._seg_cur.setObjectName('pwSegL')
        self._seg_pot = QPushButton('At potential')
        self._seg_pot.setObjectName('pwSegR')
        grp = QButtonGroup(self)
        grp.setExclusive(True)
        bold = QFont()
        bold.setPixelSize(11)
        bold.setBold(True)
        fm = QFontMetrics(bold)
        for b in (self._seg_cur, self._seg_pot):
            b.setCheckable(True)
            b.setFixedSize(fm.horizontalAdvance(b.text()) + 28, 24)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            grp.addButton(b)
            sl.addWidget(b)
        self._seg_cur.setChecked(True)
        self._seg_group = grp
        p = self._person
        enabled, tip = _pot.availability(p.get('ca'), p.get('pa'), person_age(p))
        self._pot_note = tip if enabled else ''
        self._seg_pot.setEnabled(enabled)
        if tip:
            self._seg_pot.setToolTip(tip)
        if not enabled:
            seg.setToolTip(tip)
        self._seg_cur.clicked.connect(lambda checked=False: self._set_pot(False))
        self._seg_pot.clicked.connect(lambda checked=False: self._set_pot(True))
        rh.addWidget(seg)
        panel, v = self._panel('Attributes', right)
        self._attr_v = v
        self._grid = self._make_grid()
        v.addWidget(self._grid)
        self._cap = _lab(CAPTION, 'pwNote')
        self._cap.setContentsMargins(12, 0, 12, 10)
        self._cap.setWordWrap(True)
        self._cap.setVisible(False)
        v.addWidget(self._cap)
        v.addStretch()
        return panel

    def _set_pot(self, on):
        if on == self._pot_on:
            return
        self._pot_on = on
        old = self._grid
        self._grid = self._make_grid()
        self._attr_v.replaceWidget(old, self._grid)
        old.hide()
        old.deleteLater()
        self._cap.setVisible(on)
        note = ''
        if on:
            note = self._pot_note
            pr = self._projection()
            if pr.saturated:
                note = (note + ' ' if note else '') + f'Reaches about CA {pr.reaches(self._person["ca"])}.'
        self._note.setText(note)

    def _projection(self):
        if self._proj is None:
            p = self._person
            self._proj = _pot.project_attrs(p['raw_attrs'], p['ca'], p['pa'], person_age(p), p['positions'])
        return self._proj

    def _make_grid(self):
        raw = self._person.get('raw_attrs') or []
        proj = self._projection().proj if (self._pot_on and raw) else None
        host = QWidget()
        h = QHBoxLayout(host)
        h.setContentsMargins(4, 2, 4, 10)
        h.setSpacing(8)
        if self._is_gk:
            cols = [('Goalkeeping', GKA, ('Footedness', FOOT)), ('Mental', MENT, None),
                    ('Physical', PHYS, ('Hidden', HIDD)), ('Technical', TECH, None)]
        else:
            cols = [('Technical', TECH, None), ('Mental', MENT, None), ('Physical', PHYS, ('Footedness', FOOT)),
                    ('Hidden', HIDD, None)]
        for title, attrs, extra in cols:
            c = QVBoxLayout()
            c.setSpacing(0)
            c.setContentsMargins(0, 0, 0, 0)
            self._tile_group(c, title, attrs, raw, proj)
            if extra:
                c.addSpacing(10)
                self._tile_group(c, extra[0], extra[1], raw, proj)
            c.addStretch()
            h.addLayout(c, 1)
        return host

    def _tile_group(self, layout, title, attrs, raw, proj):
        hd = _spaced(_lab(title.upper(), 'pwColHead', h=24))
        hd.setContentsMargins(4, 0, 4, 0)
        layout.addWidget(hd)
        for name, idx in attrs:
            if idx >= len(raw):
                continue
            cur = self._disp(raw[idx])
            new = _pot.display_value(proj[idx]) if proj is not None else cur
            row = QWidget()
            row.setFixedHeight(26)
            r = QHBoxLayout(row)
            r.setContentsMargins(4, 0, 4, 0)
            r.setSpacing(6)
            r.addWidget(_ElideLabel(name, 'pwAttrName'), 1)
            r.addWidget(self._tile(cur, new, idx in LOWER_BETTER))
            layout.addWidget(row)

    def _tile(self, cur, new, lower_better):
        # "At potential" replaces the current value with the projected one (toggle back to compare)
        v = new if self._pot_on else cur
        t = tier(21 - v if lower_better else v)
        lbl = QLabel(str(v))
        lbl.setFixedHeight(20)
        lbl.setMinimumWidth(28)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f'QLabel {{ background:{_rgba(t)}; color:{TIER_HEX[t]}; border-radius:3px; '
                          f'font-size:12px; font-weight:bold; padding:0 6px; }}')
        return lbl

    # rail (personality + traits; the contract panel lives on the Contract tab) ---------------------------------------------------------------------------------------
    def _rail(self):
        w = QWidget()
        w.setFixedWidth(216)
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(12)
        v.addWidget(self._personality_panel())
        tp = self._traits_panel()
        if tp is not None:
            v.addWidget(tp)
        v.addStretch()
        return w

    def _contract_panel(self):
        d = self._data
        panel, v = self._panel('Contract')
        until = self._contract_until()
        rows = [('Until', until if until else _lab('-', 'pwKvR'), False)]
        for label, key in (('Wage', 'wage'), ('Value', 'value')):
            val = d.get(key)
            rows.append((label, val if val else self._pend_chip(), not val))
        for i, (label, right, pend) in enumerate(rows):
            v.addWidget(self._kv(label, right, i % 2 == 1, pending=pend))
        v.addSpacing(10)
        return panel

    def _contract_until(self):
        ce = self._person.get('contract_end')
        try:
            y, m = ce.split('-')[:2]
            return f'{calendar.month_abbr[int(m)]} {int(y)}'
        except (AttributeError, ValueError, IndexError):
            return ''

    def _personality_panel(self):
        panel, v = self._panel('Personality')
        pers = self._person.get('personality') or []
        for name, val in zip(PERS, pers):
            row = QWidget()
            row.setFixedHeight(26)
            h = QHBoxLayout(row)
            h.setContentsMargins(12, 0, 12, 0)
            h.setSpacing(8)
            n = _lab(name, 'pwAttrName')
            n.setFixedWidth(96)
            h.addWidget(n)
            h.addWidget(_Bar(val / 20, TIER_HEX[tier(val)]), 1)
            vl = _lab(str(val), 'pwKvR', Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            vl.setFixedWidth(22)
            vl.setStyleSheet(f'QLabel#pwKvR {{ color:{TIER_HEX[tier(val)]}; font-weight:bold; }}')
            h.addWidget(vl)
            v.addWidget(row)
        v.addSpacing(8)
        return panel

    def _traits_panel(self):
        """Preferred moves, one wrapped row per trait. 'Trait #n' = bit whose name is not confirmed yet
        (muted + tooltip); a player without traits gets a quiet 'None' row."""
        traits = self._data.get('traits')
        if traits is None:                                  # unknown -> PENDING (only if the extra data says so)
            if not self._show_pending():
                return None
            panel, v = self._panel('Player traits', self._pend_chip())
            return panel
        panel, v = self._panel('Player traits')
        for i, t in enumerate(traits or ['None']):
            row = QFrame()
            row.setObjectName('pwRowAlt' if i % 2 else 'pwRow')
            h = QHBoxLayout(row)
            h.setContentsMargins(12, 4, 12, 4)
            lbl = _lab(t, 'pwKvL' if (t.startswith('Trait #') or not traits) else 'pwTrait')
            lbl.setWordWrap(True)
            if t.startswith('Trait #'):
                lbl.setToolTip('Name not confirmed yet')
            h.addWidget(lbl)
            v.addWidget(row)
        v.addSpacing(8)
        return panel

    # actions ------------------------------------------------------------------------------------
    def _emit_patch(self, mode):
        self._patch_mode = mode
        self.accept()

    def _do_add_shortlist(self):
        self._shortlist_added = True
        self.accept()
