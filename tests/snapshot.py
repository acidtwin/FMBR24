"""Snapshot gate for tests that pin in-game values (season stats, league tables) to a real save.

The live save keeps being played, so those values move. The exact in-game comparison runs only when the save's parsed
in-game date (Save Info) is the one the values were recorded at; otherwise the test falls back to invariants.
Point FMBR24_SNAPSHOT_SAVE at a frozen copy to force the exact run (it is still date-checked).
"""
import os

SNAPSHOT_DATE = '2028-01-02'              # in-game date the ground-truth values were read at
SNAPSHOT_GAME_NAME = '2026-27 START - Acid Twin Spurs'   # for settings the user edits (scouting budget): 150,000 at this name+date


def save_path(default):
    return os.environ.get('FMBR24_SNAPSHOT_SAVE') or default


def save_info(save):
    from fm_editor.archive import parse_archive
    from fm_editor.saveinfo import parse_save_info
    _, members, _, name, _, _ = parse_archive(save)
    return parse_save_info(save, members, name)


def snapshot_mode(save, game_name=False):
    """True = exact in-game comparison applies to this save. game_name=True also requires the recorded Game Name."""
    info = save_info(save)
    ok = info.get('in_game_date') == SNAPSHOT_DATE and (not game_name or info.get('game_name') == SNAPSHOT_GAME_NAME)
    print(f"[{os.path.basename(save)}]{' (game name too)' if game_name else ''} in-game date {info.get('in_game_date')}: "
          f"{'SNAPSHOT mode (exact in-game values)' if ok else 'INVARIANTS ONLY mode (save differs from the recorded snapshot; exact values skipped)'}")
    return ok
