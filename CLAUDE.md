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
python main.py
```

Crash log: `/tmp/fm_editor_crash.log`

## Key files

- `gui/main_window.py` — all UI/logic (~2700 lines)
- `gui/roles.py` — 82 FM24 role-duties + `role_rating()`
- `fm_editor/patch.py` — HGP/HGC detection + patching
- `HANDOVER.md` — current state, bug history, UI layout
- `PRODUCT.md` — product purpose and capabilities
