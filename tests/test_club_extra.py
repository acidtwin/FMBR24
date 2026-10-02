"""Ground-truth check for reputation / stadium / league table / scouting budget (fm_editor/clubextra.py)
against the real 2026-27 Spurs save (in-game date 2 Jan 2028, user screenshots).
Runs on the frozen 2028-01-02 snapshot (tests/snapshot.py), so the exact league tables and scouting budget are asserted.

Run directly: python3 tests/test_club_extra.py   (skips politely if the frozen snapshot is absent)
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.snapshot import snapshot_save, skip_if_missing, assert_snapshot  # noqa: E402  (frozen 2028-01-02 copy, never the live save)

SAVE = snapshot_save()


def test_club_extra():
    assert_snapshot(SAVE)
    from fm_editor.archive import parse_archive, get_member
    from fm_editor.gamedb import find_names, find_clubs
    from fm_editor import clubextra as X

    _, members, _, _, _, _ = parse_archive(SAVE)
    by = {m['name']: m for m in members}
    gdb = get_member(SAVE, by['game_db.dat'])
    cl = find_clubs(gdb, find_names(gdb)[2])
    X.add_club_status(gdb, cl)
    fix = get_member(SAVE, by['rgman/fix_man.dat'])
    X.add_club_stadiums(gdb, cl, fix)
    X.add_league_positions(cl, [X.parse_comp_table(get_member(SAVE, m)) for n, m in by.items()
                                if re.fullmatch(r'rgman/comp_\d+\.dat', n)], fix)
    c = {x['name']: x for x in cl}

    # reputation (raw u16): Barnet screen = 2 stars, Charlton = 3 stars; star mapping itself UNCONFIRMED
    assert (c['Barnet']['rep'], c['Charlton Athletic']['rep'], c['Tottenham Hotspur']['rep']) == (4349, 6153, 8553)
    assert c['Tottenham Hotspur']['rep'] > c['Charlton Athletic']['rep'] > c['Barnet']['rep']
    assert sum('rep' in x for x in cl) > 43000 and all(1 <= x['rep'] <= 10000 for x in cl if 'rep' in x)

    # stadium vs Club page: Charlton The Valley 27,111 built 1919; Barnet used capacity 6,421; Spurs 62,850 / 2019
    s = c['Charlton Athletic']['stadium']
    assert (s['capacity'], s['built']) == (27111, 1919), s
    assert c['Barnet']['stadium']['capacity'] == 6421 and c['Barnet']['stadium']['seats'] == 6500
    assert (c['Tottenham Hotspur']['stadium']['capacity'], c['Tottenham Hotspur']['stadium']['built']) == (62850, 2019)

    # which clubs carry league data is a fixed fact
    assert all('league' in c[n] for n in ('Charlton Athletic', 'Fulham', 'Southampton', 'Hull City', 'Middlesbrough',
                                          'West Bromwich Albion', 'Swansea City', 'Barnet', 'Tottenham Hotspur'))

    def rec(n):
        g = c[n]['league']
        return g['pos'], g['of'], g['P'], g['W'], g['D'], g['L'], g['GF'], g['GA'], g['PTS']
    # league tables vs in-game screens (Championship, League Two, Premier League) at the snapshot date
    assert rec('Charlton Athletic') == (23, 24, 26, 5, 8, 13, 22, 34, 23)
    assert rec('Fulham') == (1, 24, 25, 17, 3, 5, 47, 23, 54)
    assert rec('Southampton') == (2, 24, 26, 13, 9, 4, 44, 28, 48)
    assert rec('Hull City')[0] == 3 and rec('Middlesbrough')[0] == 4 and rec('West Bromwich Albion')[0] == 5
    assert rec('Swansea City') == (9, 24, 25, 10, 7, 8, 31, 31, 37)
    assert rec('Barnet')[:3] == (12, 24, 27)
    assert rec('Tottenham Hotspur') == (1, 20, 20, 14, 5, 1, 56, 24, 47)
    # invariants hold for every club. Only round-robin tables count as a league (cup group stages such as the
    # Scottish League Cup, comp_1301431, flattened 24 clubs / P=4, used to be attached to Scottish lower-league clubs, whose
    # own divisions have no table in the save): so PTS == 3W+D always (no shootout bonus points) and 1 <= pos <= of
    for x in cl:
        if 'league' in x:
            pos, of, P, W, D, L, GF, GA, PTS = rec(x['name'])
            assert P == W + D + L and PTS == 3 * W + D and 1 <= pos <= of and GF >= 0 and GA >= 0, (x['name'], x['league'])
            assert P <= 2 * (of - 1) + 4, (x['name'], x['league'])   # a 3-4 team cup group stage inside a big table would break this
    # the 8 clubs that got comp 603 (League Cup group): no league now, or at least a real league size, never the 24-club group
    for n in ('Alloa Athletic', 'Ayr United', 'Raith Rovers', 'Clyde', 'Partick Thistle', 'Ross County', 'Peterhead', 'Annan Athletic'):
        lg = c[n].get('league')
        assert lg is None or lg['of'] in (10, 12), (n, lg)
    # Scottish Premiership has a real 12-team table
    assert all(c[n]['league']['of'] == 12 for n in ('Celtic', 'Rangers'))
    # English league tiers keep their data (24/20-team tables)
    assert sum(x.get('league', {}).get('of') in (20, 24) for x in cl) > 100

    # scouting budget: human club only. The snapshot is the save the user made right after the 'scouting budget change'
    # (it used to read 150,000 before that edit), so the stored value is pinned to what the frozen copy holds
    sb = X.find_human_scouting_budget(gdb)
    assert sb and sb[0] == 2_340_000, sb


def _fix(*pairs):
    """Minimal fix_man.dat bytes: one fixture record per (home, away), in the layout _FIX_RX reads."""
    u = lambda v: v.to_bytes(4, 'little')  # noqa: E731
    return b''.join(b'\x18' + u(0) + u(5) + b'\x02\x00\x00' + u(h) + b'\xff\x00\x00' + u(a) + b'\xff\x00' for h, a in pairs)


def test_league_position_ranking():
    """4-team synthetic table: points, then goal difference, then goals for (rows are P, W, D, L, GF, GA, PTS)."""
    from fm_editor import clubextra as X
    tab = {14: (6, 3, 1, 2, 20, 18, 10),   # 10 pts, GD +2, GF 20
           13: (6, 3, 1, 2, 10, 5, 10),    # 10 pts, GD +5, GF 10
           12: (6, 3, 1, 2, 12, 7, 10),    # 10 pts, GD +5, GF 12 -> above 13 on goals for
           11: (6, 6, 0, 0, 9, 0, 18)}     # leader
    clubs = [{'team': t} for t in (11, 12, 13, 14)]
    X.add_league_positions(clubs, [tab])
    assert [c['league']['pos'] for c in clubs] == [1, 2, 3, 4], [c['league'] for c in clubs]
    assert all(c['league']['of'] == 4 for c in clubs)


def test_is_league_table():
    from fm_editor import clubextra as X
    league = list(range(100, 110))
    fix = _fix(*[(a, b) for a in league for b in league if a != b], (100, 200), (200, 100), (101, 201), (201, 101))
    assert X.fixture_pairs(fix) >= {frozenset((100, 101)), frozenset((100, 200))}
    row = lambda p: (p, 1, 2, p - 3, 5, 5, 5)  # noqa: E731
    cup = {100: row(6), 101: row(6), 200: row(6), 201: row(6)}   # two 2-team groups: only (100,200) and (101,201) meet
    tab = {t: row(4) for t in league}
    assert X.is_league_table(tab, X.fixture_pairs(fix)) and not X.is_league_table(cup, X.fixture_pairs(fix))
    # the cup table has MORE games for 100/101 but must not win: club 100 gets the 10-team league
    clubs = [{'team': t} for t in (100, 101, 102, 200)]
    X.add_league_positions(clubs, [cup, tab], fix)
    assert [c.get('league', {}).get('of') for c in clubs] == [10, 10, 10, None]
    # no table passes (e.g. no fixtures at all): fall back to the 'most games' rule instead of dropping everything
    X.add_league_positions(clubs, [cup], _fix((1, 2)))
    assert clubs[0]['league']['of'] == 4


if __name__ == '__main__':
    test_league_position_ranking()
    test_is_league_table()
    skip_if_missing()
    test_club_extra()
    print('OK')
