"""Frozen snapshot saves for every real-save test.

The live save keeps being played, so tests that pin in-game values (season stats, league tables, injuries, values) must
never read it. They read FROZEN COPIES instead (CLAUDE.md "Frozen test snapshot"), in ~/.local/share/fmbr24/test-saves/:
  snapshot-2028-01-02.fm  = '2026-27 START - Acid Twin Spurs (scouting budget change) (v02).fm'  (in-game 2 Jan 2028, default)
  snapshot-2028-01-12.fm  = '2026-27 START - Acid Twin Spurs (scouting budget change).fm'        (in-game 12 Jan 2028:
                            injuries + transfer values were read in-game on that day)
FMBR24_SNAPSHOT_SAVE=<path> overrides the 2 Jan copy, FMBR24_SNAPSHOT_SAVE_20280112=<path> the 12 Jan one.
Without a copy the real-save tests print SKIPPED and exit 0.
"""
import os
import sys

SNAPSHOT_DATE = '2028-01-02'              # in-game date the default snapshot (and most ground-truth values) was read at
SNAPSHOT_DATE_JAN12 = '2028-01-12'
_DIR = os.path.expanduser('~/.local/share/fmbr24/test-saves')


def _want(day):
    """(env var name, default path) for the snapshot of this in-game day."""
    return ('FMBR24_SNAPSHOT_SAVE' if day == SNAPSHOT_DATE else 'FMBR24_SNAPSHOT_SAVE_' + day.replace('-', ''),
            os.path.join(_DIR, f'snapshot-{day}.fm'))


def _path(day):
    env, default = _want(day)
    return os.environ.get(env) or default


def snapshot_save(day=SNAPSHOT_DATE):
    """Path of the frozen save for this in-game day (env override, else the default copy), or None when it is missing."""
    p = _path(day)
    return p if os.path.exists(p) else None


def skip_if_missing(day=SNAPSHOT_DATE):
    """Print SKIPPED and exit 0 when there is no frozen snapshot save."""
    if snapshot_save(day) is None:
        print(f'SKIPPED (frozen snapshot save not found at {_path(day)}; see CLAUDE.md "Frozen test snapshot")')
        sys.exit(0)


def assert_snapshot(save, day=SNAPSHOT_DATE):
    """Sanity check: the save really is the snapshot of that in-game day."""
    from fm_editor.archive import parse_archive
    from fm_editor.saveinfo import parse_save_info
    _, members, _, name, _, _ = parse_archive(save)
    got = parse_save_info(save, members, name).get('in_game_date')
    assert got == day, f'{save}: in-game date {got}, not {day}'
    print(f'[{os.path.basename(save)}] SNAPSHOT mode (in-game date {day}, exact in-game values)')
