"""Painted widgets of the player window Profile (mockups/player-window.html, Profile layout C): the Attribute groups
radar and the Footedness soles. Every number below is copied from the mockup's radar() / feet() (see the comment there);
geometry is in the mockup's SVG pixel space (origin = top-left of the widget)."""
import math
import re

from PyQt6.QtCore import QEvent, Qt, QPointF, QRectF
from PyQt6.QtGui import (QBrush, QColor, QFont, QFontMetricsF, QLinearGradient, QPainter, QPainterPath, QPen,
                         QPolygonF)
from PyQt6.QtWidgets import QToolTip, QWidget

INK = QColor('#14151A')       # dot / number ink on a solid fill
SEC = QColor('#8B96A8')       # text_secondary


def _a(x):
    """CSS alpha 0..1 -> QColor alpha (round half up, as the mockup comments list: .18 -> 46, .92 -> 235)."""
    return int(x * 255 + 0.5)


def _font(px, bold=False, spacing=0.0):
    f = QFont()
    f.setPixelSize(px)
    f.setBold(bold)
    if spacing:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
    return f


def _draw_centered(p, x, baseline, text, font, color):
    """SVG <text text-anchor=middle> at (x, baseline) incl. the trailing letter-spacing Chrome adds."""
    p.setFont(font)
    p.setPen(color)
    w = QFontMetricsF(font).horizontalAdvance(text)
    p.drawText(QPointF(x - w / 2, baseline), text)


# -- Attribute groups radar: the app's OWN six scouting groups (NOT the game's Technical/Mental/...). The axis tables live in
# fm_editor/radar_axes.py (ONE place to edit; OVERVIEW = this radar, DETAILED = Compare page); re-exported under the old names.
from fm_editor.radar_axes import OVERVIEW_GK as RADAR_GK, OVERVIEW_OUT as RADAR_OUT, axis_values  # noqa: E402


def radar_axes(values, gk):
    """values {attribute name: shown 1-20 value} -> [(axis name, mean 1-20, tooltip text)] in wheel order (six axes)."""
    return axis_values(values, gk, 'overview')


class RadarWidget(QWidget):
    """'Attribute groups' radar (mockup radar()): svg 204 x 176, centre (102, 88), R 40, six axes pointy-top from -90 deg clockwise.
    4 ring polygons, spokes, data polygon, tier-coloured dots, two-line labels (NAME 9/700 caps + mean 12/700 tier colour) anchored on
    the outer vertex. Tooltip per axis (dot + label rect, hit-tested in event(): six rects, cheap)."""
    W, H, CX, CY, R = 204, 176, 102, 88, 40

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.W, self.H)
        self.setMouseTracking(True)  # custom ToolTip events only fire on a widget that receives hover moves
        self._ax = []          # [(label, value 1-20 float, QColor, tooltip)]
        self._rects = []

    def set_axes(self, axes):
        self._ax = list(axes)
        self._rects = self._layout()
        self.update()

    def _pt(self, i, k):
        t = math.radians(-90 + i * 60)
        return QPointF(self.CX + math.cos(t) * self.R * k, self.CY + math.sin(t) * self.R * k)

    def _layout(self):
        """Per axis: (text x anchor, 'mid'|'start'|'end', name baseline, mean baseline, hit rect). Mockup: top name y_v-20 / mean y_v-7,
        bottom y_v+13 / y_v+26, sides (x_v +/- 5) y_v-1 / y_v+12."""
        lab_f = _font(9, True)
        fm = QFontMetricsF(lab_f)
        out = []
        for i, (name, v, _c, _t) in enumerate(self._ax):
            q = self._pt(i, 1)
            side = 'mid' if i % 3 == 0 else ('start' if i < 3 else 'end')
            x = q.x() + (0 if side == 'mid' else 5 if side == 'start' else -5)
            y1 = q.y() - 20 if i == 0 else q.y() + 13 if i == 3 else q.y() - 1
            w = max(fm.horizontalAdvance(name.upper()), 22)
            left = x - w / 2 if side == 'mid' else x if side == 'start' else x - w
            c = self._pt(i, v / 20)
            r = QRectF(left, y1 - 9, w, 25).united(QRectF(c.x() - 4, c.y() - 4, 8, 8))
            out.append((x, side, y1, y1 + 13, r))
        return out

    def event(self, e):
        if e.type() == QEvent.Type.ToolTip:
            for (_x, _s, _a, _b, r), ax in zip(self._rects, self._ax):
                if r.contains(QPointF(e.pos())):
                    QToolTip.showText(e.globalPos(), ax[3], self)
                    return True
            QToolTip.hideText()
            e.ignore()
            return True
        return super().event(e)

    def paintEvent(self, _e):
        ax = self._ax
        n = len(ax)
        if not n:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for k in (.25, .5, .75, 1):
            p.setPen(QPen(QColor(255, 255, 255, _a(.22 if k == 1 else .10)), 1))
            p.drawPolygon(QPolygonF([self._pt(i, k) for i in range(n)]))
        p.setPen(QPen(QColor(255, 255, 255, _a(.10)), 1))
        for i in range(n):
            p.drawLine(QPointF(self.CX, self.CY), self._pt(i, 1))
        pen = QPen(QColor('#735CE4'), 1.5)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(QColor(115, 92, 228, _a(.30)))
        p.drawPolygon(QPolygonF([self._pt(i, a[1] / 20) for i, a in enumerate(ax)]))
        lab_f, val_f = _font(9, True), _font(12, True)
        for i, ((name, v, col, _t), (x, side, y1, y2, _r)) in enumerate(zip(ax, self._rects)):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(col)
            p.drawEllipse(self._pt(i, v / 20), 3.5, 3.5)
            for text, font, color, y in ((name.upper(), lab_f, SEC, y1), (f'{v:.1f}', val_f, col, y2)):
                p.setFont(font)
                p.setPen(color)
                w = QFontMetricsF(font).horizontalAdvance(text)
                p.drawText(QPointF(x - w / 2 if side == 'mid' else x if side == 'start' else x - w, y), text)


# -- Footedness -----------------------------------------------------------------------------------------------
# Right foot in a 64 x 128 box (big toe on the left); the left foot is the same path mirrored. (mockup FOOT_SOLE / FOOT_TOES)
FOOT_SOLE = ('M30,126 C18,126 12,117 13,105 C14,92 21,85 21,72 C21,63 8,58 7,46 C6,38 10,33 18,32 L52,34 C58,35 61,40 60,46 '
             'C59,58 53,68 49,80 C47,91 52,104 47,115 C44,122 38,126 30,126 Z')
FOOT_TOES = [(17, 20, 8.5, 11.5), (32, 13, 6, 7.5), (43, 17, 5.5, 7), (52, 24, 5, 6.5), (58, 32, 4.3, 5.6)]
FOOT_STOPS = [(0, (232, 105, 106)), (.35, (224, 151, 60)), (.65, (234, 217, 92)), (1, (82, 194, 135))]


def foot_rgb(v):
    """Continuous red -> amber -> yellow -> green for a 1-20 rating (mockup footRGB)."""
    t = (max(1, min(20, v)) - 1) / 19
    a, b = FOOT_STOPS[0], FOOT_STOPS[3]
    for i in range(3):
        if FOOT_STOPS[i][0] <= t <= FOOT_STOPS[i + 1][0]:
            a, b = FOOT_STOPS[i], FOOT_STOPS[i + 1]
    u = (t - a[0]) / ((b[0] - a[0]) or 1)
    return tuple(int(c + (b[1][i] - c) * u + 0.5) for i, c in enumerate(a[1]))


def _foot_paths():
    """[sole, toe1..toe5] as QPainterPaths in the 64 x 128 box. Parses the mockup's SVG path (M / C / L / Z)."""
    sole = QPainterPath()
    tok = re.findall(r'[MLCZ]|-?\d+\.?\d*', FOOT_SOLE)
    i = 0
    while i < len(tok):
        c = tok[i]
        i += 1
        if c == 'M':
            sole.moveTo(float(tok[i]), float(tok[i + 1])); i += 2
        elif c == 'L':
            sole.lineTo(float(tok[i]), float(tok[i + 1])); i += 2
        elif c == 'C':
            f = [float(x) for x in tok[i:i + 6]]
            sole.cubicTo(f[0], f[1], f[2], f[3], f[4], f[5]); i += 6
        elif c == 'Z':
            sole.closeSubpath()
    out = [sole]
    for cx, cy, rx, ry in FOOT_TOES:
        e = QPainterPath()
        e.addEllipse(QPointF(cx, cy), rx, ry)
        out.append(e)
    return out


class FeetWidget(QWidget):
    """'Footedness' svg 204 x 184: two top-down soles (left foot mirrored) coloured by rating, number centred, LEFT / RIGHT
    labels (white dot before the stronger foot when the ratings differ by 3+), 1-20 colour legend bar."""
    W, H = 204, 184

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.W, self.H)
        self._paths = _foot_paths()
        self._l = self._r = None

    def set_feet(self, left, right):
        self._l, self._r = left, right
        self.update()

    def paintEvent(self, _e):
        if self._l is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        L, Rr = self._l, self._r
        pref = (0 if L > Rr else 1) if abs(L - Rr) >= 3 else -1
        num_f, lab_f = _font(20, True), _font(10, True, .8)
        for i, (v, x) in enumerate(((L, 19), (Rr, 121))):
            c = foot_rgb(v)
            edge = tuple(int(k + (255 - k) * .35 + 0.5) for k in c)
            p.save()
            if i == 0:
                p.translate(x + 64, 8)
                p.scale(-1, 1)
            else:
                p.translate(x, 8)
            glow = QPen(QColor(*c, _a(.18)), 7)
            glow.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(glow)
            for path in self._paths:
                p.drawPath(path)
            body = QPen(QColor(*edge), 1.5)
            body.setJoinStyle(Qt.PenJoinStyle.SvgMiterJoin)
            p.setBrush(QColor(*c, _a(.92)))
            p.setPen(body)
            for path in self._paths:
                p.drawPath(path)
            p.restore()
            # number centred (dominant-baseline central): glyph box centred on y = 8 + 62
            p.setFont(num_f)
            p.setPen(INK)
            fm = QFontMetricsF(num_f)
            p.drawText(QPointF(x + 32 - fm.horizontalAdvance(str(v)) / 2, 70 + (fm.ascent() - fm.descent()) / 2), str(v))
            lab = 'LEFT' if i == 0 else 'RIGHT'
            lx = x + 32
            if pref == i:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor('#FFFFFF'))
                p.drawEllipse(QPointF(lx - (19 if i == 0 else 22), 148), 3, 3)
            _draw_centered(p, lx + (5 if pref == i else 0), 152, lab, lab_f, SEC)
        g = QLinearGradient(18, 0, 186, 0)
        for o, c in FOOT_STOPS:
            g.setColorAt(o, QColor(*c))
        p.fillRect(QRectF(18, 162, 168, 6), QBrush(g))
        f10 = _font(10)
        p.setFont(f10)
        p.setPen(SEC)
        p.drawText(QPointF(18, 181), '1')
        p.drawText(QPointF(186 - QFontMetricsF(f10).horizontalAdvance('20'), 181), '20')


# -- Compare page: overlaid radar of two players, n axes (mockups/compare-players.html radarAB) ------------------------
A_RGB, B_RGB = (82, 176, 255), (215, 124, 255)     # identity colours: A sky blue #52B0FF, B orchid #D77CFF


class CompareRadar(QWidget):
    """Two overlaid polygons on n axes (6 Overview, 12 / 11 Detailed): svg 358 x 336, centre (179, 170), R 106, vertex i at
    -90 + 360 i / n degrees. Ring 10 / 20 labels sit between vertices 0-1 (n <= 8) or 1-2. B is drawn first (dashed outline, diamond
    markers), then A (solid, circle markers). Labels = NAME 9/700 caps + 'A / B' 12/700 in the identity colours; the anchor comes
    from cos: |cos| < .25 middle (top baseline y_v-24, bottom y_v+14), cos > 0 start (+7), else end (-7), others y_v-2.
    Tooltip per axis (label + markers, hit-tested in event())."""
    W, H, CX, CY, R = 358, 336, 179, 170, 106

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.W, self.H)
        self.setMouseTracking(True)
        self._ax = []        # [(name, a value, b value, tooltip)]
        self._lay = []

    def set_axes(self, axes):
        self._ax = list(axes)
        self._lay = self._layout()
        self.update()

    def _pt(self, i, k, n=None):
        t = math.radians(-90 + i * 360 / (n or len(self._ax)))
        return QPointF(self.CX + math.cos(t) * self.R * k, self.CY + math.sin(t) * self.R * k)

    def _layout(self):
        n = len(self._ax)
        lab_f = _font(9, True)
        fm = QFontMetricsF(lab_f)
        out = []
        for i, (name, av, bv, _t) in enumerate(self._ax):
            q = self._pt(i, 1)
            c = math.cos(math.radians(-90 + i * 360 / n))
            s = math.sin(math.radians(-90 + i * 360 / n))
            side = 'mid' if abs(c) < .25 else 'start' if c > 0 else 'end'
            x = q.x() + (0 if side == 'mid' else 7 if side == 'start' else -7)
            y1 = q.y() - 24 if s < -.9 else q.y() + 14 if s > .9 else q.y() - 2
            w = max(fm.horizontalAdvance(name.upper()), fm.horizontalAdvance(f'{av:.1f} / {bv:.1f}') + 14)
            left = x - w / 2 if side == 'mid' else x if side == 'start' else x - w
            r = QRectF(left, y1 - 9, w, 25)
            for v in (av, bv):
                m = self._pt(i, v / 20)
                r = r.united(QRectF(m.x() - 4, m.y() - 4, 8, 8))
            out.append((x, side, y1, r))
        return out

    def event(self, e):
        if e.type() == QEvent.Type.ToolTip:
            for (_x, _s, _y, r), ax in zip(self._lay, self._ax):
                if r.contains(QPointF(e.pos())):
                    QToolTip.showText(e.globalPos(), ax[3], self)
                    return True
            QToolTip.hideText()
            e.ignore()
            return True
        return super().event(e)

    def paintEvent(self, _e):
        ax = self._ax
        n = len(ax)
        if not n:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for k in (.25, .5, .75, 1):
            p.setPen(QPen(QColor(255, 255, 255, _a(.22 if k == 1 else .10)), 1))
            p.drawPolygon(QPolygonF([self._pt(i, k) for i in range(n)]))
        p.setPen(QPen(QColor(255, 255, 255, _a(.10)), 1))
        for i in range(n):
            p.drawLine(QPointF(self.CX, self.CY), self._pt(i, 1))
        sa = math.radians(-90 + (1.5 if n > 8 else .5) * 360 / n)
        sf = _font(9)
        p.setFont(sf)
        p.setPen(SEC)
        for v in (10, 20):
            x, y = self.CX + math.cos(sa) * self.R * v / 20, self.CY + math.sin(sa) * self.R * v / 20
            p.drawText(QPointF(x - 3 - QFontMetricsF(sf).horizontalAdvance(str(v)), y - 2), str(v))
        # B first (dashed), then A
        for idx, rgb, fill, dash in ((2, B_RGB, .18, True), (1, A_RGB, .22, False)):
            pen = QPen(QColor(*rgb), 1.75)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            if dash:
                pen.setDashPattern([6 / 1.75, 3 / 1.75])
            p.setPen(pen)
            p.setBrush(QColor(*rgb, _a(fill)))
            p.drawPolygon(QPolygonF([self._pt(i, a[idx] / 20) for i, a in enumerate(ax)]))
        ring = QPen(QColor('#14151A'), 1.5)
        for i, a in enumerate(ax):
            p.setPen(ring)
            p.setBrush(QColor(*A_RGB))
            p.drawEllipse(self._pt(i, a[1] / 20), 4, 4)
            c = self._pt(i, a[2] / 20)
            p.setBrush(QColor(*B_RGB))
            p.save()
            p.translate(c)
            p.rotate(45)
            p.drawRect(QRectF(-3.6, -3.6, 7.2, 7.2))
            p.restore()
        name_f, val_f = _font(9, True), _font(12, True)
        for (name, av, bv, _t), (x, side, y1, _r) in zip(ax, self._lay):
            runs = ((f'{av:.1f}', QColor(*A_RGB), val_f), (' / ', SEC, _font(12)), (f'{bv:.1f}', QColor(*B_RGB), val_f))
            nm = name.upper()
            nw = QFontMetricsF(name_f).horizontalAdvance(nm)
            total = sum(QFontMetricsF(f).horizontalAdvance(t) for t, _c, f in runs)
            for text, font, color, y, w in ((nm, name_f, SEC, y1, nw), (None, None, None, y1 + 14, total)):
                x0 = x - w / 2 if side == 'mid' else x if side == 'start' else x - w
                if text is not None:
                    p.setFont(font)
                    p.setPen(color)
                    p.drawText(QPointF(x0, y), text)
                else:
                    for t, c, f in runs:
                        p.setFont(f)
                        p.setPen(c)
                        p.drawText(QPointF(x0, y), t)
                        x0 += QFontMetricsF(f).horizontalAdvance(t)
