# FM24 Homegrown Editor — Handover

**Last updated:** 2026-09-28 (session 5)
**Project:** `/run/media/acidtwin/Gaming SSD 1/Claude Code Projects/FM-Save-Editor`

---

## Current state

Working FM24 save editor with full FM24-skin UI. Tested against a real Tottenham 2026-27 save.

All changes on `master`.

### Session 5 (2026-09-28) — Role weight presets

**Problem fixed**: Best by Role report surfaced defenders for forward roles (equal-weight scoring of key attrs meant high mental attrs gave defenders comparable scores to strikers).

**Role weight presets system** — `fm_editor/weights.py` + `fm_editor/weights/*.json`:
- **4 bundled presets**: Equal Weight (original behavior), FMScout Community (tiered weights, primary attrs score 20), Possession-Based (boosts passing/vision/technique/composure, softens pace/strength), Direct Play (boosts pace/strength/heading/crossing, softens technical attrs)
- Settings dialog (⚙ button, now wired up): preset dropdown + description. Import custom preset from JSON. Delete user presets.
- **Weight editor dialog**: pick a role → edit per-attribute weights (0-20 spinboxes) → "Save as New Preset" writes to `~/.config/fm24_editor/weights/`
- Active preset persisted in `~/.config/fm24_editor/settings.json`
- `role_rating(person, role_name, weights=None)` — weights param optional, falls back to equal-weight when None
- `_active_preset` loaded at startup in `MainWindow`; re-loaded when settings applied
- Preset name shown in `[FMScout Community]` label next to role dropdown
- Changing preset while Best by Role is open auto-refreshes the report

**Weight generation**: `scripts/gen_weights.py` (scratchpad) — GROUP_PRIMARY + ROLE_PRIMARY_OVERRIDE maps key attr indices to tiered weights; possession/direct play apply ±4 modifiers to technical/physical attr sets.

**New files**: `fm_editor/weights.py`, `fm_editor/weights/equal_weight.json`, `fm_editor/weights/fmscout_community.json`, `fm_editor/weights/possession_based.json`, `fm_editor/weights/direct_play.json`

**Changed files**: `gui/main_window.py` (SettingsDialog, WeightEditorDialog classes; _open_settings, _active_preset, weights label, _get_report_players update), `gui/roles.py` (role_rating weights param)

### Session 4 fixes/features (2026-09-28) — continued

**Status bar black corner fixed**:
- `QSizeGrip` inside `QStatusBar` didn't paint background when launched via desktop shortcut (no terminal). Fixed with `setSizeGripEnabled(False)` — window manager handles resizing.

**Badge text → pure white**:
- All `_POS_BADGE_COLORS` fg values changed to `#FFFFFF` for legibility on all badge backgrounds.

**Dot animation**:
- Changed from ping-pong `[1,2,3,4,5,4,3,2]` to growing cycle `[1,2,3,4]` (`.` `..` `...` `....` repeat).

**Inline search dropdown**:
- Multiple club matches no longer open `QInputDialog`. Instead `_show_search_dropdown()` shows a floating `QFrame(Qt.Popup)` below the search box with clickable club name buttons. Auto-dismisses on outside click.

### Session 4 fixes/features (2026-09-28)

**Sub-squad tabs** — squad view now shows First Team + youth/reserve tabs:
- Two detection strategies combined:
  - **Kind-based** (English clubs): `find_squads` now also captures kinds 18-23 into `sub_squads = {club_id: {kind: [pids]}}`. Kind 100 = first team; 21=U21, 23=U23, 20=Reserves, 19=U19, 18=U18.
  - **Prefix-based** (German/Spanish B teams): clubs named `"Main Club X"` (e.g. "FC Bayern München II") detected by name prefix match, kind 100 squad used.
- `_build_squad_tabs(club, squad)` called from `_show_squad` — removes old dynamic tabs, detects sub-squads, inserts clickable tab buttons before the stretch.
- `_switch_sub_squad(tab_idx, sub_squad)` — updates checked state across all tab buttons, swaps `self._squad`, repopulates table.
- Cache version bumped to 7 (adds `sub_squads` field).

**"First Team" text clipping fixed**:
- Tab bar height 36→40, margins `(12,3,12,0)`, QSS padding `6px→0px` with `min-width:80px`.
- `ft_btn` uses `setSizePolicy(Minimum, Expanding)` instead of `setFixedHeight` — lets Qt compute correct minimum width.

**PyQt6 disconnect() TypeError fixed**:
- `signal.disconnect()` raises `TypeError` (not `RuntimeError`) in PyQt6 6.11 when no connections — all disconnect guards now catch `(RuntimeError, TypeError)`.

**Search crash fixed**:
- `_do_search` wraps `_do_search_inner` in try/except; exceptions show status message instead of crashing to desktop.

**Nav button locking**:
- Squad, Staff, My Shortlist buttons disabled until a save is loaded.

**Column auto-fit**:
- `resizeColumnToContents(i)` called once after populate on all four tables (squad, staff, reports, players).

### Session 3 fixes (2026-09-28)

**Reports CTD — fixed** (commit `fded9c2`):
- Root cause: `clicked(bool)` in PyQt6 6.11 passes checked state as positional arg, overriding lambda default `lambda k=key:` → `_run_report(True)` → `TypeError` → `qFatal()` → crash
- Fix: all sidebar lambdas changed to `lambda checked, k=key:` and `_nav_to_squad_view(self, checked=False)`

**Crash logging — fixed** (commit `338e1dc`):
- `Terminal=false` in desktop shortcut killed all stderr; added `sys.stderr` + `faulthandler` redirect to `/tmp/fm_editor_crash.log` in `main.py`

**Report switching freeze — fixed (this session, uncommitted)**:
- Root cause: `QHeaderView.ResizeMode.ResizeToContents` on cols 1-6 triggered O(n²) text measurement on every `setItem()` across 200 rows × 6 cols
- Fix: switched cols 1-6 to `Interactive` with preset fixed widths (Pos=55, CA/PA/Dev=45, Age=40, Nation=50)
- Also added `QApplication.processEvents()` after button setChecked calls so buttons repaint before populate (eliminates double-glow during any remaining latency)

---

## What the app does

1. **Load** — file-picker for any `.fm` save; parses binary archive (~30–60 s first run, instant from cache)
2. **Search** — type a club name in the topbar search to load their squad, or a player name to find them
3. **Squad view** — shows club squad with Pos (colored badge), CA, PA, Dev Rate, Age, Nation (flag emoji), HGP, HGC columns
4. **Player detail** — double-click a player to open their profile modal (attributes, CA/PA bars, HGP/HGC pills, Make HGP / Make HGC actions)
5. **Patch** — select players in squad view, hit Make HGP or Make HGC; saves to a new file via file dialog (default: `SaveName-Edited-DATE.fm`)
6. **Save Changes** — topbar button writes current binary state to file (no patching)
7. **Reports** — Scouting → Reports sidebar section; table view with Best Prospects (PA≥160), Wonderkids (age≤21, PA≥150), Best in Position (position picker), Best by Role (coming soon)
8. **Players** — Scouting → Players sidebar section; shows all parsed players sorted by CA with name/pos/nation/min-CA/nation filters; player search results land here
9. **Staff** — Staff sidebar entry; table of all non-player people (no CA/PA) showing Name, Nation, Age; populated on save load

---

## UI layout (`gui/main_window.py`)

### Stack views (QStackedWidget `_main_stack`)

| Index | Key | View |
|-------|-----|------|
| 0 | `club` | Club overview (name, player/HGP/HGC counts) |
| 1 | `squad` | Squad table (QTableWidget `_table`) |
| 2 | `staff` | Staff table (QTableWidget `_staff_table`) — Name, Nation, Age |
| 3 | `shortlist` | My Shortlist (stub) |
| 4 | `reports` | Scouting Reports table |
| 5 | `players` | All Players view (QTableWidget `_players_table`) |

### Topbar

Left: ◀ ▶ breadcrumb | Center: search box (leads to club squad or Players view) | Right: Save Changes · Load · Reload · ⚙

### Sidebar

- **MAIN**: Club, Squad, Staff, My Shortlist
- **SCOUTING**: Players, then Reports sub-section (Best Prospects, Wonderkids, Best in Position, Best by Role)

### Squad table columns

Name | Pos (badge) | CA | PA | Dev | Age | Nation (flag) | HGP | HGC

- Pos column uses `_PosBadgeDelegate` — colored rounded badge (GK=amber, DEF=blue, MID=green, FWD=red)
- Nation column shows flag emoji from `_NATION_FLAG` dict; falls back to nation name

### Players view filters

Name text | Position dropdown | Min CA | Nation dropdown | Clear button

Double-click a player in Players view → navigates to their club's squad.

---

## Key classes / functions

| Symbol | Location | Purpose |
|--------|----------|---------|
| `_populate_staff_table` | main_window.py | Fills `_staff_table` with people who have no CA/PA |
| `ParseWorker` | main_window.py | QThread — parses .fm archive |
| `PatchWorker` | main_window.py | QThread — patches HGP/HGC or `mode='save_only'` |
| `PlayerDetailDialog` | main_window.py | Player profile modal (attrs, CA/PA bars, action strip) |
| `_PosBadgeDelegate` | main_window.py | Custom QStyledItemDelegate for Pos column badges |
| `_attr_val_color(v)` | main_window.py | Returns color for attr value (gold ≥17, green ≥16, …) |
| `_NATION_FLAG` | main_window.py | nation_id → flag emoji mapping |
| `_POS_BADGE_COLORS` | main_window.py | pos string → (bg, fg) for badge delegate |
| `_DOT_SEQ` | main_window.py | `[1,2,3,4,3,2]` ping-pong dot animation |
| `NATIONS` | main_window.py | nation_id → nation name (35 entries) |
| `POSITIONS` | main_window.py | FM24 position strings list |
| `find_club_entity_id` | fm_editor/patch.py | Finds club entity ID from b11=0x6a records |
| `is_hgc` | fm_editor/patch.py | Checks HGC status from training records |
| `patch_to_hgc` | fm_editor/patch.py | Patches/inserts HGC training record |

---

## Known limitations / UI stubs

| Feature | Status |
|---------|--------|
| Staff view | Live — table of Name/Nation/Age, no filters yet |
| My Shortlist | Stub — wire up Add to Shortlist from player modal |
| Best by Role report | Live — 4 bundled weight presets (FMScout Community default). Weight editor + import in Settings (⚙). |
| ▶ / ▼ navigation buttons | Disabled (greyed) — no back/forward history yet |
| Right tab nav in player modal | Only Profile tab active; Transfer/Positions/Ratings are future |
| Squad number (#) column | Not implemented — mockup had it, excluded by design |
| Sub-squads (U21/B team) | Live — tabs generated from kind-based (English) and prefix-based (German/Spanish) detection. English clubs with no kind-18/21 records in squads won't show sub-tabs. |
| Players view: load all | Currently loads all people with CA data (no explicit limit enforced in filter; display caps at 3000 rows); slow on first open for large saves |
| HGP/HGC patching from cache | Disabled — requires binary `b` in memory; user must Load (not use cached version) |
| Player photo | Placeholder person icon; FM save doesn't store player photos |

---

## Binary format quick-ref

See memory file: `~/.claude/projects/-run-media-acidtwin-Gaming-SSD-1-Claude-Code-Projects-FM-Save-Editor/memory/fm24-binary-format.md`

- **Ability block**: scanned from `names_end + 57`, gate at `b[at-37]==0 && b[at-35]==0`; CA at `b[at-38]`, attrs at `b[at..at+54]`
- **HGP**: secondary nation record `b10=0x08, b11=0x46`
- **HGC**: training record `b10=0x01, b11=0x48`, bytes 0-3 = club entity ID (LE u32)
- **Personality**: `b[end+17..end+25]` in person record, 8 bytes 1-20

---

## Next steps / ideas

- Wire **Add to Shortlist** in player modal → My Shortlist view
- **Back/forward** navigation history (`_nav_history` stack)
- **Sub-squad tabs** — working for clubs with kind data; investigate if kind 18-23 presence varies by league setup or save age
- **Best by Role** report — map positions to FM roles, rank by relevant attributes
- **Player photo** — if FM24 image packs can be located on disk, load by player ID
- **Bulk export** — export squad CSV
- **Season update** — `FM_SEASON_YEAR` is hardcoded to 2024; could derive from save filename or header
