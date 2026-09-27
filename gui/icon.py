"""App icon: football with a home badge, drawn at runtime via QPainter."""
import math
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor, QPainterPath, QPen
from PyQt6.QtCore import Qt, QRectF, QPointF


def _pentagon(cx, cy, r, rotation_deg=0):
    path = QPainterPath()
    pts = [
        QPointF(cx + r * math.cos(math.radians(i * 72 + rotation_deg - 90)),
                cy + r * math.sin(math.radians(i * 72 + rotation_deg - 90)))
        for i in range(5)
    ]
    path.moveTo(pts[0])
    for pt in pts[1:]:
        path.lineTo(pt)
    path.closeSubpath()
    return path


def make_app_icon(size=256):
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size

    # ── Background: deep green rounded square ──────────────────────────────────
    bg = QPainterPath()
    bg.addRoundedRect(QRectF(s * 0.02, s * 0.02, s * 0.96, s * 0.96), s * 0.18, s * 0.18)
    p.fillPath(bg, QColor('#1B4332'))

    # ── Football ───────────────────────────────────────────────────────────────
    cx, cy = s * 0.50, s * 0.46
    r = s * 0.305

    p.setBrush(QColor('white'))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(cx, cy), r, r)

    patch = QColor('#0d1f0d')
    p.fillPath(_pentagon(cx, cy, r * 0.265, 0), patch)
    for i in range(5):
        a = math.radians(i * 72 - 90)
        p.fillPath(_pentagon(cx + r * 0.60 * math.cos(a),
                             cy + r * 0.60 * math.sin(a),
                             r * 0.235, i * 72 + 36), patch)

    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor('#0d1f0d'), s * 0.012))
    p.drawEllipse(QPointF(cx, cy), r, r)

    # ── House badge (bottom-right) ─────────────────────────────────────────────
    bx, by = s * 0.745, s * 0.745
    br = s * 0.175

    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor('#52B788'))
    p.drawEllipse(QPointF(bx, by), br, br)

    hw = br * 1.05
    hh = br * 1.0

    # Roof
    roof = QPainterPath()
    roof.moveTo(bx,            by - hh * 0.56)
    roof.lineTo(bx - hw * 0.56, by - hh * 0.04)
    roof.lineTo(bx + hw * 0.56, by - hh * 0.04)
    roof.closeSubpath()
    p.fillPath(roof, QColor('white'))

    # Walls
    p.fillRect(QRectF(bx - hw * 0.36, by - hh * 0.04, hw * 0.72, hh * 0.52), QColor('white'))

    # Door cutout
    p.fillRect(QRectF(bx - hw * 0.125, by + hh * 0.16, hw * 0.25, hh * 0.32), QColor('#1B4332'))

    p.end()
    return QIcon(px)
