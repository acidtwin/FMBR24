"""Faint random stadium photo behind the player window panels.

Images live in a USER folder (not in the repo: stock photos are not ours to publish):
`~/.local/share/fmbr24/backgrounds/*.webp|png|jpg`. One is picked at random each time a window opens; none =
no background. The photo is painted 'cover'-scaled at OPACITY over the window colour, under the (opaque) panels, so it
shows in the gaps and empty areas. Settings: `player_background` (on/off).
"""
import os
import random

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

BG_DIR = os.path.join(os.path.expanduser('~'), '.local', 'share', 'fmbr24', 'backgrounds')
OPACITY = 0.13           # 'very very faded'; tune here
_EXT = ('.webp', '.png', '.jpg', '.jpeg')
_CACHE = {}              # path -> QPixmap (decoded once per session)


def list_backgrounds(folder=None):
    folder = folder or BG_DIR
    try:
        return sorted(os.path.join(folder, n) for n in os.listdir(folder) if n.lower().endswith(_EXT))
    except OSError:
        return []


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
