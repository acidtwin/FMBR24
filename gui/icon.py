"""App icon: loaded from the pre-rendered size ladder in resources/icons/."""
import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

_ICON_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'resources', 'icons')
_SIZES = (16, 24, 32, 48, 64, 128, 256, 512)


def make_app_icon():
    icon = QIcon()
    for n in _SIZES:
        icon.addFile(os.path.join(_ICON_DIR, f'icon-{n}.png'))
    return icon


_SVG = os.path.join(os.path.dirname(_ICON_DIR), 'icon.svg')
_SVG_CACHE = {}


def logo_pixmap(size, dpr=1.0):
    """The FMBR24 floppy rendered from the vector master (resources/icon.svg) at size x size logical px,
    crisp at any device pixel ratio. Returns a null QPixmap if the SVG is missing/invalid (callers fall back)."""
    key = (size, round(dpr, 2))
    px = _SVG_CACHE.get(key)
    if px is None:
        r = QSvgRenderer(_SVG)
        px = QPixmap()
        if r.isValid():
            px = QPixmap(round(size * dpr), round(size * dpr))
            px.fill(Qt.GlobalColor.transparent)
            p = QPainter(px)
            p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
            r.render(p)
            p.end()
            px.setDevicePixelRatio(dpr)
        _SVG_CACHE[key] = px
    return px
