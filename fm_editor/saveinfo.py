"""Save metadata ("Save Info" page): game name, dates, times saved, version, manager, club...

Sources (all verified against a real FM24 save, see memory fm24-binary-format.md):
  archive_name (FMF index)      -> game_name
  game_info.dat  (small member) -> times_saved @0x42, date_created @0x46, game_build @0x4a
  save_game_summary.dat (small) -> nations/leagues, game_version, manager, club, in_game_date, game_time
  game_db.dat header (optional) -> database_version @0x14, database_changes @0x28
  rgman/rgman.dat header        -> start_date (ISO): the in-game "Game Start Date". The nation part
                                   ("Italy") is the wizard's explicit "Starting Nation" option, NOT the
                                   human manager's first job (his only job link is the current club, and
                                   tc_manager_history holds no entry for him) -> start_nation not derivable
                                   yet, deliberately omitted (see memory fm24-binary-format.md)

Returns a plain JSON-serialisable dict; a key is present ONLY if it was found and passed
sanity checks. Never raises for a missing/odd member - just returns a smaller dict.
"""
import struct
from datetime import date, timedelta

_MAGIC = b'\x03\x01tad.'


def _u16(b, p): return struct.unpack_from('<H', b, p)[0]
def _u32(b, p): return struct.unpack_from('<I', b, p)[0]


def _date(b, p):
    """FM date at p: u16 (day-of-year in low 9 bits, high bits are flags) + u16 year -> 'YYYY-MM-DD'."""
    doy, year = _u16(b, p) & 0x1FF, _u16(b, p + 2)
    if not (1 <= doy <= 366 and 1900 <= year <= 2200):
        return None
    try:
        return (date(year, 1, 1) + timedelta(doy - 1)).isoformat()
    except (ValueError, OverflowError):
        return None


def _game_info(b, out):
    if bytes(b[:6]) != _MAGIC or len(b) < 0x52:
        return
    n = _u32(b, 0x42)
    if 1 <= n <= 1_000_000:
        out['times_saved'] = n
    d = _date(b, 0x46)
    if d:
        out['date_created'] = d
    build = _u32(b, 0x4A)
    if 100_000 <= build < 100_000_000 and build == _u32(b, 0x4E):  # stored twice
        out['game_build'] = build


def _pstr(b, p, maxlen=200):
    """u32-length-prefixed string at p -> (str, next_pos) or (None, p) if implausible."""
    if p + 4 > len(b):
        return None, p
    n = _u32(b, p)
    if n > maxlen or p + 4 + n > len(b):
        return None, p
    try:
        s = bytes(b[p + 4:p + 4 + n]).decode('utf-8')
    except UnicodeDecodeError:
        return None, p
    return s, p + 4 + n


def _summary(b, out):
    if bytes(b[:6]) != _MAGIC or len(b) < 20:
        return
    # nations: u32 len + CSV "id,GENDER,flag,flag,id,..." (4 fields per nation)
    csv, p = _pstr(b, 8, 100_000)
    if csv is None:
        return
    fields = csv.split(',')
    if len(fields) % 4 == 0 and fields != ['']:
        out['nations_count'] = len(fields) // 4
    ver, p = _pstr(b, p, 32)
    if ver and ver.replace('.', '').isdigit():
        out['game_version'] = ver
    else:
        return
    # leagues: u32 count + strings, one per loaded nation
    if p + 4 > len(b):
        return
    cnt = _u32(b, p); p += 4
    if cnt > 1000:
        return
    leagues = []
    for _ in range(cnt):
        s, p = _pstr(b, p, 100)
        if s is None:
            return
        leagues.append(s)
    if leagues:
        out['leagues'] = leagues
    # then: 01, u32 (save id?), u16, 01, manager name, club (short) name, date, u32 game-time seconds
    p += 8
    name, p = _pstr(b, p, 100)
    if not name:
        return
    out['manager_name'] = name
    club, p = _pstr(b, p, 100)
    if club is None:
        return
    if club:
        out['manager_club_short'] = club  # empty string = unemployed
    if p + 8 <= len(b):
        d = _date(b, p)
        if d:
            out['in_game_date'] = d
        secs = _u32(b, p + 4)
        if 0 < secs < 10 ** 9:
            out['game_time_seconds'] = secs


def _gamedb_header(b, out):
    if len(b) < 64 or bytes(b[:6]) != _MAGIC:
        return
    ver = bytes(b[0x14:0x18])
    if ver.isdigit() and len(ver) == 4:  # b"2430" -> 24.3.0
        out['database_version'] = f'{ver[:2].decode()}.{ver[2:3].decode()}.{ver[3:4].decode()}'
    ch = _u32(b, 0x28)
    if 0 < ch < 10 ** 9:
        out['database_changes'] = ch
    if 'in_game_date' not in out:
        d = _date(b, 0x24)
        if d:
            out['in_game_date'] = d


def _rgman(b, out):
    """rgman/rgman.dat header: game start date sits right before a null date (1900-01-00 = 01 00 6c 07)."""
    if len(b) < 0x40 or bytes(b[:6]) != _MAGIC:
        return
    i = bytes(b[:0x40]).find(b'\x01\x00\x6c\x07', 10)
    if i >= 4:
        d = _date(b, i - 4)
        if d:
            out['start_date'] = d


def _resolve_club(out, gdb, clubs, people):
    short = out.get('manager_club_short')
    if not short or not clubs:
        return
    cands = [c for c in clubs if c['short'] == short or c['name'] == short]
    chosen = None
    if gdb is not None and people:
        ids = {c['id'] + 1: c for c in cands}  # entity id = club id + 1
        for p in people:
            if p.get('name') != out.get('manager_name'):
                continue
            end = p['end']
            if end + 35 > len(gdb):
                continue
            for k in range(min(gdb[end + 34], 60)):
                r = end + 35 + k * 16
                if r + 16 <= len(gdb) and gdb[r + 10] == 0x01 and gdb[r + 11] == 0x03:
                    hit = ids.get(_u32(gdb, r))
                    if hit:
                        chosen = hit
                        break
            if chosen:
                break
    if chosen is None and len(cands) == 1:
        chosen = cands[0]
    if chosen:
        out['manager_club_id'] = chosen['id']
        out['manager_club_name'] = chosen['name']


def human_pids(humans_dat, known_pids=None):
    """Person ids of the human managers, from humans.dat.

    Layout (identical in all 6 distinct humans / ~30 saves checked): header, u16 count @8, then one
    record per human starting with the u32 person id (@10 for the first); every record carries the
    float -1.0 (00 00 80 bf) exactly 16 bytes after its pid. Only single-human saves were available:
    for count > 1 the later records are found by that anchor, unverified.
    """
    d = humans_dat
    if not d or len(d) < 14 or bytes(d[:6]) != _MAGIC:
        return []
    n = min(_u16(d, 8), 16)
    out = [_u32(d, 10)] if n >= 1 else []
    p = 30
    while len(out) < n:
        i = bytes(d).find(b'\x00\x00\x80\xbf', p)
        if i < 16:
            break
        pid = _u32(d, i - 16)
        if pid not in out and (known_pids is None or pid in known_pids):
            out.append(pid)
        p = i + 4
    return out


def human_club_ids(save_data, humans_dat=None):
    """Club ids (not entity ids) managed by a human in this save. Always includes
    save_info['manager_club_id'] when known. Each human's club is his job link (b10=1, b11=3),
    whose first u32 is the club entity id (= club id + 1)."""
    out = set()
    si = save_data.get('save_info') or {}
    if si.get('manager_club_id') is not None:
        out.add(si['manager_club_id'])
    b, people = save_data.get('b'), save_data.get('people') or []
    if humans_dat is None or b is None:
        return out
    ids = {c['id'] for c in save_data.get('clubs') or []}
    by_id = {p.get('id'): p for p in people}
    for pid in human_pids(humans_dat, by_id):
        p = by_id.get(pid)
        if not p or 'end' not in p:
            continue
        e = p['end']
        if e + 35 > len(b):
            continue
        for k in range(min(b[e + 34], 60)):
            r = e + 35 + k * 16
            if r + 16 <= len(b) and b[r + 10] == 0x01 and b[r + 11] == 0x03 \
                    and _u32(b, r) - 1 in ids:
                out.add(_u32(b, r) - 1)
                break
    return out


def parse_save_info(save_path, members, archive_name=None, gdb=None, clubs=None,
                    people=None, get_member_fn=None):
    """Build the Save Info dict.

    save_path    : .fm path
    members      : member list from parse_archive()
    archive_name : parse_archive()[3] (== in-game "Game Name")
    gdb          : already-decompressed game_db.dat (optional; adds database_* fields)
    clubs/people : find_clubs()/find_people()+match_identities() results (optional; resolve
                   manager_club_id / manager_club_name)
    get_member_fn: defaults to fm_editor.archive.get_member (only ~5 KB of small members read)
    """
    if get_member_fn is None:
        from fm_editor.archive import get_member as get_member_fn
    out = {}
    if archive_name:
        out['game_name'] = archive_name
    by_name = {m['name']: m for m in members if m.get('group', '') == ''}
    for fname, fn in (('game_info.dat', _game_info), ('save_game_summary.dat', _summary)):
        m = by_name.get(fname)
        if m:
            fn(get_member_fn(save_path, m), out)
    m = next((x for x in members if x.get('name') == 'rgman/rgman.dat'), None)
    if m:
        try:
            _rgman(get_member_fn(save_path, m), out)
        except Exception:  # never raise for a bad member
            pass
    if gdb is not None:
        _gamedb_header(gdb, out)
    _resolve_club(out, gdb, clubs, people)
    return out
