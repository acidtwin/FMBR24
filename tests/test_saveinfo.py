"""Ground-truth check for fm_editor.saveinfo.parse_save_info against a real FM24 save.

Run directly: python3 tests/test_saveinfo.py   (skips politely if the save is absent)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.snapshot import snapshot_save, skip_if_missing, assert_snapshot  # noqa: E402  (frozen 2028-01-02 copy, never the live save)
SAVE = snapshot_save()


def test_save_info():
    from fm_editor.archive import parse_archive, get_member
    from fm_editor.gamedb import find_names, find_clubs
    from fm_editor.saveinfo import parse_save_info

    _, members, _, name, _, _ = parse_archive(SAVE)
    gdb = get_member(SAVE, next(m for m in members if m['name'] == 'game_db.dat'))
    clubs = find_clubs(gdb, find_names(gdb)[2])
    r = parse_save_info(SAVE, members, name, gdb=gdb, clubs=clubs)

    assert r['game_name'] == '2026-27 START - Acid Twin Spurs (scouting budget change)', r
    assert r['times_saved'] == 126 and r['in_game_date'] == '2028-01-02', r
    assert r['date_created'] == '2026-09-11', r
    assert r['game_time_seconds'] == 123552, r
    assert r['game_version'] == '24.4.2' and r['game_build'] == 2081827, r
    assert r['database_version'] == '24.3.0' and r['database_changes'] == 8809924, r
    assert r['start_date'] == '2026-07-13', r  # in-game "Game Start Date" (Italy - 13/7/2026)
    assert r['manager_name'] == 'Elliot Nathan', r
    assert r['manager_club_id'] == 492 and r['manager_club_name'] == 'Tottenham Hotspur', r
    assert r['nations_count'] == 46 and len(r['leagues']) == 46, r
    assert r['leagues'][:3] == ['J1 League', 'Saudi Pro League', 'MLS'], r

    # robustness: no game_db / no members -> smaller dict, no exception
    assert 'database_changes' not in parse_save_info(SAVE, members, name)
    assert parse_save_info(SAVE, [], None) == {}


if __name__ == '__main__':
    skip_if_missing()
    assert_snapshot(SAVE)
    test_save_info()
    print('OK: parse_save_info')
