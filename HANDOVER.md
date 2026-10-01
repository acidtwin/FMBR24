# FM Backroom 24 - Handover (current state)

Written 2026-10-02 (branch `cleanup/all`), refreshed on `main` @ `7f3ead8` by the `fix/review-misc` review pass. Facts were checked against the code unless marked **(unverified)**. Old session-by-session diary: `docs/HANDOVER-archive.md` (partly stale, kept unchanged). Product scope: `PRODUCT.md`. Rules and Qt gotchas: `CLAUDE.md`. Binary format: memory `fm24-binary-format.md` (not copied here).

## 1. What this is, how to run and test

PyQt6 desktop tool (Linux, Python 3.12) that parses FM24 save files (`.fm`, FMF archive, zstd members) and shows clubs, squads, staff, scouting reports, shortlists, Save Info and a detailed player window, plus homegrown (HGP/HGC) patching. Unofficial: never imply affiliation with Sports Interactive / SEGA (disclaimer in README, About dialog, `fm_editor/settings.py::LEGAL_LINE`). FM24 only (FM23 saves fail in `archive.py`).

```bash
pip install -r requirements.txt        # PyQt6, zstandard, numpy (numpy is NOT in CLAUDE.md's pip comment)
python main.py                         # crash log /tmp/fm_editor_debug.log (sys.excepthook logs slot exceptions)
FMBR24_CONFIG_DIR=/tmp/x QT_QPA_PLATFORM=offscreen python3 tests/test_<name>.py   # tests are plain scripts, no pytest
```

- Always set `FMBR24_CONFIG_DIR` for tests/verification so the real `~/.config/fm24_editor/settings.json` is untouched. Cache dir `~/.cache/fm24_editor` and config dir `~/.config/fm24_editor` keep the old app name on purpose.
- 31 test scripts in `tests/` (`ls tests/test_*.py`), plus `tests/snapshot.py` (helper) and `tests/golden_parse.json` (parser fingerprint). Real-save tests print `SKIPPED (save not found): ...` (exit 0) when the save is absent: `test_injuries, test_parse_golden (~40 s), test_squads (~30 s), test_human_clubs, test_club_extra, test_saveinfo, test_player_stats, test_club_info, test_value_est`. The rest use synthetic data (patch queue, savefile, player window, themes, radar, badges, settings, ...).
- **Snapshot-gated tests** (`test_club_extra`, `test_player_stats`): in-game values (league tables, season stats, scouting budget) move as the user keeps playing the save. `tests/snapshot.py` runs the exact in-game comparison only when the save's in-game date is `SNAPSHOT_DATE = 2028-01-02` (budget test also needs the recorded game name); otherwise it prints "INVARIANTS ONLY" and checks invariants. On 2026-10-02 the live save is at 2028-01-12, so these run invariants only. `FMBR24_SNAPSHOT_SAVE` points at a frozen copy to force the exact run. `tests/golden_parse.json` hashes offset-INDEPENDENT fields only (ids, names, nation, birth, ca/pa, attributes, hgp, ...), so a re-save by the app (HGC/HGP insert shifts offsets) no longer breaks it; offsets (`offset`/`end`/`identity_offset`/`he`) are checked for self-consistency instead. Re-baseline (delete it, rerun) only after a deliberate parser change. `FMBR24_GOLDEN_SAVE=<path>` runs it on another copy.
- Verify UI changes headlessly: `QT_QPA_PLATFORM=offscreen`, construct the window, `.grab().save()`, and LOOK at the PNG. Wrapped labels need `processEvents()` twice before `grab()`.
- Workflow rules (CLAUDE.md): **mockup first** (`mockups/player-window.html` is the master for the player window; the user tests the live page, serve with `cd mockups && python3 -m http.server 8792`), **Close is always the last button**, **star-ratings rule** (every stars display keeps a numbers mode; `ability_display`).

## 2. Repo and branch state

- Remote `git@github.com:acidtwin/FMBR24.git` (private). The parent `Claude Code Projects` folder is a separate monorepo: never push it. Commit/push only when asked, with explicit `git add` paths.
- **`main` is the integration branch.** `cleanup/all` was merged into it (the old feature/design branches are gone). Nothing is pushed beyond `origin/main` (`git rev-list --count origin/main..main` for how far ahead).
- Leftovers: branch `worktree-agent-a2f1416595792e647` + worktree `.claude/worktrees/agent-a2f1416595792e647` (contained in `main`, may have uncommitted edits: check `git -C <worktree> status` before removing); `origin/feat/player-staff-shortlists` (superseded PR #1). Review branches `fix/review-safety` and `fix/review-misc` (worktrees under `.claude/worktrees/review-*`) wait to be merged into `main` by the user. Nothing was deleted without asking.

## 3. Architecture and UI map

`gui/` (Qt) on top of `fm_editor/` (no Qt, pure parsing/logic). Line counts: `gui/main_window.py` 5685, `gui/player_window.py` 1620, `fm_editor/gamedb.py` 763.

| File | Role |
|---|---|
| `fm_editor/archive.py` | FMF container read/write (zstd members) |
| `fm_editor/gamedb.py` | `game_db.dat` parser: `find_names/clubs/squads/people/abilities/contracts/contract_blocks/employment/club_staff/injuries/coaching_attrs/staff_extras`, `add_club_finance`, `parse_injury_manager`, `match_identities` |
| `fm_editor/saveinfo.py` | Save Info parser; `human_pids`, `human_club_ids` (from `humans.dat`) |
| `fm_editor/clubextra.py` | club status, stadium, league table position, human-club scouting budget, `rep_stars` |
| `fm_editor/playerstats.py`, `history.py` | season stats (`player_stats.dat`); career history (save overlay + FM install DB) |
| `fm_editor/traits.py`, `traitrec.py`, `potential.py` | trait table (`TRAIT_TABLE`), trait recommender, Full Potential projection (display only) |
| `fm_editor/patch.py`, `savefile.py` | HGP/HGC patching, safe save writer (section 4) |
| `fm_editor/cache.py` | parse cache, `_CACHE_VERSION = 30`, `file_signature` (mtime_ns + size captured before the parse) |
| `fm_editor/settings.py` | settings JSON, no Qt; `DEFAULTS` is the key list |
| `fm_editor/abilitystars.py`, `agecalc.py`, `weights.py`, `nations.py` | star mapping, the one age helper (`person_age`, `set_ref`), role weight presets (`fm_editor/weights/*.json`), nation names/flags |
| `gui/workers.py` | `ParseWorker` (full parse pipeline; uses cache when `use_cache`), `SaveWorker` |
| `gui/main_window.py` | all main UI/logic; `gui/theme.py` COLORS + app QSS; `gui/people_model.py` virtualised `PeopleModel` (all 77,966 players / 54,058 staff, no cap) |
| `gui/player_window.py`, `pw_widgets.py`, `pw_themes.py` | player window, radar + foot widgets, texture themes |
| `gui/settings_page.py`, `about_dialog.py`, `search_suggest.py`, `stars.py`, `roles.py`, `icon.py` | Settings page, About, search autocomplete, shared `_StarWidget`, role definitions, app icon |

**Views** (`MainWindow._VIEW_INDEX`, `_main_stack`, Back/Forward via `_nav_history`): `club` 0, `squad` 1, `staff` 2, `shortlist` 3 (players only), `reports` 4 (top 200), `players` 5, `club_staff` 6, `welcome` 7, `save_info` 8 (landing page by default), `staff_shortlist` 9, `settings` 10 (opened by the top-right gear; the sidebar Settings button was removed).
Sidebar: MAIN (Save Info, Club, Squads, Club Staff, Player Shortlist, Staff Shortlist), SCOUTING (Players, Staff), PLAYER REPORTS (Best Prospects, Wonderkids, Best in Position, Best by Role), STAFF REPORTS (stub). Search box: club -> Club page, player -> Players, staff -> Staff; autocomplete in `gui/search_suggest.py`.

**Settings keys** (`fm_editor/settings.py::DEFAULTS`): `default_save_dir`, `role_weights_preset` ('FMScout Community'), `landing_page` ('save_info'; also 'club', 'players'), `show_pending` (True), `use_cache` (True), `ability_display` ('stars' | 'numbers'), `player_theme` ('steel'; also pitch, floodlit, plain), `trait_threshold` (11, range 1-20). `FMBR24_CONFIG_DIR` overrides the config dir.

**Parse and cache.** Load goes through `ParseWorker`; with `use_cache` on, `load_cache` is used on a normal Load and **Reload always re-parses** (`_reload_save(use_cache=...)`). The cache is keyed by path + mtime_ns + size and is cleared after a successful save. Reported timings from session 17 (not re-timed for this document): full parse about 15 s (numpy / `bytes.find` prefilters in people, abilities, identities, squads; golden fingerprint unchanged), cached load about 2 s. Bump `_CACHE_VERSION` whenever a parsed field is added or changes; `tests/test_cache_use.py` and `test_parse_golden.py` cover this.
Pitfalls that stay true: no `ResizeToContents`, no `processEvents()` mid-populate, QSS has no `opacity`/`letter-spacing` (see CLAUDE.md).

## 4. Save and patch system (HGP / HGC)

HGP = secondary-nation record `b10=0x08,b11=0x46`; HGC = training record `b10=0x01,b11=0x48`, bytes 0-3 = club entity id = club id + 1 (`MainWindow._entity_of`, `patch.find_club_entity_id`). Record layouts: memory `fm24-binary-format.md`.

**Queue flow (nothing patches game_db in memory):**
1. Controls: the **HGP / HGC pills in the player window header** (queue / un-queue via `queue_toggle`), plus the Squads toolbar `Make HGP` / `Make HGC` buttons (`_queue_selected`, bulk queue, still present in the Squads toolbar). Pills only act for players whose club is human-managed (`save_data['human_clubs']` from `humans.dat`), from any page; other players get a display-only pill ('Not your club' / 'Open from Squads to patch').
2. Queue = `MainWindow._queue`, dict `(person id, 'hgp'|'hgc') -> person`. `_queue_changed` sets `_dirty`, status text, sidebar 'Unsaved changes', enables Save and refreshes badges and the open player window (`refresh_queue`). Cleared by Load/Reload/`_finish_load` and after a successful save.
3. **Save Changes** (`_do_save`): the Save button first shows ONE confirm dialog (backup plan; skipped on the close/load-another paths, `confirm=False`). Then `_apply_queue_copy` runs `fm_editor.patch.apply_queue` on a COPY of the buffer: all HGP that have a 0x46 record in place, then the inserts (HGC record; plus a new England 0x46 record for a person with NO 0x46 at all, e.g. a foreign signing) for persons sorted by record offset **descending** (a 16-byte insert only shifts later bytes); only the missing part is added. `SaveWorker` -> `savefile.save_in_place`: writes `<save>.fm.tmp`, re-opens it and verifies (member list, sha256 of every unmodified member, decompressed `game_db.dat` equals the patched buffer), makes backups, then `os.replace`. Any failure leaves the original file, the in-memory buffer and the queue untouched.
4. After success `_on_save_done` clears the queue and **reloads automatically** (`_reload_save()`, no dialog; skipped when a close/load-another is pending). **Reload (auto after save, and the Reload button) restores the UI:** `_reload_save` takes `_capture_ui_state()` (view, club id + squad tab, search text, filter widgets, Players search subset by person ids, sort, top-visible row / selection by person id, Back/Forward history by club id) and `_finish_load` calls `_apply_ui_state()` instead of `_land_after_load()`; a different file, a missing club or the Settings page falls back to the landing page. Test `test_reload_restore.py`. Not restored: the open player window, queued changes (cleared as before), pixel scroll offset (top row id instead). Status bar: 'Saved ... HGP x, HGC y'. The old 'Make both' action and the 'stale offsets, save and reload first' prompt no longer exist.
- Backups: `<save>.fm.bk1` = file as it was just before this save, `.bk2` = previous bk1; first save makes both copies of the original. Names end in `.bk1/.bk2` so FM24's Load Game list ignores them. Space check 3x file size on first save, else 2x (+16 MB). Save is refused if the file changed on disk since load (`save_data['disk_sig']`). Dirty guards: Reload asks 'Discard unsaved changes?'; Load another save and window close ask Save / Discard / Cancel.
- **List badges:** `_HGBadgeDelegate` draws HGP/HGC pills in Squads (HGP+HGC), Reports and Players (HGP only; Shortlists have no HG column); queued = yellow `+ HGP`; `_RowMarkDelegate` (`ROWQ_ROLE`) tints queued rows and draws a yellow bar on the Name cell; `PeopleModel.set_queue` repaints only affected rows; `_refresh_queue_marks` drives all of it.
- Tests: `test_patch_queue.py` (apply order/offsets, queue model, save on a synthetic archive, failure injection leaves the file byte-identical, pill states, strip = Add to Shortlist + Close), `test_savefile.py`, `test_hg_badges.py`, `test_human_clubs.py`.
- **Not verified in game:** that FM24 loads a save whose HGC insert changed the file size (our own re-parse reads it back correctly, a 16-byte insert was tested on a copy of the real save); that any changed patch bytes behave in game. The HGP patch may flip `0x40` -> `0x47` records; 2,460/2,460 `0x40` records were checked not to be read as injuries (memory note 'HGP 0x40->0x47 flip vs injuries'), but in-game verification of changed patch bytes is still needed.

## 5. Player window (`gui/player_window.py`, mockup `mockups/player-window.html`)

`PlayerWindow(QDialog)`, 1122x760 (min 1062x640), opened by double-click from any list through `MainWindow._run_player_window`. Always opens on Profile.
- **Header** (persistent, `QFrame#pwHeader`, `ThemedFrame('header')`): identity + HGP/HGC pills (variant A 'calm'), then four boxes on one grid (`_HG_*`: 56 high; boxes 136 wide, queue widget 160): CURRENT ABILITY, POTENTIAL ABILITY, DEVELOPMENT RATE, and the **CHANGES QUEUED** widget. CA/PA/Dev Rate show stars or number + bar per `ability_display` (raw number kept in the tooltip; mapping in `fm_editor/abilitystars.py`: CA/PA = value/40, Dev Rate = value/4, nearest half star rounded half up (`half_stars`, also used by `rep_stars`), clamp 0.5..5, one place to tune).
- **Tabs** (`TABS`, left strip, `ActiveTabButton`): Profile, Contract & Transfer, Positions, General Rating (placeholder), Role Rating (placeholder), Training (Recommended traits panel + a 'Coming soon' block), History. Add a real tab = write `_page_<key>` and name it in `TABS`; `None` = 'Coming soon' text from `SOON`.
- **Action strip** (`ThemedFrame('bar')`, `#actionStrip`): `Add to Shortlist` + `Close` (Close last). No Make buttons.
- **Profile layout C**: cards Position | This season (or Career) | Fitness; attribute grid (follows the `Current | Full Potential` toggle) with the right column radar over Footedness; Personality (7 mini bars) + Player traits.
- **Six-axis radar**: one table `RADAR_OUT` / `RADAR_GK` in `gui/pw_widgets.py` (axis, attributes, lower-is-better names; axis = mean, Injury Prone / Dirtiness / Eccentricity inverted as 21-v). Outfield axes: Attacking, Creativity, Athleticism, Defending, Reliability, Mentality; GK: Shot-stopping, Command, Athleticism, Distribution, Reliability, Mentality. These are the app's own scouting groups, not the game's Technical/Mental/Physical. `RadarWidget` has per-axis tooltips; `FeetWidget` draws the two soles (`foot_rgb`). Test `test_radar_axes.py`.
- **Themes** (`gui/pw_themes.py`): registry `THEMES` = steel (default), pitch, floodlit, plain; settings key `player_theme`, Settings > Interface dropdown. `STEEL_ALPHA = 0.75` scales every translucent Steel layer (mirrors the mockup). Add a theme = registry entry + the `PLAYER_THEMES` tuple in `fm_editor/settings.py` (`test_themes.py` enforces both).
- **Data fed to the window**: `player_extra_data` (wage, value, height/weight, traits), `fm_editor/history.py::career_for_person` (needs the FM install DB; PENDING chip when absent), Full Potential via `potential.project_attrs` (toggle always selectable (session-17 decision), tooltip note when PA <= CA or age >= 30 (`potential.availability` is advisory)). Ages: exact from birth year + day (`agecalc`), reference date = the save's in-game date.
- Known layout items: Profile scrolls about 136 px at the default size (user: ignore for now); GK profile has a gap under the Goalkeeping column.

## 6. Data and binary pointers

All byte-level facts live in memory `fm24-binary-format.md` (read it before touching a parser). Index: s1 player record, s2 linked records, s3 staff, s4 Save Info, s5 club record, s6 finances, s7 season stats, s8 squad arrays, s9 traits, s10 reputation/stadium/league table/scouting budget, s11 height/weight/wage (a second '11' is career history), s12 contract block + wage, s13 injuries + transfer value. Dead ends and open decodes are listed there too (Save Info: start nation, database size, future transfer mode, editor allowed/used, manageable teams need a second save with known different settings).
Not in the save at all (checked): club Region/Founded/Facilities, contract bonuses and clauses, player photos, staff reputation.

## 7. Verified vs unverified

**Verified against in-game screens** (user ground truth): Save Info fields; squad membership (Spurs = 25 in-game names); club finances (Spurs); season stats; ages; club reputation/stadium/league table positions (snapshot 2 Jan 2028); height/weight, contract end/start and weekly wage (18 players, cache v26); injuries and transfer value (u32 at attributes+54, 16/16, cache v27/v28); 56 of 64 trait bits (A grade); History vs real careers.

**Unverified or partial - do not present as fact:**
- FM24 loading a saved file that contains an HGC insert (section 4).
- Trait bit 48 unknown (guess: Attempts To Develop Weaker Foot; holders such as Philip Andersson, Michalis Michail not scouted yet). Bit 53 = flag carried only by staff/non-players. Bits 49, 61, 62 are set in the save but never shown by the game (hidden in the UI).
- Foot words (`foot_word`: Weak 7-8, Reasonable 9-11, Fairly Strong 12-14, Strong 15-19, Very Strong 20): Strong at 17-19 vs Very Strong and the Very Weak range are unconfirmed.
- Position familiarity words (Natural / Accomplished / Competent / Unconvincing / Awkward / Ineffective) number ranges: need an in-game hover screenshot.
- Club reputation stars: `rep_stars` = rep/2000 to the nearest half star (half up), 5 stars from 9125; fitted to about 9 clubs; the 9125 boundary is a midpoint (9053 = 4.5, 9197 = 5), not decoded.
- Weekly wage: the stored u32 is within 2% of the in-game figure (18/18); the display rounding steps are inferred (the 50K step above 300K rests on one player); a few outliers (Saliba 1.46M, Sancet 964K) are unchecked. `find_contracts` / 'Until' from the old `b11=0x6a` record is wrong for current saves and unused; the app reads `find_contract_blocks`.
- Asking price and transfer/loan status are not found in the save (market value is stored; the game shows a range around it); those rows stay PENDING.
- General Rating and Role Rating tabs: need in-game screens from the user (Role Rating could mirror the in-game 'Role and Duty' list).
- Personality: the player window shows 7 bars (Adaptability .. Temperament). The save has an 8th byte, `personality[7]` = 'Controversy' (parsed; the Staff popup shows it). Whether Controversy is a hidden attribute the game does not display is unknown: check the bytes against a player screen before adding it.
- History: seasons simulated inside the save (2025-28) are not shown; plain-year season labels for calendar-year leagues are an assumption; needs the FM install DB.
- Dev Rate and CA/PA star mappings are approximations of FM's relative stars.
- 'One player would not set homegrown' (FIXED, merged into main, **verified in game 2026-10-01**: Montoro queued HGP, saved, game shows both tags): the old HGP patch only rewrote an EXISTING 0x46 record, so a player with none (55k of 128k; e.g. Alvaro Montoro) was a silent no-op ('needed no edit'). Now a 0x46 England record is inserted. Open: the HGP/HGC patches still REWRITE a player's existing 0x46 / 0x48 records (losing e.g. other-nation or previous-club records); decision 2026-10-01: leave (works in game). A player with no club shows no HGC pill (club unknown).
- Loading state: while a SAVE or a RELOAD runs (not on a first load: the Welcome page has its own), `_set_busy` disables `_main_stack` and shows `_BusyVeil` (dim, click-blocking layer, `ALPHA` 140) with a centred "Saving" / "Reloading" label and bouncing dots (`_DOT_SEQ`). Test `tests/test_busy_veil.py`.

## 8. Open TODOs (priority order)

1. **Merge** the review branches (`fix/review-safety`, `fix/review-misc`) into `main`, then delete the leftover branches/worktrees listed in section 2 once the user agrees. Optionally push; the user decides.
   Open review items not done in `fix/review-misc`: club-header reputation stars have no numbers mode / tests (5a), `SettingsPage` has no tests (5b), unsupported-QSS properties (`letter-spacing`, `text-transform`, e.g. `_CLUB_PENDING_QSS` in `gui/main_window.py`, theme.py) are pre-existing and ignored by Qt.
2. Ask the user for the in-game evidence that closes the section 7 items: trait bit 48 screenshot, reputation stars for more clubs, foot word at 17-19, position-word hover screenshot, General/Role Rating screens, Controversy check.
3. **Reports / Players HGC column** (Reports and Players lists show HGP only).
4. **Staff window redesign** (parked; `StaffDetailDialog` still the old layout, no mockup yet).
5. Fill the Training tab (only Recommended traits exist) and the General/Role Rating tabs once screens exist.
6. **GitHub polish** at 1.0 (description, topics, social preview), then **Flatpak** (app id e.g. `io.github.acidtwin.FMBR24`) and **Windows** builds (Steam/save path handling). Bundle Barlow Condensed (not installed, falls back to Noto Sans).
7. Small items: Staff Reports (sidebar stub); more Staff / Club Staff filters; FM23 save support in `archive.py`; weight the Full Potential growth shares by CA weight (low-relevance attributes grow slightly); update `CLAUDE.md` Run section (add numpy, list the current test files).

Full history, per-session notes, mockup geometry and old branch map: `docs/HANDOVER-archive.md`.
