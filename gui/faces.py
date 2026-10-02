"""Face pictures and club badges for Qt widgets: background index load (fm_editor/faces.py) + a small scaled-QPixmap LRU cache.

    svc = get_service()
    px = svc.pixmap(person.get('uid'), 54, 64, dpr, radius=3)   # QPixmap or None (none / index still loading / off)
    bx = svc.club_pixmap(club.get('uid'), 18, dpr)              # club badge in an 18x18 box (aspect kept, transparent) or None
    svc.set_clubs(clubs, extra_uids, save_path)                 # on every save load, before start(): the uid -> logo id key table
    svc.ready.connect(refresh)                                  # emitted once when the index (and the club key table) is available

The index is loaded in a background thread (first run ~0.6 s to build, ~0.2 s from its disk cache), so the GUI thread only
ever does dictionary lookups plus decoding one small PNG per visible face.
"""
import threading
from collections import OrderedDict

from PyQt6.QtCore import QObject, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPainter, QPainterPath, QPixmap

from fm_editor import faces as _faces

LRU_SIZE = 256


class FaceService(QObject):
    ready = pyqtSignal()    # the index finished loading (also after start() with faces off: nothing to wait for)
    _loaded = pyqtSignal()  # worker thread -> GUI thread (queued)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lru = OrderedDict()   # (path, w, h, dpr, radius, fit) -> QPixmap
        self._clubs = None          # (clubs, extra uids, save path) of the loaded save: key table input
        self._busy = False
        self._started = False
        self._loaded.connect(self._on_loaded)

    def set_clubs(self, clubs, extra=(), save_path=None):
        """Remember the loaded save's clubs (list of dicts with 'uid') and its second-layout club uids; the next start() builds the
        club uid -> logo id table from them in the background thread (fm_editor/clublogo.py)."""
        self._clubs = (clubs, extra, save_path)

    def start(self, save_path=None):
        """(Re)read the settings and load the index in the background. Safe to call again (Settings saved, new save).
        A plain daemon thread, not a QThread: a QThread still running when a script / the app exits aborts the process."""
        self._lru.clear()
        self._started = True
        idx = _faces.configure(save_path)
        if idx is None:
            self.ready.emit()
            return
        self._busy = True
        threading.Thread(target=self._load, args=(idx, self._clubs), daemon=True, name='face-index').start()

    def _load(self, idx, clubs=None):
        try:
            if not idx.ready:
                idx.load()
            if clubs is not None:
                from fm_editor import clublogo
                _faces.set_club_uids(clublogo.build(*clubs))
        except Exception:
            import traceback
            traceback.print_exc()   # a broken pack folder must never take the app down: faces just stay off
        if idx is not _faces._index:
            return                  # superseded by a newer start(): that thread reports
        try:
            self._loaded.emit()
        except RuntimeError:
            pass                    # service deleted at shutdown

    def _on_loaded(self):
        self._busy = False
        self.ready.emit()

    def loading(self):
        return self._busy

    def path(self, uid, kind='person'):
        if not self._started:
            self.start()          # first request without an explicit start(): auto-detect, picture appears on `ready`
        return _faces.club_logo_path(uid) if kind == 'club' else _faces.face_path(uid, kind)

    def pixmap(self, uid, w, h, dpr=1.0, radius=0, kind='person', fit=False):
        """Face scaled for a w x h (logical px) box, or None. fit=False: fill the box (KeepAspectRatioByExpanding,
        anchored top-centre, so a head-and-shoulders cutout loses its bottom first); fit=True: whole picture inside the
        box, centred. radius clips the corners (the widget's background shows through)."""
        path = self.path(uid, kind)
        if not path:
            return None
        key = (path, w, h, dpr, radius, fit)
        px = self._lru.get(key)
        if px is not None:
            self._lru.move_to_end(key)
            return px
        px = _render(path, w, h, dpr, radius, fit)
        if px is None:
            return None
        self._lru[key] = px
        while len(self._lru) > LRU_SIZE:
            self._lru.popitem(last=False)
        return px

    def club_pixmap(self, club_uid, size, dpr=1.0):
        """Club badge (club['uid'], the parsed save uid) fitted inside a size x size box: aspect kept, centred, transparent
        background, smooth. None = no pack / no logo for this club / still loading / Settings > Club badges off."""
        return self.pixmap(club_uid, size, size, dpr, kind='club', fit=True)


def _render(path, w, h, dpr, radius, fit):
    img = QImage(path)
    if img.isNull():
        return None
    W, H = round(w * dpr), round(h * dpr)
    mode = Qt.AspectRatioMode.KeepAspectRatio if fit else Qt.AspectRatioMode.KeepAspectRatioByExpanding
    sc = img.scaled(W, H, mode, Qt.TransformationMode.SmoothTransformation)
    out = QPixmap(W, H)
    out.setDevicePixelRatio(dpr)
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    if radius:
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, w, h), radius, radius)
        p.setClipPath(clip)
    # CSS object-position 50% 0 (mockup): x centred, y from the top
    x = int((W - sc.width()) * 0.5)
    y = int((H - sc.height()) * (0.5 if fit else 0.0))
    p.drawImage(QRectF(x / dpr, y / dpr, sc.width() / dpr, sc.height() / dpr), sc)
    p.end()
    return out


_service = None


def get_service():
    global _service
    if _service is None:
        _service = FaceService()
    return _service
