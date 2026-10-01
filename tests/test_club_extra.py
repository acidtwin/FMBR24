"""Ground-truth check for reputation / stadium / league table / scouting budget (fm_editor/clubextra.py)
against the real 2026-27 Spurs save (in-game date 2 Jan 2028, user screenshots).

Run directly: python3 tests/test_club_extra.py   (skips politely if the save is absent)
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.test_club_info import SAVE  # noqa: E402


def test_club_extra():
    from fm_editor.archive import parse_archive, get_member
    from fm_editor.gamedb import find_names, find_clubs
    from fm_editor import clubextra as X

    _, members, _, _, _, _ = parse_archive(SAVE)
    by = {m['name']: m for m in members}
    gdb = get_member(SAVE, by['game_db.dat'])
    cl = find_clubs(gdb, find_names(gdb)[2])
    X.add_club_status(gdb, cl)
    X.add_club_stadiums(gdb, cl, get_member(SAVE, by['rgman/fix_man.dat']))
    X.add_league_positions(cl, [X.parse_comp_table(get_member(SAVE, m)) for n, m in by.items()
                                if re.fullmatch(r'rgman/comp_\d+\.dat', n)])
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

    # league tables vs in-game screens (Championship, League Two, Premier League)
    def rec(n):
        g = c[n]['league']
        return g['pos'], g['of'], g['P'], g['W'], g['D'], g['L'], g['GF'], g['GA'], g['PTS']
    assert rec('Charlton Athletic') == (23, 24, 26, 5, 8, 13, 22, 34, 23)
    assert rec('Fulham') == (1, 24, 25, 17, 3, 3 + 2, 47, 23, 54)
    assert rec('Southampton') == (2, 24, 26, 13, 9, 4, 44, 28, 48)
    assert rec('Hull City')[0] == 3 and rec('Middlesbrough')[0] == 4 and rec('West Bromwich Albion')[0] == 5
    assert rec('Swansea City') == (9, 24, 25, 10, 7, 8, 31, 31, 37)
    assert rec('Barnet')[:3] == (12, 24, 27)
    assert rec('Tottenham Hotspur') == (1, 20, 20, 14, 5, 1, 56, 24, 47)

    # scouting budget: human club only (Spurs in-game 150,000)
    sb = X.find_human_scouting_budget(gdb)
    assert sb and sb[0] == 150_000, sb


if __name__ == '__main__':
    if not os.path.exists(SAVE):
        print('SKIP: save file not found')
    else:
        test_club_extra()
        print('OK')
