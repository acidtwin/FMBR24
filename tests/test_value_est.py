"""Transfer value = u32 at at+54 (GBP), vs in-game ranges (Jan 2028). Plain script; skips without the save."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tests.test_parse_golden import SAVE

# person id -> in-game Transfer Value range in GBP millions (the stored value is the true value; display is a range)
GT = {36039: (241, 263), 45362: (143, 209), 26552: (43, 62), 109583: (129, 146), 78933: (110, 161),
      33168: (162, 178), 32846: (35, 43), 33096: (247, 272), 73674: (96, 96), 33782: (154, 179),
      46790: (24, 34), 69244: (9, 13), 88506: (73, 73), 51319: (2.7, 5.4)}
NOT_FOR_SALE = (16963, 32666)  # Muriqi, Grealish -> 300,000,000


def test_value_est():
    if not os.path.exists(SAVE):
        print('SKIPPED (save not found): test_value_est'); return
    from fm_editor.archive import parse_archive, get_member
    from fm_editor.gamedb import find_names, find_abilities
    _, members, _, _, _, _ = parse_archive(SAVE)
    gdb = get_member(SAVE, next(m for m in members if m['name'] == 'game_db.dat'))
    ab = find_abilities(gdb, find_names(gdb)[3])
    bad = {pid: (ab[pid]['value_est'], r) for pid, (lo, hi) in GT.items() for r in [(lo, hi)]
           if not (lo * 0.99e6 <= ab[pid]['value_est'] <= hi * 1.01e6)}  # 1%: the game rounds the display
    assert not bad, bad
    assert all(ab[p]['value_est'] == 300_000_000 for p in NOT_FOR_SALE)
    print(f'value_est OK: {len(GT)}/{len(GT)} in range, {len(NOT_FOR_SALE)} Not-for-Sale = 300M')


if __name__ == '__main__':
    test_value_est()
