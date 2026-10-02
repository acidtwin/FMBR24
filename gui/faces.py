"""Face pictures and club badges for Qt widgets: background index load (fm_editor/faces.py) + a small scaled-QPixmap LRU cache.

    svc = get_service()
    px = svc.pixmap(person.get('uid'), 54, 64, dpr, radius=3)   # QPixmap or None (none / index still loading / off)
    bx = svc.club_pixmap(club.get('uid'), 18, dpr)              # club badge in an 18x18 box (aspect kept, transparent) or None
    fx = svc.nation_pixmap(person.get('nation'), 22, dpr)       # nation picture (our nation entity id) or None
    cx = svc.comp_pixmap(club['league']['comp_uid'], 16, dpr)   # competition logo or None
    svc.active('club')                                          # True when badges are on, the index is loaded and a pack has some
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

LRU_SIZE = 2048   # tiny pixmaps (a 20x24 face is 2 KB): the Players list shows ~100 distinct pictures per screen


class FaceService(QObject):
    ready = pyqtSignal()    # the index finished loading (also after start() with faces off: nothing to wait for)
    _loaded = pyqtSignal()  # worker thread -> GUI thread (queued)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lru = OrderedDict()   # (path, w, h, dpr, radius, fit) -> QPixmap
        self._act = {}              # kind -> bool, see active()
        self._bad = set()           # picture files that failed to decode (vanished / corrupt): not retried on every paint
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
        self._act = {}
        self._bad = set()
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
        self._act = {}
        self.ready.emit()

    def active(self, kind):
        """True when pictures of `kind` ('person', 'club', 'nation', 'comp', 'kit') can show: the setting is on, the index is
        loaded and some pack holds some. The lists use it to pick the picture layout over the text one (cached per index load)."""
        a = self._act.get(kind)
        if a is None:
            a = self._act[kind] = bool(self._started and not self._busy and _faces.has_kind(kind))
        return a

    def loading(self):
        return self._busy

    def path(self, uid, kind='person'):
        """Picture file for a key of `kind` (person UniqueID, club save uid, our nation id, competition UniqueID) or None. No
        file-exists stat (paint path): a vanished file fails once in _render."""
        if not self._started:
            self.start()          # first request without an explicit start(): auto-detect, picture appears on `ready`
        if kind == 'club':
            return _faces.club_logo_path(uid, False)
        if kind == 'nation':
            return _faces.nation_logo_path(uid, False)
        if kind == 'comp':
            return _faces.comp_logo_path(uid, False)
        return _faces.media_path('person', uid, False) if kind == 'person' else None

    def pixmap(self, uid, w, h, dpr=1.0, radius=0, kind='person', fit=False):
        """Face scaled for a w x h (logical px) box, or None. fit=False: fill the box (KeepAspectRatioByExpanding,
        anchored top-centre, so a head-and-shoulders cutout loses its bottom first); fit=True: whole picture inside the
        box, centred. radius clips the corners (the widget's background shows through)."""
        path = self.path(uid, kind)
        if not path:
            return None
        if path in self._bad:
            return None
        key = (path, w, h, dpr, radius, fit)
        px = self._lru.get(key)
        if px is not None:
            self._lru.move_to_end(key)
            return px
        px = _render(path, w, h, dpr, radius, fit)
        if px is None:
            self._bad.add(path)
            return None
        self._lru[key] = px
        while len(self._lru) > LRU_SIZE:
            self._lru.popitem(last=False)
        return px

    def club_pixmap(self, club_uid, size, dpr=1.0):
        """Club badge (club['uid'], the parsed save uid) fitted inside a size x size box: aspect kept, centred, transparent
        background, smooth. None = no pack / no logo for this club / still loading / Settings > Club badges off."""
        return self.pixmap(club_uid, size, size, dpr, kind='club', fit=True)

    def nation_pixmap(self, nation_id, size, dpr=1.0):
        """Nation picture (our nation entity id) fitted inside size x size, or None (Settings > Nation flags off / no pack /
        no picture for the nation / still loading)."""
        return self.pixmap(nation_id, size, size, dpr, kind='nation', fit=True)

    def comp_pixmap(self, comp_uid, size, dpr=1.0):
        """Competition logo (competition UniqueID) fitted inside size x size, or None."""
        return self.pixmap(comp_uid, size, size, dpr, kind='comp', fit=True)


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
