"""Player window (master visual: mockups/player-window.html). Persistent header (identity, chips, CA/PA, per-tab
slot) above a left tab strip + QStackedWidget, and a persistent action strip (Close / Make HGP / Make HGC / Shortlist).

TABS rows = (key, label, page builder method name | None, header-slot method name). None = "Coming soon" placeholder
described by SOON[key]. Add a real tab = write `_page_<key>` and name it in TABS; the slot method returns
(label, [widgets], sub text). Positions = list + pitch; its Current | Future switch has Future disabled (position
ratings are stored in the save, not derived from attributes).

Data the save does not give us yet is read from `data` (see `player_extra_data`) and shown as PENDING
(respecting Settings > Show PENDING markers). Projected ("at potential") values are display only.
"""
import calendar
import math


from PyQt6.QtCore import Qt, QPointF, QRect, QRectF
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QKeySequence, QPainter, QPen, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QButtonGroup, QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from fm_editor import potential as _pot
from fm_editor import settings as _settings
from fm_editor.abilitystars import ability_stars, dev_stars
from gui.stars import _StarWidget
from fm_editor import traitrec as _tr
from fm_editor.agecalc import person_age
from fm_editor.traits import trait_ids, trait_names
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
# Mockup position tables (list order = mockup POS). Save order stays POS_ORDER (byte order of the 15 ratings).
POS_DISPLAY = ['GK', 'SW', 'DL', 'DC', 'DR', 'WBL', 'WBR', 'DM', 'ML', 'MC', 'MR', 'AML', 'AMC', 'AMR', 'ST']
POS_CODE = {'GK': 'GK', 'SW': 'SW', 'DL': 'D(L)', 'DC': 'D(C)', 'DR': 'D(R)', 'WBL': 'WB(L)', 'WBR': 'WB(R)',
            'DM': 'DM', 'ML': 'M(L)', 'MC': 'M(C)', 'MR': 'M(R)', 'AML': 'AM(L)', 'AMC': 'AM(C)', 'AMR': 'AM(R)',
            'ST': 'ST'}
POS_FULL = {'GK': 'Goalkeeper', 'SW': 'Sweeper', 'DL': 'Defender (Left)', 'DC': 'Defender (Centre)',
            'DR': 'Defender (Right)', 'WBL': 'Wing Back (Left)', 'WBR': 'Wing Back (Right)',
            'DM': 'Defensive Midfielder', 'ML': 'Midfielder (Left)', 'MC': 'Midfielder (Centre)',
            'MR': 'Midfielder (Right)', 'AML': 'Attacking Mid (Left)', 'AMC': 'Attacking Mid (Centre)',
            'AMR': 'Attacking Mid (Right)', 'ST': 'Striker'}
# Pitch slot of each position as fractions of the marked field rect, attacking UP (mockup SLOTS). ONE table: edit here.
SLOTS = {
    'ST': (.50, .11),
    'AML': (.16, .25), 'AMC': (.50, .25), 'AMR': (.84, .25),
    'ML': (.12, .40), 'MC': (.50, .40), 'MR': (.88, .40),
    'DM': (.50, .535),
    'WBL': (.08, .60), 'WBR': (.92, .60),
    'DL': (.20, .72), 'DC': (.50, .72), 'DR': (.80, .72),
    'SW': (.50, .835),
    'GK': (.50, .94),
}

_PERSON_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#525B68" '
               'stroke-width="1.6"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/></svg>')

# (key, label, builder method name or None = "Coming soon" placeholder described by SOON[key])
TABS = [
    ('profile', 'Profile', '_page_profile', '_slot_profile'),
    ('contract', 'Contract & Transfer', '_page_contract', '_slot_contract'),
    ('positions', 'Positions', '_page_positions', '_slot_positions'),
    ('general', 'General Rating', None, '_slot_profile'),
    ('role', 'Role Rating', None, '_slot_profile'),
    ('history', 'History', None, '_slot_history'),
]
SOON = {
    'general': 'Overall rating and a summary of the role ratings.',
    'role': 'Suitability for each tactical role.',
    'history': 'Career stats by season and club.',
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
    return {'wage': None, 'value': None, 'height_cm': person.get('height_cm'), 'weight_kg': person.get('weight_kg'), 'traits': traits, 'history': None}



def _dlg_qss():
    c = COLORS
    return f"""
QDialog#playerWindow {{ background:{c['window_bg']}; }}
QDialog#playerWindow QWidget {{ background:transparent; }}
QDialog#playerWindow QScrollArea {{ background:transparent; border:none; }}
QDialog#playerWindow QScrollBar:vertical {{ background:{c['surface']}; width:6px; margin:0; border:none; }}
QDialog#playerWindow QScrollBar::handle:vertical {{ background:{c['border_bright']}; border-radius:3px; min-height:20px; }}
QDialog#playerWindow QScrollBar::add-line:vertical, QDialog#playerWindow QScrollBar::sub-line:vertical {{ height:0; }}
QDialog#playerWindow QScrollBar::add-page:vertical, QDialog#playerWindow QScrollBar::sub-page:vertical {{ background:transparent; }}
QDialog#playerWindow QWidget#pwBody {{ background:{c['window_bg']}; }}
QDialog#playerWindow QLabel {{ background:transparent; color:{c['text_primary']}; font-size:12px; }}
QDialog#playerWindow QFrame#pwPanel {{ background:{c['surface']}; border:1px solid {c['border']}; border-radius:3px; }}
QDialog#playerWindow QFrame#pwRowAlt {{ background:{C_ALT}; }}
QDialog#playerWindow QFrame#pwRowNat {{ background:{c['selection_bg']}; }}
QDialog#playerWindow QFrame#pwRow {{ background:transparent; }}
QDialog#playerWindow QFrame#pwTabs {{ background:{c['surface']}; border:1px solid {c['border']}; border-radius:3px; }}
QDialog#playerWindow QPushButton#pwTab {{ background:transparent; border:none; border-left:3px solid transparent;
    color:{c['text_secondary']}; text-align:left; padding:0 2px 0 8px; font-size:12px; font-weight:600; border-radius:0; }}
QDialog#playerWindow QPushButton#pwTab:hover {{ background:{c['elevated']}; color:{c['text_primary']};
    border-left:3px solid {c['border_bright']}; }}
QDialog#playerWindow QPushButton#pwTab:checked {{ background:{c['selection_bg']}; color:{c['text_primary']};
    font-weight:bold; border-left:3px solid {c['accent']}; }}
QDialog#playerWindow QFrame#actionStrip {{ background:{c['surface']}; border:none; border-top:1px solid {c['border']}; }}
QDialog#playerWindow QWidget#pwSlot {{ border:none; border-left:1px solid {c['border']}; }}
QDialog#playerWindow QFrame#pwCab {{ background:{c['window_bg']}; border:1px solid {c['border']}; border-radius:3px; }}
QDialog#playerWindow QLabel#pwSoonT {{ font-size:20px; font-weight:bold; }}
QDialog#playerWindow QLabel#pwSoonTag {{ color:{c['text_secondary']}; font-size:10px; font-weight:bold;
    border:1px solid {c['border_bright']}; border-radius:10px; padding:0 10px; }}
QDialog#playerWindow QLabel#pwSoonD {{ color:{c['text_secondary']}; font-size:12px; }}
QDialog#playerWindow QWidget#pwHead {{ background:transparent; }}
QDialog#playerWindow QLabel#pwHeadT, QDialog#playerWindow QLabel#pwColHead, QDialog#playerWindow QLabel#pwSubT {{
    color:{c['text_secondary']}; font-size:11px; font-weight:bold; }}
QDialog#playerWindow QLabel#pwSubE {{ color:{c['text_secondary']}; font-size:11px; }}
QDialog#playerWindow QLabel#pwName {{ font-size:20px; font-weight:bold; }}
QDialog#playerWindow QLabel#pwSub {{ color:{c['text_secondary']}; font-size:12px; }}
QDialog#playerWindow QLabel#pwHw {{ color:{c['text_secondary']}; font-size:11px; }}
QDialog#playerWindow QLabel#pwBigLab {{ color:{c['text_secondary']}; font-size:10px; font-weight:bold; }}
QDialog#playerWindow QLabel#pwBigNum {{ font-size:20px; font-weight:bold; }}
QDialog#playerWindow QLabel#pwSlotV {{ font-size:20px; font-weight:bold; }}
QDialog#playerWindow QLabel#pwSlotS {{ color:{c['text_secondary']}; font-size:11px; }}
QDialog#playerWindow QLabel#pwAttrName, QDialog#playerWindow QLabel#pwKvL {{ color:{c['text_secondary']}; }}
QDialog#playerWindow QLabel#pwKvR {{ font-weight:600; }}
QDialog#playerWindow QLabel#pwTrait {{ font-weight:600; }}
QDialog#playerWindow QLabel#pwPosName {{ color:#FFFFFF; }}
QDialog#playerWindow QLabel#pwPosNameB {{ color:#FFFFFF; font-weight:bold; }}
QDialog#playerWindow QLabel#pwWord {{ color:{c['text_secondary']}; }}
QDialog#playerWindow QLabel#pwWordNat {{ color:#FFFFFF; font-weight:bold; }}
QDialog#playerWindow QLabel#pwNote {{ color:{c['text_secondary']}; font-size:11px; }}
QDialog#playerWindow QLabel#pwHint {{ color:{c['text_secondary']}; font-size:11px; }}
QDialog#playerWindow QLabel#pwAvatar {{ background:{c['elevated']}; border-radius:3px; }}
QDialog#playerWindow QLabel#pwBadge {{ color:#FFFFFF; font-size:10px; font-weight:bold; border-radius:2px; }}
QDialog#playerWindow QLabel#pwPill {{ color:{c['text_secondary']}; font-size:10px; font-weight:bold;
    border:1px solid {c['border_bright']}; border-radius:10px; padding:0 9px; }}
QDialog#playerWindow QLabel#pwPillOn {{ color:{c['hgp_green']}; font-size:10px; font-weight:bold;
    border:1px solid {c['hgp_green']}; border-radius:10px; padding:0 9px; background:rgba(90,160,209,36); }}
QDialog#playerWindow QLabel#pwPillUnk {{ color:{c['text_secondary']}; font-size:10px; font-weight:bold; padding:0 2px; }}
QDialog#playerWindow QLabel#pwChipInj {{ background:#8B1A1A; color:#FFFFFF; font-size:11px; font-weight:600;
    border-radius:3px; padding:0 8px; }}
QDialog#playerWindow QLabel#pwChipOk {{ background:{c['elevated']}; color:#52C287; font-size:11px; font-weight:600;
    border-radius:3px; padding:0 8px; }}
QDialog#playerWindow QFrame#pwSeg {{ background:{c['window_bg']}; border:1px solid {c['border_bright']}; border-radius:3px; }}
QDialog#playerWindow QPushButton#pwSegL, QDialog#playerWindow QPushButton#pwSegR {{ background:{c['window_bg']}; color:{c['text_secondary']};
    border:none; font-size:11px; font-weight:bold; padding:0 12px; }}
QDialog#playerWindow QPushButton#pwSegL {{ border-top-left-radius:2px; border-bottom-left-radius:2px; }}
QDialog#playerWindow QPushButton#pwSegR {{ border-top-right-radius:2px; border-bottom-right-radius:2px; }}
QDialog#playerWindow QPushButton#pwSegL:checked, QDialog#playerWindow QPushButton#pwSegR:checked {{ background:{c['accent']}; color:#FFFFFF; }}
QDialog#playerWindow QPushButton#pwSegR:disabled {{ color:{C_TX3}; background:{c['window_bg']}; }}
QDialog#playerWindow QPushButton#pwPrimary {{ background:{c['accent']}; color:#FFFFFF; border:1px solid transparent; border-radius:3px;
    font-size:12px; font-weight:bold; padding:0 16px; }}
QDialog#playerWindow QPushButton#pwPrimary:hover {{ background:{c['accent_hover']}; }}
QDialog#playerWindow QPushButton#pwPrimary:pressed {{ background:{c['accent_press']}; }}
QDialog#playerWindow QPushButton#pwShortOn, QDialog#playerWindow QPushButton#pwShortOn:disabled {{ background:{c['selection_bg']}; color:{C_POT};
    border:1px solid {c['accent_hover']}; border-radius:3px; font-size:12px; font-weight:bold; padding:0 16px; }}
QDialog#playerWindow QPushButton#pwGhost {{ background:{c['surface']}; color:#FFFFFF; border:1px solid {c['border_bright']};
    border-radius:3px; font-size:12px; font-weight:bold; padding:0 16px; }}
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



def word(v):
    """Rating word. Thresholds per mockup; 1 = Ineffective / 2-4 = Awkward is UNVERIFIED (open question 2)."""
    return ('Natural' if v >= 20 else 'Accomplished' if v >= 15 else 'Competent' if v >= 10
            else 'Unconvincing' if v >= 5 else 'Awkward' if v >= 2 else 'Ineffective')


def foot_word(v):
    """Verified vs in-game screens (24 players): Weak 7-8, Reasonable 9-11, Fairly Strong 12-14, Strong 15-16,
    Very Strong 20. UNVERIFIED: Very Weak (<=5 assumed), Strong 17-19 (assumed)."""
    return ('Very Weak' if v <= 5 else 'Weak' if v <= 8 else 'Reasonable' if v <= 11
            else 'Fairly Strong' if v <= 14 else 'Strong' if v <= 19 else 'Very Strong')


_FUTURE_TIP = ('Not available yet: position ratings are stored in the save, not calculated from attributes, '
               'so they cannot be recomputed from projected attributes.')


class _PitchBig(QWidget):
    """Mockup pitchSVG: 12 grass bands, markings, 15 rating dots (lowest first so the best sit on top).
    Geometry constants are the mockup's `g` table; dot slots = SLOTS (fractions of the marked field, attacking up)."""
    M = 22
    G = dict(boxW=238, boxD=88, sixW=108, sixD=29, circR=54, spotD=58, goalW=43, goalD=6)

    def __init__(self, ratings, parent=None):
        super().__init__(parent)
        self._r = ratings
        self.setMinimumSize(300, 420)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g, M = self.G, self.M
        W, H = self.width(), self.height()
        p.fillRect(0, 0, W, H, QColor('#15301F'))
        bh = H / 12
        for i in range(1, 12, 2):
            p.fillRect(QRectF(0, i * bh, W, bh), QColor('#1D4229'))
        ln = QColor(255, 255, 255, round(0.42 * 255))
        x0 = y0 = M
        w, h = W - 2 * M, H - 2 * M
        cx, cy, y1 = x0 + w / 2, y0 + h / 2, y0 + h
        p.setPen(QPen(ln, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(QRectF(x0 + .5, y0 + .5, w, h))
        p.drawLine(QPointF(x0, cy), QPointF(x0 + w, cy))
        p.drawEllipse(QPointF(cx, cy), g['circR'], g['circR'])
        p.setBrush(ln)
        p.drawEllipse(QPointF(cx, cy), 2, 2)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for bot in (0, 1):
            bx, sx, gx = cx - g['boxW'] / 2, cx - g['sixW'] / 2, cx - g['goalW'] / 2
            by = y1 - g['boxD'] if bot else y0
            sy = y1 - g['sixD'] if bot else y0
            gy = y1 if bot else y0 - g['goalD']
            p.drawRect(QRectF(bx, by + .5, g['boxW'], g['boxD']))
            p.drawRect(QRectF(sx, sy + .5, g['sixW'], g['sixD']))
            p.drawRect(QRectF(gx, gy + .5, g['goalW'], g['goalD']))
            spot_y = y1 - g['spotD'] if bot else y0 + g['spotD']
            dy = abs(g['boxD'] - g['spotD'])
            alpha = math.degrees(math.asin(dy / g['circR']))
            p.setBrush(ln)
            p.drawEllipse(QPointF(cx, spot_y), 2, 2)
            p.setBrush(Qt.BrushStyle.NoBrush)
            r = g['circR']
            rect = QRectF(cx - r, spot_y - r, 2 * r, 2 * r)
            span = round((180 - 2 * alpha) * 16)
            if bot:
                p.drawArc(rect, round(alpha * 16), span)        # above the box edge
            else:
                p.drawArc(rect, round(-alpha * 16), -span)      # below the box edge
        f = QFont(p.font())
        f.setPixelSize(12)
        f.setBold(True)
        fl = QFont(f)
        fl.setPixelSize(10)
        for pos in sorted(POS_DISPLAY, key=lambda q: (self._r.get(q, 1), -POS_DISPLAY.index(q))):
            sx_, sy_ = SLOTS[pos]
            x, y = M + sx_ * w, M + sy_ * h
            v = self._r.get(pos, 1)
            t = tier(v)
            col = QColor(TIER_HEX[t])
            if v >= 20:
                p.setPen(QPen(QColor('#FFFFFF'), 2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(x, y), 18, 18)
            ghost = t == 1
            if ghost:
                p.setPen(QPen(col, 1))
                p.setBrush(QColor(20, 21, 26, round(0.55 * 255)))
                p.drawEllipse(QPointF(x, y), 13.5, 13.5)
            else:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(col)
                p.drawEllipse(QPointF(x, y), 14, 14)
            p.setFont(f)
            p.setPen(col if ghost else QColor('#14151A'))
            p.drawText(QRectF(x - 14, y - 14, 28, 28), Qt.AlignmentFlag.AlignCenter, str(v))
            p.setFont(fl)
            p.setPen(QColor(255, 255, 255, round(0.72 * 255)))
            p.drawText(QRectF(x - 30, y - 34, 60, 12), Qt.AlignmentFlag.AlignCenter, POS_CODE[pos])


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
        self._ability_stars = _settings.ability_as_stars()  # read once when the window opens
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
        self._init_state()
        self._build()

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

    def _init_state(self):
        from gui import main_window as mw
        from fm_editor.patch import is_hgc
        p = self._person
        pos_list = p.get('positions') or [1] * 15
        self._ratings = dict(zip(POS_ORDER, pos_list))
        self._pos = mw._primary_pos(pos_list) if p.get('positions') else None
        self._is_gk = self._pos == 'GK'
        b = self._save_data.get('b') if self._save_data else None
        self._hgp = bool(p.get('hgp', False))
        self._hgc = is_hgc(b, p, self._club_entity_id) if (b is not None and self._club_entity_id) else None

    # -- shell: header / (tab strip | pages) / action strip ---------------------------------------
    def _build(self):
        global _LAST_TAB
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(12, 12, 12, 12)
        bl.setSpacing(12)
        bl.addWidget(self._header())
        main = QHBoxLayout()
        main.setSpacing(12)
        strip = QFrame()
        strip.setObjectName('pwTabs')
        strip.setFixedWidth(150)
        sv = QVBoxLayout(strip)
        sv.setContentsMargins(6, 6, 6, 6)
        sv.setSpacing(2)
        self._stack = QStackedWidget()
        self._tab_btns = {}
        self._tab_keys = [t[0] for t in TABS]
        grp = QButtonGroup(self)
        grp.setExclusive(True)
        self._tab_group = grp
        for key, label, builder, _slot in TABS:
            btn = QPushButton(label.replace('&', '&&'))
            btn.setObjectName('pwTab')
            btn.setFixedHeight(34)
            btn.setCheckable(True)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._select_tab(k))
            grp.addButton(btn)
            sv.addWidget(btn)
            self._tab_btns[key] = btn
            self._stack.addWidget(getattr(self, builder)() if builder else self._page_soon(label, SOON[key]))
        sv.addStretch()
        main.addWidget(strip)
        main.addWidget(self._stack, 1)
        bl.addLayout(main, 1)
        outer.addWidget(body, 1)
        outer.addWidget(self._action_strip())
        QShortcut(QKeySequence('Ctrl+Tab'), self, activated=lambda: self._step_tab(1))
        QShortcut(QKeySequence('Ctrl+Shift+Tab'), self, activated=lambda: self._step_tab(-1))
        self._select_tab(_LAST_TAB if _LAST_TAB in self._tab_btns else 'profile')

    def _select_tab(self, key):
        global _LAST_TAB
        _LAST_TAB = key
        self._tab_btns[key].setChecked(True)
        self._stack.setCurrentIndex(self._tab_keys.index(key))
        slot = next(t[3] for t in TABS if t[0] == key)
        label, vals, sub = getattr(self, slot)()
        self._set_slot(label, vals, sub)

    def _step_tab(self, d):
        self._select_tab(self._tab_keys[(self._stack.currentIndex() + d) % len(self._tab_keys)])

    @staticmethod
    def _scrolled(content):
        """Wrap a page in a vertical-only scroll area (content top-aligned, transparent over the window)."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content.setObjectName('pwBody')
        scroll.setWidget(content)
        return scroll

    def _page(self, *widgets, stretch=None, fill=False):
        """Page = row of panels top-aligned (mockup .content: flex, align-items:flex-start, gap 12)."""
        body = QWidget()
        h = QHBoxLayout(body)
        h.setContentsMargins(0, 0, 6, 0)
        h.setSpacing(12)
        for i, w in enumerate(widgets):
            if fill:
                h.addWidget(w, (stretch or {}).get(i, 0))
            else:
                h.addWidget(w, (stretch or {}).get(i, 0), Qt.AlignmentFlag.AlignTop)
        if not stretch and not fill:
            h.addStretch()
        return self._scrolled(body)

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

    # -- pages -----------------------------------------------------------------------------------
    def _page_profile(self):
        attrs = self._attr_panel()
        return self._page(attrs, self._rail(), stretch={0: 1})

    def _page_contract(self):
        col = QWidget()
        cv = QVBoxLayout(col)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(12)
        cv.addWidget(self._contract_panel())
        tag = _spaced(_lab('COMING', 'pwSoonTag', Qt.AlignmentFlag.AlignCenter, 20))
        panel, v = self._panel('Bonuses & clauses', tag)
        note = _lab('Bonuses, clauses and release terms will be added here.', 'pwNote')
        note.setWordWrap(True)
        note.setContentsMargins(12, 0, 12, 14)
        v.addWidget(note)
        cv.addWidget(panel)
        cv.addWidget(self._transfer_panel())
        cv.addStretch()
        col.setFixedWidth(360)
        return self._page(col)

    def _page_positions(self):
        return self._page(self._positions_list(), self._positions_pitch(), stretch={1: 1}, fill=True)

    # -- panels ----------------------------------------------------------------------------------
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

    def _seg(self, left, right, right_enabled=True, right_tip=''):
        """Segmented control h24 (mockup .sg) -> (frame, left btn, right btn)."""
        seg = QFrame()
        seg.setObjectName('pwSeg')
        sl = QHBoxLayout(seg)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)
        bl_, br_ = QPushButton(left), QPushButton(right)
        bl_.setObjectName('pwSegL')
        br_.setObjectName('pwSegR')
        grp = QButtonGroup(seg)
        grp.setExclusive(True)
        bold = QFont()
        bold.setPixelSize(11)
        bold.setBold(True)
        fm = QFontMetrics(bold)
        for b in (bl_, br_):
            b.setCheckable(True)
            b.setFixedSize(fm.horizontalAdvance(b.text()) + 28, 24)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            grp.addButton(b)
            sl.addWidget(b)
        bl_.setChecked(True)
        br_.setEnabled(right_enabled)
        if right_tip:
            br_.setToolTip(right_tip)
            if not right_enabled:
                seg.setToolTip(right_tip)
        seg._grp = grp
        return seg, bl_, br_

    # -- header (persistent) ---------------------------------------------------------------------
    def _badge(self, pos, wide=False):
        from gui.main_window import _POS_BADGE_COLORS
        bg = _POS_BADGE_COLORS.get(pos, ('#2A2D35', '#FFFFFF'))[0]
        lbl = _lab(POS_CODE.get(pos, pos), 'pwBadge', Qt.AlignmentFlag.AlignCenter, 16)
        lbl.setMinimumWidth(44 if wide else 28)
        lbl.setStyleSheet(f'QLabel#pwBadge {{ background:{bg}; padding:0 5px; }}')
        return lbl

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

    # Star-mode header grid (CA / PA / slot share it so labels, stars and captions line up across all three):
    # top pad 8 | label 14 | gap 4 | value row 24 | gap 4 | caption 14  = 68px
    _HG_TOP, _HG_LAB, _HG_GAP, _HG_VAL, _HG_CAP = 8, 14, 4, 24, 14
    _HG_H = _HG_TOP + _HG_LAB + _HG_GAP + _HG_VAL + _HG_GAP + _HG_CAP
    _CAB_CAPTION = {'CA': 'Current ability', 'PA': 'Potential ability'}

    @staticmethod
    def _star_row(n):
        sw = QWidget()
        sh = QHBoxLayout(sw)
        sh.setContentsMargins(0, 0, 0, 0)
        sh.setSpacing(2)
        for i in range(5):
            sh.addWidget(_StarWidget(max(0.0, min(1.0, n - i))), 0, Qt.AlignmentFlag.AlignVCenter)
        sh.addStretch()
        return sw

    def _cab_stars(self, label, val):
        """Star-mode CA / PA box: label, 5 stars, caption on the shared header grid."""
        f = QFrame()
        f.setObjectName('pwCab')
        f.setFixedSize(116, self._HG_H)
        f.setToolTip(f'{label} {val}')
        v = QVBoxLayout(f)
        v.setContentsMargins(12, self._HG_TOP, 10, 0)
        v.setSpacing(self._HG_GAP)
        v.addWidget(_spaced(_lab(label, 'pwBigLab', None, self._HG_LAB), 0.8))
        sw = self._star_row(ability_stars(val))
        sw.setFixedHeight(self._HG_VAL)
        v.addWidget(sw)
        v.addWidget(_lab(self._CAB_CAPTION.get(label, ''), 'pwSlotS', None, self._HG_CAP))
        v.addStretch()
        return f

    def _cab(self, label, val, color):
        """CA / PA box 104x52: label 10/700 + value 20/700 on one 26px row, then a 6px bar (mockup .cab)."""
        if self._ability_stars and val is not None:
            return self._cab_stars(label, val)
        f = QFrame()
        f.setObjectName('pwCab')
        f.setFixedSize(104, 52)
        v = QVBoxLayout(f)
        v.setContentsMargins(10, 6, 10, 0)
        v.setSpacing(0)
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.addWidget(_spaced(_lab(label, 'pwBigLab'), 0.8), 0, Qt.AlignmentFlag.AlignVCenter)
        top.addStretch()
        stars = self._ability_stars and val is not None
        if stars:
            f.setToolTip(f'{label} {val}')
        else:
            num = _lab(str(val) if val is not None else '?', 'pwBigNum')
            num.setStyleSheet(f'QLabel#pwBigNum {{ color:{color}; }}')
            top.addWidget(num, 0, Qt.AlignmentFlag.AlignVCenter)
        tw = QWidget()
        tw.setFixedHeight(26)
        tw.setLayout(top)
        v.addWidget(tw)
        if stars:
            n = ability_stars(val)
            sw = QWidget()
            sh = QHBoxLayout(sw)
            sh.setContentsMargins(0, 0, 0, 0)
            sh.setSpacing(1)
            for i in range(5):
                sh.addWidget(_StarWidget(max(0.0, min(1.0, n - i))))
            sh.addStretch()
            v.addWidget(sw)
        else:
            v.addSpacing(3)
            v.addWidget(_Bar((val or 0) / 200, color))
        v.addStretch()
        return f

    def _header(self):
        from gui import main_window as mw
        p = self._person
        nation = mw.NATIONS.get(p.get('nation'), f"n={p.get('nation')}")
        hero = QFrame()
        hero.setObjectName('pwPanel')
        hero.setFixedHeight(80)
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(16, 0, 16, 0)
        hl.setSpacing(14)
        av = QLabel()
        av.setObjectName('pwAvatar')
        av.setFixedSize(48, 48)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setPixmap(self._svg_pixmap(_PERSON_SVG, 30))
        hl.addWidget(av)
        col = QVBoxLayout()
        col.setSpacing(5)
        col.setContentsMargins(0, 0, 0, 0)
        col.addStretch(1)
        r1 = QHBoxLayout()
        r1.setSpacing(10)
        r1.setContentsMargins(0, 0, 0, 0)
        nm = _lab(p['name'], 'pwName')
        nm.setFixedHeight(24)
        r1.addWidget(nm, 0)
        if self._pos:
            r1.addWidget(self._badge(self._pos), 0, Qt.AlignmentFlag.AlignVCenter)
        r1.addStretch(1)
        r1w = QWidget()
        r1w.setFixedHeight(24)
        r1w.setLayout(r1)
        col.addWidget(r1w)
        sub = ' · '.join(s for s in (nation, f'{person_age(p)} years ({self._born_text()})', self._club_name()) if s)
        s2 = _ElideLabel(sub, 'pwSub')
        s2.setFixedHeight(16)
        col.addWidget(s2)
        r3 = QHBoxLayout()
        r3.setSpacing(6)
        r3.setContentsMargins(0, 0, 0, 0)
        for lab, on in (('HGP', self._hgp), ('HGC', self._hgc)):
            if on:
                c = _lab(lab, 'pwPillOn', Qt.AlignmentFlag.AlignCenter, 20)
            elif on is False:
                c = _lab(lab, 'pwPill', Qt.AlignmentFlag.AlignCenter, 20)
            else:
                c = _lab(lab + '?', 'pwPillUnk', Qt.AlignmentFlag.AlignCenter, 20)
                c.setToolTip('Homegrown status at this club could not be determined')
            r3.addWidget(c)
        if p.get('injured'):
            d = p.get('injury_days', 0)
            r3.addWidget(_lab(f'Injured · {d} days' if d else 'Injured', 'pwChipInj', Qt.AlignmentFlag.AlignCenter, 20))
        else:
            r3.addWidget(_lab('Fit', 'pwChipOk', Qt.AlignmentFlag.AlignCenter, 20))
        r3.addSpacing(2)
        self._hw_lbl = self._height_weight_line()
        r3.addWidget(self._hw_lbl)
        r3.addStretch(1)
        r3w = QWidget()
        r3w.setFixedHeight(20)
        r3w.setLayout(r3)
        col.addWidget(r3w)
        col.addStretch(1)
        hl.addLayout(col, 1)
        hl.addWidget(self._cab('CA', p.get('ca'), COLORS['accent_hover']))
        hl.addWidget(self._cab('PA', p.get('pa'), C_POT))
        self._slot_w = QWidget()
        self._slot_w.setObjectName('pwSlot')
        stars_grid = self._ability_stars
        self._slot_w.setFixedSize(172, self._HG_H if stars_grid else 56)
        sv = QVBoxLayout(self._slot_w)
        sv.setContentsMargins(16, self._HG_TOP if stars_grid else 0, 0, 0)
        sv.setSpacing(self._HG_GAP if stars_grid else 3)
        self._slot_l = _spaced(_lab('', 'pwBigLab'), 0.8)
        if stars_grid:
            self._slot_l.setFixedHeight(self._HG_LAB)
        self._slot_vh = QHBoxLayout()
        self._slot_vh.setContentsMargins(0, 0, 0, 0)
        self._slot_vh.setSpacing(8)
        vw = QWidget()
        vw.setFixedHeight(24)
        vw.setLayout(self._slot_vh)
        self._slot_s = _ElideLabel('', 'pwSlotS')
        self._slot_s.setFixedHeight(14)
        if not stars_grid:
            sv.addStretch()
        sv.addWidget(self._slot_l)
        sv.addWidget(vw)
        sv.addWidget(self._slot_s)
        sv.addStretch()
        hl.addWidget(self._slot_w)
        return hero

    def _set_slot(self, label, widgets, sub):
        self._slot_l.setText(label.upper())
        while self._slot_vh.count():
            it = self._slot_vh.takeAt(0)
            w = it.widget()
            if w is not None:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        for w in widgets:
            self._slot_vh.addWidget(w, 0, Qt.AlignmentFlag.AlignVCenter)
        self._slot_vh.addStretch()
        self._slot_s._full = sub or ''
        self._slot_s.setText(sub or '')

    @staticmethod
    def _slot_val(text, color=None):
        lbl = _lab(text, 'pwSlotV')
        if color:
            lbl.setStyleSheet(f'QLabel#pwSlotV {{ color:{color}; }}')
        return lbl

    def _slot_profile(self):
        from gui import main_window as mw
        dev = mw._progress_rate(self._person)
        if dev is None:
            return 'Dev Rate', [self._slot_val('-')], ''
        if self._ability_stars:
            sw = self._star_row(dev_stars(dev))
            sw.setToolTip(f'Dev Rate {dev} out of 20')
            return 'Dev Rate', [sw], 'How fast they develop'
        return 'Dev Rate', [self._slot_val(str(dev), TIER_HEX[tier(dev)])], 'out of 20'

    def _slot_contract(self):
        return 'Contract until', [self._slot_val(self._contract_until() or '-')], self._club_name()

    def _slot_positions(self):
        R = self._ratings
        best = self._best_pos(R)
        v = R[best]
        return 'Best position', [self._badge(best, True), self._slot_val(str(v), TIER_HEX[tier(v)])], word(v)

    def _slot_history(self):
        return 'Apps · Goals', [self._pend_chip()], 'Not in the save yet'

    def _best_pos(self, R):
        """Highest rating; ties -> the listed (primary) position, then mockup list order."""
        return sorted(POS_DISPLAY, key=lambda q: (-R[q], q != self._pos, POS_DISPLAY.index(q)))[0]

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
        hb.setContentsMargins(0, 0, 0, 0)
        hb.setSpacing(6)
        if h is None or w is None:
            hb.addWidget(_lab('Height / weight', 'pwHw'))
            hb.addWidget(self._pend_chip(), 0, Qt.AlignmentFlag.AlignVCenter)
            if not self._show_pending():
                host.setVisible(False)
        else:
            hb.addWidget(_lab(f'{h} cm · {w} kg', 'pwHw'))
        return host

    # -- action strip (persistent) -----------------------------------------------------------------
    def _action_strip(self):
        strip = QFrame()
        strip.setObjectName('actionStrip')
        strip.setFixedHeight(52)
        h = QHBoxLayout(strip)
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(8)
        h.addStretch(1)
        close = QPushButton('Close')
        close.setObjectName('pwGhost')
        close.setFixedHeight(32)
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(lambda checked=False: self.reject())
        h.addWidget(close)
        tips = 'Open from Squads to patch'
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
            h.addWidget(btn)
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
        sl.setMinimumWidth(164)
        h.addWidget(sl)
        return strip

    # -- positions tab -------------------------------------------------------------------------------
    def _tile_label(self, v, t, width=None):
        lbl = QLabel(str(v))
        lbl.setFixedHeight(20)
        lbl.setMinimumWidth(width or 30)
        if width:
            lbl.setFixedWidth(width)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f'QLabel {{ background:{_rgba(t)}; color:{TIER_HEX[t]}; border-radius:3px; '
                          f'font-size:12px; font-weight:bold; padding:0 6px; }}')
        return lbl

    def _positions_list(self):
        R = self._ratings
        seg, _cur, fut = self._seg('Current', 'Future', right_enabled=False, right_tip=_FUTURE_TIP)
        panel, v = self._panel('Positions', seg)
        panel.setFixedWidth(456)
        for i, pos in enumerate(POS_DISPLAY):
            val = R[pos]
            nat = val >= 20
            row = QFrame()
            row.setObjectName('pwRowNat' if nat else 'pwRowAlt' if i % 2 == 0 else 'pwRow')
            row.setFixedHeight(26)
            h = QHBoxLayout(row)
            h.setContentsMargins(12, 0, 12, 0)
            h.setSpacing(8)
            h.addWidget(self._badge(pos, True))
            h.addWidget(_lab(POS_FULL[pos], 'pwPosNameB' if pos == self._pos else 'pwPosName'), 1)
            h.addWidget(self._tile_label(val, tier(val), 34))
            w = _lab(word(val), 'pwWordNat' if nat else 'pwWord')
            w.setFixedWidth(112)
            h.addWidget(w)
            v.addWidget(row)
        raw = self._person.get('raw_attrs') or []
        if len(raw) > 25:
            lf, rf = self._disp(raw[24]), self._disp(raw[25])
            footed = ('Left-footed' if lf > rf else 'Right-footed') if abs(lf - rf) >= 4 else 'Either foot'
            sub = QWidget()
            sub.setFixedHeight(30)
            sh = QHBoxLayout(sub)
            sh.setContentsMargins(12, 0, 12, 0)
            sh.addWidget(_spaced(_lab('FEET', 'pwSubT')))
            sh.addStretch()
            sh.addWidget(_lab(footed, 'pwSubE'))
            v.addSpacing(4)
            v.addWidget(sub)
            for i, (name, val) in enumerate((('Left Foot', lf), ('Right Foot', rf))):
                row = QFrame()
                row.setObjectName('pwRowAlt' if i == 0 else 'pwRow')
                row.setFixedHeight(26)
                h = QHBoxLayout(row)
                h.setContentsMargins(12, 0, 12, 0)
                h.setSpacing(8)
                h.addWidget(_lab(name, 'pwPosName'), 1)
                h.addWidget(self._tile_label(val, tier(val), 34))
                w = _lab(foot_word(val), 'pwWord')
                w.setFixedWidth(112)
                h.addWidget(w)
                v.addWidget(row)
        v.addStretch()
        v.addWidget(self._positions_key())
        return panel

    def _positions_key(self):
        key = QWidget()
        kv = QVBoxLayout(key)
        kv.setContentsMargins(12, 6, 12, 12)
        kv.setSpacing(4)
        lg = QHBoxLayout()
        lg.setSpacing(12)
        for lab, t in (('1–4', 1), ('5–8', 2), ('9–11', 3), ('12–13', 4), ('14–16', 5), ('17–20', 6)):
            sw = QLabel()
            sw.setFixedSize(10, 10)
            sw.setStyleSheet(f'QLabel {{ background:{TIER_HEX[t]}; border-radius:2px; }}')
            lg.addWidget(sw)
            lg.addSpacing(-7)
            lg.addWidget(_lab(lab, 'pwNote'))
        lg.addStretch()
        kv.addLayout(lg)
        txt = _lab('White ring = Natural (20) · bold = listed position<br>'
                   '<span style="color:#FFFFFF">Natural</span> 20 · Accomplished 15–19 · Competent 10–14<br>'
                   'Unconvincing 5–9 · Awkward 2–4 · Ineffective 1', 'pwNote')
        txt.setTextFormat(Qt.TextFormat.RichText)
        kv.addWidget(txt)
        return key

    def _positions_pitch(self):
        f = QFrame()
        f.setObjectName('pwPanel')
        f.setMaximumWidth(444)
        f.setMinimumWidth(300)
        v = QVBoxLayout(f)
        v.setContentsMargins(1, 1, 1, 1)
        v.addWidget(_PitchBig(self._ratings), 1)
        f.setMinimumHeight(440)
        return f

    # attribute grid -----------------------------------------------------------------------------
    def _attr_panel(self):
        right = QWidget()
        rh = QHBoxLayout(right)
        rh.setContentsMargins(0, 0, 0, 0)
        rh.setSpacing(8)
        self._note = _lab('', 'pwNote')
        rh.addWidget(self._note)
        seg, self._seg_cur, self._seg_pot = self._seg('Current', 'Potential')
        self._seg_group = seg._grp
        p = self._person
        _enabled, tip = _pot.availability(p.get('ca'), p.get('pa'), person_age(p))
        self._pot_note = tip  # always selectable; the note explains when potential is moot
        if tip:
            self._seg_pot.setToolTip(tip)
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
        if getattr(self, '_rec_slot', None) is not None:
            oldp = self._rec_slot.takeAt(0).widget()
            self._rec_slot.addWidget(self._rec_panel())
            oldp.hide()
            oldp.deleteLater()
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
        return self._tile_label(v, tier(21 - v if lower_better else v))

    # rail (personality + traits) ---------------------------------------------------------------------
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
        self._rec_slot = QVBoxLayout()
        self._rec_slot.setContentsMargins(0, 0, 0, 0)
        self._rec_slot.addWidget(self._rec_panel())
        v.addLayout(self._rec_slot)
        v.addStretch()
        return w

    def _rec_panel(self):
        """Top trait recommendations (fm_editor/traitrec.py; source GuideToFM). Follows the Current | Potential
        toggle. Owned traits are ticked; a quiet line when nothing reaches the Settings threshold."""
        thr = _settings.load()['trait_threshold']
        raw = self._person.get('raw_attrs') or []
        panel, v = self._panel('Recommended traits')
        panel.setToolTip('Average of the attributes behind each trait (source: GuideToFM).\n'
                         f'Needs an average of {thr}+ (Settings > Trait recommender threshold).')
        note = ''
        if self._is_gk or len(raw) < 54:
            note = 'Not applicable to goalkeepers.' if self._is_gk else 'No attribute data.'
            recs = []
        else:
            attrs = ([_pot.display_value(x) for x in self._projection().proj] if self._pot_on
                     else _tr.attrs_from_raw(raw))
            have = trait_ids(self._person.get('trait_mask') or 0)
            recs = [r for r in _tr.recommend(attrs, thr, have) if r.met or r.has][:5]
            if not recs:
                note = f'No trait reaches an average of {thr}.'
        for i, r in enumerate(recs):
            row = QFrame()
            row.setObjectName('pwRowAlt' if i % 2 else 'pwRow')
            h = QHBoxLayout(row)
            h.setContentsMargins(12, 2, 12, 2)
            h.setSpacing(6)
            n = _lab(('\u2713 ' if r.has else '') + r.name, 'pwKvL' if r.has else 'pwTrait')
            n.setWordWrap(True)
            tip = r.desc + ('\nPlayer already has this trait.' if r.has else '')
            if r.missing:
                tip += '\nBelow ' + str(thr) + ': ' + ', '.join(f'{a} {x}' for a, x in r.missing)
            n.setToolTip(tip)
            h.addWidget(n, 1)
            sc = _lab(f'{r.score:.1f}', 'pwKvR', Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            sc.setFixedWidth(30)
            sc.setStyleSheet(f'QLabel#pwKvR {{ color:{TIER_HEX[tier(round(r.score))]}; font-weight:bold; }}')
            h.addWidget(sc)
            v.addWidget(row)
        if note:
            v.addWidget(_lab(note, 'pwNote'))
            v.itemAt(v.count() - 1).widget().setContentsMargins(12, 6, 12, 6)
            v.itemAt(v.count() - 1).widget().setWordWrap(True)
        v.addSpacing(4)
        return panel

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

    def _transfer_panel(self):
        d = self._data
        panel, v = self._panel('Transfer')
        rows = []
        for label, key in (('Market value', 'value'), ('Asking price', 'asking_price'),
                           ('Transfer / loan status', 'transfer_status')):
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
