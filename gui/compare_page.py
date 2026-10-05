"""Compare Players page (master visual: mockups/compare-players.html). A QScrollArea page of the main window:
selector bar (two PlayerCombo, swap, Add both to Shortlist) | header (two player panels + VS) | variant A: left panel 'Compare'
(Current | Full Potential, radar axes Overview | Detailed, overlaid radar, difference bars) + right column 'Attributes' (who is ahead
per attribute, tally) + 'Key facts'. No player yet / one player = the empty state with the recently viewed players.
Identity colours: A sky blue #52B0FF (circle, solid), B orchid #D77CFF (diamond, dashed). Keepers are only compared with keepers.
The page scrolls (the main window is only ~570 px tall); below 1100 px the header is compact, below 900 px the main area is one column.

Pure helpers (tested without Qt widgets): CompareSide, good(), attrs_won(), key_facts()."""
import calendar

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import (QBoxLayout, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QToolTip, QVBoxLayout,
                             QWidget)

from fm_editor import potential as _pot
from fm_editor import settings as _settings
from fm_editor.abilitystars import ability_stars
from fm_editor.agecalc import get_ref, person_age
from fm_editor.nations import nation_flag
from fm_editor.player_search import is_keeper
from fm_editor.radar_axes import axis_table, axis_values
from gui.faces import get_service as _faces_service
from gui.player_picker import PlayerCombo, PlayerPicker, fill_rows, make_row_list, person_pixmap, person_pos
from gui.player_window import (GKA, HIDD, LOWER_BETTER, MENT, NOT_FOR_SALE, PHYS, POS_CODE, TECH, TIER_HEX, TIER_RGB, TILE_ALPHA,
                               _Bar, _ElideLabel, fmt_value, fmt_wage, player_extra_data, tier)
from gui.pw_widgets import A_RGB, B_RGB, CompareRadar
from gui.stars import star_row_pixmap
from gui.theme import COLORS

A_HEX, B_HEX = '#52B0FF', '#D77CFF'
DF_CAP = 6          # table diff bar: a difference of 6 or more fills the whole half (ONE place to change)
EDGE_FULL = 4       # 'Difference by group': a mean difference of 4 fills the whole half
SEC = QColor(COLORS['text_secondary'])
# (key, title, attribute table) in table order; Footedness is its own pair of rows
GROUPS = {'tech': ('Technical', TECH), 'ment': ('Mental', MENT), 'phys': ('Physical', PHYS), 'hid': ('Hidden', HIDD),
          'gk': ('Goalkeeping', GKA)}
LEFT_FOOT, RIGHT_FOOT = 24, 25     # raw_attrs indices
COLUMNS_OUT = (('tech', 'foot'), ('ment',), ('phys', 'hid'))
COLUMNS_GK = (('gk', 'foot'), ('ment',), ('phys', 'hid'))
COUNTED_OUT, COUNTED_GK = ('tech', 'ment', 'phys', 'hid'), ('gk', 'ment', 'phys', 'hid')   # attributes won: no Footedness; a keeper's outfield Technical is hidden
FACTS_STRETCH = (80, 95, 130, 90, 100, 80)       # mockup .facts fractions .8 .95 1.3 .9 1 .8
DENSITY = {   # level -> (avatar w, h, box w, name px, star px, pad, gap, box title px, title spacing)
    0: (54, 64, 100, 20, 13, 14, 12, 10, 0.8), 1: (46, 56, 92, 17, 11, 10, 8, 10, 0.4), 2: (40, 48, 76, 15, 9, 10, 8, 9, 0.0)}


def good(v, lower):
    """Rank value: lower-is-better attributes (Eccentricity, Dirtiness, Injury Prone) compare on 21 - v."""
    return 21 - v if lower else v


def short_name(p):
    return p['name'].split()[-1] if p.get('name') else '?'


class CompareSide:
    """One player's compare data: attribute values for Current / Full Potential by group (same tables as the player window)."""

    def __init__(self, person, save_data=None):
        self.person, self.sd = person, save_data or {}
        self.gk = is_keeper(person)
        self.raw = person.get('raw_attrs') or []
        self._proj = None
        self.extra = player_extra_data(person, self.sd)

    def _value(self, idx, pot):
        if pot:
            if self._proj is None:
                p = self.person
                self._proj = _pot.project_attrs(self.raw, p.get('ca'), p.get('pa'), person_age(p), p.get('positions') or [1] * 15)
            return _pot.display_value(self._proj.proj[idx])
        return _pot.display_value(self.raw[idx] / 5)

    def rows(self, key, pot=False):
        """[(name, value 1-20, lower_is_better)] of one group; attributes missing from the save are skipped."""
        if key == 'foot':
            return [(n, _pot.display_value(self.raw[i] / 5), False) for n, i in (('Left Foot', LEFT_FOOT), ('Right Foot', RIGHT_FOOT))
                    if i < len(self.raw)]
        return [(n, self._value(i, pot), i in LOWER_BETTER) for n, i in GROUPS[key][1] if i < len(self.raw)]

    def values(self, pot=False):
        """{attribute name: value} of every rated attribute (radar input, Footedness excluded)."""
        return {n: v for k in GROUPS for n, v, _l in self.rows(k, pot)}


def attrs_won(a, b, pot=False):
    """(a wins, b wins, level): every attribute counts equally; Footedness is not counted; a keeper's outfield Technical group is
    not listed or counted. Lower-is-better attributes compare on 21 - v. Both sides must be the same kind (outfield / keeper)."""
    wa = wb = lv = 0
    for k in (COUNTED_GK if a.gk else COUNTED_OUT):
        rb = {n: (v, lo) for n, v, lo in b.rows(k, pot)}
        for n, v, lo in a.rows(k, pot):
            if n not in rb:
                continue
            d = good(v, lo) - good(*rb[n])
            wa, wb, lv = wa + (d > 0), wb + (d < 0), lv + (d == 0)
    return wa, wb, lv


def _contract_years(p):
    try:
        y, m = p['contract_end'].split('-')[:2]
        ref = get_ref()
        return (int(y) - ref.year) + (int(m) - ref.month) / 12
    except (AttributeError, KeyError, ValueError, TypeError):
        return None


def _contract_text(p):
    try:
        y, m = p['contract_end'].split('-')[:2]
        return f'{calendar.month_abbr[int(m)]} {int(y)}'
    except (AttributeError, KeyError, ValueError, IndexError):
        return '-'


def key_facts(a, b):
    """[(title, a text, b text, difference line, tooltip)] for the 'Key facts' strip (mockup factsAB)."""
    pa, pb = a.person, b.person

    def val(p):
        v = p.get('value_est')
        return 'Not for sale' if v == NOT_FOR_SALE else (fmt_value(v) or '-')
    va, vb = pa.get('value_est'), pb.get('value_est')
    if va and vb and NOT_FOR_SALE not in (va, vb):
        dv = abs(va - vb)
        vdiff = f'{fmt_value(dv)} apart' if dv else 'equal'
    else:
        vdiff = ''
    ages = (person_age(pa), person_age(pb))
    da = abs(ages[0] - ages[1])
    ca, cb = _contract_years(pa), _contract_years(pb)
    dc = abs(ca - cb) if ca is not None and cb is not None else None
    wage = lambda s: (s.extra.get('wage') or '-').replace(' p/w', '')       # noqa: E731
    hw = lambda s: ' · '.join(str(x) if x else '-' for x in (s.person.get('height_cm'), s.person.get('weight_kg')))   # noqa: E731
    ta, tb = a.extra.get('traits'), b.extra.get('traits')
    na, nb = (len(ta) if ta is not None else None), (len(tb) if tb is not None else None)
    return [
        ('Age', str(ages[0]), str(ages[1]), (f'{da} yr{"s" if da > 1 else ""} apart' if da else 'same age'), ''),
        ('Contract', _contract_text(pa), _contract_text(pb), '' if dc is None else (f'{dc:.1f} yrs apart' if dc >= .05 else 'same length'), ''),
        ('Transfer value', val(pa), val(pb), vdiff, 'Market value as stored in the save; a value of exactly £300M is the game\'s '
         '"Not for sale" marker. The asking price is not in the save.'),
        ('Wage p/w', wage(a), wage(b), '', ''),
        ('cm / kg', hw(a), hw(b), '', f'Height / weight: {pa["name"]} {hw(a)}; {pb["name"]} {hw(b)}'),
        ('Traits', '-' if na is None else str(na), '-' if nb is None else str(nb), 'same count' if na is not None and na == nb else '', ''),
    ]


# -- small widgets ------------------------------------------------------------------------------------------------
class DiffCell(QWidget):
    """34 x 20 split bar between the two value tiles (mockup .df): two 14 px halves (x 2..16 | 18..32) around a 2 px centre tick,
    6 px high, r3. The winner's half fills from the centre outwards in its identity colour, length 3 + (min(|d|, DF_CAP) - 1) /
    (DF_CAP - 1) * 11 px; level = the track only (fainter). d = good(A) - good(B)."""

    def __init__(self, d, tip, parent=None):
        super().__init__(parent)
        self.d = d
        self.setFixedSize(34, 20)
        self.setToolTip(tip)
        self.setAccessibleName(tip)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        eq = self.d == 0
        track = QColor(139, 150, 168, 20 if eq else 46)
        p.setPen(Qt.PenStyle.NoPen)
        for x0, left in ((2, True), (18, False)):
            p.save()
            p.setClipRect(QRectF(x0, 7, 14, 6))
            p.setBrush(track)
            p.drawRoundedRect(QRectF(x0 - (0 if left else 4), 7, 18, 6), 3, 3)
            p.restore()
        if not eq:
            w = 3 + (min(abs(self.d), DF_CAP) - 1) / (DF_CAP - 1) * 11
            a_wins = self.d > 0
            p.save()
            p.setBrush(QColor(*(A_RGB if a_wins else B_RGB)))
            if a_wins:      # fills leftwards from the centre, outer (left) end rounded
                p.setClipRect(QRectF(16 - w, 7, w, 6))
                p.drawRoundedRect(QRectF(16 - w, 7, w + 4, 6), 3, 3)
            else:           # fills rightwards, outer (right) end rounded
                p.setClipRect(QRectF(18, 7, w, 6))
                p.drawRoundedRect(QRectF(14, 7, w + 4, 6), 3, 3)
            p.restore()
        p.setBrush(QColor(82, 91, 104) if eq else SEC)
        p.drawRoundedRect(QRectF(16, 5, 2, 10), 1, 1)


class EdgeRow(QWidget):
    """'Difference by group / axis' row (mockup .dvr, 20 high): label 78 | track 8 px split at the centre (gap 2) | value 30."""

    def __init__(self, name, a, b, tip, parent=None):
        super().__init__(parent)
        self.name, self.d = name, a - b
        self.setFixedHeight(20)
        self.setToolTip(tip)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        f = QFont()
        f.setPixelSize(12)
        p.setFont(f)
        p.setPen(SEC)
        p.drawText(QRectF(0, 0, 78, 20), int(Qt.AlignmentFlag.AlignVCenter), self.name)
        tx0, tx1 = 86, w - 38
        half = (tx1 - tx0 - 2) / 2
        bg = QColor(COLORS['border'])
        p.fillRect(QRectF(tx0, 6, half, 8), bg)
        p.fillRect(QRectF(tx0 + half + 2, 6, half, 8), bg)
        ad = abs(self.d)
        if ad >= .05:
            fl = min(1.0, ad / EDGE_FULL) * half
            if self.d > 0:
                p.fillRect(QRectF(tx0 + half - fl, 6, fl, 8), QColor(*A_RGB))
            else:
                p.fillRect(QRectF(tx0 + half + 2, 6, fl, 8), QColor(*B_RGB))
        sf = QFont()
        sf.setPixelSize(11)
        sf.setBold(True)
        p.setFont(sf)
        p.setPen(QColor(*A_RGB) if self.d > .05 else QColor(*B_RGB) if self.d < -.05 else SEC)
        p.drawText(QRectF(w - 30, 0, 30, 20), int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight), '=' if ad < .05 else f'{ad:.1f}')


class _Ghost(QWidget):
    """Empty-state radar: two faint dashed polygons (mockup svg 180 x 168)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 168)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        poly = lambda pts: QPolygonF([QPointF(x, y) for x, y in pts])      # noqa: E731
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 26), 1))
        p.drawPolygon(poly([(90, 14), (154, 51), (154, 117), (90, 154), (26, 117), (26, 51)]))
        p.drawPolygon(poly([(90, 49), (122, 67.5), (122, 100.5), (90, 119), (58, 100.5), (58, 67.5)]))
        p.setPen(QPen(QColor(*A_RGB, 89), 1.5))
        p.setBrush(QColor(*A_RGB, 26))
        p.drawPolygon(poly([(90, 30), (138, 60), (140, 108), (90, 138), (40, 104), (44, 62)]))
        pen = QPen(QColor(*B_RGB, 89), 1.5)
        pen.setDashPattern([5 / 1.5, 3 / 1.5])
        p.setPen(pen)
        p.setBrush(QColor(*B_RGB, 20))
        p.drawPolygon(poly([(90, 24), (148, 56), (132, 112), (90, 144), (48, 112), (36, 60)]))


def _qss():
    c = COLORS
    return f"""
QWidget#comparePage QWidget {{ background:transparent; }}
QScrollArea#comparePage {{ background:{c['window_bg']}; border:none; }}
QWidget#cmpBody {{ background:{c['window_bg']}; }}
QWidget#comparePage QScrollBar:vertical {{ background:{c['window_bg']}; width:6px; margin:0; border:none; }}
QWidget#comparePage QScrollBar::handle:vertical {{ background:{c['border_bright']}; border-radius:3px; min-height:20px; }}
QWidget#comparePage QScrollBar::add-line:vertical, QWidget#comparePage QScrollBar::sub-line:vertical {{ height:0; }}
QWidget#comparePage QLabel {{ color:{c['text_primary']}; }}
QWidget#comparePage QFrame#cmpPanel {{ background:{c['surface']}; border:1px solid {c['border']}; border-radius:3px; }}
QWidget#comparePage QFrame#cmpHp {{ background:{c['surface']}; border:1px solid {c['border']}; border-top:3px solid {A_HEX}; border-radius:3px; }}
QWidget#comparePage QFrame#cmpHp[side="b"] {{ border-top:3px solid {B_HEX}; }}
QWidget#comparePage QFrame#cmpHp[empty="true"] {{ background:transparent; border:1px dashed {c['border_bright']}; border-top:3px solid {A_HEX}; }}
QWidget#comparePage QFrame#cmpHp[empty="true"][side="b"] {{ border-top:3px solid {B_HEX}; }}
QWidget#comparePage QFrame#cmpCab {{ background:{c['window_bg']}; border:1px solid {c['border']}; border-radius:3px; }}
QWidget#comparePage QFrame#cmpEmpty {{ background:{c['surface']}; border:1px solid {c['border']}; border-radius:3px; }}
QWidget#comparePage QLabel#cmpHeadT {{ color:{c['text_secondary']}; font-size:11px; font-weight:bold; }}
QWidget#comparePage QLabel#cmpCabT {{ color:{c['text_secondary']}; font-size:10px; font-weight:bold; }}
QWidget#comparePage QLabel#cmpName {{ font-weight:bold; }}
QWidget#comparePage QLabel#cmpSub {{ color:{c['text_secondary']}; }}
QWidget#comparePage QLabel#cmpVs {{ color:{c['text_secondary']}; font-size:11px; font-weight:bold; }}
QWidget#comparePage QLabel#cmpNote {{ color:{c['text_secondary']}; font-size:11px; }}
QWidget#comparePage QLabel#cmpAttrName {{ color:{c['text_secondary']}; }}
QWidget#comparePage QLabel#cmpEh {{ color:{c['text_secondary']}; font-size:10px; font-weight:bold; }}
QWidget#comparePage QLabel#cmpFactT {{ color:{c['text_secondary']}; font-size:10px; font-weight:bold; }}
QWidget#comparePage QLabel#cmpFactV {{ font-weight:600; }}
QWidget#comparePage QLabel#cmpFactD {{ color:{c['text_secondary']}; font-size:11px; }}
QWidget#comparePage QLabel#cmpEmptyT {{ font-size:16px; font-weight:bold; }}
QWidget#comparePage QLabel#cmpEmptyS {{ color:{c['text_secondary']}; }}
QWidget#comparePage QLabel#cmpBadge {{ color:#FFFFFF; font-size:10px; font-weight:bold; border-radius:2px; padding:0 5px; }}
QWidget#comparePage QFrame#cmpSeg {{ background:{c['window_bg']}; border:1px solid {c['border_bright']}; border-radius:3px; }}
QWidget#comparePage QPushButton#cmpSegBtn {{ background:{c['window_bg']}; color:{c['text_secondary']}; border:none; font-size:11px; font-weight:bold; padding:0 12px; }}
QWidget#comparePage QPushButton#cmpSegBtn:checked {{ background:{c['accent']}; color:#FFFFFF; }}
QWidget#comparePage QPushButton#cmpSegBtn:hover:!checked {{ color:#FFFFFF; }}
QWidget#comparePage QPushButton#cmpGhost {{ background:{c['surface']}; color:#FFFFFF; border:1px solid {c['border_bright']}; border-radius:3px;
    font-size:12px; font-weight:bold; padding:0 16px; }}
QWidget#comparePage QPushButton#cmpGhost:hover {{ background:{c['elevated']}; }}
QWidget#comparePage QPushButton#cmpGhost:disabled {{ background:{c['elevated']}; color:{c['text_dim']}; border:1px solid {c['border']}; }}
QWidget#comparePage QPushButton#cmpSwap {{ background:{c['surface']}; color:#FFFFFF; border:1px solid {c['border_bright']}; border-radius:3px; font-size:16px; }}
QWidget#comparePage QPushButton#cmpSwap:hover {{ background:{c['elevated']}; }}
QWidget#comparePage QPushButton#cmpSwap:disabled {{ background:{c['elevated']}; color:{c['text_dim']}; border:1px solid {c['border']}; }}
QWidget#comparePage QFrame#cmpHair {{ background:{c['border']}; border:none; }}
"""


def _lbl(text, name, h=None, align=None):
    lb = QLabel(text)
    lb.setObjectName(name)
    if h:
        lb.setFixedHeight(h)
    if align is not None:
        lb.setAlignment(align)
    return lb


def _spaced(lb, px=0.88):
    f = lb.font()
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, px)
    lb.setFont(f)
    return lb


def _tile(v, lower):
    t = tier(good(v, lower))
    r, g, b = TIER_RGB[t]
    lb = QLabel(str(v))
    lb.setFixedSize(26, 20)
    lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lb.setStyleSheet(f'QLabel {{ background:rgba({r},{g},{b},{TILE_ALPHA}); color:{TIER_HEX[t]}; border-radius:3px; font-size:12px; font-weight:bold; }}')
    return lb


def _marker(slot, size=8):
    """Identity marker: A circle, B diamond (QLabel painted via a rich-text glyph keeps the layout simple)."""
    lb = QLabel('●' if slot == 'a' else '◆')
    lb.setStyleSheet(f'QLabel {{ color:{A_HEX if slot == "a" else B_HEX}; font-size:{size + 3}px; }}')
    lb.setFixedWidth(size + 4)
    return lb


def _panel(title, right=None):
    f = QFrame()
    f.setObjectName('cmpPanel')
    v = QVBoxLayout(f)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(0)
    head = QWidget()
    head.setFixedHeight(36)
    h = QHBoxLayout(head)
    h.setContentsMargins(12, 0, 12, 0)
    h.setSpacing(8)
    h.addWidget(_spaced(_lbl(title.upper(), 'cmpHeadT')))
    h.addStretch(1)
    if right is not None:
        h.addWidget(right, 0, Qt.AlignmentFlag.AlignVCenter)
    v.addWidget(head)
    return f, v


def _seg(items, current, on_pick, tip=''):
    """Segmented control h24: items [(key, label)]; clicking a segment calls on_pick(key)."""
    seg = QFrame()
    seg.setObjectName('cmpSeg')
    h = QHBoxLayout(seg)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(0)
    bold = QFont()
    bold.setPixelSize(11)
    bold.setBold(True)
    fm = QFontMetricsF(bold)
    for key, label in items:
        b = QPushButton(label)
        b.setObjectName('cmpSegBtn')
        b.setCheckable(True)
        b.setChecked(key == current)
        b.setFixedSize(int(fm.horizontalAdvance(label)) + 26, 24)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        b.clicked.connect(lambda checked, k=key: on_pick(k))
        h.addWidget(b)
    if tip:
        seg.setToolTip(tip)
    return seg


class ComparePage(QScrollArea):
    """The page. `set_context(PickerContext)` after a save is loaded; `set_players(a, b)` / `players()`; signals for the host."""
    playersChanged = pyqtSignal()
    shortlistBoth = pyqtSignal(dict, dict)
    message = pyqtSignal(str)
    playerViewed = pyqtSignal(dict)   # a player was picked on this page: the host records it in the recents

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('comparePage')
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(_qss())
        f = self.font()
        f.setPixelSize(12)
        self.setFont(f)
        self._ctx = None
        self._a = self._b = None
        self._sides = {}
        self._pot = False
        self._mode = 'overview'
        self._density, self._narrow = 0, False
        self._picker = None
        self._active = None
        body = QWidget()
        body.setObjectName('cmpBody')
        self._outer = QVBoxLayout(body)
        self._outer.setContentsMargins(12, 12, 12, 12)
        self._outer.setSpacing(12)
        self.setWidget(body)
        # selector bar (persistent: the combos keep focus / text while the content below is rebuilt)
        bar = QHBoxLayout()
        bar.setSpacing(8)
        self._combo = {}
        self._swap = QPushButton('⇄')
        self._swap.setObjectName('cmpSwap')
        self._swap.setFixedSize(40, 40)
        self._swap.setToolTip('Swap sides: A becomes B and B becomes A')
        self._swap.setAccessibleName('Swap sides')
        self._swap.setCursor(Qt.CursorShape.PointingHandCursor)
        self._swap.clicked.connect(lambda checked=False: self.set_players(self._b, self._a))
        self._both = QPushButton('Add both to Shortlist')
        self._both.setObjectName('cmpGhost')
        self._both.setFixedHeight(32)
        self._both.setToolTip('Add both players to the Player Shortlist')
        self._both.setCursor(Qt.CursorShape.PointingHandCursor)
        self._both.clicked.connect(lambda checked=False: self.shortlistBoth.emit(self._a, self._b))
        self._pk = {}
        for slot, col in (('a', A_HEX), ('b', B_HEX)):
            cb = PlayerCombo(slot, col, self._picker_for)
            cb.personPicked.connect(lambda p, s=slot: self._chosen(s, p))
            cb.cleared.connect(lambda s=slot: self._clear(s))
            self._combo[slot] = cb
        bar.addWidget(self._combo['a'], 1)
        bar.addWidget(self._swap)
        bar.addWidget(self._combo['b'], 1)
        bar.addWidget(self._both)
        self._outer.addLayout(bar)
        self._dyn = None
        self._rebuild()

    # -- public ----------------------------------------------------------------------------------
    def set_context(self, ctx):
        """New save (or reload): picker context; clears the players (the host re-sets them from the snapshot)."""
        self._ctx = ctx
        if self._picker is not None:
            self._picker.close_popup()
            self._picker.deleteLater()
            self._picker = None
        self.set_players(None, None)

    def players(self):
        return self._a, self._b

    def on_shown(self):
        """Page navigated to: the empty state's RECENTLY VIEWED list was built when the page was last rebuilt, re-read it."""
        if self._a is None or self._b is None:
            self._rebuild()

    def mode(self):
        return self._mode

    def set_mode(self, mode):
        if mode in ('overview', 'detailed') and mode != self._mode:
            self._mode = mode
            self._rebuild()

    def refresh(self):
        """Settings > Ability display changed."""
        self._rebuild()

    def set_players(self, a, b):
        """Show these two players (None = empty slot). A keeper next to an outfield player clears B."""
        if a is not None and b is not None and is_keeper(a) != is_keeper(b):
            b = None
        self._a, self._b = a, b
        self._sides = {}
        self._rebuild()
        self.playersChanged.emit()

    def subtitle(self):
        if self._a and self._b:
            return f"{self._a['name']} vs {self._b['name']}"
        return 'Pick two players'

    # -- picking ---------------------------------------------------------------------------------
    def _picker_for(self, slot):
        """The shared popup (created on first use: it is a child of the top-level window); `slot` = the combo that opens it."""
        self._active = slot
        if self._picker is None:
            self._picker = PlayerPicker(self.window(), self._ctx)
            self._picker.picked.connect(self._on_picked)
            self._picker.closed.connect(self._on_closed)
        return self._picker

    def _sync_combos(self):
        for slot, cb in self._combo.items():
            other = self._b if slot == 'a' else self._a
            cb.exclude_ids = (other['id'],) if other else ()
            cb.keeper = is_keeper(other) if other else None
            cb.set_person(self._a if slot == 'a' else self._b)
            cb.setEnabled(self._ctx is not None)

    def _on_picked(self, person):
        if self._active:
            self._chosen(self._active, person)

    def _on_closed(self):
        for cb in self._combo.values():
            cb.picker_closed()

    def _chosen(self, slot, person):
        a, b = (person, self._b) if slot == 'a' else (self._a, person)
        if a is not None and b is not None and is_keeper(a) != is_keeper(b):
            self.message.emit(f"Player {'B' if slot == 'a' else 'A'} cleared: goalkeepers are only compared with goalkeepers.")
        self.playerViewed.emit(person)
        self.set_players(a, b)

    def _clear(self, slot):
        self.set_players(None if slot == 'a' else self._a, None if slot == 'b' else self._b)

    def _empty_pick(self, person):
        slot = 'a' if self._a is None else 'b'
        self._chosen(slot, person)

    # -- layout ----------------------------------------------------------------------------------
    def resizeEvent(self, e):
        super().resizeEvent(e)
        w = self.viewport().width()
        dens, narrow = (2 if w < 900 else 1 if w < 1100 else 0), w < 900
        if (dens, narrow) != (self._density, self._narrow):
            self._density, self._narrow = dens, narrow
            self._rebuild()

    def _side(self, p):
        s = self._sides.get(p['id'])
        if s is None:
            s = self._sides[p['id']] = CompareSide(p, (self._ctx.sd if self._ctx else {}))
        return s

    def _rebuild(self):
        self._sync_combos()
        both = self._a is not None and self._b is not None
        self._swap.setEnabled(both)
        self._both.setVisible(both)
        if self._dyn is not None:
            self._outer.removeWidget(self._dyn)
            self._dyn.hide()
            self._dyn.setParent(None)
            self._dyn.deleteLater()
        dyn = QWidget()
        v = QVBoxLayout(dyn)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(12)
        self._stars_on = _settings.ability_as_stars()
        if self._a or self._b:
            v.addWidget(self._header())
        v.addWidget(self._main_area() if both else self._empty_state(), 0)
        v.addStretch(1)
        self._dyn = dyn
        self._outer.addWidget(dyn, 1)

    # -- header ----------------------------------------------------------------------------------
    def _header(self):
        row = QWidget()
        row.setFixedHeight(80)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(self._player_panel(self._a, 'a'), 1)
        vs = _lbl('VS', 'cmpVs', align=Qt.AlignmentFlag.AlignCenter)
        vs.setFixedWidth(40)
        _spaced(vs, 0.88)
        h.addWidget(vs)
        h.addWidget(self._player_panel(self._b, 'b'), 1)
        return row

    def _player_panel(self, p, slot):
        fr = QFrame()
        fr.setObjectName('cmpHp')
        fr.setProperty('side', slot)
        fr.setProperty('empty', p is None)
        fr.setFixedHeight(80)
        h = QHBoxLayout(fr)
        if p is None:
            h.setAlignment(Qt.AlignmentFlag.AlignCenter)
            h.addWidget(_lbl(f"Player {slot.upper()}: not picked yet", 'cmpSub'))
            return fr
        aw, ah, bw, npx, spx, pad, gap, _tp, _ts = DENSITY[self._density]
        h.setContentsMargins(pad, 0, pad, 0)
        h.setSpacing(gap)
        dpr = self.devicePixelRatioF()
        av = QLabel()
        av.setFixedSize(aw, ah)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setPixmap(person_pixmap(p, aw, ah, dpr, radius=3))
        right = slot == 'b'
        col = QVBoxLayout()
        col.setSpacing(4)
        col.setContentsMargins(0, 0, 0, 0)
        col.addStretch(1)
        r1 = QHBoxLayout()
        r1.setSpacing(8)
        r1.setContentsMargins(0, 0, 0, 0)
        nm = _ElideLabel(p['name'], 'cmpName', natural=True)
        nm.setStyleSheet(f'QLabel#cmpName {{ font-size:{npx}px; font-weight:bold; }}')
        nm.setToolTip(p['name'])
        nm.setFixedHeight(24)
        pos = person_pos(p)
        items = [nm, self._badge(pos)] if pos else [nm]
        for w in (reversed(items) if right else items):
            r1.addWidget(w, 0, Qt.AlignmentFlag.AlignVCenter)
        r1.addStretch(1) if not right else r1.insertStretch(0, 1)
        r1w = QWidget()
        r1w.setFixedHeight(24)
        r1w.setLayout(r1)
        col.addWidget(r1w)
        r2 = QHBoxLayout()
        r2.setSpacing(6)
        r2.setContentsMargins(0, 0, 0, 0)
        club = (self._ctx.club_of(p) if self._ctx else None)
        parts = []
        fl = nation_flag(p.get('nation'))
        if fl:
            fw = QLabel(fl)
            ff = QFont('Noto Color Emoji')
            ff.setPixelSize(14)
            fw.setFont(ff)
            fw.setFixedHeight(16)
            parts.append(fw)
        if club:
            unit = QWidget()
            ul = QHBoxLayout(unit)
            ul.setContentsMargins(0, 0, 0, 0)
            ul.setSpacing(5)
            cpx = _faces_service().club_pixmap(club.get('uid'), 16, dpr)
            if cpx is not None:
                cl = QLabel()
                cl.setFixedSize(16, 16)
                cl.setPixmap(cpx)
                ul.addWidget(cl)
            ul.addWidget(_ElideLabel(club['name'], 'cmpSub', natural=True), 1)
            unit.setFixedHeight(16)
            parts += [unit]
        age = _lbl(f'{person_age(p)} years', 'cmpSub', 16)
        parts += [_lbl('·', 'cmpSub', 16), age] if (fl or club) else [age]
        if right:
            parts = parts[::-1]
        for w in parts:
            r2.addWidget(w)
        r2.addStretch(1) if not right else r2.insertStretch(0, 1)
        r2w = QWidget()
        r2w.setFixedHeight(16)
        r2w.setLayout(r2)
        col.addWidget(r2w)
        col.addStretch(1)
        cab = [self._cab('CURRENT', 'CA', p.get('ca'), COLORS['accent_hover'], bw, spx),
               self._cab('POTENTIAL', 'PA', p.get('pa'), '#9A8AF5', bw, spx)]
        seq = [av, col, *cab]
        if right:
            seq = seq[::-1]
        for w in seq:
            if isinstance(w, QVBoxLayout):
                h.addLayout(w, 1)
            else:
                h.addWidget(w)
        return fr

    def _badge(self, pos):
        from gui.main_window import _POS_BADGE_COLORS
        code = POS_CODE.get(pos, pos)
        lb = _lbl(code, 'cmpBadge', 16, Qt.AlignmentFlag.AlignCenter)
        bf = QFont()
        bf.setPixelSize(10)
        bf.setBold(True)
        lb.setFixedWidth(max(28, int(QFontMetricsF(bf).horizontalAdvance(code)) + 12))
        lb.setStyleSheet(f'QLabel#cmpBadge {{ background:{_POS_BADGE_COLORS.get(pos, ("#2A2D35",))[0]}; padding:0 5px; }}')
        return lb

    def _cab(self, title, code, val, color, w, spx):
        """CA / PA box (mockup .cab, w x 56): title 10/700 caps, 5 stars (spx px, gap 2) or the number + a 6 px bar; raw number in the tooltip."""
        f = QFrame()
        f.setObjectName('cmpCab')
        f.setFixedSize(w, 56)
        f.setToolTip(f'{code} {val}' if val is not None else '')
        v = QVBoxLayout(f)
        v.setContentsMargins(10 if self._density == 0 else 8, 6, 8, 0)
        v.setSpacing(4)
        tl = _lbl(title, 'cmpCabT', 14)
        tl.setStyleSheet(f'QLabel#cmpCabT {{ font-size:{DENSITY[self._density][7]}px; }}')
        v.addWidget(_spaced(tl, DENSITY[self._density][8]))
        if self._stars_on and val is not None:
            sl = QLabel()
            sl.setPixmap(star_row_pixmap(ability_stars(val), spx, 2, self.devicePixelRatioF()))
            sl.setFixedHeight(24)
            v.addWidget(sl)
        else:
            row = QWidget()
            row.setFixedHeight(24)
            rh = QHBoxLayout(row)
            rh.setContentsMargins(0, 0, 0, 0)
            rh.setSpacing(6)
            num = QLabel(str(val) if val is not None else '?')
            num.setStyleSheet(f'QLabel {{ color:{color}; font-size:{20 if self._density == 0 else 16 if self._density == 1 else 14}px; font-weight:bold; }}')
            rh.addWidget(num, 0, Qt.AlignmentFlag.AlignVCenter)
            rh.addWidget(_Bar((val or 0) / 200, color), 1, Qt.AlignmentFlag.AlignVCenter)
            v.addWidget(row)
        v.addStretch(1)
        return f

    # -- empty state -----------------------------------------------------------------------------
    def _empty_state(self):
        host = QWidget()
        hl = QHBoxLayout(host)
        hl.setContentsMargins(0, 0, 0, 0)
        fr = QFrame()
        fr.setObjectName('cmpEmpty')
        fr.setMaximumWidth(640)
        fr.setMinimumWidth(300)
        v = QVBoxLayout(fr)
        v.setContentsMargins(24, 22, 24, 14)
        v.setSpacing(6)
        v.addWidget(_Ghost(), 0, Qt.AlignmentFlag.AlignHCenter)
        one = self._a or self._b
        v.addWidget(_lbl('Now pick the second player' if one else 'Pick two players to compare', 'cmpEmptyT', align=Qt.AlignmentFlag.AlignCenter))
        sub = _lbl('Search any player in the save above. Goalkeepers can only be compared with goalkeepers.' if one else
                   'Search any player in the save above, or start from a player you looked at recently.', 'cmpEmptyS',
                   align=Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        v.addWidget(sub)
        if self._ctx is not None:
            other = self._a or self._b
            rows = [p for p in self._ctx.recent() if not other or (p['id'] != other['id'] and is_keeper(p) == is_keeper(other))][:8]
            if rows:
                hair = QFrame()
                hair.setObjectName('cmpHair')
                hair.setFixedHeight(1)
                v.addSpacing(8)
                v.addWidget(hair)
                v.addWidget(_spaced(_lbl('RECENTLY VIEWED', 'cmpEh', 24)))
                grid = QHBoxLayout()
                grid.setSpacing(16)
                halves = [rows[:4], rows[4:]] if not self._narrow else [rows]
                for part in halves:
                    if not part:
                        continue
                    lw = make_row_list()
                    lw.setFixedHeight(len(part) * 44)
                    lw.setMinimumWidth(240)
                    fill_rows(lw, part, self._ctx, '', self._stars_on)
                    lw.itemClicked.connect(lambda it: self._empty_pick(it.data(Qt.ItemDataRole.UserRole)))
                    grid.addWidget(lw, 1, Qt.AlignmentFlag.AlignTop)
                v.addLayout(grid)
        hl.addStretch(1)
        hl.addWidget(fr, 100)
        hl.addStretch(1)
        return host

    # -- main area (variant A) -------------------------------------------------------------------
    def _main_area(self):
        host = QWidget()
        lay = QBoxLayout(QBoxLayout.Direction.TopToBottom if self._narrow else QBoxLayout.Direction.LeftToRight, host)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        left = self._compare_panel()
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(12)
        rv.addWidget(self._attr_panel(), 1)
        rv.addWidget(self._facts_panel())
        lay.addWidget(left, 0 if self._narrow else 36)
        lay.addWidget(right, 0 if self._narrow else 64)
        return host

    def _axes(self):
        a, b = self._side(self._a), self._side(self._b)
        va, vb = a.values(self._pot), b.values(self._pot)
        table = {n: attrs for n, attrs, _i in axis_table(a.gk, self._mode)}
        bm = {n: m for n, m, _t in axis_values(vb, b.gk, self._mode)}
        out = []
        for n, m, _t in axis_values(va, a.gk, self._mode):
            if n in bm:
                tip = (f'{n} (mean of {len(table[n])} attributes): {short_name(self._a)} {m:.1f}, {short_name(self._b)} {bm[n]:.1f}. '
                       + ', '.join(table[n]))
                out.append((n, m, bm[n], tip))
        return out

    def _compare_panel(self):
        p = self._side(self._a)
        pot_seg = _seg([(False, 'Current'), (True, 'Full Potential')], self._pot, self._set_pot)
        panel, v = _panel('Compare', pot_seg)
        n_det = len(axis_table(p.gk, 'detailed'))
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(12, 2, 12, 8)
        rl.setSpacing(8)
        rl.addWidget(_lbl('Radar axes', 'cmpNote'))
        rl.addWidget(_seg([('overview', 'Overview (6)'), ('detailed', f'Detailed ({n_det})')], self._mode, self.set_mode,
                          'Detailed: more specific axes (aerial, passing, finishing...); hover an axis label for its attributes'))
        rl.addStretch(1)
        v.addWidget(row)
        axes = self._axes()
        radar = CompareRadar()
        radar.set_axes(axes)
        v.addWidget(radar, 0, Qt.AlignmentFlag.AlignHCenter)
        leg = QWidget()
        ll = QHBoxLayout(leg)
        ll.setContentsMargins(12, 0, 12, 4)
        ll.setSpacing(6)
        for slot, per in (('a', self._a), ('b', self._b)):
            ll.addWidget(_marker(slot))
            nm = _ElideLabel(per['name'], 'cmpName', natural=True)
            nm.setStyleSheet('QLabel#cmpName { font-weight:600; }')
            ll.addWidget(nm)
            ll.addSpacing(8)
        ll.addStretch(1)
        v.addWidget(leg)
        note = _lbl('solid / dashed outline · ring 10 and 20' + (' · hover a label for its attributes' if self._mode == 'detailed' else ''), 'cmpNote')
        note.setContentsMargins(12, 0, 12, 8)
        v.addWidget(note)
        hair = QFrame()
        hair.setObjectName('cmpHair')
        hair.setFixedHeight(1)
        v.addWidget(hair)
        edge = QWidget()
        ev = QVBoxLayout(edge)
        ev.setContentsMargins(12, 6, 12, 8)
        ev.setSpacing(0)
        ev.addWidget(_spaced(_lbl(f"DIFFERENCE BY {'AXIS' if self._mode == 'detailed' else 'GROUP'} (MEAN OF 1 TO 20)", 'cmpEh', 20)))
        for n, a, b, _tip in axes:
            ev.addWidget(EdgeRow(n, a, b, f'{n}: {short_name(self._a)} {a:.1f}, {short_name(self._b)} {b:.1f}'))
        v.addWidget(edge)
        v.addStretch(1)
        return panel

    def _set_pot(self, on):
        if on != self._pot:
            self._pot = on
            self._rebuild()

    def _attr_panel(self):
        a, b = self._side(self._a), self._side(self._b)
        wa, wb, lv = attrs_won(a, b, self._pot)
        tally = QLabel(f'<span style="color:{A_HEX}">●</span> <b style="color:{A_HEX}">{wa}</b>&nbsp;&nbsp;'
                       f'<span style="color:{B_HEX}">◆</span> <b style="color:{B_HEX}">{wb}</b>&nbsp;&nbsp;<span style="color:{COLORS["text_secondary"]}">· {lv} level</span>')
        tally.setTextFormat(Qt.TextFormat.RichText)
        tally.setToolTip(f"Attributes won: {self._a['name']} {wa}, {self._b['name']} {wb}, {lv} level. Every attribute counts equally; "
                         'Footedness is not counted' + ('; the outfield Technical group of keepers is not listed or counted.' if a.gk else '.'))
        panel, v = _panel('Attributes', tally)
        cols = QHBoxLayout()
        cols.setContentsMargins(10, 0, 10, 8)
        cols.setSpacing(10)
        for keys in (COLUMNS_GK if a.gk else COLUMNS_OUT):
            c = QVBoxLayout()
            c.setSpacing(0)
            for i, k in enumerate(keys):
                if i:
                    c.addSpacing(6)
                title = 'Footedness' if k == 'foot' else GROUPS[k][0]
                c.addWidget(_spaced(_lbl(title.upper(), 'cmpEh', 22)))
                for (n, va, lo), (_n, vb, _l) in zip(a.rows(k, self._pot), b.rows(k, self._pot)):
                    c.addWidget(self._attr_row(n, va, vb, lo, k == 'foot'))
            c.addStretch(1)
            cols.addLayout(c, 1)
        v.addLayout(cols)
        v.addStretch(1)
        return panel

    def _attr_row(self, name, va, vb, lower, foot=False):
        row = QWidget()
        row.setFixedHeight(22)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 1, 0, 1)
        h.setSpacing(4)
        h.addWidget(_ElideLabel(name, 'cmpAttrName'), 1)
        d = good(va, lower) - good(vb, lower)
        who = short_name(self._a) if d > 0 else short_name(self._b)
        tip = 'Level' if d == 0 else f'{who} higher by {abs(d)}'
        h.addWidget(_tile(va, lower))
        h.addWidget(DiffCell(d, tip))
        h.addWidget(_tile(vb, lower))
        row.setToolTip(f"{name}: {short_name(self._a)} {va}, {short_name(self._b)} {vb}" + (' (lower is better)' if lower else ''))
        return row

    def _facts_panel(self):
        a, b = self._side(self._a), self._side(self._b)
        note = _lbl('Transfer value (market value) and wage as stored in the save', 'cmpNote')
        panel, v = _panel('Key facts', note)
        row = QHBoxLayout()
        row.setContentsMargins(4, 0, 4, 8)
        row.setSpacing(0)
        for i, (title, ta, tb, diff, tip) in enumerate(key_facts(a, b)):
            col = QWidget()
            if i:
                col.setStyleSheet(f"QWidget#cmpFact {{ border-left:1px solid {COLORS['border']}; }}")
            col.setObjectName('cmpFact')
            cv = QVBoxLayout(col)
            cv.setContentsMargins(10 if i else 8, 2, 8, 0)
            cv.setSpacing(0)
            cv.addWidget(_spaced(_lbl(title.upper(), 'cmpFactT', 18), 0.8))
            for slot, t in (('a', ta), ('b', tb)):
                r = QWidget()
                r.setFixedHeight(22)
                rh = QHBoxLayout(r)
                rh.setContentsMargins(0, 0, 0, 0)
                rh.setSpacing(6)
                rh.addWidget(_marker(slot, 6))
                rh.addWidget(_ElideLabel(t, 'cmpFactV', natural=True), 1)
                cv.addWidget(r)
            cv.addWidget(_lbl(diff, 'cmpFactD', 18))
            if tip:
                col.setToolTip(tip)
            row.addWidget(col, FACTS_STRETCH[i])
        v.addLayout(row)
        return panel
