"""Faint random stadium photo behind the player window panels.

Images: the ones shipped in `gui/assets/backgrounds/` (Envato stock photos the user paid for; resized to 1920 px) plus
any the user drops into `~/.local/share/fmbr24/backgrounds/*.webp|png|jpg`. One is picked at random each time a window
opens; none = no background. The photo is painted 'cover'-scaled at OPACITY over the window colour, under the (opaque) panels, so it
shows in the gaps and empty areas. Settings: `player_background` (on/off).
"""
import os
import random

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

BG_DIR = os.path.join(os.path.expanduser('~'), '.local', 'share', 'fmbr24', 'backgrounds')   # user's own images
BUNDLED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'backgrounds')   # shipped with the app
OPACITY = 0.13           # 'very very faded'; tune here
_EXT = ('.webp', '.png', '.jpg', '.jpeg')
_CACHE = {}              # path -> QPixmap (decoded once per session)


def list_backgrounds(folder=None):
    """Images of `folder`, or (default) the bundled ones plus the user's own folder."""
    out = []
    for fo in ([folder] if folder else [BUNDLED_DIR, BG_DIR]):
        try:
            out += sorted(os.path.join(fo, n) for n in os.listdir(fo) if n.lower().endswith(_EXT))
        except OSError:
            pass
    return out


def pick_background(folder=None, rng=random):
    """Random background QPixmap, or None when there are no images / they cannot be read."""
    files = list_backgrounds(folder)
    rng.shuffle(files)
    for p in files:                      # first readable one
        if p not in _CACHE:
            px = QPixmap(p)
            _CACHE[p] = None if px.isNull() else px
        if _CACHE[p] is not None:
            return _CACHE[p]
    return None


def cover(px, w, h):
    """px scaled to cover w x h and centre-cropped to exactly that size (None when px is None)."""
    if px is None or w <= 0 or h <= 0:
        return None
    s = px.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
    return s.copy((s.width() - w) // 2, (s.height() - h) // 2, w, h)


class BgPainter:
    """Shared by every window that wears the background (player window, staff window): picks one photo when created
    (None when `enabled` is False or the folder has no images) and paints colour + faint photo in a paintEvent."""

    def __init__(self, enabled=True):
        self.src = pick_background() if enabled else None
        self._scaled = None

    def paint(self, widget, color):
        from PyQt6.QtGui import QPainter, QColor
        p = QPainter(widget)
        p.fillRect(widget.rect(), QColor(color))
        if self.src is not None:
            sz = widget.size()
            if self._scaled is None or self._scaled[0] != sz:
                self._scaled = (sz, cover(self.src, sz.width(), sz.height()))
            if self._scaled[1] is not None:
                p.setOpacity(OPACITY)
                p.drawPixmap(0, 0, self._scaled[1])
        p.end()
