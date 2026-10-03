# FM Backroom 24 (FMBR24)

PyQt6 6.11 desktop app, Linux, Python 3.12, FM24 saves only (formerly "FM24 Homegrown Editor"). Unofficial: never imply affiliation with Sports Interactive / SEGA.

## Run / test

```bash
pip install -r requirements.txt   # PyQt6, zstandard, numpy
python main.py                    # crash log: /tmp/fm_editor_debug.log
FMBR24_CONFIG_DIR=$(mktemp -d) QT_QPA_PLATFORM=offscreen python3 tests/test_<name>.py   # plain scripts, no pytest
```

- Always set `FMBR24_CONFIG_DIR` (temp dir) for tests and verification: the real `~/.config/fm24_editor/settings.json` must stay untouched.
- **Tests never read the live save** (the user keeps playing it, values drift). Real-save tests read frozen copies in `~/.local/share/fmbr24/test-saves/` (`tests/snapshot.py`), print `SKIPPED` and exit 0 when a copy is absent. Never point a test at the live save, never modify or delete the copies. Paths, sizes, sha256, recreate steps: `HANDOVER.md` section 1.
- Docs map: `HANDOVER.md` (state, architecture/UI map, TODOs; read before big work), `PRODUCT.md` (scope), `docs/DESIGN-BACKLOG.md` (mockups to come back to: goal-net header (built), solid sidebar icons; Compare players is built), `README.md` (public face), `docs/HANDOVER-archive.md` (old diary, partly stale). FM24 binary format: memory `fm24-binary-format.md`, check it before touching a parser.
- Bump `_CACHE_VERSION` (`fm_editor/cache.py`) when a parsed field is added or changes.

## Workflow rules

- **Mockup first:** every VISUAL change to the player window (and other designed surfaces) is made and approved in `mockups/player-window.html` (or that surface's mockup) BEFORE app code changes; then build the app mechanically from it. Exception: pure bug fixes with no visual design decision. The user views mockups by opening the HTML file straight from disk in the browser (`file:///.../mockups/<name>.html`, refresh to reload); NO local web server (a waste of time and tokens: do not start one). To show a mockup, open it in the USER'S OWN browser with `xdg-open file://<repo>/mockups/<name>.html` (default Chrome); the built-in browser pane opens files as static snapshots with scripts blocked, so the mockup buttons/toggles do not work there. Do not send screenshots to the user (take them only for your own checks).
- **Homegrown (HGP/HGC) changes never open dialogs:** they are queued, then Save Changes writes them (one confirm dialog at Save only).
- **Button order:** Close is ALWAYS the last (far-right) button of any button row or action strip (player window: Compare to... / Add to Shortlist / Close). Applies to every dialog and mockup you touch.
- **Verify UI headlessly:** construct `MainWindow()` under `QT_QPA_PLATFORM=offscreen`, `.grab().save('x.png')` and LOOK at the PNG; reading QSS misses bugs. Sub-agents without Bash (cavecrew-builder) cannot run tests: verify their output yourself.
- **Busy lock:** `_set_busy` disables every nav/sidebar button (incl. Player Reports `_report_btns`) during Save/Reload; a new nav button must be added there and in `_update_ui_state` (adding it to the `_nav_btns` list in `_make_sidebar` covers `_set_busy`, as 'Compare Players' does). Page header icons: `_set_header(icon=)`, files in `resources/icons/pages/` (HANDOVER section 3).
- **Sub-agent worktrees:** create the worktree off `main`, merge back with `--no-ff`, then delete the worktree AND its branch. Do not delete someone else's worktree without asking. No bare `git stash` in worktrees (the stash list is shared by all of them).
- **README:** when features or UI change, run `python3 scripts/make_screenshots.py <save>` (read-only on the save, offscreen, writes `docs/screenshots/`; it forces faces/logos/flags OFF so no third-party pictures are published) and refresh the README feature list. The README's last line is the non-affiliation disclaimer: keep it exactly.

## Mockup -> PyQt6 rule

When told to match a mockup 1:1: read the artifact HTML/CSS first, extract every value (px, opacity, gradient stops, alpha, letter-spacing, font-size, radius), translate mechanically, never by eye. `rgba(r,g,b,a)` -> `QColor(r,g,b,round(a*255))`; `background-position: center X%` -> `y_off=int((h-scaled.height())*X/100)`; CSS `opacity` on image -> `p.setOpacity(N)`; gradient stops -> `grad.setColorAt(pos, QColor(...))`.

## Star ratings rule

Any rating shown as a number or bar (CA, PA, Dev Rate, later more) that we convert to stars MUST keep a raw-number mode too, switched by the Settings option (`ability_display`, Stars / Numbers; extend it or add a sibling key, never hard-code stars). Use `fm_editor/abilitystars.py` (the one value -> stars mapping, `half_stars` rounding) and the shared widget `gui/stars.py`; in stars mode keep the raw number in a tooltip. Add the setting default, Reset-to-defaults handling and a test whenever a new rating is converted. Mappings approximate FM's relative stars: document them, keep them adjustable in one place. Never remove the numbers option. Stars are used in the player-window header boxes, the Compare page header boxes and picker rows, club-header reputation, and the CA/PA/Dev columns of the player lists (`StarsDelegate`, switched live by `_apply_ui_prefs`); staff lists have no ratings; Best by Role's Rating column stays a number.

## PyQt6 / Qt gotchas (burned us before)

- `clicked(bool)` passes checked as first arg: `lambda checked, k=key:`, never `lambda k=key:`
- `ResizeToContents` on headers -> O(n^2) freeze; use `Interactive` + fixed widths on ALL tables
- `QApplication.processEvents()` in a slot -> re-entrant loop -> qFatal; never mid-populate
- Loop var `w` overwriting a widget ref -> GC RuntimeError; use `cw`/`idx`. Keep refs for widgets removed from layouts (`_squad_header_bar`)
- `disconnect()` raises `RuntimeError` or `TypeError` by version: catch both; `next()` needs a default + guard
- Bare `QFrame {...}` selectors leak onto child QLabels (QLabel is a QFrame): scope with `QFrame#objectName`
- A per-widget `setStyleSheet` shadows app QSS for overlapping selectors/subcontrols (caused the spinbox arrow gap); QSpinBox needs explicit up/down-button heights (theme.py)
- QSS `opacity`, `letter-spacing`, `text-transform`, keyframes are not honoured: use `QFont` letter spacing, `.upper()`, QTimer + stylesheet (`_tick_shimmer`), `setOpacity` when painting
- `border-radius` >= half the size renders square
- Dialog-scoped QSS: app QSS `QWidget{background}` paints every plain QWidget opaque; add `QDialog#x QWidget{background:transparent}` FIRST and prefix later rules with the same `QDialog#x` (equal specificity, later wins). Wrapped QLabels/Flow layouts and `replaceWidget` need `processEvents()` (twice) before `grab()` in offscreen checks.
- Barlow Condensed / Inter are not installed (fallback Noto Sans)

## Repo / GitHub

Own git repo (branch `main`, remote `git@github.com:acidtwin/FMBR24.git`, PUBLIC). The parent `Claude Code Projects` folder is a separate monorepo: never push it. Commit/push only when asked, specific `git add` paths. Push uses the SSH agent: after a restart the user runs `ssh-add ~/.ssh/id_ed25519` (never store credentials/passphrases anywhere). The user's GitHub account is currently FLAGGED by GitHub's abuse system (support ticket open): see HANDOVER section 2 before pushing or relying on GitHub features. SSH agent + `gh` details: memory `reference-github-setup.md`.
