# FM Backroom 24 — Handover

**Last updated:** 2026-09-30 (end of session 12). Repo: `/run/media/acidtwin/Gaming SSD 1/Claude Code Projects/FM-Save-Editor` (own git repo, branch `main`, remote `git@github.com:acidtwin/FMBR24.git`, private). Check `git status` for uncommitted work. Deep binary facts: memory `fm24-binary-format.md`.

## Current state

- PyQt6 FM24 save tool ("FM Backroom 24", FMBR24; unofficial, FM24 only, Linux). Tested on a real Tottenham 2026-27 save (~188 MB, parse ~58 s).
- Parse cache `_CACHE_VERSION = 16` (`fm_editor/cache.py`; stores people, squads, clubs, `save_info`). `load_cache` is imported in `gui/main_window.py` but never called, so every load re-parses (perf win available).
- Tests (plain scripts, run with `python3 tests/<file>`): `test_saveinfo.py` (real save, skips if absent), `test_saveinfo_format.py`, `test_club_contracts.py`.
- Cache/config dirs still `~/.cache/fm24_editor`, `~/.config/fm24_editor` (active weight preset in `settings.json`) — intentional.
- Leftover local worktree `.claude/worktrees/agent-a2f1416595792e647` (stale edits; safe to delete, ask user).

## Session 12 summary (rename, Club page, Save Info, branding, GitHub)

- **Rename** to FM Backroom 24 applied (window title, welcome/breadcrumb, `main.py`); README carries the unofficial disclaimer; About section (with disclaimer) lives on the Settings page.
- **Club page** (`_make_view_club` / `_update_club_view`): flat KPI bar + 3 columns; unparsed data shown as PENDING chips (`_club_pending_chip`): region, founded, status, reputation, facilities, finances, manager, match rating; masthead subtitle "Division pending · Country pending · Position pending"; 3 stars + "CLUB REPUTATION" are decorative placeholders.
- **Quick Filters**: shared `_make_quick_filters_frame()`; Players is the reference; Reports adds name/CA/PA/Dev + Clear and keeps Position/Role pickers; Shortlist filters (staff exempt from CA/PA/Dev); Staff and Club Staff have age-only filters. All age spinboxes are 0..99, default 0/0 where 0 = bound disabled (`_age_in_range`); nobody is hidden by default. Per-page title bars removed; masthead carries titles (`_REPORT_LABELS` for report subtitle + count).
- **Search routing**: club -> Club page (`_show_squad` tail, `_nav_restore` keyed on 'club'), player -> Players, staff -> Staff (`_show_staff_results`; staff no longer leak into Players).
- **Search autocomplete** (session 13): `_SearchSuggest` (child QFrame#searchDropdown of MainWindow, not a Popup window, so it never steals focus; QListWidget + `_SuggestDelegate` paints name, muted club, right-aligned Club/Staff/Player tag). Shown from >=3 chars, 130 ms debounce (`_sg_timer`), up to `_SG_MAX`=12 rows ranked prefix > word-start > substring, then Club < Staff < Player, then name. Index `_sg_index()` = lazy list of `(lname, name, kind, obj)`, reset to None in `_on_parse_done`. Keys: Up/Down/Esc/Enter filtered on the search box (row 0 preselected, so Enter picks the top hit; <3 chars or no hits falls back to the old `_do_search`); click outside closes via app event filter. `_sg_pick` reuses `_show_squad` / `_show_player_results([p])` / `_show_staff_results([p])`. `_show_search_dropdown(matches)` (old Enter multi-club case) now feeds the same popup. QCompleter was rejected: awkward two-column row styling.
- **Loading states**: `_set_busy` disables all nav buttons, `_update_ui_state` restores; topbar Load shows static "Loading", welcome button "Loading Save"; dot animation only in the status bar. `_BTN_SS` disabled style fixed (QSS opacity is ignored). Spinbox arrow gap fixed by deleting per-widget `_spin_ss` and setting `QSpinBox::up-button/down-button` height 13px in `gui/theme.py`.
- **Save Info page** (design B: identity rail `#141c27` + ledger; table-driven `_SI_LAYOUT`, one tuple per field; rows hide when data absent, no PENDING; view key `save_info` = stack index 8; first sidebar item in MAIN; app lands here after load/reload) built on `fm_editor/saveinfo.py::parse_save_info`. Fields: game name, times saved, dates (created/in-game/start), game time, game version/build, db version/changes, manager + club, nations/leagues, players+staff. Not decodable yet: database size, start nation, future transfer mode, editor allowed/used, manageable teams, dedication (details + what would settle them: memory `fm24-binary-format.md` section 4).
- **Sidebar/brand**: header = floppy logo `gui/assets/brand_mark.png` (`_BRAND_MARK_PX`=34) + wordmark `_APP_WORDMARK` ('FMBR24') + status line (No save loaded / Save loaded · date / Unsaved changes with gold dot via `self._dirty`, `_update_sidebar_status`). App icon = save-disk-over-pitch, ladder `resources/icons/icon-{16..512}.png`, master `resources/icon-source.png`, loaded by `gui/icon.py::make_app_icon()`. Sidebar texture: `gui/assets/sidebar.webp` (dark diagonal grain) drawn by `_SidebarFrame.paintEvent` at 0.22 opacity.
- **Mockups** (`mockups/`): club-page-design-a, save-info-page-design-a/b (B built), sidebar-header-options (A built).

## Settings page (session 13)

- Replaces the old `SettingsDialog` (deleted). 1:1 from `mockups/settings-page-design-a.html`. View key `settings` = stack index 10 (`_VIEW_INDEX`), normal history entry; opened by the hero gear (checkable, shows page-open state via `_update_header_for_view`) and a "Settings" sidebar entry pinned at the bottom (`_nav_btns['settings']`, kept enabled by `_set_busy`). Hero image: `_PAGE_IMAGE['settings']` = stadium.
- Code: `gui/settings_page.py` (`SettingsPage`; page QSS scoped under `QWidget#settingsPage`, chevron/check SVGs written to tempdir like `_SPIN_UP_SVG`), `fm_editor/settings.py` (no Qt: `load/save/defaults/folder_status/save_dialog_dir`, `APP_VERSION='0.0.0-dev'`, legal line), cache helpers `cache_dir/cache_info/clear_all_caches` in `fm_editor/cache.py` (delete only `*.json` inside the cache dir). Test: `tests/test_settings.py`.
- Storage: `~/.config/fm24_editor/settings.json` (same file as the active weight preset; `weights.py` now takes its paths from `settings.config_dir()`). Override with env `FMBR24_CONFIG_DIR` (tests/verification must set it). Unknown keys preserved; corrupt file -> defaults.
- Wired: default save folder (live validation; Load dialog opens there via `_load_file`), role weight preset + Edit Weights... + Import... (+ Delete..., shown only for user presets, kept from the old dialog; staged until Save, Edit/Import/Delete act immediately as before), landing page after load (`_land_after_load`: Save Info / Club (current club, else the manager's club) / Players; falls back to Save Info; never pulls you off the Settings page), Show PENDING markers (`_SHOW_PENDING` module flag; `_club_pending_chip/_club_set_pending/_club_set_value` hide chips + their `clubKvRow`; `_apply_ui_prefs` refreshes the club view), Clear cache (confirm), Open cache folder, About. Footer: Save enabled only when dirty and folder valid; Reset to defaults (confirm) fills widgets, persists only on Save.
- Coming soon (disabled, as designed): auto-detect locations, reopen last save on launch, table density, use parse cache.
- Also fixed: `_nav_push` truncated forward history when Back/Forward re-entered `_nav_to` (dedupe check now first).
- Not verifiable headlessly: real file dialogs (Browse/Import), `QDesktopServices.openUrl`, popup look of the combo list; Barlow Condensed/Inter absent so the chip is wider than the mockup and two "Coming soon" labels wrap.

## Earlier work digest (sessions 5-11)

- **Session 11**: "Quick Filters" labels; squad tab bar bg `COLORS['elevated']` (disabled Make HGP/HGC: surface bg + border); sidebar texture.
- **Session 10**: topbar merged into `_HeaderHeroWidget` (186px = 38px nav row + 148px content); per-page hero images `_HeaderHeroWidget._PAGE_IMAGE` (key -> `gui/assets/<name>.webp`: welcome, stadium (club), squad, staff (also staff), club_staff, shortlist, reports, players; fallback stadium.webp); `_update_header_for_view(key)` -> `self._hero.set_page(key)` is the single hook for page switches (call it from every path, `_run_report` once missed it); progress bar 3px at hero bottom edge; nav button states (Save = dark green `#1a3d28`, Reload = dark amber `#3a2608`, Load blue `#2b6cb0`, semi-transparent dark buttons/search over hero); Club nav disabled until a club is chosen; squad secondary header removed, stats (players/HGP/HGC/injured) in hero right slot; `_squad_header_bar` kept as instance attr (widget GC crash on load otherwise).
- **Session 9**: Players filter = 5 QSpinBoxes (`_players_ca_filter`, `_players_pa_filter`, `_players_age_min_filter`, `_players_age_max_filter`, `_players_dev_filter`; `_apply_players_filter`, `_clear_players_filter` uses blockSignals); Reports columns match squad (65 cols, filter row, sort by Pos); sidebar "PLAYER REPORTS" + disabled "STAFF REPORTS" stub ("Coming Soon").
- **Session 8**: coaching attrs (17 per staff), staff CA/PA, injuries, all 54 player attrs as columns (`max(1,min(20,round(raw/5)))`, `_ATTR_DISPLAY`, `_ATTR_ABBREV`, tooltips `_COL_TT`), contract end (`CtrE`), Squad/Staff table overhaul, DM badge purple `#5A3A8A`, `StaffDetailDialog` (780px: coaching, mental, ability, personality), PlayerDetailDialog action strip = Add to Shortlist only, "Squad" renamed "Squads", status bar `● Ready · file · N clubs, N players, N staff`. `slim_people` cache: players keep ca, pa, positions, raw_attrs, injured, injury_days, contract_end; staff keep coaching, staff_ca, staff_pa.
- **Session 7-6**: `scripts/probe_staff_attrs.py`; `find_club_staff`.
- **Session 5**: role weight presets (`fm_editor/weights.py` + `weights/*.json`: Equal Weight, FMScout Community, Possession-Based, Direct Play; ⚙ Settings dialog with import/delete and per-attr weight editor).

## UI map (`gui/main_window.py`)

`_main_stack` (QStackedWidget), `_VIEW_INDEX`:

| Index | Key | View |
|---|---|---|
| 0 | `club` | Club overview |
| 1 | `squad` | Squads table (`_table`) |
| 2 | `staff` | Staff table (`_staff_table`) |
| 3 | `shortlist` | Player Shortlist (`self._shortlist`, players only) |
| 4 | `reports` | Scouting Reports |
| 5 | `players` | All Players (display capped at 3000 rows) |
| 6 | `club_staff` | Club Staff |
| 7 | `welcome` | Welcome / Load |
| 8 | `save_info` | Save Info |
| 9 | `staff_shortlist` | Staff Shortlist (`self._staff_shortlist`, staff only; table via shared `_make_staff_table()` / `_fill_staff_rows()`, age-only Quick Filters) |

Sidebar: MAIN (Save Info, Club, Squads, Club Staff, Player Shortlist, Staff Shortlist), SCOUTING (Players, Staff), PLAYER REPORTS (Best Prospects / Wonderkids / Best in Position / Best by Role), STAFF REPORTS (stub). Back/Forward use `_nav_history`.

**Squad table columns**: `Name(0) INJ(1) Pos(2) CA(3) PA(4) Dev(5) Age(6) Nation(7) HGP(8) HGC(9) CtrE(10) Cro(11)..Cnc(64)` (54 attrs). Reports table: `Name INJ Pos CA PA Dev Age Nation HGP Club CtrE + 54 attrs` (65). INJ = dark red `#8B1A1A` badge, sorts injured first; Pos numeric key `_POS_SORT_ORDER`: GK0 DR1 WBR2 DL3 WBL4 DC5 SW6 DM7 MC8 MR9 AMR10 ML11 AML12 AMC13 ST14, default sort Pos. Staff tables: 17 coaching cols `Atk Def Fit Mnt SPc Tac Tch WwY Det Mot PMg JPA JSA TKn Neg GKH GKS` + 8 personality `Adp Amb Loy Prs Pro Spt Tmp Ctr`, header tooltips `_STAFF_COL_TOOLTIPS`, `_coaching_col_map` set in `_make_view_staff`. Sub-squads: English clubs kind-based, German/Spanish B teams prefix-based. Squad populate uses fixed widths (`_configure_table_for_mode`); no `resizeColumnToContents` (O(n^2)).

## Key symbols

| Symbol | Where | Purpose |
|---|---|---|
| `find_coaching_attrs` / `find_staff_extras` | gamedb.py | staff coaching dict / CA+PA |
| `find_injuries`, `find_contracts`, `find_employment` | gamedb.py | `injured`/`injury_days`; `contract_end` 'YYYY-MM'; manager + ex-player coach jobs |
| `find_club_staff` | gamedb.py | `{club_id: [pids]}` from club PID arrays |
| `parse_save_info` | saveinfo.py | Save Info dict (only ~5 KB of small members read) |
| `is_hgc`, `patch_to_hgc`, `find_club_entity_id` | patch.py | HGC detection/patching |
| `ParseWorker` | main_window.py | QThread full parse pipeline |
| `_HeaderHeroWidget`, `_SidebarFrame`, `_PosBadgeDelegate` | main_window.py | hero header, textured sidebar, Pos/INJ badges |
| `_SI_LAYOUT`, `_update_save_info_view` | main_window.py | Save Info ledger |
| `_make_quick_filters_frame`, `_club_pending_chip` | main_window.py | shared filter bar, PENDING chip |
| `StaffDetailDialog`, `PlayerDetailDialog` | main_window.py | popups (double-click) |

## Binary quick-ref (full detail in memory `fm24-binary-format.md`)

Ability block `names_end+57` (CA `b[at-38]`, attrs `b[at..at+54]`); personality `b[end+17..end+25]`; HGP `b10=0x08,b11=0x46`; HGC `b10=0x01,b11=0x48` (bytes0-3 = club entity id = club_id+1); injury `b11=0x47` (trail byte0 = days); contract `b10=0x01,b11=0x6a` (byte13=year-2000, byte14=month); coaching magic `XX 1a ea 07` at records_end+10 (CA magic+33, PA magic+35, Section B magic+81 14 bytes /5, Section A extras magic+37+33/36/39); club staff arrays = flat u32 PID arrays, byte before count == 0x00.

## Known limitations / TODO

- GitHub polish at 1.0 (description, topics, social preview), then Flatpak (app-id e.g. `io.github.acidtwin.FMBR24`) and Windows builds (Steam/save path handling).
- Save Info: start nation, database size, future transfer mode, editor allowed/used, manageable teams need a second FM24 save with known different settings to diff (see memory).
- Perf: parse cache is written but never read back (58 s parse each load).
- Club page (session 13): Status + Country (header subtitle) + human-club Manager now real (`find_clubs` adds `nation`/`status`; `fm_editor/nations.py`; `tests/test_club_info.py`; cache v17). Finances (`add_club_finance` -> `club['fin']`, cache v19, structural detection, no hardcoding): 251 clubs with the FULL block (transfer budget, wage budget p/w, balance; Spurs exact vs in-game screen) + ~2,870 clubs with balance only (Championship and below; budgets not stored, stay PENDING); scouting budget not stored; memory section 6. Still pending: Region (city id only, no names), Founded, Reputation, facilities, scouting budget, division/position (comp files undecoded), stadium not stored. Evidence + dead ends: memory `fm24-binary-format.md` section 5. Header star rating is still decorative.
- Staff Reports nav stub; more Staff / Club Staff filters; bundle Barlow Condensed; other icon concepts (shield+grid, scouting lens, data node, nib) for polish.
- `archive.py` fails on FM23 saves (u32 size prefix before zstd frames).
- Not in binary / not found: transfer values, player photos, staff reputation/training rating/roles, contract start date, injury days > 255 encoding; JSA label may be JPP; DM/MC sort order unconfirmed.
