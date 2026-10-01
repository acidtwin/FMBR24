"""Injuries come from injury_manager.dat (verified vs in-game 12 Jan 2028). Plain script; skips without the save."""
import datetime
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tests.test_parse_golden import SAVE


def test_injuries():
    if not os.path.exists(SAVE):
        print('SKIP: save not found'); return
    from fm_editor.archive import parse_archive, get_member
    from fm_editor import gamedb as G
    from fm_editor.saveinfo import parse_save_info
    _, members, _, name, _, _ = parse_archive(SAVE)
    b = get_member(SAVE, next(m for m in members if m['name'] == 'game_db.dat'))
    today = datetime.date.fromisoformat(str(parse_save_info(SAVE, members, name)['in_game_date']))
    inj = G.parse_injury_manager(get_member(SAVE, next(m for m in members if m['name'] == 'injury_manager.dat')))
    fn, ln, ns, ne = G.find_names(b)
    people = G.find_people(b, fn, ln, ne)
    G.match_identities(b, people, ne)
    abil = G.find_abilities(b, ne)
    G.find_injuries(b, people, set(abil), inj, today)
    assert all(z >= today for _, z in inj.values()), 'expired rows must be dropped by the game'
    star = {}
    for p in people:
        a = abil.get(p.get('id'))
        if a and a['ca'] >= 120:
            star.setdefault(p['name'], p)
    # in game: Reece James fractured lower leg (6 wk-2 mo), Alisson pulled knee ligaments (11 d-3 wk)
    assert star['Reece James']['injured'] and 30 <= star['Reece James']['injury_days'] <= 70
    assert star['Alisson Becker']['injured'] and 5 <= star['Alisson Becker']['injury_days'] <= 21
    for n in ('Harry Kane', 'Phil Foden', 'Declan Rice', 'Jude Bellingham', 'Florian Wirtz', 'James Maddison'):
        assert not star[n]['injured'], n
    print('injuries OK', len(inj), 'rows')


if __name__ == '__main__':
    test_injuries()
