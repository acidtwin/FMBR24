"""FM24 facepack lookup: person UniqueID -> picture file. No Qt, READ-ONLY on the game folder.

How FM resolves a face (checked on a real DF11 + FMNEWGAN install, see HANDOVER 'Faces'):
  <FM24 user dir>/graphics/<pack>/config.xml maps picture files to resource paths:
      <record from="7458500" to="graphics/pictures/person/7458500/portrait"/>
  `from` = file name without extension (relative to the config.xml folder), the id in `to` = the person's
  UniqueID (our identity `uid` from gamedb.match_identities, NOT our internal `id`). The same resource path serves
  players AND staff. Generated players (newgens) are written by tools as `r-<uid>` (FM24 convention), so the lookup
  tries `<uid>` then `r-<uid>`. A second layout is the real resource tree inside a pack folder:
      <pack>/pictures/person/<uid>/portrait.png
  Packs without a config.xml (the FMNEWGAN ethnic folders) are not mapped by FM either until a tool writes one.

Index = one small JSON per pack in the cache dir (`faces-<hash>.fidx`, never touched by Settings > Clear cache),
validated by mtime/size of the pack folder, its config.xml(s) and pictures/person. Building it for 200k pictures is
~0.5 s (one regex pass over a 16 MB config + one directory listing); loading the cached index ~0.2 s. Neither
runs on the GUI thread (gui/faces.py). Pack priority: `faces_pack_order` setting (folder names, first wins), then
alphabetical; FM itself leaves duplicates undefined.
"""
import hashlib
import html
import json
import os
import re
import threading
from collections import namedtuple

from fm_editor import settings as _settings

_FM_NAME = 'Football Manager 2024'
_STEAM_APPID = '2252570'
_EXTS = ('.png', '.jpg', '.jpeg')                      # lookup priority when a stem exists in several formats
_RECORD = re.compile(rb'<record\s+from="([^"]*)"\s+to="graphics/pictures/person/([^/"]+)/portrait"')
_INDEX_VERSION = 1
_EXT_RANK = {e: i for i, e in enumerate(_EXTS)}
Pack = namedtuple('Pack', 'name path flat')   # flat: the graphics folder itself (its config.xml only, no subfolders)


# ---------------------------------------------------------------- locating the FM24 user dir

def candidate_dirs():
    """Known FM24 user-dir locations (Steam/Proton, Flatpak Steam, native Linux, Windows, macOS). Targeted paths only."""
    h = os.path.expanduser('~')
    si = os.path.join('Sports Interactive', _FM_NAME)
    out = []
    for steam in (os.path.join(h, '.local/share/Steam'), os.path.join(h, '.steam/steam'),
                  os.path.join(h, '.var/app/com.valvesoftware.Steam/.local/share/Steam')):
        out.append(os.path.join(steam, 'steamapps/compatdata', _STEAM_APPID,
                                'pfx/drive_c/users/steamuser/Documents', si))
    out += [os.path.join(h, '.local/share', si), os.path.join(h, 'Documents', si),
            os.path.join(h, 'Library/Application Support', si)]
    return out


def find_fm_dir(configured='', save_path=None):
    """FM24 user folder (the one holding `games` and `graphics`) or None.
    Order: env FMBR24_FM_DIR, the Settings value, the folder above the loaded save's `games` dir, known locations.
    An explicit value (env/Settings) that is not a folder returns None: the user must see that it is wrong."""
    for explicit in (os.environ.get('FMBR24_FM_DIR', ''), configured or ''):
        explicit = explicit.strip()
        if explicit:
            explicit = os.path.expanduser(explicit)
            return explicit if os.path.isdir(explicit) else None
    if save_path:
        d = os.path.dirname(os.path.abspath(save_path))
        if os.path.basename(d).lower() == 'games' and os.path.isdir(os.path.join(os.path.dirname(d), 'graphics')):
            return os.path.dirname(d)
    for c in candidate_dirs():
        if os.path.isdir(os.path.join(c, 'graphics')):
            return c
    return None


# ---------------------------------------------------------------- packs

def _configs(pack_dir, flat=False):
    """config.xml files of a pack: the pack folder itself and its direct subfolders (FM applies each to its own folder)."""
    out = []
    try:
        entries = sorted(os.scandir(pack_dir), key=lambda e: e.name)
    except OSError:
        return out
    for e in entries:
        if e.is_file() and e.name.lower() == 'config.xml':
            out.append(e.path)
    for e in entries:
        if e.is_dir() and not flat:
            c = os.path.join(e.path, 'config.xml')
            if os.path.isfile(c):
                out.append(c)
    return out


def _has_person_records(config_path):
    try:
        with open(config_path, 'rb') as f:
            return b'pictures/person/' in f.read(1 << 20)
    except OSError:
        return False


def is_facepack(pack_dir):
    if os.path.isdir(os.path.join(pack_dir, 'pictures', 'person')):
        return True
    return any(_has_person_records(c) for c in _configs(pack_dir))


def discover_packs(fm_dir, order=()):
    """[Pack(name, path, flat)] facepacks under <fm_dir>/graphics, highest priority first. The graphics folder itself counts when
    it holds a config.xml with person records (the classic 'config.xml + faces/ in graphics' install)."""
    g = os.path.join(fm_dir or '', 'graphics')
    packs = []
    try:
        names = sorted((e.name for e in os.scandir(g) if e.is_dir()), key=str.casefold)
    except OSError:
        return packs
    root_cfg = os.path.join(g, 'config.xml')
    if os.path.isfile(root_cfg) and _has_person_records(root_cfg):
        packs.append(Pack('graphics', g, True))
    packs += [Pack(n, os.path.join(g, n), False) for n in names if is_facepack(os.path.join(g, n))]
    rank = {n: i for i, n in enumerate(order)}
    return sorted(packs, key=lambda p: rank.get(p.name, len(rank)))  # stable: alphabetical within the unlisted


# ---------------------------------------------------------------- index

def _signature(pack_dir, flat=False):
    def st(p):
        try:
            s = os.stat(p)
            return [os.path.relpath(p, pack_dir), s.st_mtime_ns, s.st_size]
        except OSError:
            return [os.path.relpath(p, pack_dir), 0, 0]
    paths = [pack_dir, os.path.join(pack_dir, 'pictures', 'person')] + _configs(pack_dir, flat)
    return [st(p) for p in paths]


def _listing(folder, memo):
    """stem.casefold() -> file name, for the picture files of one folder (best format wins); memoised."""
    got = memo.get(folder)
    if got is None:
        got = {}
        rank = {}
        try:
            for e in os.scandir(folder):
                stem, dot, ext = e.name.rpartition('.')
                ext = dot + ext.lower()
                if ext in _EXT_RANK and e.is_file():
                    k = stem.casefold()
                    if k not in got or _EXT_RANK[ext] < rank[k]:
                        got[k], rank[k] = e.name, _EXT_RANK[ext]
        except OSError:
            pass
        memo[folder] = got
    return got


def _build_pack(pack_dir, flat=False):
    """{id key -> path relative to pack_dir, '' = '<key>.png' next to the pack's top config.xml}."""
    out = {}
    memo = {}
    for cfg in _configs(pack_dir, flat):
        base = os.path.dirname(cfg)
        reldir = os.path.relpath(base, pack_dir)
        try:
            with open(cfg, 'rb') as f:
                data = f.read()
        except OSError:
            continue
        for m in _RECORD.finditer(data):
            frm = m.group(1).decode('utf-8', 'replace')
            if '&' in frm:
                frm = html.unescape(frm)
            key = m.group(2).decode('utf-8', 'replace')
            folder, _, stem = frm.replace('\\', '/').rpartition('/')
            name = _listing(os.path.join(base, folder) if folder else base, memo).get(stem.casefold())
            if not name or key in out:
                continue
            rel = os.path.normpath(os.path.join(reldir, folder, name)) if (folder or reldir != '.') else name
            out[key] = '' if rel == key + '.png' else rel
    pdir = os.path.join(pack_dir, 'pictures', 'person')
    try:
        ids = [e.name for e in os.scandir(pdir) if e.is_dir()]
    except OSError:
        ids = []
    for key in ids:
        if key in out:
            continue
        name = _listing(os.path.join(pdir, key), memo).get('portrait')
        if name:
            out[key] = os.path.join('pictures', 'person', key, name)
    return out


def _cache_file(cache_dir, pack_dir):
    h = hashlib.sha1(os.path.abspath(pack_dir).encode()).hexdigest()[:12]
    return os.path.join(cache_dir, f'faces-{h}.fidx')


def load_pack_index(pack_dir, cache_dir, flat=False):
    """Index of one pack from the disk cache when its signature still matches, else rebuilt and cached."""
    sig = _signature(pack_dir, flat)
    cf = _cache_file(cache_dir, pack_dir)
    try:
        with open(cf, encoding='utf-8') as f:
            data = json.load(f)
        if data.get('v') == _INDEX_VERSION and data.get('sig') == sig:
            return data['map']
    except Exception:
        pass
    idx = _build_pack(pack_dir, flat)
    try:
        os.makedirs(cache_dir, exist_ok=True)
        tmp = cf + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump({'v': _INDEX_VERSION, 'sig': sig, 'map': idx}, f, separators=(',', ':'))
        os.replace(tmp, cf)
    except OSError:
        pass  # a read-only cache dir only costs a rebuild next time
    return idx


class FaceIndex:
    """uid -> picture path over all facepacks. `load()` blocks (run it in a worker); `path()` never does."""

    def __init__(self, fm_dir, order=(), cache_dir=None):
        if cache_dir is None:
            from fm_editor import cache
            cache_dir = cache.cache_dir()
        self.fm_dir = fm_dir
        self.order = list(order)
        self.cache_dir = cache_dir
        self.packs = []        # [Pack] after load()
        self._maps = []        # parallel to packs
        self.ready = False

    def load(self):
        packs = discover_packs(self.fm_dir, self.order) if self.fm_dir else []
        maps = [load_pack_index(p.path, self.cache_dir, p.flat) for p in packs]
        self.packs, self._maps, self.ready = packs, maps, True   # published last: path() reads these lock-free

    def count(self):
        return sum(len(m) for m in self._maps)

    def path(self, uid):
        """Best picture file for a UniqueID, or None (not loaded, no pack has it, file vanished)."""
        for key in (str(uid), 'r-' + str(uid)):
            for pk, m in zip(self.packs, self._maps):
                rel = m.get(key)
                if rel is not None:
                    p = os.path.join(pk.path, rel or key + '.png')
                    if os.path.isfile(p):
                        return p
        return None


# ---------------------------------------------------------------- shared instance (settings driven)

_lock = threading.Lock()
_index = None


def configure(save_path=None, cache_dir=None):
    """(Re)create the shared index from the settings (faces_enabled, faces_dir, faces_pack_order, env). Cheap: nothing is
    read until `ensure_loaded()`. Returns the index or None when face pictures are off / no FM24 folder."""
    global _index
    s = _settings.load()
    fm = find_fm_dir(s['faces_dir'], save_path) if s['faces_enabled'] else None
    with _lock:
        _index = FaceIndex(fm, s['faces_pack_order'], cache_dir) if fm else None
        return _index


def ensure_loaded():
    """Blocking: load the shared index (call from a worker thread). Returns it, or None when disabled."""
    idx = _index
    if idx is not None and not idx.ready:
        idx.load()
    return idx


def face_path(uid, kind='person'):
    """Picture path for a person UniqueID or None. Never blocks and never raises: None until the index is loaded,
    when face pictures are off, or for any kind other than 'person' (staff share the person pictures)."""
    idx = _index
    if kind != 'person' or idx is None or not idx.ready or not uid:
        return None
    try:
        return idx.path(uid)
    except Exception:
        return None


def status(configured='', save_path=None):
    """(fm_dir, [pack names]) for the Settings row. Cheap (no index build): discovery only."""
    fm = find_fm_dir(configured, save_path)
    s = _settings.load()
    return fm, [p.name for p in discover_packs(fm, s['faces_pack_order'])] if fm else []
