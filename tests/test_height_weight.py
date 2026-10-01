"""Height/weight vs in-game values (Jan 2028, 18 players) in the real FM24 save.

Run directly: python3 tests/test_height_weight.py   (skips politely if the save is absent; ~15 s)
Weight kg = b[at+82], height cm = b[at+84] where `at` = start of the 54 attribute bytes (find_abilities).
Weekly wage is NOT decoded (no field fits); see memory fm24-binary-format.md.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SAVE = os.path.expanduser(
    '~/.local/share/Steam/steamapps/compatdata/2252570/pfx/drive_c/users/steamuser/'
    'Documents/Sports Interactive/Football Manager 2024/games/'
    '2026-27 START - Acid Twin Spurs.fm')

# person id -> (height cm, weight kg) from the in-game profiles
GT = {45362: (188, 86), 36039: (186, 75), 16963: (194, 92), 26552: (175, 73), 109583: (173, 66),
      78933: (177, 71), 33168: (179, 91), 74717: (187, 82), 32846: (175, 73), 33096: (185, 80),
      73674: (190, 85), 25517: (191, 91), 33782: (187, 88), 46790: (190, 91), 32666: (175, 82),
      88506: (180, 70), 69244: (167, 65), 51319: (181, 82)}


def test_height_weight():
    from fm_editor.archive import parse_archive, get_member
    from fm_editor.gamedb import find_names, find_abilities

    _, members, _, _, _, _ = parse_archive(SAVE)
    gdb = get_member(SAVE, next(m for m in members if m['name'] == 'game_db.dat'))
    ab = find_abilities(gdb, find_names(gdb)[3])
    bad = {pid: (ab[pid]['height_cm'], ab[pid]['weight_kg'], hw) for pid, hw in GT.items()
           if (ab[pid]['height_cm'], ab[pid]['weight_kg']) != hw}
    assert not bad, bad
    hs = [a['height_cm'] for a in ab.values()]
    ws = [a['weight_kg'] for a in ab.values()]
    assert 140 <= min(hs) and max(hs) <= 215 and max(ws) <= 120, (min(hs), max(hs), min(ws), max(ws))
    assert sum(1 for w in ws if 45 <= w <= 120) >= 0.99 * len(ws), 'weights mostly outside 45-120 kg'  # a few players have 0 (unset)
    print(f'height/weight OK: {len(GT)}/{len(GT)} match, {len(ab)} players, '
          f'height {min(hs)}-{max(hs)}, weight {min(ws)}-{max(ws)}')


if __name__ == '__main__':
    if not os.path.exists(SAVE):
        print('SKIPPED (save not found): test_height_weight')
    else:
        test_height_weight()
