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


# Competition id (pl_hist row +19 / club['league']['comp_uid']) -> in-game division name. The save/install DB carry no
# competition names (comp_<id>.dat holds editor file names such as eng_prem; the language DB / comps.dbc hold no plain
# league names), so ONLY ids verified one of two ways are listed, unknown ids give None ('-' in the table):
#  * in-game: Nico Paz's Career Stats screen (11, 32, 67, 2000048844/6);
#  * game data + an in-game name seen: the install `lnc/*.lnc` files name a comp id explicitly (`# Sky Bet Championship
#    FM ID = 12`, `COMP_LONG_NAME_CHANGE 5123054 "Vanarama National League North"`, `# Optibet Virsliga FM ID =
#    8403697`), or the id is the TOP flight of its nation (highest mean club reputation of the nation's league tables)
#    and the save's `save_game_summary.dat` league-name list / the in-game names seen carry exactly one name for that
#    nation's top flight (Germany 22 Bundesliga, France 16 Ligue 1 Uber Eats, Belgium 1 Jupiler Pro League, Netherlands
#    29 Eredivisie, Scotland 45 William Hill SPFL, Poland 129558, Wales 130672, N. Ireland 130023, Denmark 6, Japan
#    102428, Saudi Arabia 7920263). 109201 = England tier 5 (24 clubs, the only 24-club league below League Two besides
#    North/South, which lnc names) = Vanarama National League.
COMP_NAMES = {11: 'Premier Division', 12: 'Sky Bet Championship', 13: 'Sky Bet League One', 14: 'Sky Bet League Two',
              109201: 'Vanarama National League', 5123054: 'Vanarama National League North',
              5123055: 'Vanarama National League South',
              32: 'Serie A', 67: 'First Division', 2000048844: 'Spanish Federation 1A',
              2000048846: 'Spanish Federation 1B',
              22: 'Bundesliga', 16: 'Ligue 1 Uber Eats', 1: 'Jupiler Pro League', 29: 'Eredivisie',
              30: 'Keuken Kampioen Divisie', 45: 'William Hill SPFL', 129558: 'PKO BP Ekstraklasa',
              130672: 'JD Cymru Premier', 130023: 'NIFL Premiership', 6: '3F Superliga', 7: 'NordicBet Liga',
              102428: 'J1 League', 7920263: 'Saudi Pro League', 8403697: 'Optibet Virsliga'}


def career_totals(rows):
    """Total row of the in-game Career Stats screen over `rows`: fee (sum), apps, goals, assists, pom (sums of the
    recorded values only, None when no row has one) and avg = rating weighted by rated apps (None without a rated
    row). The game does the same: '-' cells (not recorded) are skipped."""
    def tot(k):
        v = [r[k] for r in rows if r.get(k) is not None]
        return sum(v) if v else None
    rr = [(r['rating'], r.get('rated') or r.get('apps') or 0) for r in rows if r.get('rating') is not None]
    w = sum(n for _x, n in rr)
    return {'fee': tot('fee'), 'apps': tot('apps'), 'goals': tot('goals'), 'assists': tot('assists'),
            'pom': tot('pom'), 'avg': round(sum(x * n for x, n in rr) / w, 2) if w else None}


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
_IDX = {}         # (id(clubs), id(sub_squads)) -> ({club id: club}, {club entity id: club}, {pid: club id of a youth/reserve array})


def _club_index(sd):
    clubs, sub = sd.get('clubs') or [], sd.get('sub_squads') or {}
    key = (id(clubs), id(sub))
    with _LOCK:
        hit = _IDX.get(key)
    if hit is None:
        by_id = {c['id']: c for c in clubs}
        by_ent = {c['id'] + 1: c for c in clubs}
        sub_of = {}
        for cid, kinds in sub.items():
            for pids in kinds.values():
                for pid in pids:
                    sub_of.setdefault(pid, cid)
        hit = (by_id, by_ent, sub_of)
        with _LOCK:
            _IDX.clear()
            _IDX[key] = hit
    return hit


def current_clubs(person, sd):
    """(club dict, parent club dict or None) the player belongs to NOW, or (None, None): the first-team squad
    club (the BORROWING club for a loan), else the youth/reserve array club (sub_squads), else the club of the
    last contract record (`employment`; on the 2 Jan 2028 snapshot these 8.2k players look like employed players,
    24% have season stats and 83% are adults, free agents with no club record: 2% and 19%).
    `person['loan_parent']` (gamedb.find_loans) gives the parent of a loanee."""
    by_id, by_ent, sub_of = _club_index(sd)
    pid = person.get('id')
    cur = by_id.get((sd.get('squads') or {}).get(pid)) or by_id.get(sub_of.get(pid))
    if cur is None:
        cur = by_ent.get((sd.get('employment') or {}).get(pid))
    par = by_id.get(person.get('loan_parent')) if cur is not None else None
    return cur, (par if par is not cur else None)


def current_season_year(ref, calendar_year=False):
    """Start year of the season running on `ref` (the save's in-game date): July-June, or the calendar year for
    the calendar-year leagues (CALENDAR_NATIONS)."""
    return ref.year if calendar_year or ref.month >= 7 else ref.year - 1


def _add_current(out, person, sd):
    """Append the CURRENT season row(s) to out['rows'] (oldest first, so last): the club the player is at now,
    preceded by his parent club on a loan. Season = the in-game date's; apps/goals from person['stats'] (all
    competitions of this season) else None. Not added when the rows already hold this season at that club."""
    cur, par = current_clubs(person, sd)
    if cur is None:
        return
    from fm_editor.agecalc import get_ref
    rows = out['rows']
    st = person.get('stats') or {}

    def row(c, kind, apps, goals, full=False):
        nat = c.get('nation')
        y = current_season_year(get_ref(), nat in CALENDAR_NATIONS)
        det = {'assists': st.get('assists'), 'pom': st.get('pom'), 'rating': st.get('rating'),
               'rated': st.get('rated')} if full else {'assists': None, 'pom': None, 'rating': None, 'rated': None}
        return y, {**det, 'division': COMP_NAMES.get((c.get('league') or {}).get('comp_uid')),
                   'year': y, 'year_end': None, 'kind': kind, 'apps': apps, 'goals': goals, 'fee': None,
                   'club_raw': None, 'comp': None, 'order': 0, 'start': None, 'end': None, 'club': c['name'],
                   'club_uid': c['uid'], 'nation': nat, 'from_save': True, 'current': True}

    y, r = row(cur, 'loan' if par else None, st.get('apps'), st.get('goals'), True)
    if any(x['club_uid'] == cur['uid'] and x['year'] >= y for x in rows):
        return
    if par is not None and not any(x['club_uid'] == par['uid'] and x['year'] >= y for x in rows):
        _y, pr = row(par, None, None, None)
        pr['current'] = False
        pr['parent'] = True
        rows.append({**pr, 'season': season_label(pr, pr['nation'] in CALENDAR_NATIONS)})
    rows.append({**r, 'season': season_label(r, r['nation'] in CALENDAR_NATIONS)})


# ---------------------------------------------------------------- past-season stats (player_stats_hist)
# `player_stats_hist_dt.cmt` (+ `rgman/player_stats_hist_ls.dat`): one 152-byte row per person, team, season and
# competition class, written when a season ends or a player changes team.  Row (offsets from the row start):
#   +1 u32 stats team id (= club['team']: Spurs 619, Como 946)   +5 u16 league index of that season (7 = English tier 1,
#   22 = Serie A: the division AT THE TIME, mapped to a comp uid in `Psh.comp_of`)   +7 u32 transfer fee on the row of
#   the club the player LEFT (ffffffff none)   +11 u16 season start year   +13 u16 rating sum x10   +15 u16 minutes
#   +23 u8 apps this season in the same competition class for the PREVIOUS club of the same season (carry-over)
#   +24 starts, +25 subs, +26 rated apps, +27 goals, +28 assists, +29 player of the match (u8)   +31 u8 competition class
#   (1 league, 0 friendlies, 2 domestic cup, 3 super cup, 4 continental): a person's rows of one team-season are a
#   GROUP, class ascending, and the group starts at the class-1 row (the league row the Career Stats screen shows).
# No person id in the rows.  The person -> rows link (verified on Nico Paz, see tests/test_history.py):
#   * game_db person record: u32 at `person['offset'] - 21` = SLOT in `_ls` (0xffffffff = none; 76,303 of 77,966 players,
#     all distinct; slots 51378-51391 are Spurs' 2026/27 squad: Maddison, Austin, van de Ven, Kulusevski, Udogie, Porro,
#     van Hecke, Tonali, Robertson, Simons, Savio, Kinsky, Bergvall, Gray);
#   * `_ls`: `u32 K @8`, K x u32 (a pending list, unused), `u32 N`, N x `u32 count` + count x u32, the count values =
#     off0, then pairs (rel, off).  The row offsets are the EVEN positions (off0, off1, ...; byte offset from body start,
#     /152 = row index); the odd positions are not row pointers.  The first pointer is exact (it is the class-1 row of
#     the person's first team-season: 86,013 of 86,021 entries) and its group continues contiguously; pointers after a
#     jump are STALE by 0-8 rows (the game inserted rows after writing them) so they only give a window: the group is
#     found by the carry-over check (+23 of the new group equals the previous group's apps of the same class).
#     Ties verified this way: Nico Paz Como 2026/27 -> Spurs 2026/27 (the in-game rows), Scalvini and 1,477 others.
_PSH_ROW = 152
_PSH = {}


class Psh:
    """Index of the player stats history of one save: `groups(slot)` -> the team-season groups of a person."""

    WINDOW = 8

    def __init__(self, dt, ls):
        import numpy as np
        n = self.n = (len(dt) - 8) // _PSH_ROW
        a = np.frombuffer(dt, np.uint8, count=n * _PSH_ROW, offset=8).reshape(n, _PSH_ROW)
        self.a = a
        self.flag = a[:, 31].tolist()
        self.team = np.ascontiguousarray(a[:, 1:5]).view('<u4').ravel().tolist()
        self.year = np.ascontiguousarray(a[:, 11:13]).view('<u2').ravel().tolist()
        self.apps = (a[:, 24].astype(np.int16) + a[:, 25]).tolist()
        self.j23 = a[:, 23].tolist()
        k = struct.unpack_from('<I', ls, 8)[0]
        p = 12 + 4 * k
        cnt = struct.unpack_from('<I', ls, p)[0]
        p += 4
        ents = []
        for _ in range(cnt):
            c = struct.unpack_from('<I', ls, p)[0]
            vals = struct.unpack_from('<%dI' % c, ls, p + 4)
            p += 4 + 4 * c
            ents.append(tuple(v // _PSH_ROW for v in vals[0::2] if v % _PSH_ROW == 0 and v // _PSH_ROW < n))
        self.ents = ents
        self.claimed = {}                       # first pointer (class-1 row) -> slot
        for s, e in enumerate(ents):
            if e and self.flag[e[0]] == 1 and self.year[e[0]] >= 2025:
                self.claimed[e[0]] = s
        self._ties = None
        self._comp = None

    def group(self, q):
        """Row indexes of the group starting at class-1 row q."""
        fl, tm, yr, n = self.flag, self.team, self.year, self.n
        r = q + 1
        while r < n and fl[r] != 1 and tm[r] == tm[q] and yr[r] == yr[q] and r - q < 8:
            r += 1
        return range(q, r)

    def _perflag(self, g):
        d = {}
        for r in g:
            d[self.flag[r]] = d.get(self.flag[r], 0) + self.apps[r]
        return d

    @property
    def ties(self):
        """{slot: [later group start rows]} verified by the carry-over check; a group wanted by two slots is dropped."""
        if self._ties is None:
            fl, tm, yr, n, j23 = self.flag, self.team, self.year, self.n, self.j23
            ties = {}
            for s, e in enumerate(self.ents):
                if len(e) < 2 or e[0] not in self.claimed or self.claimed[e[0]] != s:
                    continue
                chain = [self.group(e[0])]
                covered = set(chain[0])
                got = []
                for r in e[1:]:
                    if r in covered or yr[r] < 2025:
                        continue
                    prev = chain[-1]
                    old = self._perflag(prev)
                    best = []
                    for q in range(r, min(n, r + self.WINDOW + 1)):
                        if fl[q] != 1 or tm[q] != tm[r] or yr[q] != yr[r] or q in self.claimed:
                            continue
                        if tm[q] == tm[prev[0]] and yr[q] == yr[prev[0]]:
                            continue
                        g = self.group(q)
                        chk = [(fl[x], j23[x]) for x in g if j23[x] > 0]
                        if chk and all(old.get(f, 0) == v for f, v in chk):
                            best.append((len(chk), -(q - r), q))
                    best.sort(reverse=True)
                    if not best or (len(best) > 1 and best[0][0] == best[1][0]):
                        continue                    # nothing matches, or two candidates match equally well
                    g = self.group(best[0][2])
                    chain.append(g)
                    covered.update(g)
                    got.append(g[0])
                if got:
                    ties[s] = got
            want = {}
            for s, qs in ties.items():
                for q in qs:
                    want[q] = want.get(q, 0) + 1
            kept = {s: [q for q in qs if want[q] == 1] for s, qs in ties.items()}
            self._ties = {s: qs for s, qs in kept.items() if qs}
        return self._ties

    def comp_of(self, v):
        """Comp uid of the league index `v` (row +5): the modal club['league']['comp_uid'] of the clubs whose 2026/27 league
        rows carry it (None when unknown or when under 60% of the clubs agree)."""
        return (self._comp or {}).get(v)

    def build_comps(self, clubs):
        import collections
        bt = {c['team']: c for c in clubs if 'team' in c and c.get('league') and 'comp_uid' in c['league']}
        cnt = collections.defaultdict(collections.Counter)
        a = self.a
        for r in range(self.n):
            if self.flag[r] == 1 and self.year[r] == 2026 and self.apps[r] > 0 and self.team[r] in bt:
                cnt[int(a[r, 5]) | int(a[r, 6]) << 8][bt[self.team[r]]['league']['comp_uid']] += 1
        self._comp = {}
        for v, c in cnt.items():
            uid, k = c.most_common(1)[0]
            if k >= 20 and k >= 0.6 * sum(c.values()):
                self._comp[v] = uid

    def row(self, r):
        a = self.a
        rs = int(a[r, 13]) | int(a[r, 14]) << 8
        rated = int(a[r, 26])
        fee = int(a[r, 7]) | int(a[r, 8]) << 8 | int(a[r, 9]) << 16 | int(a[r, 10]) << 24
        return {'row': r, 'team': self.team[r], 'year': self.year[r], 'apps': self.apps[r], 'goals': int(a[r, 27]),
                'assists': int(a[r, 28]), 'pom': int(a[r, 29]), 'rated': rated,
                'rating': round(rs / 10 / rated, 2) if rated else None,
                'comp_idx': int(a[r, 5]) | int(a[r, 6]) << 8, 'fee': None if fee == 0xFFFFFFFF else fee}

    def groups(self, slot):
        """League rows (dicts, see `row`) of the person's team-seasons of 2025 on, in file order: the first group (exact)
        then the groups the carry-over check ties; [] when the slot has no usable pointer."""
        if slot is None or not 0 <= slot < len(self.ents):
            return []
        e = self.ents[slot]
        if not e or self.claimed.get(e[0]) != slot:
            return []
        out = [{**self.row(e[0]), 'tier': 1}]
        out += [{**self.row(q), 'tier': 2} for q in self.ties.get(slot, ())]
        return out


def psh_for(save_path, members):
    """Cached `Psh` of the save (None when the save has no player stats history members)."""
    if not save_path or not members:
        return None
    key = (save_path, os.path.getmtime(save_path))
    with _LOCK:
        hit = _PSH.get(key)
    if hit is not None:
        return hit or None
    by = {m['name']: m for m in members}
    dm, lm = by.get('player_stats_hist_dt.cmt'), by.get('rgman/player_stats_hist_ls.dat')
    psh = False
    if dm and lm:
        from fm_editor.archive import get_member
        try:
            psh = Psh(bytes(get_member(save_path, dm)), bytes(get_member(save_path, lm)))
        except Exception:
            psh = False
    with _LOCK:
        _PSH.clear()
        _PSH[key] = psh
    return psh or None


def person_slot(b, person):
    """Slot of `person` in the player stats history index (u32 21 bytes before the person record, after two null dates;
    0xffffffff = none), or None."""
    o = person.get('offset')
    if b is None or o is None or o < 29 or bytes(b[o - 29:o - 25]) != b'\x01\x00\x6c\x07':
        return None
    s = struct.unpack_from('<I', b, o - 21)[0]
    return None if s == 0xFFFFFFFF else s


def _add_past_stats(out, person, sd):
    """Fill assists/POM/rating of stored rows and ADD the team-seasons only the stats history holds (2025/26 on: the FM
    install database stops at 2024/25) from the person's tied groups. Clubs come from club['team'] (the stats team id);
    a team that is no club's first team (youth teams) is skipped."""
    b, path = sd.get('b'), sd.get('save_path')
    psh = psh_for(path, sd.get('members'))
    if psh is None or b is None:
        return
    gs = psh.groups(person_slot(b, person))
    if not gs:
        return
    clubs = sd.get('clubs') or []
    if psh._comp is None:
        psh.build_comps(clubs)
    by_team = {c['team']: c for c in clubs if 'team' in c}
    from fm_editor.agecalc import get_ref
    cur, par = current_clubs(person, sd)
    own = {c['uid'] for c in (cur, par) if c}      # the current season at these clubs is `_add_current`'s row
    rows = out['rows']
    new = []
    for g in gs:
        c = by_team.get(g['team'])
        if c is None or g['year'] < 2025 or not any(psh.apps[x] for x in psh.group(g['row']) if psh.flag[x]):
            continue                      # no club, or only friendlies played (class 0)
        nat = c.get('nation')
        if c['uid'] in own and g['year'] >= current_season_year(get_ref(), nat in CALENDAR_NATIONS):
            continue
        comp = psh.comp_of(g['comp_idx'])
        det ={'assists': g['assists'], 'pom': g['pom'], 'rating': g['rating'], 'rated': g['rated'], 'apps': g['apps'],
               'goals': g['goals']}
        hit = next((r for r in rows if r['club_uid'] == c['uid'] and r['year'] == g['year'] and not r.get('current')
                    and not r.get('parent')), None)
        if hit is not None:
            hit.update(det)
            if hit.get('fee') is None and g['fee'] is not None:
                hit['fee'] = g['fee']
            continue
        r = {**det, 'division': COMP_NAMES.get(comp), 'year': g['year'], 'year_end': None, 'kind': None,
             'fee': g['fee'], 'club_raw': None, 'comp': comp, 'order': 0, 'start': None, 'end': None,
             'club': c['name'], 'club_uid': c['uid'], 'nation': nat, 'from_save': True, 'current': False,
             'from_stats': True}
        r['season'] = season_label(r, nat in CALENDAR_NATIONS)
        new.append(r)
    if new:
        rows.extend(new)
        rows.sort(key=lambda r: r['year'])          # stable: stored rows keep their order inside a season


def _fee_to_buyer(rows):
    """The save keeps a transfer fee on the row of the club that SOLD the player; the game's Career Stats screen (Nico
    Paz: Tottenham 2026/27 shows the 97.9M as £98M, Como's row none) shows it on the row of the club he JOINED. Move each
    fee to the next row of another club in the same or the next season (a summer move ends the old row's season); a row
    from the stats history (a move inside 2026/27) needs the same season. With no such row (the buying club's row is
    missing) the fee is not shown rather than put on a wrong row."""
    fees = [r.get('fee') for r in rows]
    for r in rows:
        r['fee'] = None
    for i, f in enumerate(fees):
        if f is None:
            continue
        r = rows[i]
        for j in range(i + 1, len(rows)):
            n = rows[j]
            if n.get('club_uid') == r.get('club_uid') or n.get('parent'):
                continue
            gap = n['year'] - r['year']
            if (gap == 0 or gap == 1 and not r.get('from_stats')) and n['fee'] is None:
                n['fee'] = f
            break


def career_for_person(person, save_data, uid=None):
    """History of ONE player for the player window. `person` = people-list dict, `save_data` = the app's save
    dict ('b', 'members', 'save_path', 'clubs', 'squads', 'sub_squads', 'employment'). Returns {'status':
    'ok'|'no_install'|'none'|'no_uid', 'rows': [dict: season, year, kind, apps, goals, fee, club, club_uid,
    nation, from_save, current], 'install_dir'}. Rows are the install DB + save rows (status 'ok') PLUS, whenever
    the player has a club now, the current season row (`_add_current`), so a player without stored history
    (status 'none', e.g. a newgen) still shows his club; status keeps saying why the stored history is missing."""
    out = _career_stored(person, save_data, uid)
    for step in (_add_past_stats, _add_current):
        try:
            step(out, person, save_data or {})
        except Exception:
            pass                            # both are bonuses: never break the tab
    _fee_to_buyer(out['rows'])
    return out


def _career_stored(person, save_data, uid=None):
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
                            'assists': None, 'pom': None, 'rating': None, 'rated': None,
                            'division': COMP_NAMES.get(r['comp']),
                            'season': season_label(r, nat in CALENDAR_NATIONS), 'current': False})
    out['status'] = 'ok'
    return out
