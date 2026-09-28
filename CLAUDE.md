# FM-Save-Editor

PyQt6 6.11.0 desktop app, Linux, Python 3.12. Single file: `gui/main_window.py`.

## PyQt6 Gotchas (burned us before)

- `clicked(bool)` passes checked state as first positional arg — always `lambda checked, k=key:` never `lambda k=key:`
- `QHeaderView.ResizeMode.ResizeToContents` → O(n²) freeze on populate — use `Interactive` + fixed widths on ALL tables
- `QApplication.processEvents()` in a slot → re-entrant event loop → qFatal abort — never call it mid-populate
- Loop var name `w` in dict iteration overwrites widget ref → GC RuntimeError — rename loop vars to `cw`/`idx`/etc
- Qt QSS has no keyframe animations — motion effects need QTimer + stylesheet update (see `_tick_shimmer`)
- Signal `disconnect()` raises `RuntimeError` (not Exception) when nothing connected — catch specifically
- `next()` without default → bare StopIteration crash — always `next(..., None)` + guard

## Run

```bash
pip install -r requirements.txt  # PyQt6, zstandard
```

```bash
python main.py
```

Crash log: `/tmp/fm_editor_crash.log`

## Key files

- `gui/main_window.py` — all UI/logic (~2700 lines)
- `gui/roles.py` — 82 FM24 role-duties + `role_rating()`
- `fm_editor/patch.py` — HGP/HGC detection + patching
- `fm_editor/archive.py` — FMF archive read/write (zstd members)
- `fm_editor/gamedb.py` — game_db.dat parser (players, clubs, squads)
- `fm_editor/cache.py` — parse result cache keyed by file mtime
- `HANDOVER.md` — current state, bug history, UI layout
- `PRODUCT.md` — product purpose and capabilities

## FM24 binary format

See memory file `~/.claude/projects/…/memory/fm24-binary-format.md` — ability block offsets,
attribute indices, HGP/HGC record format, personality bytes. Always check before touching the parser.
