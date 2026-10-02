"""FM24 picture-pack lookup: person UniqueID -> face picture, club logo id -> badge. No Qt, READ-ONLY on the game folder.
(Module name kept from the faces-only version; club badges share the pack discovery, the per-pack index and the settings.)

How FM resolves a face (checked on a real DF11 + FMNEWGAN install, see HANDOVER 'Faces'):
  <FM24 user dir>/graphics/<pack>/config.xml maps picture files to resource paths:
      <record from="7458500" to="graphics/pictures/person/7458500/portrait"/>
  `from` = file name without extension (relative to the config.xml folder), the id in `to` = the person's
  UniqueID (our identity `uid` from gamedb.match_identities, NOT our internal `id`). The same resource path serves
  players AND staff. Generated players (newgens) are written by tools as `r-<uid>` (FM24 convention), so the lookup
  tries `<uid>` then `r-<uid>`. A second layout is the real resource tree inside a pack folder:
      <pack>/pictures/person/<uid>/portrait.png
  Packs without a config.xml (the FMNEWGAN ethnic folders) are not mapped by FM either until a tool writes one.

Club logos (FMG Standard Logos & co) use the same mechanism with `to="graphics/pictures/club/<id>/logo"`; the config.xml
sits 3 folders deep (`<pack>/Clubs/Normal/Normal/config.xml`, 180x180 PNGs; the sibling `Small/` config maps 25x18 `icon`s, which are
ignored) and `<id>` is the club's game UniqueID, NOT our parsed club uid (fm_editor/clublogo.py maps uid -> id). Pack folders
`Alternatives/Retro/Fantasy` have no config.xml: FM does not map them either. Folder-per-id layout:
`<pack>/pictures/club/<id>/logo.png`. One index per pack covers both kinds.

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

from fm_editor import clublogo as _clublogo
from fm_editor import settings as _settings

_FM_NAME = 'Football Manager 2024'
_STEAM_APPID = '2252570'
_EXTS = ('.png', '.jpg', '.jpeg')                      # lookup priority when a stem exists in several formats
_RECORD = re.compile(rb'<record\s+from="([^"]*)"\s+to="graphics/pictures/(person|club)/([^/"]+)/(portrait|logo)"')
_KIND_ROLE = {b'person': b'portrait', b'club': b'logo'}   # a record counts only with its own role (club `icon`s are ignored)
_INDEX_VERSION = 2
_EXT_RANK = {e: i for i, e in enumerate(_EXTS)}
_MAX_DEPTH = 3          # config.xml levels below the pack folder (FMG: Clubs/Normal/Normal)
_LEAF_FILES = 200       # a folder with this many files before any subfolder is a picture folder: do not list it further
# flat: the graphics folder itself (its config.xml only, no subfolders); kinds: {'person', 'club'} the pack holds
Pack = namedtuple('Pack', 'name path flat kinds', defaults=(frozenset({'person'}),))


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
    """config.xml files of a pack, depth first, alphabetical: the pack folder itself, then its subfolders down to _MAX_DEPTH
    (FM applies each config to its own folder). `pictures/` (folder-per-id trees, 100k+ entries) and `@2x` are not entered."""
    out = []

    def walk(d, level):
        c = os.path.join(d, 'config.xml')
        if os.path.isfile(c):
            out.append(c)
        if flat or level >= _MAX_DEPTH:
            return
        subs, files = [], 0
        try:
            for e in os.scandir(d):
                if e.is_dir():
                    subs.append(e.name)
                elif level and not e.name.lower().endswith('.xml'):
                    files += 1
                    if files >= _LEAF_FILES:
                        return          # a picture folder, not a container
        except OSError:
            return
        for n in sorted(subs):
            if n.lower() != 'pictures' and not n.startswith('@'):
                walk(os.path.join(d, n), level + 1)

    walk(pack_dir, 0)
    return out


_CLUB_LOGO_REC = re.compile(rb'pictures/club/[^/"]+/logo"')


def _config_kinds(config_path):
    try:
        with open(config_path, 'rb') as f:
            head = f.read(1 << 20)
    except OSError:
        return set()
    out = set()
    if b'pictures/person/' in head:
        out.add('person')
    if _CLUB_LOGO_REC.search(head):
        out.add('club')
    return out


def _has_person_records(config_path):
    return 'person' in _config_kinds(config_path)


def pack_kinds(pack_dir, flat=False):
    """{'person', 'club'} subset: what this folder holds (records in a config.xml, or the folder-per-id trees)."""
    out = set()
    for kind in ('person', 'club'):
        if os.path.isdir(os.path.join(pack_dir, 'pictures', kind)):
            out.add(kind)
    for c in _configs(pack_dir, flat):
        out |= _config_kinds(c)
    return out


def is_facepack(pack_dir):
    return 'person' in pack_kinds(pack_dir)


def discover_packs(fm_dir, order=(), kind='person'):
    """[Pack(name, path, flat, kinds)] picture packs under <fm_dir>/graphics holding `kind` ('person' = facepacks, 'club' =
    logo packs, None = either), highest priority first. The graphics folder itself counts when it holds a config.xml with such
    records (the classic 'config.xml + faces/ in graphics' install)."""
    g = os.path.join(fm_dir or '', 'graphics')
    packs = []
    try:
        names = sorted((e.name for e in os.scandir(g) if e.is_dir()), key=str.casefold)
    except OSError:
        return packs
    root_cfg = os.path.join(g, 'config.xml')
    cand = []
    if os.path.isfile(root_cfg):
        cand.append(Pack('graphics', g, True))
    cand += [Pack(n, os.path.join(g, n), False) for n in names]
    for pk in cand:
        kinds = frozenset(pack_kinds(pk.path, pk.flat))
        if kinds and (kind is None or kind in kinds):
            packs.append(pk._replace(kinds=kinds))
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
    paths = [pack_dir, os.path.join(pack_dir, 'pictures', 'person'), os.path.join(pack_dir, 'pictures', 'club')] \
        + _configs(pack_dir, flat)
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
    """({person key -> path}, {club logo id -> path}); paths relative to pack_dir, '' = '<key>.png' next to the pack's top
    config.xml (persons only: the short form keeps the 200k-entry DF11 index small)."""
    out = {'person': {}, 'club': {}}
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
            kind = m.group(2)
            if m.group(4) != _KIND_ROLE[kind]:
                continue
            kind = kind.decode()
            frm = m.group(1).decode('utf-8', 'replace')
            if '&' in frm:
                frm = html.unescape(frm)
            key = m.group(3).decode('utf-8', 'replace')
            dest = out[kind]
            folder, _, stem = frm.replace('\\', '/').rpartition('/')
            name = _listing(os.path.join(base, folder) if folder else base, memo).get(stem.casefold())
            if not name or key in dest:
                continue
            rel = os.path.normpath(os.path.join(reldir, folder, name)) if (folder or reldir != '.') else name
            dest[key] = '' if (kind == 'person' and rel == key + '.png') else rel
    for kind, leaf in (('person', 'portrait'), ('club', 'logo')):
        pdir = os.path.join(pack_dir, 'pictures', kind)
        try:
            ids = [e.name for e in os.scandir(pdir) if e.is_dir()]
        except OSError:
            ids = []
        for key in ids:
            if key in out[kind]:
                continue
            name = _listing(os.path.join(pdir, key), memo).get(leaf)
            if name:
                out[kind][key] = os.path.join('pictures', kind, key, name)
    return out['person'], out['club']


def _cache_file(cache_dir, pack_dir):
    h = hashlib.sha1(os.path.abspath(pack_dir).encode()).hexdigest()[:12]
    return os.path.join(cache_dir, f'faces-{h}.fidx')


def load_pack_index(pack_dir, cache_dir, flat=False):
    """(person map, club map) of one pack from the disk cache when its signature still matches, else rebuilt and cached."""
    sig = _signature(pack_dir, flat)
    cf = _cache_file(cache_dir, pack_dir)
    try:
        with open(cf, encoding='utf-8') as f:
            data = json.load(f)
        if data.get('v') == _INDEX_VERSION and data.get('sig') == sig:
            return data['map'], data['club']
    except Exception:
        pass
    people, clubs = _build_pack(pack_dir, flat)
    try:
        os.makedirs(cache_dir, exist_ok=True)
        tmp = cf + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump({'v': _INDEX_VERSION, 'sig': sig, 'map': people, 'club': clubs}, f, separators=(',', ':'))
        os.replace(tmp, cf)
    except OSError:
        pass  # a read-only cache dir only costs a rebuild next time
    return people, clubs


class FaceIndex:
    """uid -> face picture and logo id -> club badge over all picture packs. `load()` blocks (run it in a worker); `path()` and
    `club_path()` never do."""

    def __init__(self, fm_dir, order=(), cache_dir=None):
        if cache_dir is None:
            from fm_editor import cache
            cache_dir = cache.cache_dir()
        self.fm_dir = fm_dir
        self.order = list(order)
        self.cache_dir = cache_dir
        self.packs = []        # [Pack] after load()
        self._maps = []        # person maps, parallel to packs
        self._club_maps = []   # club logo maps, parallel to packs
        self.ready = False

    def load(self):
        packs = discover_packs(self.fm_dir, self.order, None) if self.fm_dir else []
        loaded = [load_pack_index(p.path, self.cache_dir, p.flat) for p in packs]
        self._club_maps = [c for _p, c in loaded]
        self.packs, self._maps, self.ready = packs, [p for p, _c in loaded], True   # published last: path() reads these lock-free

    def count(self):
        return sum(len(m) for m in self._maps)

    def club_count(self):
        return sum(len(m) for m in self._club_maps)

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

    def club_path(self, logo_id):
        """Badge file for a club logo id (the pack key, see fm_editor/clublogo.py), or None."""
        key = str(logo_id)
        for pk, m in zip(self.packs, self._club_maps):
            rel = m.get(key)
            if rel:
                p = os.path.join(pk.path, rel)
                if os.path.isfile(p):
                    return p
        return None


# ---------------------------------------------------------------- shared instance (settings driven)

_lock = threading.Lock()
_index = None
_faces_on = False       # Settings > Face pictures
_logos_on = False       # Settings > Club badges
_club_uids = None       # sorted club uid list of the loaded save (fm_editor/clublogo.build), set by set_club_uids()


def configure(save_path=None, cache_dir=None):
    """(Re)create the shared index from the settings (faces_enabled, logos_enabled, faces_dir, faces_pack_order, env). Cheap:
    nothing is read until `ensure_loaded()`. Returns the index or None when face pictures AND club badges are off / no FM24
    folder. One index serves both kinds; the two switches only gate the lookups."""
    global _index, _faces_on, _logos_on
    s = _settings.load()
    want = s['faces_enabled'] or s['logos_enabled']
    fm = find_fm_dir(s['faces_dir'], save_path) if want else None
    with _lock:
        _index = FaceIndex(fm, s['faces_pack_order'], cache_dir) if fm else None
        _faces_on, _logos_on = bool(fm and s['faces_enabled']), bool(fm and s['logos_enabled'])
        return _index


def ensure_loaded():
    """Blocking: load the shared index (call from a worker thread). Returns it, or None when disabled."""
    idx = _index
    if idx is not None and not idx.ready:
        idx.load()
    return idx


def set_club_uids(uids):
    """Sorted club uids of the loaded save (+ install DB): the key table that turns a club uid into its logo id."""
    global _club_uids
    _club_uids = uids


def face_path(uid, kind='person'):
    """Picture path for a person UniqueID or None. Never blocks and never raises: None until the index is loaded,
    when face pictures are off, or for any kind other than 'person' (staff share the person pictures)."""
    idx = _index
    if kind != 'person' or idx is None or not idx.ready or not uid or not _faces_on:
        return None
    try:
        return idx.path(uid)
    except Exception:
        return None


def club_logo_path(club_uid):
    """Badge file for a club's parsed save uid (`club['uid']`) or None. Never blocks and never raises: None until the index
    and the save's club list are loaded, when club badges are off, for an unknown club or a club the packs have no logo for.
    No fallback to the raw uid: it is the id of a different (the previous) club."""
    idx, uids = _index, _club_uids
    if idx is None or not idx.ready or not club_uid or not _logos_on or not uids:
        return None
    try:
        lid = _clublogo.logo_id(uids, club_uid)
        return idx.club_path(lid) if lid is not None else None
    except Exception:
        return None


def status(configured='', save_path=None, kind='person'):
    """(fm_dir, [pack names]) for the Settings row: facepacks (kind 'person') or logo packs ('club'). Cheap (no index
    build): discovery only."""
    fm = find_fm_dir(configured, save_path)
    s = _settings.load()
    return fm, [p.name for p in discover_packs(fm, s['faces_pack_order'], kind)] if fm else []
