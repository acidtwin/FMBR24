"""Career history of one person (see memory fm24-binary-format.md s.11). Pure python, no Qt.

Where the data lives: a person's career rows are NOT in game_db.dat. They are in the history stores
`pl_hist` (players) and `non_pl_hist` (staff career: playing years, coaching, managing).

* **Install DB** (read-only, `<Steam>/steamapps/common/Football Manager 2024/data/database/db/2430/2430_fm/`):
  `<store>_index.dat` (zstd) = `u32 N` + N sorted `(person uid, ordinal)`; `<store>_id.dat` = from byte 8 pairs
  `(start, last_row_start)` per ordinal into the decompressed `<store>_dt.dat` (zstd, one 4096-byte frame each);
  entry = [start, next entry's start). The key is the IDENTITY uid (`person['uid']`, `match_identities`), NOT
  the ability-block uid.
* **Save** (`pl_hist_dt.cmt`, `non_pl_hist_dt.cmt`): the same rows (40/20 bytes, no trailing u32) plus whatever
  the game appended (Kane: Bayern 2023-). The save's `_ls.dat` slot order is NOT derivable from the person id
  (slot != pid, != uid rank; three uid-sorted runs, no id stored in the person record), so a person's save rows
  are located by CONTENT: the install rows must appear as a contiguous run in the save dt; rows after them
  (up to the next run start from `_ls`) are the continuation.

Player row (44 B install / first 40 B in save): y1 u16 (season start year), y2 u16 (year the spell ended),
t u8 (0 normal, 1 loan, 2 youth, 3 youth loan?), apps u8 (255 unknown), goals u8 (255 unknown), fee u32
(0xffffffff none; GBP, on the SELLING club's row), club u32 (twice; see club_for: = uid of the next club), comp u32 (twice, a
competition id, names not stored), ord u8 (order inside the season), date start/end/third (u16 day-of-year
(low 9 bits) + u16 year; year 1900 = none).  apps/goals are the season's league figures.
Staff row (24 B install / 20 B save): club u32 (see club_for), date start, date end, date (null), kind u8, role u8,
u16.  (kind, role): (0x01, 0x0b) player, (0x10, 0x05) manager (Guardiola, Mourinho, Pochettino, Arteta);
other pairs (0x14/0x06, 0x02/0x08, 0x10/0x18 ...) = other coaching jobs, not labelled.
"""
import bisect
import mmap
import os
import re
import struct
import threading

_LOCK = threading.Lock()
_STORES = {}      # (dir, name) -> _Store
_SAVES = {}       # (save_path, mtime, name) -> (dt, sorted run starts)
_MAGIC = re.compile(rb'\x28\xb5\x2f\xfd')

PLAYER = {'name': 'pl_hist', 'row': 44, 'save_row': 40}
STAFF = {'name': 'non_pl_hist', 'row': 24, 'save_row': 20}


# ---------------------------------------------------------------- uid of a person (from game_db bytes)
def person_uid(b, person, next_offset=None):
    """Identity uid of `person` (dict with 'id', 'end', 'offset') read from the game_db bytes; None if not
    found. Same record and checks as gamedb.match_identities (pid u32, uid u32 right after the person record)
    but only for this one person, so no 240 MB scan."""
    pid = person['id']
    if pid is None or pid < 0:
        return None
    lo = person['end'] + 25
    hi = min(next_offset or len(b), lo + 6000)
    pat = struct.pack('<I', pid)
    p = b.find(pat, lo, hi)
    while p >= 0:
        if p >= 12 and b[p - 3:p] == b'\x00\x00\x00' and (b[p - 7] & 7) <= 2 and b[p - 4] in (0, 1, 4, 5):
            uid = struct.unpack_from('<I', b, p + 4)[0]
            if uid not in (0, 0xFFFFFFFF):
                if uid == struct.unpack_from('<I', b, p + 8)[0]:
                    return uid
                day = struct.unpack_from('<H', b, p - 12)[0] & 511
                year = struct.unpack_from('<H', b, p - 10)[0]
                src = struct.unpack_from('<I', b, p + 8)[0]
                if 1 <= day <= 366 and 1900 <= year <= 2300 and not (b[p - 6] & 0x85) and (b[p - 6] & 0x60) \
                        and src >= 1000 and src != 0xFFFFFFFF:
                    return uid
        p = b.find(pat, p + 1, hi)
    return None


# ---------------------------------------------------------------- install DB
def install_db_dir(save_path=None):
    """Directory holding pl_hist_index.dat etc., or None. Order: FMBR24_FM_DB env (the *_fm dir or its parent
    install root), the Steam library the save lives in (save under <lib>/steamapps/compatdata/...), the default
    Steam library."""
    cands = []
    env = os.environ.get('FMBR24_FM_DB')
    if env:
        cands.append(env)
    roots = []
    if save_path:
        parts = os.path.abspath(save_path).split(os.sep)
        if 'steamapps' in parts:
            roots.append(os.sep.join(parts[:parts.index('steamapps') + 1]) or os.sep)
    roots.append(os.path.expanduser('~/.local/share/Steam/steamapps'))
    for r in roots:
        base = os.path.join(r, 'common', 'Football Manager 2024', 'data', 'database', 'db')
        try:
            for v in sorted(os.listdir(base), reverse=True):
                cands.append(os.path.join(base, v, v + '_fm'))
        except OSError:
            pass
    for c in cands:
        if os.path.isfile(os.path.join(c, 'pl_hist_index.dat')):
            return c
    return None


def _unzstd_one(buf):
    import zstandard
    return zstandard.ZstdDecompressor().decompressobj().decompress(buf)


class _Store:
    """One install history store (players or staff)."""

    def __init__(self, d, spec):
        self.row = spec['row']
        name = spec['name']
        with open(os.path.join(d, name + '_index.dat'), 'rb') as f:
            raw = f.read()
        self.index = _unzstd_one(raw[raw.find(b'\x28\xb5\x2f\xfd'):])      # u32 N, then (key, ordinal) pairs
        self.n = struct.unpack_from('<I', self.index, 0)[0]
        with open(os.path.join(d, name + '_id.dat'), 'rb') as f:
            self.ids = f.read()                                          # u32 pairs from byte 8
        self._f = open(os.path.join(d, name + '_dt.dat'), 'rb')
        mm = mmap.mmap(self._f.fileno(), 0, access=mmap.ACCESS_READ)
        self.mm = mm
        self.starts = [m.start() for m in _MAGIC.finditer(mm)]            # one 4096-byte frame each
        self.starts.append(len(mm))
        self._frames = {}

    def _frame(self, i):
        fr = self._frames.get(i)
        if fr is None:
            import zstandard
            fr = zstandard.ZstdDecompressor().decompress(self.mm[self.starts[i]:self.starts[i + 1]],
                                                         max_output_size=1 << 20)
            if len(self._frames) > 64:
                self._frames.clear()
            self._frames[i] = fr
        return fr

    def _span(self, a, b):
        f0, f1 = a // 4096, (b - 1) // 4096
        buf = b''.join(self._frame(f) for f in range(f0, f1 + 1))
        return buf[a - f0 * 4096:b - f0 * 4096]

    def rows(self, uid):
        """List of raw rows (self.row bytes each) of the person with identity uid, [] if none."""
        lo, hi = 0, self.n
        while lo < hi:
            mid = (lo + hi) // 2
            if struct.unpack_from('<I', self.index, 4 + 8 * mid)[0] < uid:
                lo = mid + 1
            else:
                hi = mid
        if lo >= self.n or struct.unpack_from('<I', self.index, 4 + 8 * lo)[0] != uid:
            return []
        o = struct.unpack_from('<I', self.index, 8 + 8 * lo)[0]
        if 8 + 8 * o + 12 > len(self.ids):
            return []
        a = struct.unpack_from('<I', self.ids, 8 + 8 * o)[0]
        last = struct.unpack_from('<I', self.ids, 12 + 8 * o)[0]
        end = last + self.row                       # the entry ends with its last row
        if end <= a or (end - a) % self.row:
            return []
        buf = self._span(a, end)
        return [buf[i:i + self.row] for i in range(0, len(buf), self.row)]


def _store(d, spec):
    key = (d, spec['name'])
    with _LOCK:
        s = _STORES.get(key)
        if s is None:
            s = _STORES[key] = _Store(d, spec)
        return s


# ---------------------------------------------------------------- save overlay
def _save_dt(save_path, members, spec):
    """(dt bytes, sorted run-start offsets) of the save's history store, cached per file+mtime."""
    from fm_editor.archive import get_member
    key = (save_path, os.path.getmtime(save_path), spec['name'])
    with _LOCK:
        hit = _SAVES.get(key)
    if hit:
        return hit
    by = {m['name']: m for m in members}
    dt = get_member(save_path, by[spec['name'] + '_dt.cmt'])
    ls = get_member(save_path, by[spec['name'] + '_ls.dat'])
    # ls: u16 4, u32 K, K x u32 (first block), u32 N, N x ([u32 count][count x u32 (off, rel) pairs])
    k = struct.unpack_from('<I', ls, 8)[0]
    p = 12 + 4 * k
    n = struct.unpack_from('<I', ls, p)[0]
    p += 4
    starts = []
    for _ in range(n):
        c = struct.unpack_from('<I', ls, p)[0]
        if c:
            starts.append(struct.unpack_from('<I', ls, p + 4)[0])
        p += 4 + 4 * c
    starts.sort()
    with _LOCK:
        _SAVES.clear()                  # keep one save only (33 MB + 10 MB)
        _SAVES[key] = (dt, starts)
    return dt, starts


def _continuation(dt, starts, rows, spec):
    """Rows the save holds after the install rows of one person (list of raw save rows), or None if the
    install rows are not found as a unique contiguous run (then the person is not in the save store, or the
    game rewrote them)."""
    sr = spec['save_row']
    base = [r[:sr] for r in rows]
    n = len(base)
    found = []
    p = dt.find(base[0])
    while p >= 0:
        if (p - 8) % sr == 0 and all(dt[p + i * sr:p + (i + 1) * sr] == base[i] for i in range(n - 1)):
            found.append(p)
        p = dt.find(base[0], p + 1)
    if len(found) != 1:
        return None
    s = found[0] - 8
    i = bisect.bisect_right(starts, s)
    end = (starts[i] if i < len(starts) else len(dt) - 8) + 8
    at = found[0] + n * sr
    return [bytes(dt[x:x + sr]) for x in range(at, end, sr)]


# ---------------------------------------------------------------- row decoding
def _date(b, o):
    d, y = struct.unpack_from('<HH', b, o)
    return None if y == 1900 else (y, d & 511)


def decode_player_row(r):
    y1, y2 = struct.unpack_from('<HH', r, 0)
    fee, club = struct.unpack_from('<II', r, 7)
    return {'year': y1, 'year_end': None if y2 == 1900 else y2,
            'kind': {1: 'loan', 2: 'youth', 3: 'youth loan'}.get(r[4]),
            'apps': None if r[5] == 255 else r[5], 'goals': None if r[6] == 255 else r[6],
            'fee': None if fee == 0xFFFFFFFF else fee, 'club_raw': club,
            'comp': struct.unpack_from('<I', r, 19)[0], 'order': r[27],
            'start': _date(r, 28), 'end': _date(r, 32)}


def decode_staff_row(r):
    club = struct.unpack_from('<I', r, 0)[0]
    kind, role = r[16], r[17]
    return {'club_raw': club, 'start': _date(r, 4), 'end': _date(r, 8), 'kind': kind, 'role': role,
            'job': {(0x01, 0x0b): 'Player', (0x10, 0x05): 'Manager'}.get((kind, role))}


def _history(spec, decode, uid, save_path, members):
    if uid is None:
        return None
    d = install_db_dir(save_path)
    if not d:
        return None
    rows = _store(d, spec).rows(uid)
    if not rows:
        return None
    out = [decode(r) for r in rows]
    n_install = len(out)
    if save_path and members:
        try:
            dt, starts = _save_dt(save_path, members, spec)
            more = _continuation(dt, starts, rows, spec)
        except Exception:
            more = None
        if more and more[0] == rows[-1][:spec['save_row']]:
            more = more[1:]             # the game re-wrote the install's last (current-season) row: not a new row
        if more:
            out += [decode(r) for r in more]
    return {'rows': out, 'n_install': n_install}


def player_history(uid, save_path=None, members=None):
    """{'rows': [row dicts], 'n_install': int} for the person with identity uid, or None (no install DB /
    no history). Rows from n_install on come from the save (seasons the game appended)."""
    return _history(PLAYER, decode_player_row, uid, save_path, members)


def staff_history(uid, save_path=None, members=None):
    """Same for the career of a non-player / manager (`non_pl_hist`): rows with club_raw, start/end (year,
    day-of-year), kind/role, job ('Player', 'Manager' or None)."""
    return _history(STAFF, decode_staff_row, uid, save_path, members)


_CLUBS = {}       # install dir -> (sorted uids, {uid: name}, {uid: nation})
_CLUB_RX = re.compile(rb'\x00(....)\1\x00(....)\xff\xff\xff\xff\2\2(....)(.{6})(.{4})', re.S)


def install_clubs(d):
    """(sorted club uids, {uid: name}, {uid: nation entity id}) of EVERY club in the install DB (55.8k; the save holds 44k), from
    server_db.dat table_3 (a tad-wrapped FMF archive: the FMF starts at byte 8). Cached on disk (small JSON)."""
    import json
    import tempfile
    with _LOCK:
        hit = _CLUBS.get(d)
    if hit:
        return hit
    src = os.path.join(d, 'server_db.dat')
    st = os.stat(src)
    cp = None
    try:
        from fm_editor.cache import cache_dir
        cp = os.path.join(cache_dir(), 'clubs2-%d-%d.json.club' % (st.st_size, int(st.st_mtime)))   # not *.json: cache_clear lists those
        with open(cp, encoding='utf-8') as f:
            j = json.load(f)
        uids, names, nats = j['u'], dict(zip(j['u'], j['n'])), dict(zip(j['u'], j['t']))
    except Exception:
        from fm_editor.archive import get_member, parse_archive
        with open(src, 'rb') as f:
            f.seek(8)
            raw = f.read()
        tmp = tempfile.NamedTemporaryFile(suffix='.fmf', delete=False)
        try:
            tmp.write(raw)
            tmp.close()
            del raw
            _, members, *_r = parse_archive(tmp.name)
            b = bytes(get_member(tmp.name, next(m for m in members if m['name'] == 'table_3.dat')))
        finally:
            os.unlink(tmp.name)
        names, nats = {}, {}
        for mm in _CLUB_RX.finditer(b):
            n = struct.unpack_from('<I', b, mm.end() - 4)[0]
            if 1 <= n <= 80:
                try:
                    uid = struct.unpack('<I', mm.group(1))[0]
                    names[uid] = b[mm.end():mm.end() + n].decode('utf-8')
                    nats[uid] = struct.unpack('<I', mm.group(2))[0]
                except UnicodeDecodeError:
                    pass
        uids = sorted(names)
        if cp:
            try:
                with open(cp, 'w', encoding='utf-8') as f:
                    json.dump({'u': uids, 'n': [names[u] for u in uids], 't': [nats[u] for u in uids]}, f,
                              separators=(',', ':'))
            except OSError:
                pass
    with _LOCK:
        _CLUBS[d] = (uids, names, nats)
    return uids, names, nats


def club_for(raw, uids):
    """Club uid a history club field refers to (None if unknown): the club is the PREDECESSOR of `raw` in the
    sorted club-uid list `uids` (largest uid < raw). The field is never the club's own uid but the one after
    it (Spurs 727 -> 728, Bayern 913 -> 915, Real Madrid 1733 -> 1736, Brescia 1112 -> 1113, Molde 1351 ->
    1353); the reason is unknown (raw is not always a club uid: Bologna 1110 -> 1111). Verified on ~60 clubs
    in the rows of Kane, Rice, Grealish, Mbappe, Son, Haaland, Odegaard, Isak, Bellingham, Foden, Saka and the
    managers Guardiola, Mourinho, Pochettino, Arteta. `uids` must be the FULL list (install_clubs + the save's
    clubs): with the save's 44k alone Pep's Brescia became Bologna. If `raw` is not itself in the list the
    predecessor is only trusted when <= 6 below it (the club may be missing from both lists), else None."""
    i = bisect.bisect_left(uids, raw)
    if i == 0:
        return None
    if (i >= len(uids) or uids[i] != raw) and raw - uids[i - 1] > 6:
        return None
    return uids[i - 1]


def season_label(row, calendar_year=False):
    """'2014/15' (or '2014' for calendar-year leagues; see CALENDAR_NATIONS)."""
    y = row['year']
    return str(y) if calendar_year else f'{y}/{(y + 1) % 100:02d}'


# nation entity ids (fm_editor/nations.py) whose leagues run Jan-Dec. UNVERIFIED: ground truth needed.
CALENDAR_NATIONS = {160, 171, 142, 148, 163, 120, 189}   # Norway Sweden Finland Iceland Ireland USA Brazil (Argentina switched: left out)


class Clubs:
    """History club fields -> club (name, nation) using the install club list plus the save's clubs (save names
    win: they carry the save's renames)."""

    def __init__(self, save_clubs, install_dir=None):
        names, nats = {}, {}
        if install_dir:
            try:
                _u, names, nats = install_clubs(install_dir)
                names, nats = dict(names), dict(nats)
            except Exception:
                names, nats = {}, {}
        for c in save_clubs or ():
            names[c['uid']] = c['name']
            if c.get('nation') is not None:
                nats[c['uid']] = c['nation']
        self.names, self.nations, self.uids = names, nats, sorted(names)

    def lookup(self, raw):
        """-> (club uid, name, nation id) or (None, None, None)."""
        u = club_for(raw, self.uids)
        return (u, self.names.get(u), self.nations.get(u)) if u is not None else (None, None, None)


_CLUBOBJ = {}


def career_for_person(person, save_data, uid=None):
    """History of ONE player for the player window. `person` = people-list dict, `save_data` = the app's save
    dict ('b', 'members', 'save_path', 'clubs'). Returns {'status': 'ok'|'no_install'|'none'|'no_uid',
    'rows': [dict: season, year, kind, apps, goals, fee, club, club_uid, nation, from_save], 'install_dir'}."""
    sd = save_data or {}
    path = sd.get('save_path')
    d = install_db_dir(path)
    out = {'status': 'no_install', 'rows': [], 'install_dir': d}
    if not d:
        return out
    uid = uid or person.get('uid')
    if uid is None and sd.get('b') is not None:
        uid = person_uid(sd['b'], person)
    if uid is None:
        out['status'] = 'no_uid'
        return out
    h = player_history(uid, path, sd.get('members'))
    if not h:
        out['status'] = 'none'
        return out
    key = (id(sd.get('clubs')), d)
    with _LOCK:
        cl = _CLUBOBJ.get(key)
    if cl is None:
        cl = Clubs(sd.get('clubs'), d)
        with _LOCK:
            _CLUBOBJ.clear()
            _CLUBOBJ[key] = cl
    for i, r in enumerate(h['rows']):
        cuid, name, nat = cl.lookup(r['club_raw'])
        out['rows'].append({**r, 'club': name, 'club_uid': cuid, 'nation': nat, 'from_save': i >= h['n_install'],
                            'season': season_label(r, nat in CALENDAR_NATIONS)})
    out['status'] = 'ok'
    return out
