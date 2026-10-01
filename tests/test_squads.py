"""Squad membership vs the real FM24 save (Tottenham Squad screen, 2 Jan 2028).

Run directly: python3 tests/test_squads.py   (skips politely if the save is absent; ~30 s)
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SAVE = os.path.expanduser(
    '~/.local/share/Steam/steamapps/compatdata/2252570/pfx/drive_c/users/steamuser/'
    'Documents/Sports Interactive/Football Manager 2024/games/'
    '2026-27 START - Acid Twin Spurs.fm')

# in-game first team, 25 names (Nico Paz used to be mapped to SuperSport United)
SPURS = {
    'Diogo Costa', 'Michael Kayode', 'Jan Paul van Hecke', 'Micky van de Ven', 'Alejandro Balde',
    'Sandro Tonali', 'Manu Koné', 'Nicolás Paz', 'Xavi Simons', 'Rodrigo Mora', 'Endrick',
    'Christian Zawieschitzky', 'Strahinja Pavlović', 'Aleksandar Pavlović', 'Lionel Messi',
    'Giorgio Scalvini', 'Pedro Porro', 'Neymar', 'Souza', 'Lucas Bergvall', 'Omar Marmoush',
    'Sávio', 'Gianluca Prestianni', 'Álvaro Montoro', 'Williams-Barnett'}


def test_squads():
    from fm_editor.archive import parse_archive, get_member
    from fm_editor.gamedb import (find_names, find_clubs, find_squads, find_people,
                                  match_identities)

    _, members, _, _, _, _ = parse_archive(SAVE)
    gdb = get_member(SAVE, next(m for m in members if m['name'] == 'game_db.dat'))
    fn, ln, names_start, names_end = find_names(gdb)
    clubs = find_clubs(gdb, names_start)
    people = find_people(gdb, fn, ln, names_end)
    match_identities(gdb, people, names_end)
    by_id = {p['id']: p for p in people if p.get('id', -1) != -1}

    for with_people in (None, people):
        squads, sub = find_squads(gdb, clubs, names_start, with_people)
        spurs = {by_id[pid]['name'] for pid, c in squads.items() if c == 492 and pid in by_id}
        # substring match: the save stores full legal names ("Neymar da Silva Santos Junior")
        missing = {n for n in SPURS if not any(n in s for s in spurs)}
        assert not missing, missing
        assert len(spurs) == 25, (len(spurs), sorted(spurs))
        assert squads[101766] == 492  # Nico Paz, also listed in Argentina's national squad array

        sizes = collections.Counter(squads.values())
        for cid, lo, hi in ((492, 18, 40), (370, 18, 40), (393, 18, 45), (367, 18, 40),
                            (443, 18, 40)):  # Spurs, Barnet, Charlton, Arsenal, Man City
            assert lo <= sizes[cid] <= hi, (cid, sizes[cid])

        # sub squads: Spurs U21 is club 492's own array (owner id is club id + 1 for kind 21)
        u21 = {by_id[p]['name'] for p in sub[492][21] if p in by_id}
        assert any('Glancy' in n for n in u21), u21

    # most squad members have their contract at the squad's club (loans / B teams explain the rest)
    from fm_editor.gamedb import _contract_clubs
    cc = _contract_clubs(gdb, people)
    known = [(pid, c) for pid, c in squads.items() if pid in cc]
    agree = sum(1 for pid, c in known if c in cc[pid]) / len(known)
    assert agree > 0.9, agree
    # same bug class elsewhere: employment = LAST 6a record (Kone: Gladbach -> Spurs, entity 493)
    from fm_editor.gamedb import find_employment, find_abilities, find_club_staff
    emp = find_employment(gdb, people)
    kone = next(p['id'] for p in people if p.get('name') == 'Manu Koné')
    assert emp[kone] == 493, emp[kone]
    # the last club record has no successor: its staff scan used to cover ~80 MB (874 staff)
    staff = find_club_staff(gdb, clubs, people, find_abilities(gdb, names_end), names_start)
    assert max(len(v) for v in staff.values()) < 150, max(len(v) for v in staff.values())
    holders = collections.Counter(pid for v in staff.values() for pid in v)
    assert not [pid for pid, n in holders.items() if n > 1], 'staff in two clubs arrays'
    print('OK', len(squads), 'squad members; contract agreement %.1f%%' % (100 * agree))


if __name__ == '__main__':
    if not os.path.exists(SAVE):
        print('SKIPPED (save not found): test_squads')
    else:
        test_squads()
