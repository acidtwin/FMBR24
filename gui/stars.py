"""Shared painted star widget (club header, player window CA/PA boxes)."""
import math

from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import QWidget


class _StarWidget(QWidget):
    """One 14px star filled 0, 0.5 or 1 (left half) in gold over a dim outline colour."""
    def __init__(self, fill, parent=None):
        super().__init__(parent)
        self._fill = fill
        self.setFixedSize(15, 15)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        c, ro, ri = 7.5, 7.2, 3.0
        for k in range(10):
            r = ro if k % 2 == 0 else ri
            a = -math.pi / 2 + k * math.pi / 5
            pt = QPointF(c + r * math.cos(a), c + r * math.sin(a) + 0.4)
            path.moveTo(pt) if k == 0 else path.lineTo(pt)
        path.closeSubpath()
        p.fillPath(path, QColor('#3A4050'))
        if self._fill > 0:
            p.setClipRect(QRectF(0, 0, 15 * self._fill, 15))
            p.fillPath(path, QColor('#F5C518'))
