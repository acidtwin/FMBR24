# FM Backroom 24 - Handover (current state)

Refreshed on `main` @ `cff88f3`. Facts were checked against the code unless marked **(unverified)**. Scope: `PRODUCT.md`. Rules and Qt gotchas: `CLAUDE.md`. Binary format: memory `fm24-binary-format.md` (not copied here). Old session diary (partly stale, untouched): `docs/HANDOVER-archive.md`.

## 1. What this is, run and test

PyQt6 desktop tool (Linux, Python 3.12) that parses FM24 saves (`.fm`, FMF archive, zstd members) and shows clubs, squads, staff, scouting reports, shortlists, Save Info and a detailed player window, plus homegrown (HGP/HGC) patching. Unofficial: never imply affiliation with Sports Interactive / SEGA (disclaimer in README, About dialog, `fm_editor/settings.py::LEGAL_LINE`). FM24 only (FM23 saves fail in `archive.py`).

```bash
pip install -r requirements.txt        # PyQt6, zstandard, numpy
python main.py                         # crash log /tmp/fm_editor_debug.log (sys.excepthook logs slot exceptions)
FMBR24_CONFIG_DIR=$(mktemp -d) QT_QPA_PLATFORM=offscreen python3 tests/test_<name>.py   # plain scripts, no pytest
```

- Always set `FMBR24_CONFIG_DIR` (temp dir) so `~/.config/fm24_editor/settings.json` is untouched. Cache dir `~/.cache/fm24_editor` and config dir `~/.config/fm24_editor` keep the old app name on purpose.
- 35 test scripts (`ls tests/test_*.py`) plus `tests/snapshot.py` (helper) and `tests/golden_parse.json`. Need the real save (print `SKIPPED ...`, exit 0 when absent): `test_parse_golden` (~40 s reported), `test_squads` (~30 s reported), `test_saveinfo`, `test_injuries`, `test_human_clubs` (real part), `test_club_extra`, `test_player_stats`, `test_club_info`, `test_contract_block`, `test_height_weight`, `test_value_est`, `test_history` (also needs the FM install DB). `test_traits` / `test_potential` skip their real-player part without a scratchpad pickle. The rest are synthetic (patch queue, savefile, player window, themes, radar, badges, settings, busy veil, reload restore, hero glow, cache use, ...).
- **Snapshot-gated tests** (`test_club_extra`, `test_player_stats`): in-game values (league tables, season stats, scouting budget) move as the user plays. `tests/snapshot.py` runs the exact comparison only when the save's in-game date is `SNAPSHOT_DATE = 2028-01-02` (budget also needs the recorded game name), else prints "INVARIANTS ONLY" and checks invariants. `FMBR24_SNAPSHOT_SAVE=<frozen copy>` forces the exact run.
- **Golden test** (`test_parse_golden`): `tests/golden_parse.json` hashes offset-INDEPENDENT fields only (ids, names, nation, birth, ca/pa, attributes, hgp, ...), so a re-save by the app (an HGC/HGP insert shifts offsets) does not break it; `offset/end/identity_offset/he` are only checked for self-consistency. Re-baseline (delete the json, rerun) only after a deliberate parser change. `FMBR24_GOLDEN_SAVE=<path>` runs it on another copy.
- Headless UI check: see `CLAUDE.md` (offscreen, `grab().save()`, LOOK at the PNG).

## 2. Repo state

- Remote `git@github.com:acidtwin/FMBR24.git` (private), `main` = integration branch, in sync with `origin/main` at refresh time (`git rev-list --count origin/main..main` = 0). The parent `Claude Code Projects` folder is a separate monorepo: never push it. Commit/push only when asked, explicit `git add` paths.
- **Stale worktree `.claude/worktrees/agent-a2f1416595792e647`** (branch `worktree-agent-a2f1416595792e647`) holds UNREVIEWED, UNCOMMITTED staff-parsing work (modified `fm_editor/cache.py`, `fm_editor/gamedb.py`, `gui/main_window.py`, new `scripts/probe_staff_extended.py`). The user is undecided: do NOT delete it without asking, and check `git -C <worktree> status` first. Also `origin/feat/player-staff-shortlists` (superseded PR #1).
- Everything else (cleanup/review/feature branches) is merged and gone.

## 3. Architecture and UI map

`gui/` (Qt) on top of `fm_editor/` (no Qt: parsing/logic). Sizes: `gui/main_window.py` ~6080 lines, `gui/player_window.py` ~1620, `fm_editor/gamedb.py` ~760.

| File | Role |
|---|---|
| `fm_editor/archive.py` | FMF container read/write (zstd members) |
| `fm_editor/gamedb.py` | `game_db.dat` parser: `find_names/clubs/squads/people/abilities/contracts/contract_blocks/employment/club_staff/injuries/coaching_attrs/staff_extras`, `add_club_finance`, `parse_injury_manager`, `match_identities` |
| `fm_editor/saveinfo.py` | Save Info parser; `human_pids`, `human_club_ids` (from `humans.dat`) |
| `fm_editor/clubextra.py` | club status/reputation, stadium, league table position, human-club scouting budget, `rep_stars`, `is_league_table`, `fixture_pairs` |
| `fm_editor/playerstats.py`, `history.py` | season stats (`player_stats.dat`); career history (save overlay + FM install DB) |
| `fm_editor/traits.py`, `traitrec.py`, `potential.py` | trait table (`TRAIT_TABLE` = the one source of trait names), trait recommender, Full Potential projection (display only) |
| `fm_editor/patch.py`, `savefile.py` | HGP/HGC patching (`apply_queue`), safe save writer (`save_in_place`), section 4 |
| `fm_editor/cache.py` | parse cache, `_CACHE_VERSION = 30`, `file_signature` (mtime_ns + size taken before the parse) |
| `fm_editor/settings.py` | settings JSON, no Qt; `DEFAULTS` is the key list; `PLAYER_THEMES`, `LEGAL_LINE` |
| `fm_editor/abilitystars.py`, `agecalc.py`, `weights.py`, `nations.py` | star mapping + `half_stars`, the one age helper (`person_age`, `set_ref`), role weight presets (`fm_editor/weights/*.json`), nations |
| `gui/workers.py` | `ParseWorker` (full parse; uses cache when `use_cache`), `SaveWorker` |
| `gui/main_window.py` | all main UI/logic; `gui/theme.py` COLORS + app QSS; `gui/people_model.py` virtualised `PeopleModel` (all players/staff, no cap) |
| `gui/player_window.py`, `pw_widgets.py`, `pw_themes.py` | player window; radar + foot widgets; texture themes |
| `gui/settings_page.py`, `about_dialog.py`, `search_suggest.py`, `stars.py`, `roles.py`, `icon.py` | Settings page, About, search autocomplete, shared `_StarWidget`, role definitions, app icon (`make_app_icon`); images in `gui/assets/` |

**Views** (`MainWindow._VIEW_INDEX`, `_main_stack`, Back/Forward via `_nav_history`): `club` 0, `squad` 1, `staff` 2, `shortlist` 3, `reports` 4 (top 200), `players` 5, `club_staff` 6, `welcome` 7, `save_info` 8 (default landing page), `staff_shortlist` 9, `settings` 10 (top-right gear). Sidebar: MAIN (Save Info, Club, Squads, Club Staff, Player Shortlist, Staff Shortlist), SCOUTING (Players, Staff), PLAYER REPORTS (Best Prospects, Wonderkids, Best in Position, Best by Role), STAFF REPORTS (a disabled 'Coming Soon' stub). Search box: club -> Club page, player -> Players, staff -> Staff (`gui/search_suggest.py`).

**Settings keys** (`DEFAULTS`): `default_save_dir`, `role_weights_preset` ('FMScout Community'), `landing_page` ('save_info'; also 'club', 'players'), `show_pending` (True), `use_cache` (True), `ability_display` ('stars' | 'numbers'), `player_theme` ('steel'; pitch, floodlit, plain), `trait_threshold` (11, 1-20).

**Parse and cache.** Load goes through `ParseWorker`; with `use_cache` a normal Load uses `load_cache`, **Reload always re-parses** (`_reload_save(use_cache=...)`). Cache keyed by path + mtime_ns + size, cleared after a successful save. Reported timings (not re-timed): full parse ~15 s, cached load ~2 s. Bump `_CACHE_VERSION` whenever a parsed field is added or changes (`test_cache_use.py`, `test_parse_golden.py`).

**Busy veil.** While a SAVE or RELOAD runs (not on a first load: the Welcome page has its own state) `_set_busy` sets `self._busy`, which `_update_ui_state`, `_nav_back_btn_update`, `_update_patch_btns`, `_do_save`, `_reload_save`, `_load_path` honour (no re-entrancy; Save/Reload/Search/nav/Settings stay disabled). It disables `_main_stack` and shows `_BusyVeil` (`ALPHA` 140, "Saving"/"Reloading" + bouncing dots `_DOT_SEQ`). Tests `test_busy_veil.py`, `test_review_fixes.py`.

**Hero glow** (`HERO_GLOW` dict above `_HeaderHeroWidget`): the Welcome header's grid lines pulse during a FIRST load only. `_set_busy(True)` with no veil starts it; the glow begins after `delay_ms` 0.8 s (a ~2 s cached load gets a short pulse, sub-second none), `_set_busy(False)` eases it out over `fade_ms`, and it is cut as soon as the header leaves the Welcome page. Smooth sine (`period_ms` 3400, `peak_alpha` 0.10, 60 fps timer stopped when idle), NOT tied to the progress-bar value. Test `test_hero_glow.py`.

## 4. Save and patch system (HGP / HGC)

HGP = secondary-nation record `b10=0x08,b11=0x46`; HGC = training record `b10=0x01,b11=0x48`, bytes 0-3 = club entity id = club id + 1. `MainWindow._entity_of` is the ONE helper for display and write (`patch.find_club_entity_id` is a vote that disagrees for ~1,800 clubs; unused by the GUI). Record scans cover the full record count (some players have up to 125), bounded by the buffer. Layouts: memory `fm24-binary-format.md`.

**Queue flow (nothing patches `game_db` in memory):**
1. Controls: HGP/HGC pills in the player window header (`queue_toggle`) and the Squads toolbar `Make HGP` / `Make HGC` (`_queue_selected`, `_update_patch_btns`). Only players of a human-managed club (`save_data['human_clubs']`) are queueable; others get a display-only pill ('Not your club' / 'Open from Squads to patch'). A player with no club shows NO HGC pill (club unknown).
2. Queue = `MainWindow._queue`, `(person id, 'hgp'|'hgc') -> person`. `_queue_changed` sets `_dirty`, status text, sidebar 'Unsaved changes', enables Save, refreshes badges and the open player window (`refresh_queue`). Cleared by Load/Reload/`_finish_load` and after a successful save.
3. **Save Changes** (`_do_save`): ONE confirm dialog (backup plan; skipped on close/load-another, `confirm=False`). `_apply_queue_copy` runs `patch.apply_queue` on a COPY of the buffer: HGP on existing 0x46 records in place, then inserts for persons sorted by record offset descending (an HGC record; plus a NEW England 0x46 record for a person with no 0x46 at all, e.g. a foreign signing; only the missing part is added). `SaveWorker` -> `savefile.save_in_place`: writes `<save>.fm.tmp`, re-opens and verifies (member list, sha256 of every unmodified member, decompressed `game_db.dat` equals the patched buffer), backups, then `os.replace`. Any failure leaves the original file, in-memory buffer and queue untouched.
4. `_on_save_done` clears the queue and **reloads automatically** (`_reload_save()`; skipped when a close/load-another is pending). **Restore after reload:** `_reload_save` takes `_capture_ui_state()` (view, club id + squad tab, search text, filters, Players subset by person ids, sort, top row/selection by person id, Back/Forward history by club id); `_finish_load` calls `_apply_ui_state()` instead of `_land_after_load()`. A different file, a missing club or the Settings page falls back to the landing page. Not restored: the open player window, queued changes, pixel scroll offset. Test `test_reload_restore.py`.
- **Backups:** `<save>.fm.bk1` = file just before this save, `.bk2` = previous bk1; the first save (no backup yet) makes both from the original; a lone bk2 is kept as the original. A failed rotation after the replace counts as saved ('backup rotation failed', `info['backup_error']`). Names end `.bk1/.bk2` so FM24's Load Game list ignores them. Space check 3x file size on a first save (or only legacy `bk1-<name>.fm`), else 2x (+16 MB). Save is refused if the file changed on disk since load (`save_data['disk_sig']`). Dirty guards: Reload asks 'Discard unsaved changes?'; Load another / window close ask Save / Discard / Cancel.
- **List badges:** `_HGBadgeDelegate` draws HGP/HGC pills in Squads (both), Reports and Players (HGP only; Shortlists none); queued = yellow `+ HGP`; `_RowMarkDelegate` (`ROWQ_ROLE`) tints queued rows + yellow bar on Name; `PeopleModel.set_queue` repaints affected rows; `_refresh_queue_marks` drives it.
- Tests: `test_patch_queue.py`, `test_savefile.py`, `test_hg_badges.py`, `test_human_clubs.py`.
- **Decision (2026-10-01):** the patches still overwrite a player's existing 0x46 / 0x48 records (losing e.g. other-nation or previous-club records); decided to leave it, it works in game.

## 5. Player window (`gui/player_window.py`, master mockup `mockups/player-window.html`)

`PlayerWindow(QDialog)`, 1122x760 (min 1062x640), opened by double-click from any list via `MainWindow._run_player_window`; always opens on Profile.
- **Header** (`QFrame#pwHeader`): identity + HGP/HGC pills, then boxes CURRENT ABILITY, POTENTIAL ABILITY, DEVELOPMENT RATE, CHANGES QUEUED. CA/PA/Dev Rate show stars or number + bar per `ability_display` (raw number in the tooltip). Mapping in `fm_editor/abilitystars.py`: CA/PA = value/40, Dev Rate = value/4, nearest half star, ties UP (`half_stars`, also used by `rep_stars`), clamp 0.5..5.
- **Tabs** (`TABS`): Profile, Contract & Transfer, Positions, General Rating (placeholder), Role Rating (placeholder), Training (Recommended traits + 'Coming soon' block), History. New tab = write `_page_<key>` and name it in `TABS`; `None` = 'Coming soon' text from `SOON`.
- **Action strip** (`#actionStrip`): `Add to Shortlist` + `Close` (Close last). No Make buttons (the pills do that).
- **Profile**: cards Position | This season (or Career) | Fitness; attribute grid (follows the `Current | Full Potential` toggle) with the radar over Footedness; Personality (7 bars) + Player traits (names from `TRAIT_TABLE`, threshold `trait_threshold`).
- **Six-axis radar:** one table `RADAR_OUT` / `RADAR_GK` in `gui/pw_widgets.py` (axis, attributes, lower-is-better names; axis = mean, inverted attributes as 21-v). Outfield: Attacking, Creativity, Athleticism, Defending, Reliability, Mentality; GK: Shot-stopping, Command, Athleticism, Distribution, Reliability, Mentality. The app's own groups, not the game's Technical/Mental/Physical. Test `test_radar_axes.py`.
- **Themes** (`gui/pw_themes.py`): registry `THEMES` = steel (default), pitch, floodlit, plain; setting `player_theme`. `STEEL_ALPHA = 0.75` scales every translucent Steel layer (mirrors the mockup). New theme = registry entry + `PLAYER_THEMES` in `fm_editor/settings.py` (`test_themes.py` enforces both).
- **Data fed in:** `player_extra_data` (wage, value, height/weight, traits); `history.career_for_person` (needs the FM install DB, PENDING chip when absent); Full Potential via `potential.project_attrs` (toggle ALWAYS selectable, user decision; tooltip note when PA <= CA or age >= 30, `potential.availability` is advisory). Ages exact from birth year + day (`agecalc`), reference date = the save's in-game date. Club contract-expiry counts also use the in-game date (`_contract_expiry_counts(..., _get_age_ref())`), not the wall clock.
- **League table rule:** a club's league position comes only from a table that is a round robin (`clubextra.is_league_table`: >= 90% of team pairs have a fixture in `fix_man.dat`, `fixture_pairs`); cup group stages are excluded; clubs whose division has no table get no 'league'.
- Known layout items: Profile scrolls ~136 px at the default size (ignore for now); GK profile has a gap under the Goalkeeping column.

## 6. Data pointers

Byte-level facts live in memory `fm24-binary-format.md` (read before touching a parser). Section index: s1 player record, s2 linked records, s3 staff, s4 Save Info, s5 club record, s6 finances, s7 season stats, s8 squad arrays, s9 traits, s10 reputation/stadium/league table/scouting budget, s11 height/weight/wage (a second '11' is career history), s12 contract block + wage, s13 injuries + transfer value. Dead ends and open decodes are listed there (Save Info: start nation, database size, future transfer mode, editor allowed/used, manageable teams need a second save with known different settings). Not in the save (checked): club Region/Founded/Facilities, contract bonuses/clauses, player photos, staff reputation.

## 7. Verified vs unverified

**Verified against in-game screens** (user ground truth): Save Info fields; squad membership (Spurs = 25); club finances (Spurs); season stats; ages; club reputation/stadium/league positions (snapshot 2 Jan 2028); height/weight, contract start/end, weekly wage (18 players); injuries and transfer value (16/16); 56 of 64 trait bits; History vs real careers; **HGP insert for a player with no 0x46 record (Montoro: queued, saved, both tags show in game, 2026-10-01)**.

**Unverified or partial, do not present as fact:**
- FM24 loading a save whose HGC insert changed the file size (our re-parse reads it back; a 16-byte insert was tested on a copy of the real save). The HGP patch may flip `0x40` -> `0x47`; 2,460/2,460 `0x40` records were checked not to be injuries (memory note), in-game check of changed bytes still open.
- Trait bit 48 unknown (guess: Attempts To Develop Weaker Foot). Bit 53 = flag carried only by staff/non-players. Bits 49, 61, 62 are set but never shown by the game (hidden in the UI).
- `foot_word` ranges (Weak 7-8, Reasonable 9-11, Fairly Strong 12-14, Strong 15-19, Very Strong 20): Strong at 17-19 vs Very Strong and the Very Weak range are unconfirmed. Position familiarity word ranges (Natural .. Ineffective): need an in-game hover screenshot.
- Club reputation stars: `rep_stars` = rep/2000 to the nearest half star, 5 stars from 9125 (midpoint of 9053..9197, not decoded); fitted to ~9 clubs.
- Weekly wage: stored u32 within 2% of in-game (18/18); display rounding steps inferred (the 50K step above 300K rests on one player); outliers (Saliba, Sancet) unchecked. `find_contracts` ('Until' from the old `b11=0x6a` record) is wrong for current saves and unused; the app reads `find_contract_blocks`.
- Asking price and transfer/loan status are not in the save (market value is; the game shows a range); those rows stay PENDING.
- Personality: the window shows 7 bars; the save has an 8th byte `personality[7]` = 'Controversy' (parsed, shown in the Staff popup). Whether the game hides it is unknown: compare with a player screen before adding it.
- History: seasons simulated inside the save (2025-28) are not shown; plain-year season labels for calendar-year leagues are an assumption.
- CA/PA and Dev Rate star mappings approximate FM's relative stars.

## 8. Open TODOs (priority order)

1. Club-header reputation stars have no numbers mode (star-ratings rule) and `SettingsPage` has no tests.
2. **Reports / Players HGC column** (both show HGP only).
3. **Staff window redesign** (parked; `StaffDetailDialog` is the old layout, no mockup yet). Decide what to do with the stale staff-parsing worktree (section 2).
4. General Rating / Role Rating tabs: need in-game screens from the user (Role Rating could mirror the 'Role and Duty' list); fill the Training tab beyond Recommended traits.
5. Per-group league tables for Brazil / Spain (groups; today only a full round robin counts).
6. Personality 'Controversy' check (section 7); more in-game evidence for the unverified items.
7. Unsupported QSS properties (`letter-spacing`, `text-transform`, e.g. `_CLUB_PENDING_QSS` in `gui/main_window.py`, `theme.py`): ignored by Qt, replace with `QFont`/`.upper()`.
8. Unlock-on-failure: `_on_parse_done` (before `_step_preload` takes over) and the post-replace `parse_archive` in `_on_save_done` can leave the busy lock on if they throw.
9. GitHub polish at 1.0 (description, topics, social preview); then Flatpak (`io.github.acidtwin.FMBR24`) and Windows builds (Steam/save path handling); bundle Barlow Condensed.
10. Small: Staff Reports (sidebar stub); more Staff / Club Staff filters; FM23 support in `archive.py`; weight Full Potential growth shares by CA weight.
**Page icons.** The header badge circle shows `resources/icons/pages/<name>.png` (512 px transparent PNGs, glyph about 62 % of the cell) via `_set_header(..., icon=name)` / `_page_icon` (falls back to the page's initial letter if the file is missing). Names: save_info, club, squads, club_staff, player_shortlist, staff_shortlist, players, staff, settings, and the Player Reports icons by `_REPORT_ICONS` (best_prospects, wonderkids, best_in_position, best_by_role; generic player_reports). Spare, not wired yet: staff_reports, search_results, transfers, contracts. Sheets are AI-generated 1536x1024 (3x2 cells of 512); cut with `scripts/cut_icon_sheet.py SHEET OUT_DIR name1..name6` (colour un-mix background removal, recentres each glyph on its visible bounding box).
