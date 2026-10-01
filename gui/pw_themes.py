"""Player window texture themes (QPainter port of the THEMES registry in mockups/player-window.html).

ONE registry, THEMES: add / remove / change a theme = one entry. Each Theme has a recipe per surface
('header', 'strip', 'bar') = fn(p, w, h) painting the PADDING box (0,0,w,h) of the panel (the 1px QSS
border is drawn on top by the frame; panels keep `border:1px solid`), layers bottom first.
Noise / dust tiles are built once, lazily (_tile). No Qt widgets are needed to use the recipes.

WIRING (gui/player_window.py), see also the docstrings below:
  1. Panels: header panel = ThemedFrame, objectName 'pwHeader'; left tab strip = ThemedFrame 'pwTabStrip';
     bottom bar = ThemedFrame 'actionStrip'.  QSS must make them transparent (the recipe paints the
     surface colour itself):  THEMED_QSS  (below) is that QSS, append it inside the QDialog#playerWindow block.
  2. After building the layout call apply_active_theme(self) once (sets each ThemedFrame's surface and
     reads settings.load()['player_theme']).
  3. Primary-button halo: bar.halo_for = <the 'Add to Shortlist' QPushButton> (a direct child of the bar).
  4. Active tab: make the tab buttons ActiveTabButton (checkable QPushButton); QSS for the checked tab
     must have `background:transparent` (the class paints selection_bg + glow itself).
"""
import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (QBrush, QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
                         QRadialGradient)
from PyQt6.QtWidgets import QFrame, QPushButton

from fm_editor import settings as _settings

SURFACE = QColor('#1A2226')
SEL = QColor('#2A1B4A')
BORDER = '#343740'
BORDER2 = '#454A58'
RADIUS = 3


def _c(*rgba):
    return QColor(*rgba)


# ---- tiles (built once) ------------------------------------------------------------------------
_TILES = {}


def _tile(kind):
    """128x128 seeded noise tile, same LCG as the mockup (mkTile). 'fine' = grain, 'dust' = sparse specks."""
    t = _TILES.get(kind)
    if t is None:
        img = QImage(128, 128, QImage.Format.Format_ARGB32)
        img.fill(0)
        r = 1234567

        def rnd():
            nonlocal r
            r = (r * 1664525 + 1013904223) & 0xFFFFFFFF
            return r / 4294967296

        for y in range(128):
            for x in range(128):
                if kind == 'fine':
                    v = rnd()
                    a = round(rnd() * (14 if v < .5 else 9) * (STEEL_ALPHA if kind == 'fine' else 1))
                    img.setPixelColor(x, y, QColor(0, 0, 0, a) if v < .5 else QColor(255, 255, 255, a))
                elif rnd() < .008:
                    img.setPixelColor(x, y, QColor(200, 215, 255, 30 + round(rnd() * 30)))
        t = _TILES[kind] = QPixmap.fromImage(img)
    return t


def _vgrad(y0, y1, *stops):
    g = QLinearGradient(0, y0, 0, y1)
    for pos, col in stops:
        g.setColorAt(pos, col)
    return g


def _fill(p, w, h, brush, y=0, hh=None):
    p.fillRect(QRectF(-1, y if y else -1, w + 2, (h - y if hh is None else hh) + (0 if y else 2)), brush)


def _ellipse_glow(p, w, h, cx, cy, rx, ry, stops):
    """Elliptical radial gradient (CSS `radial-gradient(ellipse rx ry at cx cy)`), painted over the whole rect."""
    g = QRadialGradient(0, 0, rx)
    for pos, col in stops:
        g.setColorAt(pos, col)
    k = ry / rx
    p.save()
    p.translate(cx, cy)
    p.scale(1, k)
    p.fillRect(QRectF(-1 - cx, (-1 - cy) / k, w + 2, (h + 2) / k), QBrush(g))
    p.restore()


# ---- STEEL --------------------------------------------------------------------------------------
STEEL_ALPHA = 0.75  # ONE knob: multiplies the alpha of every translucent Steel layer (grain, pinstripe, shadow, sheen, tab glow,
#                    halo); the opaque base gradient and the selected-tab fill are untouched. 1.0 = original look. Mirrors
#                    STEEL_ALPHA in mockups/player-window.html.


def _sa(a):
    """Scale an 0-255 alpha by STEEL_ALPHA."""
    return int(a * STEEL_ALPHA + .5)


def _steel(sheen_h=14):
    def paint(p, w, h):
        _fill(p, w, h, _vgrad(0, h, (0, _c(0x22, 0x2D, 0x32)), (.55, _c(0x1A, 0x22, 0x26)), (1, _c(0x16, 0x1D, 0x21))))
        p.drawTiledPixmap(QRectF(-1, -1, w + 2, h + 2).toRect(), _tile('fine'))
        # pinstripe: repeating-linear-gradient(135deg, white .04 0 1px, clear 1px 3px) -> period 3 along the diagonal
        s = 3 / math.sqrt(2)
        g = QLinearGradient(0, 0, s, s)
        g.setSpread(QLinearGradient.Spread.RepeatSpread)
        g.setColorAt(0, _c(255, 255, 255, _sa(10)))
        g.setColorAt(1 / 3 - .001, _c(255, 255, 255, _sa(10)))
        g.setColorAt(1 / 3, _c(255, 255, 255, 0))
        g.setColorAt(1, _c(255, 255, 255, 0))
        _fill(p, w, h, g)
        _fill(p, w, h, _vgrad(h - 12, h, (0, _c(0, 0, 0, 0)), (1, _c(0, 0, 0, _sa(77)))), h - 12, 12)
        f = 1 / sheen_h
        p.fillRect(QRectF(-1, 0, w + 2, sheen_h), _vgrad(0, sheen_h, (0, _c(255, 255, 255, _sa(23))), (f, _c(255, 255, 255, _sa(23))),
                                                         (f, _c(255, 255, 255, _sa(9))), (1, _c(255, 255, 255, 0))))
    return paint


def _steel_tab_glow(p, rect):
    """Active tab row: selected fill + violet glow (left->.75w, and bottom 18px)."""
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    p.fillRect(rect, SEL)
    g = QLinearGradient(x, 0, x + w * .75, 0)
    g.setColorAt(0, _c(115, 92, 228, _sa(51)))
    g.setColorAt(1, _c(115, 92, 228, 0))
    p.fillRect(QRectF(x, y, w, h), g)
    p.fillRect(QRectF(x, y + h - 18, w, 18), _vgrad(y + h, y + h - 18, (0, _c(115, 92, 228, _sa(87))), (1, _c(115, 92, 228, 0))))


def _steel_halo(p, btn):
    """Elliptical halo behind the primary button; btn = its rect in the bar's coordinates."""
    c = btn.center()
    rx, ry = btn.width() / 2 + 18, btn.height() / 2 + 12
    g = QRadialGradient(0, 0, rx)
    g.setColorAt(0, _c(115, 92, 228, _sa(166)))
    g.setColorAt(.55, _c(115, 92, 228, _sa(66)))
    g.setColorAt(1, _c(115, 92, 228, 0))
    p.save()
    p.translate(c)
    p.scale(1, ry / rx)
    p.fillRect(QRectF(-rx, -rx, 2 * rx, 2 * rx), g)
    p.restore()


# ---- PITCH --------------------------------------------------------------------------------------
def _stripes(p, w, h, period, on, off):
    half = period // 2
    for x in range(0, w + period, period):
        p.fillRect(QRectF(x, -1, half, h + 2), on)
        p.fillRect(QRectF(x + half, -1, half, h + 2), off)


def _pitch_header(p, w, h):
    _fill(p, w, h, SURFACE)
    _stripes(p, w, h, 80, _c(29, 66, 41, 56), _c(21, 48, 31, 26))
    cx = w - 67.5
    p.setPen(QPen(_c(255, 255, 255, 41), 1))
    p.drawEllipse(QPointF(cx, h / 2), 46, 46)
    p.drawLine(QPointF(cx, 0), QPointF(cx, h))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(_c(255, 255, 255, 36))
    p.drawEllipse(QPointF(cx, h / 2), 2, 2)
    p.setBrush(Qt.BrushStyle.NoBrush)
    g = QLinearGradient(0, 0, w, 0)
    g.setColorAt(0, _c(26, 34, 38, 0))
    g.setColorAt(.40, _c(26, 34, 38, 0))
    g.setColorAt(.78, _c(26, 34, 38, 140))
    g.setColorAt(1, _c(26, 34, 38, 0))
    _fill(p, w, h, g)


def _pitch_tabs(p, w, h):
    _fill(p, w, h, SURFACE)
    _stripes(p, w, h, 44, _c(29, 66, 41, 61), _c(21, 48, 31, 26))


def _pitch_bar(p, w, h):
    _fill(p, w, h, SURFACE)
    _stripes(p, w, h, 80, _c(29, 66, 41, 51), _c(21, 48, 31, 20))
    g = _vgrad(0, 12, (0, _c(82, 194, 135, 46)), (.5, _c(82, 194, 135, 13)), (1, _c(82, 194, 135, 0)))
    p.fillRect(QRectF(-1, 0, w + 2, 12), g)


def _plain(p, w, h):
    _fill(p, w, h, SURFACE)


# ---- FLOODLIT -----------------------------------------------------------------------------------
def _glass(p, w, line_a, sheen_a, hh):
    p.fillRect(QRectF(-1, 0, w + 2, 1), _c(255, 255, 255, line_a))
    p.fillRect(QRectF(-1, 1, w + 2, hh - 1), _vgrad(1, hh, (0, _c(255, 255, 255, sheen_a)), (1, _c(255, 255, 255, 0))))


def _bloom(p, w, h, rx, ry, a_stops):
    _ellipse_glow(p, w, h, w, 0, rx, ry, [(pos, _c(205, 222, 255, a)) for pos, a in a_stops])


def _flood_header(p, w, h):
    _fill(p, w, h, _vgrad(0, h, (0, _c(0x1F, 0x2A, 0x3C)), (.55, _c(0x1A, 0x22, 0x30)), (1, _c(0x17, 0x1C, 0x23))))
    # rays: 5deg wedge every 12deg, CSS 'from 195deg' (clockwise from up) at the top right corner
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(_c(205, 222, 255, 15))
    r = math.hypot(w, h) + 10
    box = QRectF(w - r, -r, 2 * r, 2 * r)
    for k in range(30):
        a = 195 + 12 * k
        p.drawPie(box, round((90 - (a + 5)) * 16), 5 * 16)
    p.setBrush(Qt.BrushStyle.NoBrush)
    _ellipse_glow(p, w, h, w, 0, 620, 170, [(0, _c(26, 34, 48, 0)), (1, _c(26, 34, 48, 235))])
    _bloom(p, w, h, 300, 140, [(0, 56), (.45, 20), (1, 0)])
    p.drawTiledPixmap(QRectF(-1, -1, w + 2, h + 2).toRect(), _tile('dust'))
    _glass(p, w, 41, 13, 22)


def _flood_tabs(p, w, h):
    _fill(p, w, h, _vgrad(0, h, (0, _c(0x1C, 0x26, 0x39)), (.5, _c(0x18, 0x1F, 0x2B)), (1, _c(0x16, 0x19, 0x1F))))
    _bloom(p, w, h, 230, 300, [(0, 26), (1, 0)])
    p.drawTiledPixmap(QRectF(-1, -1, w + 2, h + 2).toRect(), _tile('dust'))
    _glass(p, w, 36, 10, 18)


def _flood_bar(p, w, h):
    _fill(p, w, h, _vgrad(0, h, (0, _c(0x1A, 0x22, 0x30)), (1, _c(0x16, 0x1B, 0x22))))
    _bloom(p, w, h, 360, 70, [(0, 26), (1, 0)])
    p.drawTiledPixmap(QRectF(-1, -1, w + 2, h + 2).toRect(), _tile('dust'))
    _glass(p, w, 36, 10, 14)


# ---- REGISTRY (Settings lists these, in this order; first = default) ------------------------------
class Theme:
    def __init__(self, name, header, strip, bar, bar_border=BORDER, tab_glow=None, halo=None):
        self.name, self.recipes = name, {'header': header, 'strip': strip, 'bar': bar}
        self.bar_border, self.tab_glow, self.halo = QColor(bar_border), tab_glow, halo


THEMES = {
    'steel': Theme('Steel', _steel(), _steel(), _steel(), BORDER2, _steel_tab_glow, _steel_halo),
    'pitch': Theme('Pitch lines', _pitch_header, _pitch_tabs, _pitch_bar, '#8C52C287'),
    'floodlit': Theme('Floodlit', _flood_header, _flood_tabs, _flood_bar),
    'plain': Theme('Plain', _plain, _plain, _plain),
}
DEFAULT_THEME = 'steel'


def theme_for(tid):
    return THEMES.get(tid) or THEMES[DEFAULT_THEME]


def active_theme():
    """Theme chosen in Settings (settings.load()['player_theme']); unknown id -> default. Read when a window opens."""
    return theme_for(_settings.load().get('player_theme'))


THEMED_QSS = ('QFrame#pwHeader, QFrame#pwTabStrip, QFrame#actionStrip { background:transparent; }')


# ---- widgets ------------------------------------------------------------------------------------
class ThemedFrame(QFrame):
    """Paints the active theme's recipe for `surface` ('header'|'strip'|'bar') before its children.
    QSS keeps the 1px border (bar: border-top only; its colour is repainted by the theme)."""

    def __init__(self, surface='header', parent=None, theme=None):
        super().__init__(parent)
        self.surface, self.theme, self.halo_for = surface, theme or active_theme(), None

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bar = self.surface == 'bar'
        ox, oy = (0, 1) if bar else (1, 1)  # padding box (QSS border 1px; bar: top only)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, w, h), RADIUS, RADIUS) if not bar else clip.addRect(QRectF(0, 0, w, h))
        p.setClipPath(clip)
        p.save()
        p.translate(ox, oy)
        self.theme.recipes[self.surface](p, w - 2 * ox, h - oy - (0 if bar else 1))
        if bar and self.theme.halo and self.halo_for is not None and not self.halo_for.isHidden():
            r = self.halo_for.geometry()
            self.theme.halo(p, QRectF(r.x() - ox, r.y() - oy, r.width(), r.height()))
        p.restore()
        p.end()
        super().paintEvent(e)
        if bar:  # theme colours the top line
            p = QPainter(self)
            p.fillRect(QRectF(0, 0, w, 1), self.theme.bar_border)
            p.end()


class ActiveTabButton(QPushButton):
    """Tab row: when checked paints selection_bg (+ the theme's glow) before the QSS/text."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.theme = active_theme()

    def paintEvent(self, e):
        if self.isChecked():
            p = QPainter(self)
            r = QRectF(self.rect())
            (self.theme.tab_glow or (lambda q, rr: q.fillRect(rr, SEL)))(p, r)
            p.end()
        super().paintEvent(e)


def apply_active_theme(root):
    """Give every ThemedFrame under `root` (found by objectName) its surface and the active theme."""
    th = active_theme()
    for name, surface in (('pwHeader', 'header'), ('pwTabStrip', 'strip'), ('actionStrip', 'bar')):
        for w in root.findChildren(QFrame, name):
            if isinstance(w, ThemedFrame):
                w.surface, w.theme = surface, th
                w.update()
    for b in root.findChildren(ActiveTabButton):
        b.theme = th
        b.update()
