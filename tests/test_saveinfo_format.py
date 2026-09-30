"""Formatting helpers for the Save Info page. Run: python3 tests/test_saveinfo_format.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from gui.main_window import _fmt_game_date, _fmt_game_time, _fmt_file_size


def test_formats():
    assert _fmt_game_date('2028-01-02') == 'Sunday 2nd January 2028'
    assert _fmt_game_date('2026-09-11') == 'Friday 11th September 2026'
    assert _fmt_game_date('2026-09-21') == 'Monday 21st September 2026'
    assert _fmt_game_date('2026-09-23') == 'Wednesday 23rd September 2026'
    assert _fmt_game_date('2026-09-12') == 'Saturday 12th September 2026'
    assert _fmt_game_date('bad') is None and _fmt_game_date(None) is None
    assert _fmt_game_time(116137) == '1 Day, 8 Hours, 16 Minutes'   # 1936.6 min -> rounds up
    assert _fmt_game_time(116130) == '1 Day, 8 Hours, 16 Minutes'
    assert _fmt_game_time(3600) == '1 Hour' and _fmt_game_time(0) == '0 Minutes'
    assert _fmt_game_time(2 * 86400 + 60) == '2 Days, 1 Minute'
    assert _fmt_file_size(500) == '500 B' and _fmt_file_size(188.4 * 1024 ** 2) == '188.4 MB'


if __name__ == '__main__':
    test_formats()
    print('OK: saveinfo formatting')
