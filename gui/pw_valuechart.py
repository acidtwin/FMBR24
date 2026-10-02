"""Value by age chart for the player window's Contract & Transfer tab (mockups/player-window.html, 'VALUE BY AGE CHART').

ValueChart paints one fm_editor.valuecurve.ValueCurve: money grid, round GBP ticks, the 25-75% band, the dashed
'At full potential' line, the 'Expected' line, the Now dot + label, the contract-end marker, end labels, a hover
guide + bubble per age column, and an empty state. ChartLegend is the header legend. Every number below is the
mockup's (plot margins L66 T36 R60 B34 stay constant when the widget resizes). Mouse tracking is REQUIRED for hover.
"""
import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QSizePolicy, QWidget

L, T, R, B = 66, 36, 60, 34
YEL, GRN, ORG = QColor(234, 217, 92), QColor(82, 194, 135), QColor(224, 151, 60)
TX2, WHITE, RING = QColor('#8B96A8'), QColor('#FFFFFF'), QColor('#14151A')
GRID, BASE = QColor('#343740'), QColor('#454A58')
BAND = QColor(234, 217, 92, 23)                       # rgba(234,217,92,.09)
GUIDE = QColor(255, 255, 255, 56)                     # rgba(255,255,255,.22)
TIP_BG, TIP_BORDER = QColor('#292B32'), QColor('#454A58')
VC_EST = "Estimated from how values changed over time in simulated FM24 careers; not FM's own formula."
VC_NOTE = (' Based on 132,000 observed player value changes in 11 saves of 5 games, anchored on his current value.'
           ' The band holds about half of real outcomes. Assumes he renews his contract.')
EMPTY_T = 'No value curve'
EMPTY_D = ('The save has no market value for this player (it is 0 or Not for Sale), '
           'so there is nothing to anchor an estimate on.')


def _num(x):
    """JS-style number text: 2.8 -> '2.8', 3.0 -> '3'."""
    return ('%.1f' % x).rstrip('0').rstrip('.')


def _round(x):
    return math.floor(x + 0.5)                        # JS Math.round


def fmt_m(v):
    return ('£%d' % _round(v / 1e6) + 'M' if v >= 1e7 else '£' + _num(_round(v / 1e5) / 10) + 'M' if v >= 1e6
            else '£%dK' % _round(v / 1e3) if v >= 1e3 else '£%d' % _round(v))


def nice_axis(mx):
    """-> (step, top): step = 1 / 2 / 5 x 10^n with ~4 intervals, top = first multiple of step >= mx."""
    raw = mx / 4
    mag = 10 ** math.floor(math.log10(raw))
    m = raw / mag
    step = (1 if m <= 1 else 2 if m <= 2 else 5 if m <= 5 else 10) * mag
    return step, math.ceil(mx / step - 1e-9) * step


def tick_m(v, step):
    return ('£0' if v == 0 else '£%dM' % _round(v / 1e6) if step >= 1e6 else '£' + _num(_round(v / 1e5) / 10) + 'M'
            if step >= 1e5 else '£%dK' % _round(v / 1e3))


def _font(bold=False, px=11):
    f = QFont()
    f.setPixelSize(px)
    f.setBold(bold)
    return f


def tip_text(c, i):
    """Hover bubble text of age column i (mockup: Now column = 'Market value')."""
    if i == 0:
        return f'Age {c.ages[0]} (now)\nMarket value  {fmt_m(c.expected[0])}'
    t = (f'Age {c.ages[i]} (in {i} year{"s" if i > 1 else ""})\nExpected  {fmt_m(c.expected[i])}'
         f'\nTypical range  {fmt_m(c.lo[i])} - {fmt_m(c.hi[i])}')
    return t + (f'\nAt full potential  {fmt_m(c.full[i])}' if c.full is not None else '')


class ValueChart(QWidget):
    def __init__(self, curve=None, until='', parent=None):
        super().__init__(parent)
        self._c, self._until, self._hover = curve, until, None
        self.setMouseTracking(True)                   # REQUIRED: hover without a pressed button
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(T + B + 120)

    # -- geometry ---------------------------------------------------------------------------------------
    def _geom(self):
        c = self._c
        pw, ph = self.width() - L - R, self.height() - T - B
        n = len(c.ages)
        top = nice_axis(max(max(c.expected), max(c.full) if c.full is not None else 0) * 1.04)
        X = lambda i: L + (i * pw / (n - 1) if n > 1 else pw / 2)
        Y = lambda v: T + ph - min(v, top[1]) / top[1] * ph
        return pw, ph, n, top, X, Y

    def curve(self):
        return self._c

    def contract_marker(self):
        """-> index-space x of the contract-end marker (years left), or None (unknown / beyond the last age)."""
        c = self._c
        if c is None or c.empty or c.years_left is None or c.years_left > len(c.ages) - 1:
            return None
        return c.years_left

    # -- hover ------------------------------------------------------------------------------------------
    def _column_at(self, x, y):
        c = self._c
        if c is None or c.empty or not (T <= y <= self.height() - B):
            return None
        pw, ph, n, top, X, Y = self._geom()
        cw = pw / (n - 1) if n > 1 else pw
        i = int((x - (X(0) - cw / 2)) // cw)
        return i if 0 <= i < n else None

    def mouseMoveEvent(self, e):
        p = e.position()
        i = self._column_at(p.x(), p.y())
        if i != self._hover:
            self._hover = i
            self.update()

    def leaveEvent(self, e):
        self._hover = None
        self.update()

    # -- painting ---------------------------------------------------------------------------------------
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self._c
        if c is None or c.empty:
            self._paint_empty(p)
        else:
            self._paint_chart(p, c)
        p.end()

    def _paint_empty(self, p):
        t, d = _font(True, 13), _font(False, 12)
        rect = QRectF(40, 0, self.width() - 80, self.height())
        dh = QFontMetrics(d).boundingRect(rect.toRect(), Qt.TextFlag.TextWordWrap, EMPTY_D).height()
        th = QFontMetrics(t).height()
        y0 = (self.height() - (th + 6 + dh)) / 2
        p.setFont(t)
        p.setPen(WHITE)
        p.drawText(QRectF(40, y0, rect.width(), th), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, EMPTY_T)
        p.setFont(d)
        p.setPen(TX2)
        p.drawText(QRectF(40, y0 + th + 6, rect.width(), dh), Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap, EMPTY_D)

    @staticmethod
    def _text(p, x, y, s, color, bold=False, anchor='l'):
        """Text with its baseline at y; anchor l / m / r = SVG text-anchor start / middle / end."""
        p.setFont(_font(bold))
        p.setPen(color)
        w = p.fontMetrics().horizontalAdvance(s)
        p.drawText(QPointF(x - (w if anchor == 'r' else w / 2 if anchor == 'm' else 0), y), s)

    def _paint_chart(self, p, c):
        pw, ph, n, (step, top), X, Y = self._geom()
        pts = lambda ys: [QPointF(X(i), Y(v)) for i, v in enumerate(ys)]
        v = 0.0
        while v <= top + 1:                                              # gridlines + money ticks
            y = Y(v) + 0.5
            p.setPen(QPen(GRID if v else BASE, 1))
            p.drawLine(QPointF(L, y), QPointF(L + pw, y))
            self._text(p, L - 10, Y(v) + 4, tick_m(v, step), TX2, anchor='r')
            v += step
        for i, a in enumerate(c.ages):                                   # age labels
            self._text(p, X(i), T + ph + 20, str(a), WHITE if i == 0 else TX2, bold=i == 0, anchor='m')
        p.setPen(Qt.PenStyle.NoPen)                                      # band (hi forward, lo backward)
        p.setBrush(BAND)
        p.drawPolygon(QPolygonF(pts(c.hi) + pts(c.lo)[::-1]))
        p.setBrush(Qt.BrushStyle.NoBrush)
        ym = self.contract_marker()                                      # contract end
        if ym is not None:
            x = X(ym)
            left = x > L + pw - 200
            pen = QPen(ORG, 1)
            pen.setDashPattern([4, 3])
            p.setPen(pen)
            p.drawLine(QPointF(x, T - 10), QPointF(x, T + ph))
            lab = f'Contract ends {self._until}' if self._until else 'Contract ends'
            self._text(p, x + (-6 if left else 6), T - 14, lab + (' (value is lower while it runs out)' if c.runs_out else ''),
                       ORG, anchor='r' if left else 'l')
        if c.full is not None:                                           # at full potential (dashed)
            pen = QPen(GRN, 2)
            pen.setDashPattern([2.5, 2])
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.drawPolyline(QPolygonF(pts(c.full)))
        pen = QPen(YEL, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)                                                    # expected
        p.drawPolyline(QPolygonF(pts(c.expected)))
        for i, q in enumerate(pts(c.expected)):
            p.setBrush(YEL)
            if i:
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(q, 3, 3)
            else:
                p.setPen(QPen(RING, 2))
                p.drawEllipse(q, 5, 5)
        p.setBrush(Qt.BrushStyle.NoBrush)
        up = n > 1 and max(c.expected[1], c.full[1] if c.full is not None else 0) > c.expected[0]
        self._text(p, X(0) + 10, Y(c.expected[0]) + (22 if up else -12), f'Now  {fmt_m(c.expected[0])}', WHITE, True)
        if n > 1:                                                        # end labels (>= 14 px apart)
            ye = Y(c.expected[-1]) + 4
            yf = Y(c.full[-1]) + 4 if c.full is not None else ye
            if c.full is not None and abs(ye - yf) < 14:
                if ye > yf:
                    ye = yf + 14
                else:
                    yf = ye + 14
            self._text(p, X(n - 1) + 9, ye, fmt_m(c.expected[-1]), YEL, True)
            if c.full is not None:
                self._text(p, X(n - 1) + 9, yf, fmt_m(c.full[-1]), GRN, True)
        if self._hover is not None:
            self._paint_hover(p, c, X, Y, ph)

    def _paint_hover(self, p, c, X, Y, ph):
        i = self._hover
        p.setPen(QPen(GUIDE, 1))
        p.drawLine(QPointF(X(i), T), QPointF(X(i), T + ph))
        lines = tip_text(c, i).split('\n')
        f = _font()
        fm = QFontMetrics(f)
        w, h = max(fm.horizontalAdvance(s) for s in lines) + 16 + 2, 15 * len(lines) + 8 + 2    # padding 4 8, border 1, line-height 15
        x = max(6, min(self.width() - w - 6, X(i) - w / 2))
        y = Y(c.expected[i]) - h - 8                                       # bubble above the point (mockup)
        if y < 2:
            y = Y(c.expected[i]) + 12                                      # no room above: below it
        p.setBrush(TIP_BG)
        p.setPen(QPen(TIP_BORDER, 1))
        p.drawRoundedRect(QRectF(x + 0.5, y + 0.5, w - 1, h - 1), 3, 3)
        p.setFont(f)
        p.setPen(WHITE)
        for j, s in enumerate(lines):
            p.drawText(QPointF(x + 9, y + 5 + 15 * j + (15 - fm.height()) / 2 + fm.ascent()), s)


class ChartLegend(QWidget):
    """Header legend: 16 x 2 swatches (dashed = two 7 px dashes), 10 x 10 r2 band swatch at alpha .24, 11 px secondary, gap 14."""

    def __init__(self, full, parent=None):
        super().__init__(parent)
        self._items = [('line', 'Expected')] + ([('dash', 'At full potential')] if full else []) + [('band', 'Typical range')]
        fm = QFontMetrics(_font())
        self._w = [(16 if k != 'band' else 10) + 6 + fm.horizontalAdvance(t) for k, t in self._items]
        self.setFixedSize(sum(self._w) + 14 * (len(self._items) - 1), 20)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setFont(_font())
        fm = p.fontMetrics()
        x, cy = 0.0, self.height() / 2
        for (kind, text), w in zip(self._items, self._w):
            if kind == 'line':
                p.fillRect(QRectF(x, cy - 1, 16, 2), YEL)
            elif kind == 'dash':
                for dx in (0, 9):
                    p.fillRect(QRectF(x + dx, cy - 1, 7, 2), GRN)
            else:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(234, 217, 92, 61))                      # rgba(234,217,92,.24)
                p.drawRoundedRect(QRectF(x, cy - 5, 10, 10), 2, 2)
            p.setPen(TX2)
            p.drawText(QPointF(x + (10 if kind == 'band' else 16) + 6, cy + (fm.ascent() - fm.descent()) / 2), text)
            x += w + 14
        p.end()
