# FM Backroom 24 (FMBR24)

PyQt6 6.11 desktop app, Linux, Python 3.12, FM24 saves only (formerly "FM24 Homegrown Editor"). Unofficial: never imply affiliation with Sports Interactive / SEGA.

## Run / test

```bash
pip install -r requirements.txt  # PyQt6, zstandard
python main.py                    # crash log: /tmp/fm_editor_debug.log
python3 tests/test_saveinfo.py    # also test_saveinfo_format.py, test_club_contracts.py (plain scripts, skip if save absent)
```

## Key files

- `gui/main_window.py` — all UI/logic (~5900 lines); `gui/theme.py` (COLORS + app QSS), `gui/roles.py`, `gui/icon.py` (`make_app_icon`), `gui/assets/` (hero/sidebar/brand images)
- `fm_editor/` — `archive.py` (FMF/zstd), `gamedb.py` (game_db.dat parser), `patch.py` (HGP/HGC), `saveinfo.py` (Save Info parser), `cache.py` (parse cache, `_CACHE_VERSION`), `weights.py`
- `resources/icon-source.png` (master) + `resources/icons/icon-{16..512}.png`; `mockups/` design references
- `HANDOVER.md` — state, UI map, key symbols, TODOs. `PRODUCT.md` — purpose/scope. Read both before big work.
- FM24 binary format: memory file `fm24-binary-format.md` — always check before touching the parser.

## PyQt6 / Qt gotchas (burned us before)

- `clicked(bool)` passes checked as first arg — `lambda checked, k=key:`, never `lambda k=key:`
- `ResizeToContents` on headers → O(n²) freeze; use `Interactive` + fixed widths on ALL tables
- `QApplication.processEvents()` in a slot → re-entrant loop → qFatal; never mid-populate
- Loop var `w` overwriting a widget ref → GC RuntimeError; use `cw`/`idx`. Keep refs for widgets removed from layouts (`_squad_header_bar`)
- `disconnect()` raises `RuntimeError` or `TypeError` by version — catch both; `next()` needs a default + guard
- Bare `QFrame {…}` selectors leak onto child QLabels (QLabel is a QFrame) — scope with `QFrame#objectName`
- A per-widget `setStyleSheet` shadows app QSS for overlapping selectors/subcontrols (caused the spinbox arrow gap); QSpinBox needs explicit up/down-button heights (theme.py)
- QSS `opacity`, `letter-spacing`, `text-transform`, keyframes are not honoured — use `QFont` letter spacing, `.upper()`, QTimer + stylesheet (`_tick_shimmer`), `setOpacity` when painting
- `border-radius` ≥ half the size renders square
- Dialog-scoped QSS: app QSS `QWidget{background}` paints every plain QWidget opaque; add `QDialog#x QWidget{background:transparent}` FIRST and prefix later rules with the same `QDialog#x` (equal specificity, later wins). Wrapped QLabels/Flow layouts and `replaceWidget` need `processEvents()` before `grab()` in offscreen checks.
- Barlow Condensed / Inter are not installed (fallback Noto Sans)

## Verify UI headlessly

`QT_QPA_PLATFORM=offscreen`, construct `MainWindow()`, `.grab().save('x.png')` and LOOK at the PNG — reading QSS misses bugs. Sub-agents without Bash (cavecrew-builder) cannot run tests: verify their output yourself.

## Mockup → PyQt6 rule

When told to match a mockup 1:1: read the artifact HTML/CSS first, extract every value (px, opacity, gradient stops, alpha, letter-spacing, font-size, radius), translate mechanically, never by eye. `rgba(r,g,b,a)` → `QColor(r,g,b,round(a*255))`; `background-position: center X%` → `y_off=int((h-scaled.height())*X/100)`; CSS `opacity` on image → `p.setOpacity(N)`; gradient stops → `grad.setColorAt(pos, QColor(...))`.

## Repo / GitHub

Own git repo (branch `main`, remote `git@github.com:acidtwin/FMBR24.git`, private). The parent `Claude Code Projects` folder is a separate monorepo: never push it. Commit/push only when asked, specific `git add` paths. SSH agent + `gh` details in memory `reference-github-setup.md`. Never store credentials/passphrases anywhere.
