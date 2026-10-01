"""Club reputation, league position, stadium and scouting budget (FM24 game_db.dat + rgman members).

All layouts were decoded against the real 2026-27 Spurs save (2 Jan 2028 state) and checked with
in-game screens; see memory fm24-binary-format.md section 10. Every reader returns None/skips on
anything that does not match structurally - callers show PENDING for missing values.
"""
import re
import struct

_u32 = lambda b, p: struct.unpack_from('<I', b, p)[0]

# -- Club status table: reputation (1-10000) + last completed season's league finish ------------
# Anchor h: u32 ordinal @h-4, u32 uid, u32 uid (copy) @h, kind 0x0a/0x0b @h+8, last league
# position u8 @h+10, reputation u16 @h+11. Team id used by fixtures / league tables = ordinal+1.
_STATUS_RX = re.compile(rb'\x00{10}(....)(....)\2([\x0a\x0b])(.)(.)(..)', re.S)


def add_club_status(b, clubs):
    """Set club['rep'] (1-10000), club['last_pos'] (0 = none) and club['team'] (fixture team id)."""
    by_uid = {c['uid']: c for c in clubs}
    for m in _STATUS_RX.finditer(b):
        c = by_uid.get(_u32(m.group(2), 0))
        rep = struct.unpack('<H', m.group(6))[0]
        if c is None or 'rep' in c or not 1 <= rep <= 10000:
            continue
        c['rep'] = rep
        c['last_pos'] = m.group(5)[0]
        c['team'] = _u32(m.group(1), 0) + 1


# -- Stadium table: 181-byte rows, ordinal 1.. ----------------------------------------------------
# +0 ordinal, +4 uid, +8 uid copy, +12 zero, +13 all-seater capacity, +21 expansion capacity,
# +29 owner club entity id (club id + 1, ffffffff none), +34 "used capacity" (0 = not set),
# +50 built (u16 day-of-year, u16 year). Names/cities are not stored in the save.
_STAD_RX = re.compile(rb'\x01\x00\x00\x00(....)\1\x00', re.S)
_STAD_ROW = 181


def find_stadium_table(b):
    """Offset of the ordinal-1 row, or None (needs 7 consecutive well-formed rows)."""
    for m in _STAD_RX.finditer(b):
        p = m.start()
        if all(b[p + _STAD_ROW * (k - 1):p + _STAD_ROW * (k - 1) + 4] == struct.pack('<I', k)
               and b[p + _STAD_ROW * (k - 1) + 4:p + _STAD_ROW * (k - 1) + 8]
               == b[p + _STAD_ROW * (k - 1) + 8:p + _STAD_ROW * (k - 1) + 12]
               and not b[p + _STAD_ROW * (k - 1) + 12] for k in range(2, 8)):
            return p
    return None


def stadium_row(b, base, ordinal):
    """{'seats','expansion','capacity','built'} for 1-based row `ordinal`, or None if past the table."""
    o = base + _STAD_ROW * (ordinal - 1)
    if o + _STAD_ROW > len(b) or _u32(b, o) != ordinal:
        return None
    seats, exp, used = _u32(b, o + 13), _u32(b, o + 21), _u32(b, o + 34)
    return {'seats': seats, 'expansion': exp, 'capacity': used or seats,
            'built': struct.unpack_from('<H', b, o + 52)[0]}


# -- Fixtures (fix_man.dat): home ground = modal stadium of a team's home fixtures ---------------
_FIX_RX = re.compile(rb'\x18.{4}(....)\x02..(....)\xff\x00.(....)\xff\x00', re.S)


def home_grounds(fix):
    """{team id: stadium ordinal (1-based row)} from fixtures' (stadium u32 = ordinal+1, home team)."""
    cnt = {}
    for m in _FIX_RX.finditer(fix):
        key = (_u32(m.group(2), 0), _u32(m.group(1), 0))
        cnt[key] = cnt.get(key, 0) + 1
    best = {}
    for (team, st), n in cnt.items():
        if n > best.get(team, (0, 0))[0]:
            best[team] = (n, st)
    return {t: st - 1 for t, (n, st) in best.items() if st >= 2}


def add_club_stadiums(b, clubs, fix):
    base = find_stadium_table(b)
    if base is None or not fix:
        return
    grounds = home_grounds(fix)
    for c in clubs:
        o = grounds.get(c.get('team'))
        s = stadium_row(b, base, o) if o else None
        if s:
            c['stadium'] = s


# -- League tables: rgman/comp_<id>.dat 17-byte rows -----------------------------------------------
# ff ff ff ff | P | P | W | D | L | 00 | GF u16 | GA u16 | PTS u16 | 00 ; 5 aggregate rows per team
# (total, home, away, ...); team id u32 at first row - 23; every team appears twice (current and
# previous matchday): the block with more games played wins.
_ROW_RX = re.compile(rb'\xff\xff\xff\xff(.)\1(.)(.)(.)\x00(..)(..)(..)\x00', re.S)


def parse_comp_table(d):
    """{team id: (P, W, D, L, GF, GA, PTS)} for one competition stage file."""
    rows = {}
    for m in _ROW_RX.finditer(d):
        s = m.start()
        p, w, dr, l = m.group(1)[0], m.group(2)[0], m.group(3)[0], m.group(4)[0]
        if p == 0 or w + dr + l != p or s < 23 or (s >= 17 and _ROW_RX.match(d, s - 17)):
            continue  # not a consistent row / not the first (total) row of a group
        h, a = _ROW_RX.match(d, s + 17), _ROW_RX.match(d, s + 34)  # home + away rows must add up
        if not (h and a and h.group(1)[0] + a.group(1)[0] == p):
            continue
        gf, ga, pts = (struct.unpack('<H', m.group(i))[0] for i in (5, 6, 7))
        t = _u32(d, s - 23)
        if t not in rows or p > rows[t][0]:
            rows[t] = (p, w, dr, l, gf, ga, pts)
    return rows


def add_league_positions(clubs, tables):
    """tables = [ {team: row} per comp ]. club['league'] = {pos, of, P, W, D, L, GF, GA, PTS, comp}
    from the comp where the club has played most games (= its league, not a cup/euro phase)."""
    by_team = {c['team']: c for c in clubs if 'team' in c}
    best = {}
    for ci, tab in enumerate(tables):
        if len(tab) < 2:
            continue
        ranked = sorted(tab.items(), key=lambda kv: (-kv[1][6], -(kv[1][4] - kv[1][5]), -kv[1][4]))
        for pos, (t, r) in enumerate(ranked, 1):
            if t in by_team and r[0] > 0 and r[0] >= best.get(t, (0,))[0]:
                best[t] = (r[0], ci, pos, len(ranked), r)
    for t, (p, ci, pos, n, r) in best.items():
        by_team[t]['league'] = {'pos': pos, 'of': n, 'P': r[0], 'W': r[1], 'D': r[2], 'L': r[3],
                                'GF': r[4], 'GA': r[5], 'PTS': r[6], 'comp': ci}


# -- Human club's scouting budget -----------------------------------------------------------------
# Tagged-field signature right before the human manager's pair [u32 390000][u32 scouting budget].
# AI clubs do not carry it (single hit per save). Verified by diffing saves 150,000 -> 2,340,000.
_SCOUT_SIG = b'smti\x01\x11\x00sloc\x01\x0b\x00\x00\x00\x00rbls\x01\x11\xff'


def find_human_scouting_budget(b):
    """(GBP value, offset of the u32) for the human-managed club, or None."""
    p = b.find(_SCOUT_SIG)
    if p < 0 or b.find(_SCOUT_SIG, p + 1) >= 0:
        return None
    o = p + len(_SCOUT_SIG)
    if _u32(b, o) != 390000:
        return None
    return _u32(b, o + 4), o + 4


def rep_stars(rep):
    """Club reputation (1-10000) -> stars 0-5 in half steps. FITTED, not decoded: rep/2000 rounded to the nearest
    half star matches in-game screens (Barnet 4349=2, Charlton 6153=3, Barcelona 9005=4.5), except the top end:
    PSG 9197 shows 5, so 5 stars starts at 9100 (midpoint of 9005..9197, unverified). More screenshots refine it."""
    if not rep:
        return 0.0
    return 5.0 if rep >= 9100 else min(4.5, round(rep / 2000 * 2) / 2)
