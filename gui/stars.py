"""Shared painted star widget (club header, player window CA/PA boxes)."""
import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QWidget

STAR_FULL, STAR_EMPTY = '#F5C518', '#3A4050'


def _star_path():
    """The 5-point star in the 15px design box (shared by the widget and the list cells)."""
    path = QPainterPath()
    c, ro, ri = 7.5, 7.2, 3.0
    for k in range(10):
        r = ro if k % 2 == 0 else ri
        a = -math.pi / 2 + k * math.pi / 5
        pt = QPointF(c + r * math.cos(a), c + r * math.sin(a) + 0.4)
        path.moveTo(pt) if k == 0 else path.lineTo(pt)
    path.closeSubpath()
    return path


_PATH = _star_path()
_ROW_CACHE = {}


def star_row_pixmap(stars, size=10, gap=2, dpr=1.0):
    """5 stars (`stars` 0..5 in half steps) as one transparent pixmap of (5*size+4*gap) x size logical px.
    Cached per (stars, size, gap, dpr): at most ~10 small pixmaps, so list painting never builds one per cell."""
    key = (stars, size, gap, dpr)
    pm = _ROW_CACHE.get(key)
    if pm is None:
        w = 5 * size + 4 * gap
        pm = QPixmap(round(w * dpr), round(size * dpr))
        pm.setDevicePixelRatio(dpr)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for i in range(5):
            p.save()
            p.translate(i * (size + gap), 0)
            p.scale(size / 15, size / 15)
            p.fillPath(_PATH, QColor(STAR_EMPTY))
            f = max(0.0, min(1.0, stars - i))
            if f > 0:
                p.setClipRect(QRectF(0, 0, 15 * f, 15))
                p.fillPath(_PATH, QColor(STAR_FULL))
            p.restore()
        p.end()
        _ROW_CACHE[key] = pm
    return pm


class _StarWidget(QWidget):
    """One 14px star filled 0, 0.5 or 1 (left half) in gold over a dim outline colour."""
    def __init__(self, fill, parent=None):
        super().__init__(parent)
        self._fill = fill
        self.setFixedSize(15, 15)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillPath(_PATH, QColor(STAR_EMPTY))
        if self._fill > 0:
            p.setClipRect(QRectF(0, 0, 15 * self._fill, 15))
            p.fillPath(_PATH, QColor(STAR_FULL))
