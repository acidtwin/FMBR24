"""Header bar textures: pixmap generators for the page header (`_HeaderHeroWidget`) and its loading glow.

Mechanical port of the generators in mockups/header-net.html (top comment = the spec; every number below is from its
`P` table). One function per texture builds ONE `QPainterPath` of strands (+ knot points); `texture_pixmap` strokes it
once (a single drawPath: overlaps are a union, no double alpha at crossings), dots the knots with a round-cap pen,
applies the optional DestinationIn mask and draws the optional deco. `glow_pixmaps` strokes the SAME path in the tint
and re-applies the same mask. No caching here: the widget caches one pixmap per (w, h, dpr, texture).
"""
import math

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import (QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QPolygonF,
                         QRadialGradient)

TEXTURES = ('diamond', 'squareknot', 'perspective', 'honeycomb', 'pitch')
DEFAULT_TEXTURE = 'diamond'
LABELS = {   # Settings dropdown text (mockups/settings-page-design-a.html)
    'diamond': 'Diamond net  (default)',
    'squareknot': 'Square-knot net',
    'perspective': 'Perspective net',
    'honeycomb': 'Honeycomb',
    'pitch': 'Pitch lines',
}

# line width / white alpha / knot radius / knot alpha / glow halo widths (None = the caller's HERO_GLOW['halo_widths'])
# / glow core width = line width + core_extra. Pitch = the old grid: 2 px lines at alpha 4/255, flat caps, no knots.
SPEC = {
    'diamond':     dict(w=1.2, a=0.042, kr=1.3, ka=0.026, halo=(8, 4), core_extra=0.6),
    'squareknot':  dict(w=1.1, a=0.042, kr=1.2, ka=0.026, halo=(8, 4), core_extra=0.6),
    'perspective': dict(w=1.1, a=0.048, kr=1.1, ka=0.026, halo=(8, 4), core_extra=0.6),
    'honeycomb':   dict(w=1.1, a=0.060, kr=1.2, ka=0.026, halo=(8, 4), core_extra=0.6),
    'pitch':       dict(w=2.0, a=4 / 255, kr=0.0, ka=0.0, halo=None, core_extra=0.0),
}
KNOT_GLOW_EXTRA = 0.4          # glow core knots: radius + this

# generator constants (mockup P table)
DIAMOND = dict(angle=40, ph=20)
KNOT = dict(cell=16, chunk=5, ax=2.4, ly=300, ay=3.2, lx=360)
PERSP = dict(cols=44, row_pitch=30, vp_y=0.42, persp=0.60, k=0.35, bow=7, rip=2.2, chunk=3,
             vig=(0.78, 0.45, 0.95, ((0, 1.0), (0.6, 0.70), (1, 0.30))), shadow=0.30)
HEX = dict(s=12, light=(0.68, 0.5, 30, 380, ((0, 0.30), (0.5, 1.0), (1, 0.30))),
           post=dict(x=14, w_post=6, body_a=0.06, edge_a=0.14, shadow_a=0.22, shadow_w=16,
                     bar_h=5, bar_len=300, bar_a=0.11, bar_edge_a=0.18))


def _a(x):
    return round(255 * x)


# -- geometry helpers ----------------------------------------------------------

def _clip_seg(x0, y0, x1, y1, w, h):
    """Liang-Barsky: the part of the segment inside [0,w]x[0,h] (or None)."""
    t0, t1 = 0.0, 1.0
    dx, dy = x1 - x0, y1 - y0
    for p, q in ((-dx, x0), (dx, w - x0), (-dy, y0), (dy, h - y0)):
        if p == 0:
            if q < 0:
                return None
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return None
                t0 = max(t0, r)
            else:
                if r < t0:
                    return None
                t1 = min(t1, r)
    return x0 + t0 * dx, y0 + t0 * dy, x0 + t1 * dx, y0 + t1 * dy


def _in_rect(x, y, w, h):
    return 0 <= x <= w and 0 <= y <= h


def _quad_through(F, a0, a1):
    """Quad bezier chunk through F at the chunk midpoint: ctrl = 2*F(mid) - (P0+P1)/2."""
    p0, p1, pm = F(a0), F(a1), F((a0 + a1) / 2)
    return (p0[0], p0[1], 2 * pm[0] - (p0[0] + p1[0]) / 2, 2 * pm[1] - (p0[1] + p1[1]) / 2, p1[0], p1[1])


def _touches(s, w, h):
    xs, ys = s[0::2], s[1::2]
    return max(xs) >= -4 and min(xs) <= w + 4 and max(ys) >= -4 and min(ys) <= h + 4


def _to_path(segs, path=None):
    path = path or QPainterPath()
    for s in segs:
        path.moveTo(s[0], s[1])
        if len(s) == 4:
            path.lineTo(s[2], s[3])
        else:
            path.quadTo(s[2], s[3], s[4], s[5])
    return path


def _to_chunks(segs):
    """One small path per strand. Qt's raster stroker is ~16x faster on many short curved strands than on one huge
    near-horizontal-heavy path (squareknot at 1920 px: 4 ms vs 65 ms); `_stroke` unions them (opaque, then alpha)."""
    return [_to_path([s]) for s in segs]


# -- generators: each returns dict(path, knots, mask, deco, shade) ---------------

def _pitch(w, h):
    path = QPainterPath()
    for x in range(38, w, 40):
        path.moveTo(x, 0)
        path.lineTo(x, h)
    for y in range(58, h, 60):
        path.moveTo(0, y)
        path.lineTo(w, y)
    return dict(paths=[path], knots=None, mask=None, deco=None, shade=None)


def _diamond(w, h):
    s, ph = math.tan(math.radians(DIAMOND['angle'])), DIAMOND['ph']
    lo, hi = math.floor((-s * w - ph) / ph), math.ceil((h + s * w) / ph)
    segs, knots = [], QPolygonF()
    for i in range(lo, hi + 1):
        for c in (_clip_seg(0, i * ph, w, i * ph + s * w, w, h), _clip_seg(0, i * ph, w, i * ph - s * w, w, h)):
            if c:
                segs.append(c)
    for i in range(lo, hi + 1):
        for j in range(lo, hi + 1):
            x, y = (j - i) * ph / (2 * s), (i + j) * ph / 2
            if _in_rect(x, y, w, h):
                knots.append(QPointF(x, y))
    return dict(paths=[_to_path(segs)], knots=knots, mask=None, deco=None, shade=None)


def _squareknot(w, h):
    K = KNOT
    c, st, tau = K['cell'], K['chunk'] * K['cell'], 2 * math.pi

    def F(x, y):
        return (x + K['ax'] * math.sin(tau * y / K['ly']),
                y + K['ay'] * math.sin(tau * x / K['lx'] + 0.8) * (0.4 + 0.6 * y / h))

    x0, x1, y0, y1 = -2 * c, w + 2 * c, -2 * c, h + 2 * c
    segs, knots = [], QPolygonF()
    for y in range(y0, y1 + 1, c):
        for xa in range(x0, x1, st):
            segs.append(_quad_through(lambda x: F(x, y), xa, min(xa + st, x1)))
    for x in range(x0, x1 + 1, c):
        for ya in range(y0, y1, st):
            segs.append(_quad_through(lambda yy: F(x, yy), ya, min(ya + st, y1)))
    for x in range(x0, x1 + 1, c):
        for y in range(y0, y1 + 1, c):
            q = F(x, y)
            if _in_rect(q[0], q[1], w, h):
                knots.append(QPointF(*q))
    return dict(paths=_to_chunks([s for s in segs if _touches(s, w, h)]), knots=knots, mask=None, deco=None, shade=None)


def _perspective(w, h):
    P = PERSP
    vy, N, k = P['vp_y'] * h, P['cols'], P['k']

    def Fc(u, y0):
        t = u / N
        x = w * (t - k * t * t) / (1 - k)
        f = x / w
        return (x, vy + (y0 - vy) * (1 - P['persp'] * f) + P['bow'] * 4 * f * (1 - f) * ((y0 - vy) / h)
                + P['rip'] * math.sin(2 * math.pi * x / 260 + y0 / 55))

    rows = [y0 + 7 for y0 in range(-240, int(h + 240) + 1, P['row_pitch'])]
    st = P['chunk']
    segs, knots = [], QPolygonF()
    for y0 in rows:
        for ua in range(-4, N + 4, st):
            segs.append(_quad_through(lambda u: Fc(u, y0), ua, min(ua + st, N + 4)))
    for u in range(-4, N + 5):
        for ra in range(0, len(rows) - 1, 2):
            segs.append(_quad_through(lambda yy: Fc(u, yy), rows[ra], rows[min(ra + 2, len(rows) - 1)]))
    for u in range(-4, N + 5):
        for y0 in rows:
            q = Fc(u, y0)
            if _in_rect(q[0], q[1], w, h):
                knots.append(QPointF(*q))
    fx, fy, r, stops = P['vig']

    def mask(q):
        g = QRadialGradient(QPointF(fx * w, fy * h), r * w)
        for o, a in stops:
            g.setColorAt(o, QColor(0, 0, 0, _a(a)))
        q.fillRect(0, 0, w, h, QBrush(g))

    def shade(q):   # soft corner shadow UNDER the net (not masked)
        R = w * 0.62
        g = QRadialGradient(QPointF(w * 0.55, h * 0.5), R)
        g.setColorAt(0, QColor(0, 0, 0, 0))
        g.setColorAt(min(1.0, min(w, h) * 0.25 / R), QColor(0, 0, 0, 0))
        g.setColorAt(1, QColor(0, 0, 0, _a(P['shadow'])))
        q.fillRect(0, 0, w, h, QBrush(g))

    return dict(paths=_to_chunks([s for s in segs if _touches(s, w, h)]), knots=knots, mask=mask, deco=None, shade=shade)


def _honeycomb(w, h):
    s = HEX['s']
    hx = math.sqrt(3) * s / 2
    rmax, imax = math.ceil(h / (1.5 * s)) + 1, math.ceil(w / hx) + 1
    path, knots = QPainterPath(), QPolygonF()
    for r in range(-1, rmax + 1):
        b = r * 1.5 * s
        prev = None
        for i in range(-1, imax + 1):
            x = i * hx
            odd = (i + r) % 2 == 1
            y = b + (s / 2 if odd else 0)
            if prev:
                path.moveTo(*prev)
                path.lineTo(x, y)
            if odd:
                path.moveTo(x, y)
                path.lineTo(x, b + 1.5 * s)
            if _in_rect(x, y, w, h):
                knots.append(QPointF(x, y))
            prev = (x, y)
    cx_, cy_, deg, half, stops = HEX['light']
    th = math.radians(deg)
    dx, dy, cx, cy = math.cos(th), math.sin(th), cx_ * w, cy_ * h

    def mask(q):   # light sweep
        g = QLinearGradient(cx - dx * half, cy - dy * half, cx + dx * half, cy + dy * half)
        for o, a in stops:
            g.setColorAt(o, QColor(0, 0, 0, _a(a)))
        q.fillRect(0, 0, w, h, QBrush(g))

    o = HEX['post']

    def lin(x0, x1, c0, c1):
        g = QLinearGradient(x0, 0, x1, 0)
        g.setColorAt(0, c0)
        g.setColorAt(1, c1)
        return QBrush(g)

    def deco(q):   # goal post + crossbar corner (after the net, not masked)
        px = w - o['x'] - o['w_post']
        bx = w - o['bar_len'] - o['x']
        clear_w, clear_k = QColor(255, 255, 255, 0), QColor(0, 0, 0, 0)
        q.fillRect(round(px - o['shadow_w']), 0, o['shadow_w'], h, lin(px - o['shadow_w'], px, clear_k, QColor(0, 0, 0, _a(o['shadow_a']))))
        q.fillRect(bx, o['bar_h'], o['bar_len'], 10, lin(bx, w - o['x'], clear_k, QColor(0, 0, 0, _a(0.25))))
        q.fillRect(px, 0, o['w_post'], h, QColor(255, 255, 255, _a(o['body_a'])))
        q.fillRect(px, 0, 1, h, QColor(255, 255, 255, _a(o['edge_a'])))
        q.fillRect(bx, 0, o['bar_len'], o['bar_h'], lin(bx, w - o['x'], clear_w, QColor(255, 255, 255, _a(o['bar_a']))))
        q.fillRect(bx, o['bar_h'] - 1, o['bar_len'], 1, lin(bx, w - o['x'], clear_w, QColor(255, 255, 255, _a(o['bar_edge_a']))))

    return dict(paths=[path], knots=knots, mask=mask, deco=deco, shade=None)


_GEN = {'diamond': _diamond, 'squareknot': _squareknot, 'perspective': _perspective,
        'honeycomb': _honeycomb, 'pitch': _pitch}


# -- pixmaps ---------------------------------------------------------------------

def _blank(w, h, dpr, aa=True):
    px = QPixmap(round(w * dpr), round(h * dpr))
    px.setDevicePixelRatio(dpr)
    px.fill(Qt.GlobalColor.transparent)
    q = QPainter(px)
    q.setRenderHint(QPainter.RenderHint.Antialiasing, aa)   # pitch: the old grid was never antialiased
    return px, q


def _dots(q, knots, r, color):
    if knots is not None and knots.count() and r > 0:
        q.setPen(QPen(color, 2 * r, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        q.drawPoints(knots)


def _stroke(q, paths, color, width, cap, size):
    """Union of the strands in `color` (one drawPath => no double alpha at crossings; many chunks => opaque union
    in a scratch pixmap, then composited at the colour's alpha, same result)."""
    solid = QColor(color.red(), color.green(), color.blue())
    pen = QPen(solid if len(paths) > 1 else color, width, Qt.PenStyle.SolidLine, cap, Qt.PenJoinStyle.BevelJoin)
    if len(paths) == 1:
        q.setPen(pen)
        q.setBrush(Qt.BrushStyle.NoBrush)
        q.drawPath(paths[0])
        return
    tmp, tq = _blank(*size)
    tq.setPen(pen)
    for pth in paths:
        tq.drawPath(pth)
    tq.end()
    q.setOpacity(color.alpha() / 255)
    q.drawPixmap(0, 0, tmp)
    q.setOpacity(1.0)


def _cap(tex):
    # Flat caps: Qt's raster stroker is ~100x slower with round caps/joins on long strands (123 ms vs 1 ms for the
    # diamond at 1920 px); a 1.2 px strand with flat ends is indistinguishable, and the knot dots cover the nodes.
    return Qt.PenCapStyle.FlatCap


def _mask(q, g):
    if g['mask']:
        q.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        g['mask'](q)
        q.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)


def texture_pixmap(tex, w, h, dpr):
    """The faint white texture for a w x h header (logical px) at device pixel ratio dpr."""
    sp, g = SPEC[tex], _GEN[tex](w, h)
    px, q = _blank(w, h, dpr, tex != 'pitch')
    _stroke(q, g['paths'], QColor(255, 255, 255, _a(sp['a'])), sp['w'], _cap(tex), (w, h, dpr))
    _dots(q, g['knots'], sp['kr'], QColor(255, 255, 255, _a(sp['ka'])))
    _mask(q, g)
    if g['shade']:   # under the net
        q.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOver)
        g['shade'](q)
        q.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
    if g['deco']:
        g['deco'](q)
    q.end()
    return px


def glow_pixmaps(tex, w, h, dpr, tint, pitch_halo):
    """(core, halo) loading-glow pixmaps: the SAME strand path in the tint, same mask (no shade / deco)."""
    sp, g = SPEC[tex], _GEN[tex](w, h)
    widths = sp['halo'] or pitch_halo
    cap = _cap(tex)
    core, q = _blank(w, h, dpr, tex != 'pitch')
    _stroke(q, g['paths'], QColor(*tint, 255), sp['w'] + sp['core_extra'], cap, (w, h, dpr))
    _dots(q, g['knots'], sp['kr'] + KNOT_GLOW_EXTRA if sp['kr'] else 0, QColor(*tint, 255))
    _mask(q, g)
    q.end()
    halo, q = _blank(w, h, dpr, tex != 'pitch')
    n = len(widths)
    for i, wd in enumerate(widths):
        _stroke(q, g['paths'], QColor(*tint, _a(0.35 * (i + 1) / n)), wd, cap, (w, h, dpr))
    _mask(q, g)
    q.end()
    return core, halo
