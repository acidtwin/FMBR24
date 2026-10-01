"""Contract end / start / weekly wage vs in-game values (Jan 2028, 18 players) in the real FM24 save.

Run directly: python3 tests/test_contract_block.py   (skips politely if the save is absent; ~40 s)
find_contract_blocks: block before the person record (ff*8 + end date + start date); wage = u32 in the person-id
backlink. The old b11=0x6a record is a last-evaluation month, NOT the contract end.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SAVE = os.path.expanduser(
    '~/.local/share/Steam/steamapps/compatdata/2252570/pfx/drive_c/users/steamuser/'
    'Documents/Sports Interactive/Football Manager 2024/games/'
    '2026-27 START - Acid Twin Spurs.fm')

# person id -> (weekly wage as shown in game, contract end 'YYYY-MM')
GT = {45362: (110000, '2031-06'), 36039: (350000, '2031-06'), 16963: (34500, '2029-06'),
      26552: (51000, '2029-06'), 109583: (125000, '2031-06'), 78933: (235000, '2031-06'),
      33168: (250000, '2032-06'), 74717: (100000, '2029-06'), 32846: (155000, '2030-06'),
      33096: (250000, '2030-06'), 73674: (48000, '2032-06'), 25517: (200000, '2029-06'),
      33782: (135000, '2031-06'), 46790: (81000, '2031-06'), 32666: (35000, '2029-06'),
      88506: (64000, '2032-06'), 69244: (30500, '2030-12'), 51319: (1500, '2029-12')}


def test_contract_block():
    from fm_editor.archive import parse_archive, get_member
    from fm_editor.gamedb import find_names, find_people, match_identities, find_abilities, find_contract_blocks
    from gui.player_window import fmt_wage

    _, members, _, _, _, _ = parse_archive(SAVE)
    gdb = get_member(SAVE, next(m for m in members if m['name'] == 'game_db.dat'))
    fn, ln, _, ne = find_names(gdb)
    people = find_people(gdb, fn, ln, ne)
    match_identities(gdb, people, ne)
    ab = find_abilities(gdb, ne)
    r = find_contract_blocks(gdb, people)
    for pid, (wage, end) in GT.items():
        c = r[pid]
        assert c['contract_end'] == end, (pid, c, end)
        assert abs(c['wage_week'] / wage - 1) < 0.025, (pid, c, wage)
        assert fmt_wage(c['wage_week']) == fmt_wage(wage), (pid, c, wage)
    pl = [p['id'] for p in people if p.get('id', -1) in ab]
    have = [i for i in pl if i in r]
    assert len(have) / len(pl) > 0.55, len(have) / len(pl)
    yrs = Counter(r[i]['contract_end'][:4] for i in have)
    assert all('2026' <= y <= '2040' for y in yrs), yrs
    assert not [i for i in have if 'contract_start' in r[i] and r[i]['contract_start'] > r[i]['contract_end']]
    print(f'contract block OK: {len(GT)}/{len(GT)} end+wage; {len(have)}/{len(pl)} players with end '
          f'({100 * len(have) // len(pl)}%); years {sorted(yrs.items())}')


if __name__ == '__main__':
    if not os.path.exists(SAVE):
        print('skip: save not found')
    else:
        test_contract_block()
