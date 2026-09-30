"""Ground-truth check for club-record fields (status, nation) against the real FM24 save.

Run directly: python3 tests/test_club_info.py   (skips politely if the save is absent)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SAVE = os.path.expanduser(
    '~/.local/share/Steam/steamapps/compatdata/2252570/pfx/drive_c/users/steamuser/'
    'Documents/Sports Interactive/Football Manager 2024/games/'
    '2026-27 START - Acid Twin Spurs.fm')


def test_club_info():
    from fm_editor.archive import parse_archive, get_member
    from fm_editor.gamedb import find_names, find_clubs, add_club_finance
    from fm_editor.nations import nation_name, STATUS_NAMES

    _, members, _, _, _, _ = parse_archive(SAVE)
    gdb = get_member(SAVE, next(m for m in members if m['name'] == 'game_db.dat'))
    names_start = find_names(gdb)[2]
    cl = find_clubs(gdb, names_start)
    add_club_finance(gdb, cl, names_start)
    clubs = {c['name']: c for c in cl}

    spurs = clubs['Tottenham Hotspur']
    assert spurs['id'] == 492 and spurs['nation'] == 139, spurs
    assert nation_name(spurs['nation']) == 'England'
    assert STATUS_NAMES[spurs['status']] == 'Professional', spurs
    # status verified on 3+ clubs per tier: top clubs pro, non-league semi-pro, tiny amateur
    for n in ('Arsenal', 'Walsall', 'Celtic', 'F.C. Barcelona'):
        assert clubs[n]['status'] == 1, n
    for n in ('Dartford', 'Horsham', 'Whitehawk', 'Bahlinger SC'):
        assert clubs[n]['status'] == 2, n
    assert clubs['Kirishima Reds']['status'] == 3
    # nation ids verified against marquee clubs
    for n, want in (('Celtic', 'Scotland'), ('F.C. Barcelona', 'Spain'), ('Juventus F.C.', 'Italy'),
                    ('FC Bayern München', 'Germany'), ('Paris Saint-Germain', 'France'),
                    ('Club Brugge KV', 'Belgium')):
        assert nation_name(clubs[n]['nation']) == want, (n, clubs[n]['nation'])

    # finances vs the in-game Finances screen (Tottenham, 2 Jan 2028); transfer budget is stored 1 higher
    f = spurs['fin']
    assert f['balance'] == 227_077_819, f
    assert f['transfer_budget'] in (62_333_470, 62_333_471), f
    assert f['transfer_budget_next_min'] // 100_000 == 184, f  # "minimum guaranteed £18.4M"
    assert f['transfer_budget_orig'] // 1_000_000 == 147, f    # "Original budget was £147M"
    assert f['wage_budget'] == 3_662_148 and f['wage_spending'] == 3_759_787, f
    # other clubs: block present and plausible; tiny clubs have none
    for n in ('Arsenal', 'Manchester City', 'Liverpool', 'A.C. Milan'):
        x = clubs[n]['fin']
        assert x['balance'] > 0 and 0.3 < x['wage_budget'] / x['wage_spending'] < 3, (n, x)
    # size of the record does not matter: the 3 "missing" PL clubs (medium records) have the full block
    for n in ('Fulham', 'West Ham United', 'Wolverhampton Wanderers'):
        x = clubs[n]['fin']
        assert x['wage_budget'] > 0 and x['wage_spending'] > 0 and x['balance'] > 0, (n, x)
    # 'small' layout (Championship and below): balance only, no budgets; tiers plausible
    for n in ('Southampton', 'Walsall', 'Torquay United', 'Wrexham'):
        assert list(clubs[n]['fin']) == ['balance'], (n, clubs[n]['fin'])
    assert clubs['Southampton']['fin']['balance'] > 10_000_000 > clubs['Walsall']['fin']['balance'] > 0
    assert -100_000 < clubs['Torquay United']['fin']['balance'] < 0
    assert clubs['Arsenal']['fin']['balance'] > clubs['Southampton']['fin']['balance']
    assert 'fin' not in clubs['Kirishima Reds']  # amateur club: balance 0 = not simulated
    # no club without a finance structure gets a made-up value
    assert all('wage_budget' in c['fin'] or list(c['fin']) == ['balance'] for c in clubs.values() if 'fin' in c)


if __name__ == '__main__':
    if not os.path.exists(SAVE):
        print('SKIP: save file not found')
    else:
        test_club_info()
        print('OK')
