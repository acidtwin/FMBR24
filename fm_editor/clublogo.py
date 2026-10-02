"""Club UniqueID in the save -> the id club logos are filed under. Pure python, no Qt, READ-ONLY on the game folders.

Logo packs name a club's picture by the club's game UniqueID (`graphics/pictures/club/<id>/logo`, FM resolves them through the
pack's config.xml; sortitoutsi lists Tottenham as team 728, Bayern 915, Real Madrid 1736, Galatasaray 1871). The club uid
we parse from game_db (`club['uid']`, record +4, written twice) is NOT that number: Spurs 727, Bayern 913, Real Madrid 1733,
Galatasaray 1870. The logo id is the uid of the NEXT club in the complete, uid-sorted club list (727 -> 728 Tranmere,
913 -> 915 Koeln, 1733 -> 1736 R. Madrid B, 1870 -> 1871 Gaziantepspor). It is the same rule fm_editor/history.py found for the
club field of career rows (`club_for`); the reason is unknown. Verified: ~25 clubs by eye (logo images), and on 92 clubs
through the career rows of their players (84 agree, the rest are players on another team of the club).

"Complete" matters: the save holds 44k clubs of the first record layout plus 8.4k of a second layout (`find_hidden_club_uids`), the
install DB (server_db.dat table_3) 82k clubs. A club whose next club is not loaded in the save gets the wrong id from the save alone
(about 1 of 4 on the dev save), so the install DB list is merged in when it can be found (history.install_db_dir).
"""
import bisect
import os
import struct
import tempfile

from fm_editor import history as _history


def _scan_table(b):
    """uids of every club record in table_3 bytes: both record layouts (see gamedb.find_hidden_club_uids / find_clubs)."""
    out = set()
    search = 13
    while True:
        ff = b.find(b'\xff\xff\xff\xff', search)
        if ff < 0:
            break
        search = ff + 1
        for at, nat_at in ((ff - 13, ff + 4), (ff - 17, ff - 4)):   # layout 2 (ffffffff at +13) / layout 1 (nation at +13)
            if at < 0 or ff + 12 > len(b) or b[at + 12]:
                continue
            nation = struct.unpack_from('<I', b, nat_at)[0]
            if nation > 255 or struct.unpack_from('<I', b, at + 21)[0] != nation or struct.unpack_from('<I', b, at + 25)[0] != nation:
                continue
            cid, uid, uid2 = struct.unpack_from('<III', b, at)
            if uid and uid != 0xFFFFFFFF and uid == uid2 and cid <= 100000:
                out.add(uid)
    return out


def install_club_uids(d):
    """Sorted uids of every club in the install DB dir `d` (the *_fm folder). Cached on disk next to the history caches
    (a *.json.club file, so Settings > Clear cache does not list it). Raises on a missing/unreadable server_db.dat."""
    import json
    src = os.path.join(d, 'server_db.dat')
    st = os.stat(src)
    cp = None
    try:
        from fm_editor.cache import cache_dir
        cp = os.path.join(cache_dir(), 'clubuids-%d-%d.json.club' % (st.st_size, int(st.st_mtime)))
        with open(cp, encoding='utf-8') as f:
            got = json.load(f)
        if isinstance(got, list) and got:
            return got
    except Exception:
        pass
    from fm_editor.archive import get_member, parse_archive
    with open(src, 'rb') as f:
        f.seek(8)                         # tad wrapper, the FMF archive starts at byte 8
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
    uids = sorted(_scan_table(b))
    if cp:
        try:
            os.makedirs(os.path.dirname(cp), exist_ok=True)
            with open(cp, 'w', encoding='utf-8') as f:
                json.dump(uids, f, separators=(',', ':'))
        except OSError:
            pass
    return uids


def merged_uids(save_uids, extra=(), install_dir=None):
    """Sorted unique club uids: the save's clubs + its second-layout clubs + (when `install_dir` reads) the install DB's."""
    s = set(save_uids) | set(extra or ())
    if install_dir:
        try:
            s.update(install_club_uids(install_dir))
        except Exception:
            pass                          # no / unreadable install DB: save-only list (less exact, see module doc)
    return sorted(s)


def logo_id(uids, club_uid):
    """The id the logo packs use for the club with save uid `club_uid`: the next uid in the sorted list `uids`, or None."""
    i = bisect.bisect_right(uids, club_uid)
    return uids[i] if i < len(uids) else None


def build(save_clubs, extra=(), save_path=None):
    """Sorted uid list for a loaded save (finds the install DB next to the save's Steam library)."""
    return merged_uids((c['uid'] for c in save_clubs or () if c.get('uid')), extra, _history.install_db_dir(save_path))
